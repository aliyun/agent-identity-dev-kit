"""OSS 文件读取工具（演示 STS 临时凭据注入）。

STS 凭据由 agent-identity-python-sdk 自动注入（@requires_sts_token），
代码内不出现任何长期 AK。
"""
import alibabacloud_oss_v2 as oss
from agent_identity_python_sdk.core import requires_sts_token
from agent_identity_python_sdk.model.stscredential import STSCredential
from alibabacloud_oss_v2.credentials import StaticCredentialsProvider


@requires_sts_token(
    inject_param_name="sts_credential",
)
def get_oss_object(bucket: str, key: str, region: str, sts_credential: STSCredential) -> str:
    """Retrieve an object from Alibaba Cloud OSS by bucket and key.

    Args:
        bucket: The bucket to get the object from.
        key: The object key.
        region: The region of the bucket.
        sts_credential: Automatically injected by Agent Identity.
    """
    credentials_provider = StaticCredentialsProvider(
        access_key_id=sts_credential.access_key_id,
        access_key_secret=sts_credential.access_key_secret,
        security_token=sts_credential.security_token,
    )

    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider
    cfg.region = region

    client = oss.Client(cfg)
    result = client.get_object(oss.GetObjectRequest(
        bucket=bucket,
        key=key,
    ))

    return f"{result.body.content}"


def get_object_from_oss(bucket: str, key: str, region: str = "cn-hangzhou") -> str:
    """Retrieve an object from Alibaba Cloud OSS (defaults to cn-hangzhou).

    Args:
        bucket: The bucket to get the object from.
        key: The object key.
        region: The region of the bucket.
    """
    return get_oss_object(bucket=bucket, key=key, region=region)
