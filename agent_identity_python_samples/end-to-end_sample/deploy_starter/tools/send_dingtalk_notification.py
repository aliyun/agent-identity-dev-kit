import os

import httpx
from agent_identity_python_sdk.core import requires_access_token
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


@requires_access_token(
    credential_provider_name="dingtalk-m2m-sample",
    auth_flow="M2M",
    inject_param_name="access_token",
)
async def send_dingtalk_notification(
    userid_list: str,
    message: str,
    access_token: str = None,
) -> ToolResponse:
    """Send work notifications to DingTalk users via corporate conversation API (M2M mode, no user login required).

    Args:
        userid_list (`str`):
            Comma-separated DingTalk user IDs to notify, e.g. "user001,user002".
        message (`str`):
            The notification message content to send.
        access_token (`str`):
            DingTalk access token (auto-injected by SDK, do not pass manually).

    Returns:
        `ToolResponse`:
            The result of sending the notification.
    """
    agent_id_str = os.getenv("DINGTALK_AGENT_ID")
    if not agent_id_str:
        return ToolResponse(
            content=[TextBlock(type="text", text="DINGTALK_AGENT_ID environment variable is not set")],
        )
    agent_id = int(agent_id_str)
    url = f"https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2?access_token={access_token}"
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "agent_id": agent_id,
        "userid_list": userid_list,
        "msg": {"msgtype": "text", "text": {"content": message}},
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            data = resp.json()

        if data.get("errcode") == 0:
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=f"Successfully sent work notification to {userid_list}, task_id: {data.get('task_id')}",
                )],
            )
        else:
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=f"Failed to send notification: {data.get('errmsg', 'unknown error')}",
                )],
            )
    except Exception as e:
        return ToolResponse(
            content=[TextBlock(
                type="text",
                text=f"Failed to send DingTalk notification: {str(e)}",
            )],
        )
