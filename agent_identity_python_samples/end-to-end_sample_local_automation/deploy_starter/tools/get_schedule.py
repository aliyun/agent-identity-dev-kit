from agent_identity_python_sdk.core import requires_sts_token
from agent_identity_python_sdk.model.stscredential import STSCredential
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


@requires_sts_token(
    inject_param_name="sts_credential",
)
def get_schedule(date: str, sts_credential: STSCredential) -> ToolResponse:
    """Mock tool to get schedule information

    This function simulates fetching schedule data based on a date.
    For demonstration purposes, it returns predefined schedule items
    for any given date.

    Args:
        date (str): The date to get schedule for
        sts_credential (STSCredential): The STS credential for authentication, automatically injected by Agent Identity

    Returns:
        ToolResponse: A ToolResponse object containing schedule information as text

    Raises:
        Exception: If sts_credential is empty or None
    """

    if not sts_credential:
        raise Exception("Sts credential is required")
    print(f'sts_credential: {sts_credential.access_key_id}, {sts_credential.access_key_secret}, {sts_credential.security_token}, {sts_credential.expiration}', )

    # 模拟返回
    result = f"Schedule for {date}:\n1. 9:00 AM Opening meeting\n2. 10:00 AM Check-in\n3. 11:00 AM Check-out"

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"{result}",
            ),
        ],
    )
