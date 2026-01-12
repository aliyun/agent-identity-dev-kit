import alibabacloud_oss_v2 as oss
from agent_identity_python_sdk.core import requires_sts_token
from agent_identity_python_sdk.model.stscredential import STSCredential
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse
from alibabacloud_oss_v2.credentials import StaticCredentialsProvider

from .context.context import AgentContext


@requires_sts_token(
    inject_param_name="sts_credential",
)
def get_oss_object(bucket: str, key: str, region: str, sts_credential: STSCredential) -> ToolResponse:
    """
    This function retrieves an object from Alibaba Cloud OSS based on the specified bucket and key.

    Args:
        bucket (str): The bucket to get object from
        key (str): The key to get object from
        region (str): The region to get object from
        sts_credential (STSCredential): The STS credential for authentication, automatically injected by Agent Identity

    Returns:
        ToolResponse: A ToolResponse object containing schedule information as text

    Raises:
    """

    credentials_provider = StaticCredentialsProvider(
        access_key_id=sts_credential.access_key_id,
        access_key_secret=sts_credential.access_key_secret,
        security_token=sts_credential.security_token
    )

    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider
    cfg.region = region

    client = oss.Client(cfg)
    result = client.get_object(oss.GetObjectRequest(
        bucket=bucket,
        key=key,
    ))

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"{result.body.content}",
            ),
        ],
    )
