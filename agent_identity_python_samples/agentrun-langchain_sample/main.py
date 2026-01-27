import asyncio
from typing import Any

from langchain.agents import create_agent
import pydash
import os

from agentrun.integration.langchain import model, sandbox_toolset, AgentRunConverter
from agentrun.sandbox import TemplateType
from agentrun.server import AgentRequest, AgentRunServer
from agentrun.utils.log import logger

from agent_identity_python_sdk import requires_access_token, AgentIdentityContext

from context import AgentContext
from ding_talk_tool import write_dingtalk_file
from read_oss_file import get_object_from_oss

# 请替换为您已经创建的 模型 和 沙箱 名称
MODEL_NAME = os.getenv("MODEL_NAME")
MODEL_SERVICE_NAME = os.getenv("MODEL_SERVICE_NAME")
SANDBOX_NAME = os.getenv("SANDBOX_NAME")

if not MODEL_SERVICE_NAME:
    raise ValueError("请将 MODEL_NAME 替换为您已经创建的模型名称")

code_interpreter_tools = []
if SANDBOX_NAME and not SANDBOX_NAME.startswith("<"):
    code_interpreter_tools = sandbox_toolset(
        template_name=SANDBOX_NAME,
        template_type=TemplateType.CODE_INTERPRETER,
        sandbox_idle_timeout_seconds=300,
    )
else:
    logger.warning("SANDBOX_NAME 未设置或未替换，跳过加载沙箱工具。")

@requires_access_token(
    credential_provider_name="test-provider-for-mcp-oauth",
    scopes=["profile", "openid", "aliuid", "/acs/mcp-server"],
    auth_flow="USER_FEDERATION",
    on_auth_url= lambda url: AgentContext.on_auth_url(url, "Tool"),
    force_authentication=True,  # When forced authentication is enabled, a new authorization link will be returned every time an access token is obtained
    callback_url="http://localhost:8090",
    inject_param_name="access_token",
)
def get_access_token(access_token: str) :
    print(access_token)
    return access_token

def list_ram_users():
    """
    list ram users with access token.

    Returns: ram users' name

    """
    get_access_token()
    return "alice,bob"

agent = create_agent(
    model=model(MODEL_SERVICE_NAME, model=MODEL_NAME),
    tools=[*code_interpreter_tools, list_ram_users, write_dingtalk_file, get_object_from_oss],
    system_prompt="你是一个 AgentRun 的 AI 专家，可以通过沙箱运行代码来回答用户的问题。",
)

async def collect_from_stream(stream, queue):
    try:
        async for msg in stream:
            await queue.put(msg)
        await queue.put('[END]')
    except Exception:
        await queue.put('[END]')

def invoke_agent(request: AgentRequest):
    bearer_token = request.raw_request.headers.get("Authorization")[7:]
    input: Any = {"messages": [{"content": message.content, "role": message.role} for message in request.messages]}
    converter = AgentRunConverter()

    queue = asyncio.Queue()

    try:
        if request.stream:

            async def stream_generator():
                AgentContext.queue_context.set(queue)
                AgentIdentityContext.set_user_token(bearer_token)
                result = agent.astream_events(input)
                async for chunk in result:
                    print(chunk)
                    for item in converter.convert(chunk):
                        yield item

            async def mix_generator():
                stream = stream_generator()

                asyncio.create_task(collect_from_stream(stream, queue))

                while True:
                    msg = await queue.get()
                    print(msg)
                    if isinstance(msg, str) and (msg == '[END]'):
                        break
                    yield msg

            return mix_generator()
        else:
            result = agent.invoke(input)
            return pydash.get(result, "messages.-1.content")
    except Exception as e:
        import traceback

        traceback.print_exc()
        logger.error("调用出错: %s", e)
        raise e
    finally:
        AgentIdentityContext.clear()


AgentRunServer(invoke_agent=invoke_agent).start()
"""
curl 127.0.0.1:9000/openai/v1/chat/completions -XPOST \
    -H "content-type: application/json" \
    -d '{
        "messages": [{"role": "user", "content": "写一段代码,查询现在是几点?"}], 
        "stream":true
    }'

curl 127.0.0.1:9000/ag-ui/agent -XPOST \
    -H "content-type: application/json" \
    -d '{
        "messages": [{"role": "user", "content": "写一段代码,查询现在是几点?"}]
    }'
"""
