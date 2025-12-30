from agent_identity_python_sdk.core import requires_api_key
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


@requires_api_key(
    credential_provider_name="test-provider-api-key",
    inject_param_name="api_key",
)
def weather_search(query: str, api_key: str) -> ToolResponse:
    """Mock tool to get current weather information

    This function simulates fetching weather data based on a query string.
    For demonstration purposes, it returns predefined weather conditions
    for specific locations (San Francisco area) and generic conditions
    for other queries.

    Args:
        query (str): The location or weather query to search for
        api_key (str): The API key for authentication, automatically injected by Agent Identity

    Returns:
        ToolResponse: A ToolResponse object containing weather information as text

    Raises:
        Exception: If api_key is empty or None
    """

    if not api_key:
        raise Exception("Api key is required")

    if "sf" in query.lower() or "san francisco" in query.lower():
        result = "It's 20 degrees and foggy."
    else:
        result = "It's 30 degrees and sunny."

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"{result}",
            ),
        ],
    )
