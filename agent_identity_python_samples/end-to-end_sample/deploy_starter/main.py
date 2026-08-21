import asyncio
import logging

from agent_identity_python_sdk.core import IdentityClient
from agent_identity_python_sdk.core.decorators import get_region
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg
from agentscope.pipeline import stream_printing_messages
from agentscope.tool import Toolkit
from agentscope_runtime.adapters.agentscope.memory import AgentScopeSessionHistoryMemory
from agentscope_runtime.engine.services.agent_state import InMemoryStateService
from agentscope_runtime.engine.services.session_history import InMemorySessionHistoryService
from agentscope_runtime.engine import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from agentscope.model import DashScopeChatModel

from agent_identity_python_sdk import requires_api_key
from .tools.context.config import get_config_with_default
from .tools.context.context import AgentContext
from agent_identity_python_sdk import AgentIdentityContext

from .tools.ding_talk_tool import ding_talk_tool
from .tools.get_current_time import get_current_time
from .tools.get_schedule import get_schedule
from .tools.mcp.aliyun_ram_mcp import register_aliyun_mcp
from .tools.mcp.demo_apig_mcp import register_apig_mcp
from .tools.read_oss_file import get_oss_object
from .tools.weather_search import weather_search
from .tools.send_dingtalk_notification import send_dingtalk_notification

logger = logging.getLogger(__name__)

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

user_token_map = {}

@agent_app.endpoint("/", methods=["GET","POST"])
def read_root():
    return {"hi agentDev"}

@agent_app.endpoint("/health", methods=["GET","POST"])
def health_check():
    return "OK"

async def collect_from_stream(stream, queue):
    try:
        async for msg, last in stream:
            await queue.put((msg, last))
        await queue.put(('END', True))
    except StopAsyncIteration:
        pass

@requires_api_key(
    credential_provider_name='test-provider-api-key'
)
async def get_api_key(api_key: str):
    return api_key

@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest = None,
    **kwargs,
):
    session_id = request.session_id
    user_id = request.user_id
    id_token = getattr(request, 'id_token', None)

    # Backend sends JWT as user_id field (legacy compatibility).
    # If user_id looks like a JWT (3 parts separated by '.'), treat it as id_token.
    if not id_token and user_id and isinstance(user_id, str) and user_id.count('.') == 2:
        id_token = user_id

    # Only set user context for UF requests (when user identity is present).
    # M2M requests have no id_token — use id_token as indicator since user_id may default to session_id.
    if id_token:
        AgentIdentityContext.set_user_id(user_id)
        AgentIdentityContext.set_user_token(id_token)
        AgentIdentityContext.set_custom_state(session_id)

    state = await self.state_service.export_state(
        session_id=session_id,
        user_id=user_id,
    )
    user_token_map[session_id] = user_id

    toolkit = Toolkit()
    queue = asyncio.Queue()
    AgentContext.queue_context.set(queue)

    if id_token:
        # UF mode: all tools require user identity
        toolkit.register_tool_function(weather_search)
        toolkit.register_tool_function(get_current_time)
        toolkit.register_tool_function(get_schedule)
        toolkit.register_tool_function(get_oss_object)
        toolkit.register_tool_function(ding_talk_tool)
    else:
        # M2M mode: only DingTalk work notification (no user interaction)
        toolkit.register_tool_function(send_dingtalk_notification)

    api_key = await get_api_key()
    agent = ReActAgent(
        name="Friday",
        model=DashScopeChatModel(
            model_name=get_config_with_default("DASHSCOPE_MODEL_NAME", "qwen3-max"),
            api_key=api_key,
            stream=True,
        ),
        sys_prompt="You're a helpful assistant named Friday.",
        toolkit=toolkit,
        memory=AgentScopeSessionHistoryMemory(
            service=self.session_service,
            session_id=session_id,
            user_id=user_id,
        ),
        formatter=DashScopeChatFormatter(),
    )

    if state:
        agent.load_state_dict(state)

    agent_stream = stream_printing_messages(
        agents=[agent],
        coroutine_task=call_agent(agent, msgs),
    )

    # Register MCP tools for UF requests, then stream agent output to queue.
    # APIG MCP (AI gateway) is opt-in via DEMO_MCP_SERVER config; failures degrade gracefully.
    async def register_mcp_and_invoke():
        # MCP tools require user authorization (UF flow), skip for M2M requests
        # Use id_token as indicator: UF has JWT, M2M doesn't (user_id may default to session_id)
        if id_token:
            demo_mcp = get_config_with_default('DEMO_MCP_SERVER', '')
            try:
                await register_aliyun_mcp(toolkit=toolkit)
                # APIG MCP is optional, only register when configured
                if demo_mcp and not demo_mcp.startswith('<'):
                    await register_apig_mcp(toolkit=toolkit)
            except Exception:
                logger.exception("MCP registration failed, continuing without MCP tools")
        await collect_from_stream(agent_stream, queue)

    asyncio.create_task(register_mcp_and_invoke())

    while True:
        (msg, last) = await queue.get()
        if isinstance(msg, str) and msg == 'END':
            break
        yield msg, last

    state = agent.state_dict()

    await self.state_service.save_state(
        user_id=user_id,
        session_id=session_id,
        state=state,
    )

    # clear context
    AgentIdentityContext.clear()

agent_app.run(host="0.0.0.0", port=8080)

