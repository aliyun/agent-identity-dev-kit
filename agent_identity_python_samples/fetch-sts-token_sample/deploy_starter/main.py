import os
from typing import Optional

from agent_identity_python_sdk import AgentIdentityContext
from agent_identity_python_sdk.core import IdentityClient
from agent_identity_python_sdk.core.decorators import get_region, requires_sts_token
from agent_identity_python_sdk.model import STSCredential
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg, TextBlock
from agentscope.pipeline import stream_printing_messages
from agentscope.tool import ToolResponse
from agentscope_runtime.adapters.agentscope.memory import AgentScopeSessionHistoryMemory
from agentscope_runtime.engine.services.agent_state import InMemoryStateService
from agentscope_runtime.engine.services.session_history import InMemorySessionHistoryService
from agentscope_runtime.engine import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from agentscope.model import DashScopeChatModel


from alibabacloud_vpc20160428.client import Client as Vpc20160428Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_vpc20160428 import models as vpc_20160428_models

agent_app = AgentApp(
    app_name="Friday",
    app_description="A helpful assistant",
)

@agent_app.init
async def init_func(self):
    self.state_service = InMemoryStateService()
    self.session_service = InMemorySessionHistoryService()

    await self.state_service.start()
    await self.session_service.start()

@agent_app.shutdown
async def shutdown_func(self):
    await self.state_service.stop()
    await self.session_service.stop()

async def call_agent(agent: ReActAgent, msgs: list[Msg]):
    await agent(msgs)


identity_client = IdentityClient(region_id=get_region())

@agent_app.endpoint("/", methods=["GET"])
def read_root():
    return {"hi agentDev"}

@agent_app.endpoint("/health", methods=["GET"])
def health_check():
    return "OK"

@requires_sts_token(
    inject_param_name="sts_credential"
)
def create_vpc(name: str, region_id: str = "cn-hangzhou", cidr_block: str = "192.168.0.0/16", sts_credential: Optional[STSCredential] = None) -> ToolResponse:
    config = open_api_models.Config(
        access_key_id=sts_credential.access_key_id,
        access_key_secret=sts_credential.access_key_secret,
        security_token=sts_credential.security_token,
    )
    # Endpoint 请参考 https://api.aliyun.com/product/Ecs
    config.endpoint = f'vpc.{region_id}.aliyuncs.com'
    client = Vpc20160428Client(config)
    request = vpc_20160428_models.CreateVpcRequest(
        region_id=region_id,
        cidr_block=cidr_block,
        vpc_name=name,
        description='This is a test VPC.'
    )
    response = client.create_vpc(request)
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"VPC ID: {response.body.vpc_id}",
            ),
        ],
    )


def create_vpc_with_name(name: str, region_id: str, cidr_block: str):
    return create_vpc(name=name, region_id=region_id, cidr_block=cidr_block)


@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest = None,
    **kwargs,
):
    session_id = request.session_id
    user_id = request.user_id

    AgentIdentityContext.set_user_id(user_id)

    state = await self.state_service.export_state(
        session_id=session_id,
        user_id=user_id,
    )

    agent = ReActAgent(
        name="Friday",
        model=DashScopeChatModel(
            "qwen-turbo",
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            enable_thinking=True,
            stream=True,
        ),
        sys_prompt="You're a helpful assistant named Friday.",
        memory=AgentScopeSessionHistoryMemory(
            service=self.session_service,
            session_id=session_id,
            user_id=user_id,
        ),
        formatter=DashScopeChatFormatter(),
    )

    agent.toolkit.register_tool_function(create_vpc_with_name)

    if state:
        agent.load_state_dict(state)

    async for msg, last in stream_printing_messages(
            agents=[agent],
            coroutine_task=agent(msgs),
    ):
        yield msg, last

    await self.state_service.save_state(
        user_id=user_id,
        session_id=session_id,
        state=agent.state_dict(),
    )

agent_app.run(host="0.0.0.0", port=8080)

