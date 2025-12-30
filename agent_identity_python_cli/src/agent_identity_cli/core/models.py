# -*- coding: utf-8 -*-
"""Data models for Agent Identity CLI."""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CreateRoleConfig:
    """Configuration for creating a RAM role.
    
    Attributes:
        role_name: Name of the RAM role to create. If not specified,
            defaults to AgentIdentityRole-{workload_identity_name} or
            AgentIdentityRole-{random}.
        workload_identity_name: Workload identity name for trust policy.
            If not specified, trust policy allows all workload identities.
    """
    role_name: Optional[str] = None
    workload_identity_name: Optional[str] = None
    
    def __post_init__(self):
        """Generate default role name if not specified."""
        if not self.role_name:
            if self.workload_identity_name:
                self.role_name = f"AgentIdentityRole-{self.workload_identity_name}"
            else:
                self.role_name = f"AgentIdentityRole-{uuid.uuid4().hex[:8]}"


@dataclass
class CreateRoleResult:
    """Result of creating a RAM role.
    
    Attributes:
        role_arn: ARN of the created RAM role.
        role_name: Name of the created RAM role.
        policy_name: Name of the created custom policy.
        trust_policy: Trust policy document attached to the role.
        permission_policy: Permission policy document attached to the role.
    """
    role_arn: str
    role_name: str
    policy_name: str
    trust_policy: Dict
    permission_policy: Dict
    
    def to_dict(self) -> dict:
        """Convert result to dictionary for serialization."""
        return {
            "role_arn": self.role_arn,
            "role_name": self.role_name,
            "policy_name": self.policy_name,
            "trust_policy": self.trust_policy,
            "permission_policy": self.permission_policy,
        }


@dataclass
class CreateWorkloadIdentityConfig:
    """Configuration for creating a Workload Identity.
    
    Attributes:
        workload_identity_name: Name of the workload identity (required).
        associated_role_arn: ARN of the RAM role to associate.
            If not specified, a new role will be created automatically.
        identity_provider_name: Name of the identity provider (optional).
        allowed_resource_oauth2_return_urls: List of allowed OAuth2 return URLs.
    """
    workload_identity_name: str
    associated_role_arn: Optional[str] = None
    identity_provider_name: Optional[str] = None
    allowed_resource_oauth2_return_urls: Optional[List[str]] = field(default=None)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.workload_identity_name:
            raise ValueError("workload_identity_name is required")


@dataclass
class CreateWorkloadIdentityResult:
    """Result of creating a Workload Identity.
    
    Attributes:
        workload_identity_arn: ARN of the created workload identity.
        workload_identity_name: Name of the created workload identity.
        role_result: Result of role creation (if a new role was created).
    """
    workload_identity_arn: str
    workload_identity_name: str
    role_result: Optional[CreateRoleResult] = None
    
    def to_dict(self) -> dict:
        """Convert result to dictionary for serialization."""
        result = {
            "workload_identity_arn": self.workload_identity_arn,
            "workload_identity_name": self.workload_identity_name,
        }
        if self.role_result:
            result["role_result"] = self.role_result.to_dict()
        return result
