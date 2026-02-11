import asyncio

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
    queue = asyncio.Queue()
    AgentContext.queue_context.set(queue)

    toolkit.register_tool_function(weather_search)
    toolkit.register_tool_function(get_current_time)
    toolkit.register_tool_function(get_schedule)
    toolkit.register_tool_function(get_oss_object)
    toolkit.register_tool_function(ding_talk_tool)

    agent = ReActAgent(
        name="Friday",
        model=DashScopeChatModel(
            model_name=get_config_with_default("DASHSCOPE_MODEL_NAME", "qwen3-max"),
            api_key=get_config_with_default("DASHSCOPE_API_KEY", ""),
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

    
    # Register mcp and invoke agent, when enable ai gateway authorization
    async def register_mcp_and_invoke():
        await register_aliyun_mcp(toolkit=toolkit)
        #await register_apig_mcp(toolkit=toolkit)
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

