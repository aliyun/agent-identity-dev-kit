import os
import httpx
from agent_identity_python_sdk.core import requires_access_token

from context import AgentContext


class DingTalkClient:
    """DingTalk API client class for encapsulating all DingTalk API calls"""

    def __init__(self, access_token: str):
        """Initialize the DingTalk client

        Args:
            access_token (str): DingTalk access token
        """
        self.access_token = access_token
        self.base_url = "https://api.dingtalk.com/v2.0"

    async def overwrite_document_content(self, document_id: str, content: str, data_type: str = "markdown") -> dict:
        """Write content to a DingTalk document

        Args:
            document_id (str): DingTalk document ID
            content (str): The file content to be written
            data_type (str): Content type, default is markdown

        Returns:
            dict: API response result

        Raises:
            httpx.HTTPStatusError: Raised when API call fails
        """
        url = f"{self.base_url}/doc/me/suites/documents/{document_id}/overwriteContent"
        headers = {
            "x-acs-dingtalk-access-token": self.access_token,
            "Content-Type": "application/json"
        }
        data = {
            "dataType": data_type,
            "content": content
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            print(response.text)
            response.raise_for_status()
            return response.json()

def on_auth(url: str):
    AgentContext.on_auth_url(url, "Write to DingTalk document")

"""
If you want to authenticate and authorize with dingtalk account every time you call the tool, you can just follow theses steps:
1.  set force_authentication=True to enable force authentication
2.  add custom parameters to the dingtalk oauth flow to enable force user authorization
"""
@requires_access_token(
    credential_provider_name="test-provider-for-dingtalk",
    scopes=["openid", "corpid"],
    auth_flow="USER_FEDERATION",
    on_auth_url= on_auth,
    # force_authentication=True,
    callback_url= f"{os.getenv('APP_REDIRECT_URI', 'http://localhost:8090')}/callback",
    inject_param_name="access_token",
    #  custom_parameters={"prompt": "consent"}
)
async def ding_talk_tool(
        content: str,
        access_token: str,
        document_id: str
) -> str:
    """Write content to a DingTalk document

    Args:
        content (`str`):
            The content to be written to the document.
        access_token (`str`):
            DingTalk access token.
        document_id (`str`):
            DingTalk document ID. If not specified, use the default document ID.

    Raises:
        `Exception`:
            Failed to write content to the document.

    Returns:
        `ToolResponse`:
            The result of writing to the document, either success or an exception.
    """

    try:
        # Create DingTalk client instance
        client = DingTalkClient(access_token)
        # Call DingTalk API to write document content
        # Note: Document ID is required here, temporarily using the original ID
        result = await client.overwrite_document_content(document_id, content)

        return f"Successfully wrote to DingTalk document, response: {result}"
    except Exception as e:
        raise Exception(f"Failed to write to DingTalk document: {str(e)}")


async def write_dingtalk_file(content: str, document_id: str):
    """Write content to a DingTalk document

        Args:
            content (`str`):
                The content to be written to the document.
            document_id (`str`):
                DingTalk document ID. If not specified, use the default document ID.

        Raises:
            `Exception`:
                Failed to write content to the document.

        Returns:
            `ToolResponse`:
                The result of writing to the document, either success or an exception.
        """
    resp = await ding_talk_tool(content=content, document_id=document_id)
    print(resp)
    return resp