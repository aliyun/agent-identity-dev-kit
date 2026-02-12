from agent_identity_python_sdk import requires_workload_access_token
from agentscope.mcp import HttpStatelessClient
from agentscope.tool import Toolkit

from ..context.config import get_config_with_default
from ..context.context import AgentContext


async def on_auth(url: str):
    await AgentContext.on_auth_url(url, "Alibaba cloud MCP Service (Authorization is required for the first conversation to obtain the MCP tool list. The authorized tools may not be related to this conversation.)")

@requires_workload_access_token(
    inject_param_name="workload_accesstoken",
)
async def register_apig_mcp(toolkit: Toolkit, workload_accesstoken: str):
    if not workload_accesstoken:
        raise Exception("Workload access token is required")
    stateless_client: HttpStatelessClient = HttpStatelessClient(
        name="mcp_services_stateless",
        transport="sse",
        url=get_config_with_default('DEMO_MCP_SERVER', ''),
        headers={
            "Authorization": workload_accesstoken,
        },
    )
    await toolkit.register_mcp_client(stateless_client)

