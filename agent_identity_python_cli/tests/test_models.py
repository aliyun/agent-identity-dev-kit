# -*- coding: utf-8 -*-
"""Unit tests for data models."""

import pytest
import re

from agent_identity_cli.core.models import (
    CreateRoleConfig,
    CreateRoleResult,
    CreateWorkloadIdentityConfig,
    CreateWorkloadIdentityResult,
)


class TestCreateRoleConfig:
    """Tests for CreateRoleConfig dataclass."""
    
    def test_default_role_name_with_workload_identity(self):
        """Test role name defaults to AgentIdentityRole-{workload_identity_name}."""
        config = CreateRoleConfig(workload_identity_name="my-identity")
        
        assert config.role_name == "AgentIdentityRole-my-identity"
        assert config.workload_identity_name == "my-identity"
    
    def test_default_role_name_without_workload_identity(self):
        """Test role name defaults to AgentIdentityRole-{random} when no workload identity."""
        config = CreateRoleConfig()
        
        # Role name should match pattern AgentIdentityRole-{8 hex chars}
        assert config.role_name is not None
        assert re.match(r"^AgentIdentityRole-[a-f0-9]{8}$", config.role_name)
        assert config.workload_identity_name is None
    
    def test_explicit_role_name(self):
        """Test explicit role name is preserved."""
        config = CreateRoleConfig(
            role_name="MyCustomRole",
            workload_identity_name="my-identity",
        )
        
        assert config.role_name == "MyCustomRole"
        assert config.workload_identity_name == "my-identity"
    
    def test_explicit_role_name_only(self):
        """Test explicit role name without workload identity."""
        config = CreateRoleConfig(role_name="MyCustomRole")
        
        assert config.role_name == "MyCustomRole"
        assert config.workload_identity_name is None


class TestCreateRoleResult:
    """Tests for CreateRoleResult dataclass."""
    
    def test_to_dict(self):
        """Test to_dict serialization."""
        result = CreateRoleResult(
            role_arn="acs:ram::123456789:role/TestRole",
            role_name="TestRole",
            policy_name="TestPolicy",
            trust_policy={"Version": "1", "Statement": []},
            permission_policy={"Version": "1", "Statement": []},
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["role_arn"] == "acs:ram::123456789:role/TestRole"
        assert result_dict["role_name"] == "TestRole"
        assert result_dict["policy_name"] == "TestPolicy"
        assert result_dict["trust_policy"] == {"Version": "1", "Statement": []}
        assert result_dict["permission_policy"] == {"Version": "1", "Statement": []}
    
    def test_attributes(self):
        """Test result attributes are accessible."""
        result = CreateRoleResult(
            role_arn="acs:ram::123456789:role/TestRole",
            role_name="TestRole",
            policy_name="TestPolicy",
            trust_policy={"key": "value"},
            permission_policy={"key2": "value2"},
        )
        
        assert result.role_arn == "acs:ram::123456789:role/TestRole"
        assert result.role_name == "TestRole"
        assert result.policy_name == "TestPolicy"
        assert result.trust_policy == {"key": "value"}
        assert result.permission_policy == {"key2": "value2"}


class TestCreateWorkloadIdentityConfig:
    """Tests for CreateWorkloadIdentityConfig dataclass."""
    
    def test_required_workload_identity_name(self):
        """Test workload_identity_name is required."""
        config = CreateWorkloadIdentityConfig(
            workload_identity_name="my-identity",
        )
        
        assert config.workload_identity_name == "my-identity"
        assert config.associated_role_arn is None
        assert config.identity_provider_name is None
        assert config.allowed_resource_oauth2_return_urls is None
    
    def test_empty_workload_identity_name_raises_error(self):
        """Test empty workload_identity_name raises ValueError."""
        with pytest.raises(ValueError, match="workload_identity_name is required"):
            CreateWorkloadIdentityConfig(workload_identity_name="")
    
    def test_all_optional_fields(self):
        """Test all optional fields are set correctly."""
        config = CreateWorkloadIdentityConfig(
            workload_identity_name="my-identity",
            associated_role_arn="acs:ram::123456789:role/TestRole",
            identity_provider_name="my-provider",
            allowed_resource_oauth2_return_urls=["http://localhost:8080/callback"],
        )
        
        assert config.workload_identity_name == "my-identity"
        assert config.associated_role_arn == "acs:ram::123456789:role/TestRole"
        assert config.identity_provider_name == "my-provider"
        assert config.allowed_resource_oauth2_return_urls == ["http://localhost:8080/callback"]


class TestCreateWorkloadIdentityResult:
    """Tests for CreateWorkloadIdentityResult dataclass."""
    
    def test_to_dict_without_role_result(self):
        """Test to_dict without role_result."""
        result = CreateWorkloadIdentityResult(
            workload_identity_arn="acs:agentidentity:cn-beijing:123456789:workloadidentitydirectory/default/workloadidentity/my-identity",
            workload_identity_name="my-identity",
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["workload_identity_arn"] == "acs:agentidentity:cn-beijing:123456789:workloadidentitydirectory/default/workloadidentity/my-identity"
        assert result_dict["workload_identity_name"] == "my-identity"
        assert "role_result" not in result_dict
    
    def test_to_dict_with_role_result(self):
        """Test to_dict with role_result included."""
        role_result = CreateRoleResult(
            role_arn="acs:ram::123456789:role/TestRole",
            role_name="TestRole",
            policy_name="TestPolicy",
            trust_policy={"Version": "1"},
            permission_policy={"Version": "1"},
        )
        
        result = CreateWorkloadIdentityResult(
            workload_identity_arn="acs:agentidentity:cn-beijing:123456789:workloadidentitydirectory/default/workloadidentity/my-identity",
            workload_identity_name="my-identity",
            role_result=role_result,
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["workload_identity_arn"] == "acs:agentidentity:cn-beijing:123456789:workloadidentitydirectory/default/workloadidentity/my-identity"
        assert result_dict["workload_identity_name"] == "my-identity"
        assert "role_result" in result_dict
        assert result_dict["role_result"]["role_name"] == "TestRole"

