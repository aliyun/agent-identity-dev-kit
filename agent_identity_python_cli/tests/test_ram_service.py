# -*- coding: utf-8 -*-
"""Unit tests for RAM service."""

import pytest
from unittest.mock import patch, MagicMock

from agent_identity_cli.services.ram_service import RAMService
from agent_identity_cli.utils.constants import (
    DEFAULT_REGION,
    OAUTH2_CREDENTIAL_PROVIDER,
    APIKEY_CREDENTIAL_PROVIDER,
)


class TestRAMServicePolicyBuilding:
    """Tests for RAM service policy building methods."""
    
    @pytest.fixture
    def ram_service(self, mock_account_id):
        """Create RAMService with mocked dependencies."""
        with patch("agent_identity_cli.services.ram_service.get_openapi_config"):
            with patch("agent_identity_cli.services.ram_service.RamClient"):
                with patch("agent_identity_cli.services.ram_service.get_account_id") as mock_get_account:
                    mock_get_account.return_value = mock_account_id
                    service = RAMService()
                    # Pre-set account_id to avoid lazy loading
                    service._account_id = mock_account_id
                    return service
    
    def test_build_trust_policy_without_workload_identity(self, ram_service):
        """Test trust policy without workload identity has no Condition."""
        policy = ram_service._build_trust_policy(None)
        
        assert policy["Version"] == "1"
        assert len(policy["Statement"]) == 1
        
        statement = policy["Statement"][0]
        assert statement["Effect"] == "Allow"
        assert statement["Principal"]["Service"] == "workload.agentidentity.aliyuncs.com"
        assert "sts:AssumeRole" in statement["Action"]
        assert "sts:SetContext" in statement["Action"]
        assert "Condition" not in statement
    
    def test_build_trust_policy_with_workload_identity(self, ram_service, mock_account_id):
        """Test trust policy with workload identity has Condition."""
        policy = ram_service._build_trust_policy("test-identity")
        
        assert policy["Version"] == "1"
        statement = policy["Statement"][0]
        
        assert "Condition" in statement
        assert "StringEquals" in statement["Condition"]
        
        condition_key = "sts:RequestContext/agentidentity:WorkloadIdentityArn"
        assert condition_key in statement["Condition"]["StringEquals"]
        
        expected_arn = (
            f"acs:agentidentity:{DEFAULT_REGION}:{mock_account_id}:"
            f"workloadidentitydirectory/default/workloadidentity/test-identity"
        )
        assert statement["Condition"]["StringEquals"][condition_key] == expected_arn
    
    def test_build_permission_policy_without_workload_identity(self, ram_service, mock_account_id):
        """Test permission policy uses wildcard when no workload identity."""
        policy = ram_service._build_permission_policy(None)
        
        assert policy["Version"] == "1"
        assert len(policy["Statement"]) == 2
        
        # Check OAuth2 statement
        oauth2_stmt = policy["Statement"][0]
        assert oauth2_stmt["Effect"] == "Allow"
        assert "agentidentitydata:GetResourceOAuth2Token" in oauth2_stmt["Action"]
        
        # Check APIKey statement
        apikey_stmt = policy["Statement"][1]
        assert apikey_stmt["Effect"] == "Allow"
        assert "agentidentitydata:GetResourceAPIKey" in apikey_stmt["Action"]
        
        # Check wildcard in resource ARN
        wildcard_arn = (
            f"acs:agentidentity:{DEFAULT_REGION}:{mock_account_id}:"
            f"workloadidentitydirectory/default/workloadidentity/*"
        )
        assert wildcard_arn in oauth2_stmt["Resource"]
        assert wildcard_arn in apikey_stmt["Resource"]
    
    def test_build_permission_policy_with_workload_identity(self, ram_service, mock_account_id):
        """Test permission policy uses specific ARN when workload identity provided."""
        policy = ram_service._build_permission_policy("my-identity")
        
        # Check specific identity ARN
        specific_arn = (
            f"acs:agentidentity:{DEFAULT_REGION}:{mock_account_id}:"
            f"workloadidentitydirectory/default/workloadidentity/my-identity"
        )
        assert specific_arn in policy["Statement"][0]["Resource"]
        assert specific_arn in policy["Statement"][1]["Resource"]
    
    def test_build_permission_policy_includes_token_vault_arns(self, ram_service, mock_account_id):
        """Test permission policy includes token vault ARNs."""
        policy = ram_service._build_permission_policy("my-identity")
        
        oauth2_vault_arn = (
            f"acs:agentidentity:{DEFAULT_REGION}:{mock_account_id}:"
            f"tokenvault/default/{OAUTH2_CREDENTIAL_PROVIDER}/*"
        )
        apikey_vault_arn = (
            f"acs:agentidentity:{DEFAULT_REGION}:{mock_account_id}:"
            f"tokenvault/default/{APIKEY_CREDENTIAL_PROVIDER}/*"
        )
        
        assert oauth2_vault_arn in policy["Statement"][0]["Resource"]
        assert apikey_vault_arn in policy["Statement"][1]["Resource"]
    
    def test_build_workload_identity_arn(self, ram_service, mock_account_id):
        """Test workload identity ARN format."""
        arn = ram_service._build_workload_identity_arn("test-identity")
        
        expected = (
            f"acs:agentidentity:{DEFAULT_REGION}:{mock_account_id}:"
            f"workloadidentitydirectory/default/workloadidentity/test-identity"
        )
        assert arn == expected
    
    def test_build_token_vault_arn_oauth2(self, ram_service, mock_account_id):
        """Test token vault ARN for OAuth2 provider."""
        arn = ram_service._build_token_vault_arn(OAUTH2_CREDENTIAL_PROVIDER)
        
        expected = (
            f"acs:agentidentity:{DEFAULT_REGION}:{mock_account_id}:"
            f"tokenvault/default/{OAUTH2_CREDENTIAL_PROVIDER}/*"
        )
        assert arn == expected
    
    def test_build_token_vault_arn_apikey(self, ram_service, mock_account_id):
        """Test token vault ARN for API Key provider."""
        arn = ram_service._build_token_vault_arn(APIKEY_CREDENTIAL_PROVIDER)
        
        expected = (
            f"acs:agentidentity:{DEFAULT_REGION}:{mock_account_id}:"
            f"tokenvault/default/{APIKEY_CREDENTIAL_PROVIDER}/*"
        )
        assert arn == expected


