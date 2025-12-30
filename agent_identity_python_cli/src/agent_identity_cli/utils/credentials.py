# -*- coding: utf-8 -*-
"""Credential management utilities for Alibaba Cloud SDK."""

from typing import Optional

from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi.models import Config as OpenApiConfig


def get_credential_client() -> CredentialClient:
    """Get Alibaba Cloud credential client using default credential chain.
    
    The default credential chain searches for credentials in the following order:
    1. Environment variables (ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET)
    2. OIDC Token credentials
    3. Config file credentials (~/.alibabacloud/credentials)
    4. ECS instance RAM role credentials
    5. Credentials URI
    
    Returns:
        CredentialClient instance.
    """
    return CredentialClient()


def get_openapi_config(
    endpoint: Optional[str] = None,
    region_id: str = "cn-beijing",
) -> OpenApiConfig:
    """Create OpenAPI config with credentials.
    
    Args:
        endpoint: Optional API endpoint URL. If not provided, POP SDK will
            build the endpoint from region_id automatically.
        region_id: Region ID, defaults to cn-beijing.
        
    Returns:
        OpenApiConfig instance.
    """
    credential = get_credential_client()
    
    config = OpenApiConfig(
        credential=credential,
        region_id=region_id,
    )
    # Only set endpoint if explicitly provided
    if endpoint:
        config.endpoint = endpoint
    
    return config


def get_account_id() -> str:
    """Get current Alibaba Cloud account ID.
    
    Uses STS GetCallerIdentity API to retrieve the account ID.
    
    Returns:
        Account ID string.
        
    Raises:
        RuntimeError: If failed to get account ID.
    """
    from alibabacloud_sts20150401.client import Client as StsClient
    
    config = get_openapi_config(endpoint="sts.aliyuncs.com")
    client = StsClient(config)
    
    try:
        response = client.get_caller_identity()
        return response.body.account_id
    except Exception as e:
        raise RuntimeError(f"Failed to get account ID: {e}") from e


def build_role_arn(account_id: str, role_name: str) -> str:
    """Build RAM role ARN from account ID and role name.
    
    Args:
        account_id: Alibaba Cloud account ID.
        role_name: RAM role name.
        
    Returns:
        Role ARN string in format: acs:ram::{account_id}:role/{role_name}
    """
    return f"acs:ram::{account_id}:role/{role_name}"

