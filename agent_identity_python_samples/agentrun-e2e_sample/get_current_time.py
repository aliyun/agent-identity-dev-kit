"""获取当前时间（演示 OAuth2 用户授权凭据注入）。

Access Token 由 agent-identity-python-sdk 按 USER_FEDERATION 流程获取并注入；
首次使用会产出授权链接，用户在浏览器完成授权后再次调用即可。

结构说明：装饰器作用于内部实现 _get_current_time，外层 wrapper 提供干净的
工具签名（隐藏被注入的 access_token 参数）。
"""
from agent_identity_python_sdk.core import requires_access_token

from context import AgentContext


def on_auth(url: str):
    AgentContext.on_auth_url(url, "Get system time")


@requires_access_token(
    credential_provider_name="test-provider-for-mcp-oauth",
    scopes=["profile", "openid", "aliuid"],
    auth_flow="USER_FEDERATION",
    on_auth_url=on_auth,
    # force_authentication=True,  # 开启后每次获取 access token 都会返回新的授权链接
    inject_param_name="access_token",
)
def _get_current_time(access_token: str) -> str:
    from datetime import datetime

    if not access_token:
        raise Exception("Access token is required")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")


def get_current_time() -> str:
    """Get current timestamp."""
    return _get_current_time()
