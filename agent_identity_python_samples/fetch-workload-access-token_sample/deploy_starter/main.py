import os
from typing import Optional

from agent_identity_python_sdk import AgentIdentityContext
from agent_identity_python_sdk.core import IdentityClient
from agent_identity_python_sdk.core.decorators import get_region, requires_workload_access_token
from agentscope.agent import ReActAgent
from agentscope.mcp import HttpStatelessClient
from agentscope.tool import Toolkit
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
user_token_map = {}

identity_client = IdentityClient(region_id=get_region())

@agent_app.endpoint("/", methods=["GET"])
def read_root():
    return {"hi agentDev"}

@agent_app.endpoint("/health", methods=["GET"])
def health_check():
    return "OK"


@requires_workload_access_token(
    inject_param_name="workload_accesstoken",
)
async def register_demo_mcp(toolkit: Toolkit, workload_accesstoken: str):
    """Use workload access token to invoke api gateway mcp service.

    """
    if not workload_accesstoken:
        raise Exception("Workload access token is required")
    
    stateless_client: HttpStatelessClient = HttpStatelessClient(
        name="mcp_services_stateless",
        transport="sse",
        url=os.getenv("AI_GATEWAY_MCP_SERVER", ""),
        headers={
            "Authorization": workload_accesstoken,
        },
    )
    await toolkit.register_mcp_client(stateless_client)

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
    AgentIdentityContext.set_user_token(user_id)
    AgentIdentityContext.set_custom_state(session_id)

    state = await self.state_service.export_state(
        session_id=session_id,
        user_id=user_id,
    )
    user_token_map[session_id] = user_id

    toolkit = Toolkit()
    mcp_client = None
    
    try:
        mcp_client = await register_demo_mcp(toolkit=toolkit)

        agent = ReActAgent(
            name="Friday",
            model=DashScopeChatModel(
                "qwen-max",
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
            toolkit=toolkit
        )

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

    except Exception as e:
        print(f"Error in query_func: {e}")
        raise e
    finally:        
        # 清理上下文
        AgentIdentityContext.clear()

agent_app.run(host="0.0.0.0", port=8080)

