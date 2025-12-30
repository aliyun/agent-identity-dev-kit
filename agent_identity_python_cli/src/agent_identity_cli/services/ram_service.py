# -*- coding: utf-8 -*-
"""RAM Service for creating roles and policies."""

import json
from typing import Dict, Optional, Tuple

from alibabacloud_ram20150501.client import Client as RamClient
from alibabacloud_ram20150501.models import (
    CreateRoleRequest,
    CreatePolicyRequest,
    AttachPolicyToRoleRequest,
    DetachPolicyFromRoleRequest,
    DeleteRoleRequest,
    DeletePolicyRequest,
)

from ..utils import (
    get_openapi_config,
    get_account_id,
    build_role_arn,
    DEFAULT_REGION,
    OAUTH2_CREDENTIAL_PROVIDER,
    APIKEY_CREDENTIAL_PROVIDER,
)


class RAMService:
    """Service for managing RAM roles and policies."""
    
    # RAM API endpoint
    RAM_ENDPOINT = "ram.aliyuncs.com"
    
    def __init__(self):
        """Initialize RAM service with credentials."""
        config = get_openapi_config(endpoint=self.RAM_ENDPOINT)
        self._client = RamClient(config)
        self._account_id: Optional[str] = None
    
    @property
    def account_id(self) -> str:
        """Get current account ID (cached)."""
        if self._account_id is None:
            self._account_id = get_account_id()
        return self._account_id
    
    def create_role(
        self,
        role_name: str,
        workload_identity_name: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Create a RAM role with trust policy for Agent Identity.
        
        Args:
            role_name: Name of the role to create.
            workload_identity_name: Workload identity name for trust policy.
                If None, allows all workload identities (no Condition).
            
        Returns:
            Tuple of (role_arn, trust_policy_dict).
            
        Raises:
            Exception: If role creation fails.
        """
        # Build trust policy document
        trust_policy = self._build_trust_policy(workload_identity_name)
        
        # Set description based on workload identity
        if workload_identity_name:
            description = f"Agent Identity runtime role for {workload_identity_name}"
        else:
            description = "Default runtime role automatically created by the Agent Identity CLI"
        
        request = CreateRoleRequest(
            role_name=role_name,
            assume_role_policy_document=json.dumps(trust_policy),
            description=description,
        )
        
        response = self._client.create_role(request)
        return response.body.role.arn, trust_policy
    
    def create_policy(
        self,
        policy_name: str,
        role_name: str,
        workload_identity_name: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Create a RAM policy for Agent Identity operations.
        
        Args:
            policy_name: Name of the policy to create.
            role_name: Name of the associated role (for description).
            workload_identity_name: Workload identity name for resource scope.
                If None, allows all workload identities (*).
            
        Returns:
            Tuple of (policy_name, permission_policy_dict).
            
        Raises:
            Exception: If policy creation fails.
        """
        # Build permission policy document
        permission_policy = self._build_permission_policy(workload_identity_name)
        
        request = CreatePolicyRequest(
            policy_name=policy_name,
            policy_document=json.dumps(permission_policy),
            description=f"Agent Identity policy for {role_name}",
        )
        
        response = self._client.create_policy(request)
        return response.body.policy.policy_name, permission_policy
    
    def attach_policy_to_role(
        self,
        role_name: str,
        policy_name: str,
    ) -> None:
        """Attach a custom policy to a role.
        
        Args:
            role_name: Name of the role.
            policy_name: Name of the policy to attach.
            
        Raises:
            Exception: If attach operation fails.
        """
        request = AttachPolicyToRoleRequest(
            role_name=role_name,
            policy_name=policy_name,
            policy_type="Custom",
        )
        
        self._client.attach_policy_to_role(request)
    
    def detach_policy_from_role(
        self,
        role_name: str,
        policy_name: str,
    ) -> None:
        """Detach a custom policy from a role (for rollback).
        
        Args:
            role_name: Name of the role.
            policy_name: Name of the policy to detach.
            
        Raises:
            Exception: If detach operation fails.
        """
        request = DetachPolicyFromRoleRequest(
            role_name=role_name,
            policy_name=policy_name,
            policy_type="Custom",
        )
        
        self._client.detach_policy_from_role(request)
    
    def delete_role(self, role_name: str) -> None:
        """Delete a RAM role (for rollback).
        
        Args:
            role_name: Name of the role to delete.
            
        Raises:
            Exception: If delete operation fails.
        """
        request = DeleteRoleRequest(role_name=role_name)
        self._client.delete_role(request)
    
    def delete_policy(self, policy_name: str) -> None:
        """Delete a RAM policy (for rollback).
        
        Args:
            policy_name: Name of the policy to delete.
            
        Raises:
            Exception: If delete operation fails.
        """
        request = DeletePolicyRequest(policy_name=policy_name)
        self._client.delete_policy(request)
    
    def get_role_arn(self, role_name: str) -> str:
        """Build role ARN from role name.
        
        Args:
            role_name: Name of the role.
            
        Returns:
            Role ARN string.
        """
        return build_role_arn(self.account_id, role_name)
    
    def _build_trust_policy(
        self,
        workload_identity_name: Optional[str] = None,
    ) -> Dict:
        """Build trust policy for Agent Identity service.
        
        Args:
            workload_identity_name: Workload identity name for condition.
                If None, allows all workload identities (no Condition).
                
        Returns:
            Trust policy document as dict.
        """
        statement = {
            "Effect": "Allow",
            "Principal": {
                "Service": "workload.agentidentity.aliyuncs.com"
            },
            "Action": [
                "sts:AssumeRole",
                "sts:SetContext"
            ]
        }
        
        # Add condition only if workload identity name is specified
        if workload_identity_name:
            workload_identity_arn = self._build_workload_identity_arn(
                workload_identity_name
            )
            statement["Condition"] = {
                "StringEquals": {
                    "sts:RequestContext/agentidentity:WorkloadIdentityArn": workload_identity_arn
                }
            }
        
        return {
            "Version": "1",
            "Statement": [statement]
        }
    
    def _build_permission_policy(
        self,
        workload_identity_name: Optional[str] = None,
    ) -> Dict:
        """Build permission policy for Agent Identity operations.
        
        Args:
            workload_identity_name: Workload identity name for resource scope.
                If None, allows all workload identities (*).
                
        Returns:
            Permission policy document as dict.
        """
        # Build resource ARN
        resource_arn = self._build_workload_identity_arn(
            workload_identity_name or "*"
        )
        # Build token vault ARNs
        oauth2_provider_arn = self._build_token_vault_arn(OAUTH2_CREDENTIAL_PROVIDER)
        apikey_provider_arn = self._build_token_vault_arn(APIKEY_CREDENTIAL_PROVIDER)
        
        return {
            "Version": "1",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["agentidentitydata:GetResourceOAuth2Token"],
                    "Resource": [resource_arn, oauth2_provider_arn]
                },
                {
                    "Effect": "Allow",
                    "Action": ["agentidentitydata:GetResourceAPIKey"],
                    "Resource": [resource_arn, apikey_provider_arn]
                }
            ]
        }
    
    def _build_workload_identity_arn(self, workload_identity_name: str) -> str:
        """Build workload identity ARN.
        
        Args:
            workload_identity_name: Name of the workload identity.
            
        Returns:
            Workload identity ARN string.
        """
        region = DEFAULT_REGION
        return (
            f"acs:agentidentity:{region}:{self.account_id}:"
            f"workloadidentitydirectory/default/workloadidentity/{workload_identity_name}"
        )
    
    def _build_token_vault_arn(self, provider_type: str) -> str:
        """Build token vault ARN for credential provider.
        
        Args:
            provider_type: Type of credential provider 
                (oauth2credentialprovider or apikeycredentialprovider).
            
        Returns:
            Token vault ARN string.
        """
        region = DEFAULT_REGION
        return (
            f"acs:agentidentity:{region}:{self.account_id}:"
            f"tokenvault/default/{provider_type}/*"
        )