class TestRAMServiceRoleOperations:
    """Tests for RAM service role and policy operations."""
    
    @pytest.fixture
    def ram_service_with_mock_client(self, mock_ram_client, mock_account_id):
        """Create RAMService with mocked RAM client."""
        with patch("agent_identity_cli.services.ram_service.get_openapi_config"):
            with patch("agent_identity_cli.services.ram_service.RamClient") as mock_client_class:
                mock_client_class.return_value = mock_ram_client
                with patch("agent_identity_cli.services.ram_service.get_account_id") as mock_get_account:
                    mock_get_account.return_value = mock_account_id
                    service = RAMService()
                    service._account_id = mock_account_id
                    return service
    
    def test_create_role_success(self, ram_service_with_mock_client):
        """Test successful role creation."""
        role_arn, trust_policy = ram_service_with_mock_client.create_role(
            role_name="TestRole",
            workload_identity_name="test-identity",
        )
        
        assert "acs:ram::" in role_arn
        assert "role/TestRole" in role_arn
        assert trust_policy["Version"] == "1"
        assert "Statement" in trust_policy
    
    def test_create_role_description_with_workload_identity(self, ram_service_with_mock_client):
        """Test role description when workload identity is specified."""
        ram_service_with_mock_client.create_role(
            role_name="TestRole",
            workload_identity_name="my-identity",
        )
        
        # Verify the create_role was called with correct description
        call_args = ram_service_with_mock_client._client.create_role.call_args
        request = call_args[0][0]
        assert request.description == "Agent Identity runtime role for my-identity"
    
    def test_create_role_description_without_workload_identity(self, ram_service_with_mock_client):
        """Test role description when no workload identity."""
        ram_service_with_mock_client.create_role(
            role_name="TestRole",
            workload_identity_name=None,
        )
        
        call_args = ram_service_with_mock_client._client.create_role.call_args
        request = call_args[0][0]
        assert request.description == "Default runtime role automatically created by the Agent Identity CLI"
    
    def test_get_role_arn(self, ram_service_with_mock_client, mock_account_id):
        """Test get_role_arn builds correct ARN."""
        arn = ram_service_with_mock_client.get_role_arn("MyRole")
        
        assert arn == f"acs:ram::{mock_account_id}:role/MyRole"
    
    def test_detach_policy_from_role(self, ram_service_with_mock_client):
        """Test detach_policy_from_role calls client correctly."""
        ram_service_with_mock_client.detach_policy_from_role(
            role_name="TestRole",
            policy_name="TestPolicy",
        )
        
        # Verify the detach was called
        ram_service_with_mock_client._client.detach_policy_from_role.assert_called_once()
        
        # Verify request parameters
        call_args = ram_service_with_mock_client._client.detach_policy_from_role.call_args
        request = call_args[0][0]
        assert request.role_name == "TestRole"
        assert request.policy_name == "TestPolicy"
        assert request.policy_type == "Custom"


class TestRAMServiceConstants:
    """Tests for RAM service constants."""
    
    def test_default_region_from_env(self):
        """Test DEFAULT_REGION respects environment variable."""
        # The actual value depends on environment
        assert DEFAULT_REGION is not None
        assert isinstance(DEFAULT_REGION, str)
    
    def test_credential_provider_constants(self):
        """Test credential provider type constants."""
        assert OAUTH2_CREDENTIAL_PROVIDER == "oauth2credentialprovider"
        assert APIKEY_CREDENTIAL_PROVIDER == "apikeycredentialprovider"

