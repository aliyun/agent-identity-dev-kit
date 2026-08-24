"""LangChain Agent 服务器（AgentRun Runtime 入口）。

环境变量：
    MODEL_SERVICE_NAME / MODEL_NAME  AgentRun 模型服务名与模型名
    TOOL_NAME                         托管 MCP 工具名（逗号分隔可加载多个）
    ENABLE_*                          四个本地演示工具的开关

本地测试：
    python3 main.py 启动后访问
    curl 127.0.0.1:9000/openai/v1/chat/completions -XPOST \
        -H "content-type: application/json" \
        -d '{"messages":[{"role":"user","content":"你有什么工具？"}]}'
"""

import contextvars
import os
import threading
from queue import Empty, Queue
from typing import Any

import pydash
from langchain.agents import create_agent

from agentrun.integration.builtin import tool_resource
from agentrun.integration.langchain import AgentRunConverter, model
from agentrun.server import AgentRequest, AgentRunServer
from agentrun.utils.config import Config
from agentrun.utils.log import logger
from mcp.shared.exceptions import McpError, UrlElicitationRequiredError

from context import AgentContext

MODEL_NAME = os.getenv("MODEL_NAME", "qwen-plus")
MODEL_SERVICE_NAME = os.getenv("MODEL_SERVICE_NAME", "aliyun")
TOOL_NAME = os.getenv("TOOL_NAME", "test-remote-mcp")

config = Config()

# 可选本地工具，通过环境变量开关挂载
LOCAL_TOOLS = []
if os.getenv("ENABLE_WEATHER_TOOL") == "1":
    from weather_search import weather_search

    LOCAL_TOOLS.append(weather_search)
if os.getenv("ENABLE_OSS_TOOL") == "1":
    from read_oss_file import get_object_from_oss

    LOCAL_TOOLS.append(get_object_from_oss)
if os.getenv("ENABLE_TIME_TOOL") == "1":
    from get_current_time import get_current_time

    LOCAL_TOOLS.append(get_current_time)
if os.getenv("ENABLE_SCHEDULE_TOOL") == "1":
    from get_schedule import get_schedule

    LOCAL_TOOLS.append(get_schedule)


class _AuthNeeded(Exception):
    """内部信号：工具需要 OAuth2 授权，携带授权链接。"""

    def __init__(self, url: str):
        super().__init__(url)
        self.url = url


def _extract_auth_url(exc: BaseException) -> Any:
    """从异常链（含 ExceptionGroup/TaskGroup 嵌套）中提取 OAuth2 授权链接。

    公开版 SDK 不会把 Hook 的 elicitation 响应转成 UrlElicitationRequiredError，
    而是抛 McpError（授权链接在 error.data.elicitations 里），需手动解包。
    """
    if isinstance(exc, McpError):
        data = getattr(exc.error, "data", None) or {}
        for el in data.get("elicitations") or []:
            url = el.get("url") if isinstance(el, dict) else getattr(el, "url", None)
            if url:
                return url
        return None
    for sub in getattr(exc, "exceptions", None) or []:
        url = _extract_auth_url(sub)
        if url:
            return url
    return None


def _get_tools(workload_token: Any = None):
    # 手动传递 WAT：不依赖 SDK 自动转发（公开版 SDK 无此机制），
    # 从入站请求头取出 X-Workload-Access-Token，显式塞进工具调用配置
    cfg = config
    if workload_token:
        cfg = Config(headers={"X-Workload-Access-Token": workload_token})
    # TOOL_NAME 支持逗号分隔多个托管 MCP 工具，逐个加载后合并
    mcp_tools = []
    for name in [n.strip() for n in TOOL_NAME.split(",") if n.strip()]:
        try:
            tr = tool_resource(name, config=cfg)
            tool_list = tr.tools()
            print(f"\n[Load] {name}: loaded {len(tool_list)} tools")
            mcp_tools.extend(tr.to_langchain())
        except Exception as e:
            # 优先识别授权需求（Token 过期/首次使用），把授权链接直接回给用户
            auth_url = _extract_auth_url(e)
            if auth_url:
                logger.info(f"[OAuth] {name} 需要授权: {auth_url}")
                raise _AuthNeeded(auth_url) from e
            # 拆开嵌套异常组，取最内层真实错误后再抛出
            detail = e
            while getattr(detail, "exceptions", None):
                detail = detail.exceptions[0]
            raise RuntimeError(f"加载工具 {name} 失败：{type(detail).__name__}: {detail}") from e
    return [*mcp_tools, *LOCAL_TOOLS]


