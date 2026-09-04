import asyncio

from agent_identity_python_sdk.core import requires_access_token
from agentscope.message import TextBlock, Msg
from agentscope.tool import ToolResponse

from .context.config import get_config_with_default
from .context.context import AgentContext


async def on_auth(url: str):
    await AgentContext.on_auth_url(url, "Get system time")

@requires_access_token(
    credential_provider_name="test-provider-for-mcp-oauth",
    scopes=["profile", "openid", "aliuid", "/acs/mcp-server"],
    auth_flow="USER_FEDERATION",
    on_auth_url= on_auth,
    # force_authentication=True,  # When forced authentication is enabled, a new authorization link will be returned every time an access token is obtained
    callback_url=f"{get_config_with_default('APP_REDIRECT_URI', 'http://localhost:8090')}/callback",
    inject_param_name="access_token",
)
async def get_current_time(access_token: str) -> ToolResponse:
    """Get current timestamp
    
    Args:

        access_token (str): The access token for authentication, which will be automatically obtained and injected by Agent Identity, no manual input required
        
    Returns:
        ToolResponse: A ToolResponse object containing the current timestamp in format 'YYYY-MM-DD HH:MM:SS UTC'
        
    Raises:
        Exception: If access_token is empty or None
    """
    from datetime import datetime
    if not access_token:
        raise Exception("Access token is required")
    return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                ),
            ],
        )
