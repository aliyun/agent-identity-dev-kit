# -*- coding: utf-8 -*-
"""Core deployer for Agent Identity resources."""

from .models import (
    CreateRoleConfig,
    CreateRoleResult,
    CreateWorkloadIdentityConfig,
    CreateWorkloadIdentityResult,
)
from ..services.ram_service import RAMService
from ..services.identity_service import IdentityService


def create_role(config: CreateRoleConfig) -> CreateRoleResult:
    """Create a RAM role for Agent Identity.
    
    This function:
    1. Creates a RAM role with trust policy
    2. Creates a custom permission policy
    3. Attaches the policy to the role
    
    If any step fails, previously created resources are rolled back.
    
    Args:
        config: Role creation configuration.
        
    Returns:
        CreateRoleResult containing role ARN, policies, etc.
        
    Raises:
        Exception: If any API call fails.
    
    Example:
        >>> result = create_role(CreateRoleConfig(
        ...     workload_identity_name="my-identity",
        ... ))
        >>> print(result.role_arn)
        acs:ram::123456789:role/AgentIdentityRole-my-identity
    """
    ram_service = RAMService()
    
    created_role = False
    created_policy = False
    attached_policy = False
    policy_name = f"AgentIdentityPolicy-{config.role_name}"
    role_arn = None
    trust_policy = None
    permission_policy = None
    
    try:
        # Step 1: Create role with trust policy
        role_arn, trust_policy = ram_service.create_role(
            role_name=config.role_name,
            workload_identity_name=config.workload_identity_name,
        )
        created_role = True
        
        # Step 2: Create permission policy
        _, permission_policy = ram_service.create_policy(
            policy_name=policy_name,
            role_name=config.role_name,
            workload_identity_name=config.workload_identity_name,
        )
        created_policy = True
        
        # Step 3: Attach policy to role
        ram_service.attach_policy_to_role(
            role_name=config.role_name,
            policy_name=policy_name,
        )
        attached_policy = True
        
        return CreateRoleResult(
            role_arn=role_arn,
            role_name=config.role_name,
            policy_name=policy_name,
            trust_policy=trust_policy,
            permission_policy=permission_policy,
        )
        
    except Exception:
        # Rollback on failure - must detach before delete
        if attached_policy:
            try:
                ram_service.detach_policy_from_role(config.role_name, policy_name)
            except Exception:
                pass  # Ignore rollback errors
        if created_policy:
            try:
                ram_service.delete_policy(policy_name)
            except Exception:
                pass  # Ignore rollback errors
        if created_role:
            try:
                ram_service.delete_role(config.role_name)
            except Exception:
                pass  # Ignore rollback errors
        raise


def _rollback_role(role_result: CreateRoleResult) -> None:
    """Rollback a created role by deleting it and its policy.
    
    Args:
        role_result: The result from create_role containing role and policy info.
    """
    ram_service = RAMService()
    
    # Detach policy first
    try:
        ram_service.detach_policy_from_role(
            role_result.role_name,
            role_result.policy_name,
        )
    except Exception:
        pass  # Ignore rollback errors
    
    # Delete policy
    try:
        ram_service.delete_policy(role_result.policy_name)
    except Exception:
        pass  # Ignore rollback errors
    
    # Delete role
    try:
        ram_service.delete_role(role_result.role_name)
    except Exception:
        pass  # Ignore rollback errors


def create_workload_identity(
    config: CreateWorkloadIdentityConfig,
) -> CreateWorkloadIdentityResult:
    """Create a Workload Identity.
    
    This function:
    1. If associated_role_arn is not provided, creates a new role first
    2. Creates the workload identity with the role ARN
    
    If workload identity creation fails after role was created, the role is rolled back.
    
    Args:
        config: Workload identity creation configuration.
        
    Returns:
        CreateWorkloadIdentityResult containing identity ARN and role info.
        
    Raises:
        Exception: If any API call fails.
    
    Example:
        >>> result = create_workload_identity(CreateWorkloadIdentityConfig(
        ...     workload_identity_name="my-identity",
        ... ))
        >>> print(result.workload_identity_arn)
    """
    role_result = None
    role_arn = config.associated_role_arn
    
    try:
        # If no role ARN provided, create a new role
        if not role_arn:
            role_config = CreateRoleConfig(
                workload_identity_name=config.workload_identity_name,
            )
            role_result = create_role(role_config)
            role_arn = role_result.role_arn
        
        # Create workload identity
        identity_service = IdentityService()
        workload_identity_arn = identity_service.create_workload_identity(
            workload_identity_name=config.workload_identity_name,
            role_arn=role_arn,
            identity_provider_name=config.identity_provider_name,
            allowed_resource_oauth2_return_urls=config.allowed_resource_oauth2_return_urls,
        )
        
        return CreateWorkloadIdentityResult(
            workload_identity_arn=workload_identity_arn,
            workload_identity_name=config.workload_identity_name,
            role_result=role_result,
        )
        
    except Exception:
        # Rollback: delete role if we created it
        if role_result:
            _rollback_role(role_result)
        raise
