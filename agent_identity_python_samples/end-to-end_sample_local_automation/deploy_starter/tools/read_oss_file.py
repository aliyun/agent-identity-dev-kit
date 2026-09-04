import alibabacloud_oss_v2 as oss
from agent_identity_python_sdk.core import requires_sts_token
from agent_identity_python_sdk.model.stscredential import STSCredential
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse
from alibabacloud_oss_v2.credentials import StaticCredentialsProvider


def _create_oss_client(sts_credential: STSCredential, region: str):
    credentials_provider = StaticCredentialsProvider(
        access_key_id=sts_credential.access_key_id,
        access_key_secret=sts_credential.access_key_secret,
        security_token=sts_credential.security_token
    )
    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider
    cfg.region = region
    return oss.Client(cfg)


def _success(text: str) -> ToolResponse:
    return ToolResponse(content=[TextBlock(type="text", text=text)])


def _error(text: str) -> ToolResponse:
    return ToolResponse(content=[TextBlock(type="text", text=text)])


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
    try:
        client = _create_oss_client(sts_credential, region)
        result = client.get_object(oss.GetObjectRequest(
            bucket=bucket,
            key=key,
        ))
        return _success(f"{result.body.content}")
    except Exception as e:
        return _error(f"Failed to get object '{key}' from bucket '{bucket}': {str(e)}")


@requires_sts_token(
    inject_param_name="sts_credential",
)
def create_oss_bucket(bucket: str, region: str, sts_credential: STSCredential) -> ToolResponse:
    """
    Create an OSS bucket.

    Args:
        bucket (str): The bucket name to create
        region (str): The region to create the bucket in
        sts_credential (STSCredential): The STS credential for authentication

    Returns:
        ToolResponse: Success or error message
    """
    try:
        client = _create_oss_client(sts_credential, region)
        client.put_bucket(oss.PutBucketRequest(bucket=bucket))
        return _success(f"Successfully created bucket '{bucket}' in region '{region}'.")
    except Exception as e:
        return _error(f"Failed to create bucket '{bucket}': {str(e)}")


@requires_sts_token(
    inject_param_name="sts_credential",
)
def put_oss_object(bucket: str, key: str, content: str, region: str, sts_credential: STSCredential) -> ToolResponse:
    """
    Upload content to an OSS object (create or overwrite a file).

    Args:
        bucket (str): The bucket to upload to
        key (str): The object key (file path) to create
        content (str): The content to upload
        region (str): The region of the bucket
        sts_credential (STSCredential): The STS credential for authentication

    Returns:
        ToolResponse: Success or error message
    """
    try:
        client = _create_oss_client(sts_credential, region)
        client.put_object(oss.PutObjectRequest(
            bucket=bucket,
            key=key,
            body=content.encode('utf-8') if isinstance(content, str) else content,
        ))
        return _success(f"Successfully uploaded object '{key}' to bucket '{bucket}'.")
    except Exception as e:
        return _error(f"Failed to upload object '{key}': {str(e)}")
