from agent_identity_python_sdk import requires_workload_access_token
from agentscope.mcp import HttpStatelessClient
from agentscope.tool import Toolkit
from exceptiongroup import ExceptionGroup
import json

from ..context.config import get_config_with_default
from ..context.context import AgentContext


def _unwrap_exception(exc: BaseException) -> Exception:
    """Unwrap ExceptionGroup to extract the real cause (e.g. HTTPStatusError)."""
    if isinstance(exc, ExceptionGroup):
        for sub in exc.exceptions:
            unwrapped = _unwrap_exception(sub)
            if unwrapped is not sub:
                return unwrapped
        if exc.exceptions:
            return exc.exceptions[0]
    return exc


def _wrap_mcp_tool_with_error_handling(toolkit: Toolkit):
    """Wrap MCP tool functions in the toolkit so that ExceptionGroup errors
    are unwrapped into plain Exception, allowing Toolkit.call_tool_function
    to catch them and pass the error message to the LLM."""
    for func_name, tool_func in toolkit.tools.items():
        original_func = tool_func.original_func
        owner = getattr(original_func, '__self__', original_func)
        if owner.__class__.__name__ == 'MCPToolFunction':

            async def _wrapped_call(__orig=original_func, **kwargs):
                try:
                    return await __orig(**kwargs)
                except BaseException as e:
                    raise _unwrap_exception(e) from e

            _wrapped_call.original_func = original_func
            tool_func.original_func = _wrapped_call


@requires_workload_access_token(
    inject_param_name="workload_accesstoken",
)
async def register_apig_mcp(toolkit: Toolkit, workload_accesstoken: str):
    print(workload_accesstoken, flush=True)
    if not workload_accesstoken:
        raise Exception("Workload access token is required")
    stateless_client: HttpStatelessClient = HttpStatelessClient(
        name="mcp_services_stateless",
        transport="streamable_http",
        url=get_config_with_default('DEMO_MCP_SERVER', ''),
        headers={
            "Authorization": workload_accesstoken,
        },
    )
    try:
        raw_tools = await stateless_client.list_tools()
        raw_payload = [
            t.model_dump(mode="json") if hasattr(t, "model_dump") else str(t)
            for t in raw_tools
        ]
        print(
            "[DEBUG] DEMO_MCP_SERVER tools/list raw response: "
            f"count={len(raw_tools)}, payload={json.dumps(raw_payload, ensure_ascii=False)}",
            flush=True,
        )
    except Exception as e:
        print(f"[DEBUG] DEMO_MCP_SERVER tools/list failed: {e!r}", flush=True)
    await toolkit.register_mcp_client(stateless_client)
    _wrap_mcp_tool_with_error_handling(toolkit)

