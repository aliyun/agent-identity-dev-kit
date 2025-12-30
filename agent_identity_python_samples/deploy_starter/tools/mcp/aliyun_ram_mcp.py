from agent_identity_python_sdk.core import requires_access_token
from agentscope.mcp import HttpStatelessClient
from agentscope.tool import Toolkit

from ..context.config import get_config_with_default
from ..context.context import AgentContext


async def on_auth(url: str):
    await AgentContext.on_auth_url(url, "Alibaba cloud MCP Service (Authorization is required for the first conversation to obtain the MCP tool list. The authorized tools may not be related to this conversation.)")

@requires_access_token(
    credential_provider_name="test-provider-for-mcp-oauth",
    scopes=["profile", "openid", "aliuid", "/acs/mcp-server"],
    auth_flow="USER_FEDERATION",
    on_auth_url=on_auth,
    # force_authentication=True,  # When forced authentication is enabled, a new authorization link will be returned every time an access token is obtained
    callback_url=f'{get_config_with_default("APP_REDIRECT_URI", "http://localhost:8090")}/callback',
    custom_parameters={"param1": "test-param", "param2": "test-param2"},
)
async def register_aliyun_mcp(toolkit: Toolkit, access_token: str):
    if not access_token:
        raise Exception("Access token is required")

    stateless_client: HttpStatelessClient = HttpStatelessClient(
        name="mcp_services_stateless",
        transport="streamable_http",
        url=get_config_with_default('MCP_SERVER', ''),
        headers={
            "Authorization": "Bearer " + access_token,
        },
    )
    await toolkit.register_mcp_client(stateless_client)

