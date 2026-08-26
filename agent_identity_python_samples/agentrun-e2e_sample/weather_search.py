"""天气查询工具（演示 API Key 凭据托管）。

API Key 由 agent-identity-python-sdk 自动注入（@requires_api_key），
代码内不出现任何密钥。

结构说明：装饰器作用于内部实现 _weather_search，外层 wrapper 提供干净的
工具签名（隐藏被注入的 api_key 参数，避免 Agent 框架把它当成模型可见入参）。
"""
from agent_identity_python_sdk.core import requires_api_key


@requires_api_key(
    credential_provider_name="test-provider-api-key",
    inject_param_name="api_key",
)
def _weather_search(query: str, api_key: str) -> str:
    if not api_key:
        raise Exception("Api key is required")

    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 20 degrees and foggy."
    return "It's 30 degrees and sunny."


def weather_search(query: str) -> str:
    """Query weather information by location.

    Args:
        query: The location or weather query to search for.
    """
    return _weather_search(query=query)