def invoke_agent(request: AgentRequest):
    try:
        workload_token = None
        if request.raw_request is not None:
            workload_token = request.raw_request.headers.get("X-Workload-Access-Token")
        if workload_token:
            # 同时把 WAT 放进 Agent Identity SDK 上下文，
            # 本地工具的 @requires_* 注解取凭据时要用它换发。
            # ContextVar 在线程切换时会丢（langchain 执行上下文不定），
            # 环境变量兜底保证任意线程可见（SDK 读取顺序：ContextVar → env）
            from agent_identity_python_sdk.context import AgentIdentityContext

            AgentIdentityContext.set_workload_access_token(workload_token)
            os.environ["AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN"] = workload_token
        tools = _get_tools(workload_token)
    except _AuthNeeded as e:
        return f"需要授权后才能使用工具，请前往以下链接完成授权：\n{e.url}"
    except UrlElicitationRequiredError as e:
        urls = [el.url for el in e.elicitations]
        logger.info(f"[OAuth] 需要授权: {urls[0] if urls else 'unknown'}")
        auth_url = urls[0] if urls else "unknown"
        return f"需要授权后才能使用工具，请前往以下链接完成授权：\n{auth_url}"
    except Exception as e:
        auth_url = _extract_auth_url(e)
        if auth_url:
            logger.info(f"[OAuth] 需要授权: {auth_url}")
            return f"需要授权后才能使用工具，请前往以下链接完成授权：\n{auth_url}"
        logger.error(f"[Load] 加载工具异常: {e.args}")
        return f"加载工具失败：{e.args}"

    agent = create_agent(
        model=model(MODEL_SERVICE_NAME, model=MODEL_NAME),
        tools=list(tools),
        system_prompt="你是一个 AI 助手。",
    )

    input_data: Any = {
        "messages": [
            {"content": msg.content, "role": msg.role}
            for msg in request.messages
        ]
    }
    converter = AgentRunConverter()
    try:
        if request.stream:

            async def stream_generator():
                result = agent.astream_events(input_data)
                async for chunk in result:
                    for item in converter.convert(chunk):
                        yield item

            return stream_generator()
        else:
            # 接上授权链接通道：本地工具触发授权时，SDK 通过 on_auth_url 把链接
            # 放进队列（见 context.py），这里值守队列——链接一到就先回给用户，
            # 后台线程继续轮询取 Token；用户授权后凭据落库，下次调用即可用
            auth_queue: Queue = Queue()
            AgentContext.queue_context.set(auth_queue)
            result_box: dict = {}

            def _run():
                try:
                    result_box["result"] = agent.invoke(input_data)
                except Exception as exc:
                    result_box["error"] = exc

            ctx = contextvars.copy_context()
            t = threading.Thread(target=lambda: ctx.run(_run), daemon=True)
            t.start()
            while t.is_alive():
                try:
                    auth_msg = auth_queue.get(timeout=0.5)
                    logger.info(f"[OAuth] 需要授权: {auth_msg.strip()}")
                    return f"需要授权后才能使用工具，请前往以下链接完成授权（完成后再次提问即可）：\n{auth_msg.strip()}"
                except Empty:
                    continue
            if "error" in result_box:
                raise result_box["error"]
            return pydash.get(result_box["result"], "messages.-1.content")
    except UrlElicitationRequiredError as e:
        urls = [el.url for el in e.elicitations]
        logger.info(f"[OAuth] 需要授权: {urls[0] if urls else 'unknown'}")
        auth_url = urls[0] if urls else "unknown"
        return f"需要授权后才能使用工具，请前往以下链接完成授权：\n{auth_url}"
    except Exception as e:
        auth_url = _extract_auth_url(e)
        if auth_url:
            logger.info(f"[OAuth] 需要授权: {auth_url}")
            return f"需要授权后才能使用工具，请前往以下链接完成授权：\n{auth_url}"
        logger.error(f"[Load] 加载工具异常: {e}")
        return f"加载工具失败：{e}"


if __name__ == "__main__":
    print("=" * 60)
    print("AgentRun Server - LangChain")
    print(f"  MODEL = {MODEL_SERVICE_NAME}/{MODEL_NAME}")
    print(f"  TOOL  = {TOOL_NAME}")
    print("=" * 60)
    AgentRunServer(invoke_agent=invoke_agent).start()
