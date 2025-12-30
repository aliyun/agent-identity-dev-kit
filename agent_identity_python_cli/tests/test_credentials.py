# -*- coding: utf-8 -*-
"""Unit tests for credential utilities."""

import pytest
from unittest.mock import patch, MagicMock

from agent_identity_cli.utils.credentials import (
    build_role_arn,
    get_openapi_config,
    get_account_id,
    get_credential_client,
)


class TestBuildRoleArn:
    """Tests for build_role_arn function."""
    
    def test_basic_arn_format(self):
        """Test basic ARN format is correct."""
        arn = build_role_arn("123456789012", "TestRole")
        
        assert arn == "acs:ram::123456789012:role/TestRole"
    
    def test_arn_with_hyphen_role_name(self):
        """Test ARN with hyphenated role name."""
        arn = build_role_arn("123456789012", "Agent-Identity-Role")
        
        assert arn == "acs:ram::123456789012:role/Agent-Identity-Role"
    
    def test_arn_with_underscore_role_name(self):
        """Test ARN with underscored role name."""
        arn = build_role_arn("123456789012", "Agent_Identity_Role")
        
        assert arn == "acs:ram::123456789012:role/Agent_Identity_Role"


class TestGetCredentialClient:
    """Tests for get_credential_client function."""
    
    @patch("agent_identity_cli.utils.credentials.CredentialClient")
    def test_returns_credential_client(self, mock_client_class):
        """Test function returns a CredentialClient instance."""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        
        result = get_credential_client()
        
        mock_client_class.assert_called_once_with()
        assert result == mock_instance


class TestGetOpenApiConfig:
    """Tests for get_openapi_config function."""
    
    @patch("agent_identity_cli.utils.credentials.get_credential_client")
    def test_config_with_endpoint(self, mock_get_credential):
        """Test config creation with explicit endpoint."""
        mock_credential = MagicMock()
        mock_get_credential.return_value = mock_credential
        
        config = get_openapi_config(endpoint="test.aliyuncs.com")
        
        assert config.endpoint == "test.aliyuncs.com"
        assert config.region_id == "cn-beijing"
        assert config.credential == mock_credential
    
    @patch("agent_identity_cli.utils.credentials.get_credential_client")
    def test_config_without_endpoint(self, mock_get_credential):
        """Test config creation without endpoint (POP SDK builds from region)."""
        mock_credential = MagicMock()
        mock_get_credential.return_value = mock_credential
        
        config = get_openapi_config(region_id="cn-shanghai")
        
        # endpoint should be None when not provided
        assert config.endpoint is None
        assert config.region_id == "cn-shanghai"
        assert config.credential == mock_credential
    
    @patch("agent_identity_cli.utils.credentials.get_credential_client")
    def test_config_with_custom_region(self, mock_get_credential):
        """Test config creation with custom region and endpoint."""
        mock_credential = MagicMock()
        mock_get_credential.return_value = mock_credential
        
        config = get_openapi_config(
            endpoint="test.aliyuncs.com",
            region_id="cn-shanghai",
        )
        
        assert config.endpoint == "test.aliyuncs.com"
        assert config.region_id == "cn-shanghai"
        assert config.credential == mock_credential


class TestGetAccountId:
    """Tests for get_account_id function."""
    
    @patch("agent_identity_cli.utils.credentials.get_openapi_config")
    @patch("alibabacloud_sts20150401.client.Client")
    def test_returns_account_id(self, mock_sts_class, mock_get_config):
        """Test successful account ID retrieval."""
        # Setup mocks
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        
        mock_sts_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body.account_id = "123456789012"
        mock_sts_client.get_caller_identity.return_value = mock_response
        mock_sts_class.return_value = mock_sts_client
        
        # Execute
        account_id = get_account_id()
        
        # Verify
        assert account_id == "123456789012"
        mock_get_config.assert_called_once_with(endpoint="sts.aliyuncs.com")
    
    @patch("agent_identity_cli.utils.credentials.get_openapi_config")
    @patch("alibabacloud_sts20150401.client.Client")
    def test_raises_runtime_error_on_failure(self, mock_sts_class, mock_get_config):
        """Test RuntimeError is raised when API call fails."""
        # Setup mocks
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        
        mock_sts_client = MagicMock()
        mock_sts_client.get_caller_identity.side_effect = Exception("API Error")
        mock_sts_class.return_value = mock_sts_client
        
        # Execute & Verify
        with pytest.raises(RuntimeError, match="Failed to get account ID"):
            get_account_id()

