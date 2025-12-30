# -*- coding: utf-8 -*-
"""Identity Service for managing Workload Identities."""

from typing import List, Optional

from alibabacloud_agentidentity20250901.client import Client as AgentIdentityClient
from alibabacloud_agentidentity20250901.models import CreateWorkloadIdentityRequest

from ..utils import get_openapi_config, DEFAULT_REGION, AGENT_IDENTITY_ENDPOINT


def _get_default_endpoint() -> str:
    """Get Agent Identity endpoint (from env or built from region).
    
    Returns:
        Endpoint URL string.
    """
    if AGENT_IDENTITY_ENDPOINT:
        return AGENT_IDENTITY_ENDPOINT
    return f"agentidentity.{DEFAULT_REGION}.aliyuncs.com"


class IdentityService:
    """Service for managing Workload Identities."""
    
    def __init__(self, endpoint: Optional[str] = None):
        """Initialize Identity service with credentials.
        
        Args:
            endpoint: Optional custom endpoint for Agent Identity API.
                If not provided, uses AGENT_IDENTITY_ENDPOINT env var
                or builds from AGENT_IDENTITY_REGION_ID.
        """
        endpoint = endpoint or _get_default_endpoint()
        config = get_openapi_config(endpoint=endpoint)
        self._client = AgentIdentityClient(config)
    
    def create_workload_identity(
        self,
        workload_identity_name: str,
        role_arn: str,
        identity_provider_name: Optional[str] = None,
        allowed_resource_oauth2_return_urls: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> str:
        """Create a Workload Identity.
        
        Args:
            workload_identity_name: Name of the workload identity to create.
            role_arn: ARN of the RAM role to associate with.
            identity_provider_name: Optional identity provider name.
            allowed_resource_oauth2_return_urls: Optional list of allowed OAuth2 return URLs.
            description: Optional description.
            
        Returns:
            Workload Identity ARN.
            
        Raises:
            Exception: If creation fails.
        """
        request = CreateWorkloadIdentityRequest(
            workload_identity_name=workload_identity_name,
            role_arn=role_arn,
            identity_provider_name=identity_provider_name,
            allowed_resource_oauth2_return_urls=allowed_resource_oauth2_return_urls,
            description=description or f"Workload identity for {workload_identity_name}",
        )
        
        response = self._client.create_workload_identity(request)
        return response.body.workload_identity.workload_identity_arn

