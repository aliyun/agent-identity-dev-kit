"""Tests for the IdentityClient class."""
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, PropertyMock
import pytest
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.models import Config as CredentialConfig
from agent_identity_python_sdk.core.identity import IdentityClient, _get_sts_cache_key
from agent_identity_python_sdk.model.stscredential import STSCredential


class TestGetStsCacheKey:
    """Test cases for _get_sts_cache_key function."""

    def test_get_sts_cache_key(self):
        """Test that the cache key is generated correctly."""
        user_id = "user123"
        id_token = "token456"
        role_session_name = "session789"
        
        expected_key = f"{user_id}:{id_token}:{role_session_name}"
        actual_key = _get_sts_cache_key(user_id, id_token, role_session_name)
        
        assert actual_key == expected_key


class TestIdentityClientInitialization:
    """Test cases for IdentityClient initialization."""

    def test_initialization_with_defaults(self):
        """Test IdentityClient initialization with default values."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            # Create a mock credential instance
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            assert client.region_id == "cn-beijing"
            assert client.use_sts is True  # Default value from environment
            assert client.control_api_endpoint is None
            assert client.data_api_endpoint is None
            # Verify that credential client was created
            mock_credential_client.assert_called_once_with()  # Check that credential client was created with no arguments
            assert client.control_client is mock_control_client
            assert client.data_client is mock_data_client

    def test_initialization_with_custom_endpoints(self):
        """Test IdentityClient initialization with custom endpoints."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(
                region_id="us-west-1",
                data_api_endpoint="custom-data-endpoint.com",
                control_api_endpoint="custom-control-endpoint.com"
            )
            
            assert client.region_id == "us-west-1"
            assert client.data_api_endpoint == "custom-data-endpoint.com"
            assert client.control_api_endpoint == "custom-control-endpoint.com"
            mock_credential_client.assert_called_once_with()

    def test_initialization_with_sts_disabled(self):
        """Test IdentityClient initialization with STS disabled."""
        with patch.dict(os.environ, {"AGENT_IDENTITY_USE_STS": "false"}):
            with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
                 patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
                 patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
                
                mock_credential_instance = Mock()
                mock_credential_client.return_value = mock_credential_instance
                
                mock_control_client = Mock()
                mock_control_client_class.return_value = mock_control_client
                
                mock_data_client = Mock()
                mock_data_client_class.return_value = mock_data_client
                
                client = IdentityClient(region_id="cn-beijing")
                
                assert client.use_sts is False

    def test_initialization_with_sts_enabled(self):
        """Test IdentityClient initialization with STS enabled."""
        with patch.dict(os.environ, {"AGENT_IDENTITY_USE_STS": "true"}):
            with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
                 patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
                 patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
                
                mock_credential_instance = Mock()
                mock_credential_client.return_value = mock_credential_instance
                
                mock_control_client = Mock()
                mock_control_client_class.return_value = mock_control_client
                
                mock_data_client = Mock()
                mock_data_client_class.return_value = mock_data_client
                
                client = IdentityClient(region_id="cn-beijing")
                
                assert client.use_sts is True


class TestCreateWorkloadIdentity:
    """Test cases for create_workload_identity method."""

    def test_create_workload_identity_with_provided_name(self):
        """Test creating workload identity with a provided name."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_workload_identity = Mock()
            mock_workload_identity.workload_identity_name = "my-workload"
            mock_response_body = Mock()
            mock_response_body.workload_identity = mock_workload_identity
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.control_client, 'create_workload_identity', return_value=mock_response):
                result = client.create_workload_identity(workload_identity_name="my-workload")
                
                assert result == "my-workload"

    def test_create_workload_identity_without_name_generates_uuid(self):
        """Test creating workload identity without providing a name (generates UUID)."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_workload_identity = Mock()
            mock_workload_identity.workload_identity_name = "workload-12345678"
            mock_response_body = Mock()
            mock_response_body.workload_identity = mock_workload_identity
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch('uuid.uuid4', return_value=type('obj', (object,), {'hex': '1234567890abcdef'})()):
                with patch.object(client.control_client, 'create_workload_identity', return_value=mock_response):
                    result = client.create_workload_identity()
                    
                    assert result.startswith("workload-")
                    assert len(result) == len("workload-12345678")  # UUID hex[:8]

    def test_create_workload_identity_with_all_params(self):
        """Test creating workload identity with all parameters."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_workload_identity = Mock()
            mock_workload_identity.workload_identity_name = "my-workload"
            mock_response_body = Mock()
            mock_response_body.workload_identity = mock_workload_identity
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.control_client, 'create_workload_identity', return_value=mock_response):
                result = client.create_workload_identity(
                    workload_identity_name="my-workload",
                    role_arn="role-arn",
                    allowed_resource_oauth2_return_urls=["http://example.com"],
                    identity_provider_name="my-provider"
                )
                
                assert result == "my-workload"

    def test_create_workload_identity_with_empty_allowed_urls(self):
        """Test creating workload identity with empty allowed URLs list."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_workload_identity = Mock()
            mock_workload_identity.workload_identity_name = "my-workload"
            mock_response_body = Mock()
            mock_response_body.workload_identity = mock_workload_identity
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.control_client, 'create_workload_identity', return_value=mock_response):
                result = client.create_workload_identity(
                    workload_identity_name="my-workload",
                    allowed_resource_oauth2_return_urls=[]
                )
                
                assert result == "my-workload"

    def test_create_workload_identity_error_handling(self):
        """Test error handling when creating workload identity fails."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            with patch.object(client.control_client, 'create_workload_identity', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    client.create_workload_identity(workload_identity_name="my-workload")

    def test_create_workload_identity_missing_workload_identity_in_response(self):
        """Test error handling when response has no workload_identity."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            # Mock response with body but no workload_identity attribute
            mock_response_body = Mock()
            del mock_response_body.workload_identity  # Remove the attribute
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.control_client, 'create_workload_identity', return_value=mock_response):
                with pytest.raises(AttributeError):
                    client.create_workload_identity(workload_identity_name="my-workload")

class TestGetWorkloadAccessToken:
    """Test cases for get_workload_access_token method."""

    def test_get_workload_access_token_with_user_token(self):
        """Test getting workload access token using user token."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.workload_access_token = "workload-token-jwt"
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_workload_access_token_for_jwt', return_value=mock_response):
                result = client.get_workload_access_token("my-workload", user_token="user-jwt")
                
                assert result == "workload-token-jwt"

    def test_get_workload_access_token_with_user_id(self):
        """Test getting workload access token using user ID."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.workload_access_token = "workload-token-userid"
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_workload_access_token_for_user_id', return_value=mock_response):
                result = client.get_workload_access_token("my-workload", user_id="user123")
                
                assert result == "workload-token-userid"

    def test_get_workload_access_token_without_user_info(self):
        """Test getting workload access token without user info."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.workload_access_token = "workload-token-anon"
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_workload_access_token', return_value=mock_response):
                result = client.get_workload_access_token("my-workload")
                
                assert result == "workload-token-anon"

    def test_get_workload_access_token_precedence_user_token_over_user_id(self):
        """Test that user token takes precedence over user ID when both are provided."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.workload_access_token = "workload-token-priority"
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_workload_access_token_for_jwt', return_value=mock_response):
                result = client.get_workload_access_token("my-workload", user_token="user-jwt", user_id="user123")
                
                assert result == "workload-token-priority"

    def test_get_workload_access_token_error_handling(self):
        """Test error handling when getting workload access token fails."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            with patch.object(client.data_client, 'get_workload_access_token', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    client.get_workload_access_token("my-workload")


class TestConfirmUserAuth:
    """Test cases for confirm_user_auth method."""

    def test_confirm_user_auth_with_user_id(self):
        """Test confirming user authentication with user ID."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response = Mock()
            
            with patch.object(client.data_client, 'complete_resource_token_auth', return_value=mock_response):
                result = client.confirm_user_auth("session-uri", user_id="user123")
                
                assert result == mock_response

    def test_confirm_user_auth_with_user_token(self):
        """Test confirming user authentication with user token."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response = Mock()
            
            with patch.object(client.data_client, 'complete_resource_token_auth', return_value=mock_response):
                result = client.confirm_user_auth("session-uri", user_token="user-jwt")
                
                assert result == mock_response

    def test_confirm_user_auth_with_both_user_id_and_token(self):
        """Test confirming user authentication with both user ID and token."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response = Mock()
            
            with patch.object(client.data_client, 'complete_resource_token_auth', return_value=mock_response):
                result = client.confirm_user_auth("session-uri", user_id="user123", user_token="user-jwt")
                
                assert result == mock_response

    def test_confirm_user_auth_with_neither_user_id_nor_token(self):
        """Test confirming user authentication without user ID or token."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response = Mock()
            
            with patch.object(client.data_client, 'complete_resource_token_auth', return_value=mock_response):
                result = client.confirm_user_auth("session-uri")
                
                assert result == mock_response

    def test_confirm_user_auth_error_handling(self):
        """Test error handling when confirming user authentication fails."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            with patch.object(client.data_client, 'complete_resource_token_auth', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    client.confirm_user_auth("session-uri", user_id="user123")


class TestGetToken:
    """Test cases for get_token method."""

    @pytest.mark.asyncio
    async def test_get_token_returns_access_token_immediately(self):
        """Test get_token when response contains access token immediately."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.access_token = "oauth2-access-token"
            mock_response_body.authorization_url = None
            mock_response_body.session_uri = None
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                result = await client.get_token(
                    credential_provider_name="test-provider",
                    workload_identity_token="workload-token",
                    auth_flow="USER_FEDERATION"
                )
                
                assert result == "oauth2-access-token"

    @pytest.mark.asyncio
    async def test_get_token_with_on_auth_url_callback(self):
        """Test get_token when authorization URL is provided and on_auth_url callback is used."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.access_token = None
            mock_response_body.authorization_url = "https://example.com/auth"
            mock_response_body.session_uri = "session123"
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            mock_on_auth_url = AsyncMock()
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                with patch.object(client, 'poll_for_oauth2_token', new=AsyncMock(return_value="final-token")):
                    result = await client.get_token(
                        credential_provider_name="test-provider",
                        workload_identity_token="workload-token",
                        auth_flow="USER_FEDERATION",
                        on_auth_url=mock_on_auth_url
                    )
                    
                    mock_on_auth_url.assert_called_once_with("https://example.com/auth")
                    assert result == "final-token"

    @pytest.mark.asyncio
    async def test_get_token_with_sync_on_auth_url_callback(self):
        """Test get_token when authorization URL is provided and sync on_auth_url callback is used."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.access_token = None
            mock_response_body.authorization_url = "https://example.com/auth"
            mock_response_body.session_uri = "session123"
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            mock_on_auth_url = Mock()  # Synchronous callback
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                with patch.object(client, 'poll_for_oauth2_token', new=AsyncMock(return_value="final-token")):
                    result = await client.get_token(
                        credential_provider_name="test-provider",
                        workload_identity_token="workload-token",
                        auth_flow="USER_FEDERATION",
                        on_auth_url=mock_on_auth_url
                    )
                    
                    mock_on_auth_url.assert_called_once_with("https://example.com/auth")
                    assert result == "final-token"

    @pytest.mark.asyncio
    async def test_get_token_with_force_authentication(self):
        """Test get_token with force_authentication parameter."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.access_token = None
            mock_response_body.authorization_url = "https://example.com/auth"
            mock_response_body.session_uri = "session123"
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            mock_on_auth_url = AsyncMock()
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', side_effect=[
                mock_response,  # First call
                Mock(body=Mock(access_token="final-token", authorization_url=None, session_uri=None))  # Second call after setting force_authentication=False
            ]):
                with patch.object(client, 'poll_for_oauth2_token', new=AsyncMock(return_value="final-token")):
                    result = await client.get_token(
                        credential_provider_name="test-provider",
                        workload_identity_token="workload-token",
                        auth_flow="USER_FEDERATION",
                        on_auth_url=mock_on_auth_url,
                        force_authentication=True
                    )
                    
                    assert result == "final-token"

    @pytest.mark.asyncio
    async def test_get_token_with_custom_parameters(self):
        """Test get_token with custom parameters."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.access_token = "oauth2-access-token"
            mock_response_body.authorization_url = None
            mock_response_body.session_uri = None
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                result = await client.get_token(
                    credential_provider_name="test-provider",
                    workload_identity_token="workload-token",
                    auth_flow="USER_FEDERATION",
                    custom_parameters={"param1": "value1", "param2": "value2"}
                )
                
                assert result == "oauth2-access-token"

    @pytest.mark.asyncio
    async def test_get_token_with_scopes(self):
        """Test get_token with scopes."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.access_token = "oauth2-access-token"
            mock_response_body.authorization_url = None
            mock_response_body.session_uri = None
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                result = await client.get_token(
                    credential_provider_name="test-provider",
                    scopes=["scope1", "scope2"],
                    workload_identity_token="workload-token",
                    auth_flow="USER_FEDERATION"
                )
                
                assert result == "oauth2-access-token"

    @pytest.mark.asyncio
    async def test_get_token_with_callback_url(self):
        """Test get_token with callback URL."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.access_token = "oauth2-access-token"
            mock_response_body.authorization_url = None
            mock_response_body.session_uri = None
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                result = await client.get_token(
                    credential_provider_name="test-provider",
                    workload_identity_token="workload-token",
                    auth_flow="USER_FEDERATION",
                    callback_url="https://example.com/callback"
                )
                
                assert result == "oauth2-access-token"

    @pytest.mark.asyncio
    async def test_get_token_with_custom_state(self):
        """Test get_token with custom state."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.access_token = "oauth2-access-token"
            mock_response_body.authorization_url = None
            mock_response_body.session_uri = None
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                result = await client.get_token(
                    credential_provider_name="test-provider",
                    workload_identity_token="workload-token",
                    auth_flow="USER_FEDERATION",
                    custom_state="custom-state-value"
                )
                
                assert result == "oauth2-access-token"

    @pytest.mark.asyncio
    async def test_get_token_with_custom_credential(self):
        """Test get_token with custom credential when STS is enabled."""
        with patch.dict(os.environ, {"AGENT_IDENTITY_USE_STS": "true"}):
            with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
                 patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
                 patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
                
                mock_credential_instance = Mock()
                mock_credential_client.return_value = mock_credential_instance
                
                mock_control_client = Mock()
                mock_control_client_class.return_value = mock_control_client
                
                mock_data_client = Mock()
                mock_data_client_class.return_value = mock_data_client
                
                client = IdentityClient(region_id="cn-beijing")
                mock_credential = Mock()
                mock_response_body = Mock()
                mock_response_body.access_token = "oauth2-access-token"
                mock_response_body.authorization_url = None
                mock_response_body.session_uri = None
                mock_response = Mock()
                mock_response.body = mock_response_body
                
                with patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_new_class:
                    mock_data_client_new = Mock()
                    mock_data_client_new_class.return_value = mock_data_client_new
                    
                    with patch.object(mock_data_client_new, 'get_resource_oauth2_token', return_value=mock_response):
                        result = await client.get_token(
                            credential_provider_name="test-provider",
                            workload_identity_token="workload-token",
                            auth_flow="USER_FEDERATION",
                            credential=mock_credential
                        )
                        
                        # Verify that a new data client was created with the custom credential
                        mock_data_client_new_class.assert_called()
                        assert result == "oauth2-access-token"

    @pytest.mark.asyncio
    async def test_get_token_with_sts_enabled_and_auth_url(self):
        """Test get_token when STS is enabled and authorization URL is provided."""
        with patch.dict(os.environ, {"AGENT_IDENTITY_USE_STS": "true"}):
            with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
                 patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
                 patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
                
                mock_credential_instance = Mock()
                mock_credential_client.return_value = mock_credential_instance
                
                mock_control_client = Mock()
                mock_control_client_class.return_value = mock_control_client
                
                mock_data_client = Mock()
                mock_data_client_class.return_value = mock_data_client
                
                client = IdentityClient(region_id="cn-beijing")
                
                mock_response_body = Mock()
                mock_response_body.access_token = None
                mock_response_body.authorization_url = "https://example.com/auth"
                mock_response_body.session_uri = "session123"
                mock_response = Mock()
                mock_response.body = mock_response_body
                
                mock_on_auth_url = AsyncMock()
                
                with patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_new_class:
                    mock_data_client_new = Mock()
                    mock_data_client_new_class.return_value = mock_data_client_new
                    
                    with patch.object(mock_data_client_new, 'get_resource_oauth2_token', return_value=mock_response):
                        with patch.object(client, 'poll_for_oauth2_token', new=AsyncMock(return_value="final-token")):
                            result = await client.get_token(
                                credential_provider_name="test-provider",
                                workload_identity_token="workload-token",
                                auth_flow="USER_FEDERATION",
                                on_auth_url=mock_on_auth_url
                            )
                            
                            # Verify that a new data client was created when STS is enabled
                            mock_data_client_new_class.assert_called()
                            assert result == "final-token"

    @pytest.mark.asyncio
    async def test_get_token_error_handling(self):
        """Test error handling when getting token fails."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    await client.get_token(
                        credential_provider_name="test-provider",
                        workload_identity_token="workload-token",
                        auth_flow="USER_FEDERATION"
                    )

    @pytest.mark.asyncio
    async def test_get_token_with_api_error(self):
        """Test error handling when API call in get_token raises an exception."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    await client.get_token(
                        credential_provider_name="test-provider",
                        workload_identity_token="workload-token",
                        auth_flow="USER_FEDERATION"
                    )

    @pytest.mark.asyncio
    async def test_get_token_no_token_or_auth_url_error(self):
        """Test error handling when service returns neither token nor auth URL."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.access_token = None
            mock_response_body.authorization_url = None
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                with pytest.raises(RuntimeError, match="Failed to obtain OAuth2 token"):
                    await client.get_token(
                        credential_provider_name="test-provider",
                        workload_identity_token="workload-token",
                        auth_flow="USER_FEDERATION"
                    )


class TestGetApiKey:
    """Test cases for get_api_key method."""

    @pytest.mark.asyncio
    async def test_get_api_key_returns_key(self):
        """Test get_api_key when response contains API key."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.apikey = "test-api-key"
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_resource_apikey', return_value=mock_response):
                result = await client.get_api_key(
                    credential_provider_name="test-provider",
                    agent_identity_token="workload-token"
                )
                
                assert result == "test-api-key"

    @pytest.mark.asyncio
    async def test_get_api_key_with_custom_credential(self):
        """Test get_api_key with custom credential when STS is enabled."""
        with patch.dict(os.environ, {"AGENT_IDENTITY_USE_STS": "true"}):
            with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
                 patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
                 patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
                
                mock_credential_instance = Mock()
                mock_credential_client.return_value = mock_credential_instance
                
                mock_control_client = Mock()
                mock_control_client_class.return_value = mock_control_client
                
                mock_data_client = Mock()
                mock_data_client_class.return_value = mock_data_client
                
                client = IdentityClient(region_id="cn-beijing")
                mock_credential = Mock()
                mock_response_body = Mock()
                mock_response_body.apikey = "test-api-key"
                mock_response = Mock()
                mock_response.body = mock_response_body
                
                with patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_new_class:
                    mock_data_client_new = Mock()
                    mock_data_client_new_class.return_value = mock_data_client_new
                    
                    with patch.object(mock_data_client_new, 'get_resource_apikey', return_value=mock_response):
                        result = await client.get_api_key(
                            credential_provider_name="test-provider",
                            agent_identity_token="workload-token",
                            credential=mock_credential
                        )
                        
                        # Verify that a new data client was created with the custom credential
                        mock_data_client_new_class.assert_called()
                        assert result == "test-api-key"

    @pytest.mark.asyncio
    async def test_get_api_key_with_sts_enabled(self):
        """Test get_api_key when STS is enabled and no custom credential is provided."""
        with patch.dict(os.environ, {"AGENT_IDENTITY_USE_STS": "true"}):
            with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
                 patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
                 patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
                
                mock_credential_instance = Mock()
                mock_credential_client.return_value = mock_credential_instance
                
                mock_control_client = Mock()
                mock_control_client_class.return_value = mock_control_client
                
                mock_data_client = Mock()
                mock_data_client_class.return_value = mock_data_client
                
                client = IdentityClient(region_id="cn-beijing")
                mock_response_body = Mock()
                mock_response_body.apikey = "test-api-key"
                mock_response = Mock()
                mock_response.body = mock_response_body
                
                with patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_new_class:
                    mock_data_client_new = Mock()
                    mock_data_client_new_class.return_value = mock_data_client_new
                    
                    with patch.object(mock_data_client_new, 'get_resource_apikey', return_value=mock_response):
                        result = await client.get_api_key(
                            credential_provider_name="test-provider",
                            agent_identity_token="workload-token"
                        )
                        
                        # Verify that a new data client was created when STS is enabled
                        mock_data_client_new_class.assert_called()
                        assert result == "test-api-key"

    @pytest.mark.asyncio
    async def test_get_api_key_error_handling(self):
        """Test error handling when getting API key fails."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            with patch.object(client.data_client, 'get_resource_apikey', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    await client.get_api_key(
                        credential_provider_name="test-provider",
                        agent_identity_token="workload-token"
                    )

    @pytest.mark.asyncio
    async def test_get_api_key_no_key_error(self):
        """Test error handling when service does not return an API key."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            mock_response_body = Mock()
            mock_response_body.apikey = None
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'get_resource_apikey', return_value=mock_response):
                with pytest.raises(RuntimeError, match="Agent identity service did not return an API key."):
                    await client.get_api_key(
                        credential_provider_name="test-provider",
                        agent_identity_token="workload-token"
                    )


class TestConvertToCredential:
    """Test cases for _convert_to_credential static method."""

    def test_convert_to_credential(self):
        """Test converting STSCredential to CredentialClient."""
        sts_credential = STSCredential(
            access_key_id="test-access-key-id",
            access_key_secret="test-access-key-secret",
            security_token="test-security-token",
            expiration="2025-12-31T23:59:59Z"
        )
        
        with patch('agent_identity_python_sdk.core.identity.CredentialConfig') as mock_config_class:
            mock_config_instance = Mock()
            mock_config_class.return_value = mock_config_instance
            
            with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_class:
                result = IdentityClient._convert_to_credential(sts_credential)
                
                # Verify that Config was created with the correct parameters
                mock_config_class.assert_called_once_with(
                    type='sts',
                    access_key_id="test-access-key-id",
                    access_key_secret="test-access-key-secret",
                    security_token="test-security-token"
                )
                
                # Verify that CredentialClient was instantiated with the config
                mock_credential_class.assert_called_once_with(mock_config_instance)


class TestGetStsCredentialClient:
    """Test cases for get_sts_credential_client method."""

    @pytest.mark.asyncio
    async def test_get_sts_credential_client_with_cached_credential(self):
        """Test getting STS credential client when credential is cached."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            # Mock cached credential
            cached_credential = STSCredential(
                access_key_id="cached-access-key-id",
                access_key_secret="cached-access-key-secret",
                security_token="cached-security-token",
                expiration="2025-12-31T23:59:59Z"
            )
            
            with patch('agent_identity_python_sdk.core.identity.get_cached_credential', return_value=cached_credential):
                with patch('agent_identity_python_sdk.core.identity.store_credential_in_cache') as mock_store:
                    with patch.object(client, '_convert_to_credential') as mock_convert:
                        result = await client.get_sts_credential_client("workload-token", "user123", "user-token")
                        
                        # Verify that cache was checked and cached credential was used
                        mock_convert.assert_called_once_with(cached_credential)
                        mock_store.assert_not_called()  # No need to store since it was already cached

    @pytest.mark.asyncio
    async def test_get_sts_credential_client_without_cached_credential(self):
        """Test getting STS credential client when credential is not cached."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            # Mock no cached credential
            mock_sts_credential = STSCredential(
                access_key_id="new-access-key-id",
                access_key_secret="new-access-key-secret",
                security_token="new-security-token",
                expiration="2025-12-31T23:59:59Z"
            )
            
            with patch('agent_identity_python_sdk.core.identity.get_cached_credential', return_value=None):
                with patch.object(client, 'assume_role_for_workload_identity', return_value=mock_sts_credential) as mock_assume:
                    with patch('agent_identity_python_sdk.core.identity.store_credential_in_cache') as mock_store:
                        with patch.object(client, '_convert_to_credential') as mock_convert:
                            result = await client.get_sts_credential_client("workload-token", "user123", "user-token")
                            
                            # Verify that assume_role was called, credential was stored, and converted
                            mock_assume.assert_called_once()
                            mock_store.assert_called_once()
                            mock_convert.assert_called_once_with(mock_sts_credential)


class TestAssumeRoleForWorkloadIdentity:
    """Test cases for assume_role_for_workload_identity method."""

    @pytest.mark.asyncio
    async def test_assume_role_for_workload_identity_basic(self):
        """Test assuming role for workload identity with basic parameters."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            # Mock the response from the API
            mock_credentials = Mock()
            mock_credentials.access_key_id = "sts-access-key-id"
            mock_credentials.access_key_secret = "sts-access-key-secret"
            mock_credentials.security_token = "sts-security-token"
            mock_credentials.expiration = "2025-12-31T23:59:59Z"
            
            mock_response_body = Mock()
            mock_response_body.credentials = mock_credentials
            
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'assume_role_for_workload_identity', return_value=mock_response):
                result = await client.assume_role_for_workload_identity(
                    workload_token="workload-token",
                    role_session_name="test-session"
                )
                
                assert isinstance(result, STSCredential)
                assert result.access_key_id == "sts-access-key-id"
                assert result.access_key_secret == "sts-access-key-secret"
                assert result.security_token == "sts-security-token"
                assert result.expiration == "2025-12-31T23:59:59Z"

    @pytest.mark.asyncio
    async def test_assume_role_for_workload_identity_with_duration_and_policy(self):
        """Test assuming role for workload identity with duration and policy."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            # Mock the response from the API
            mock_credentials = Mock()
            mock_credentials.access_key_id = "sts-access-key-id"
            mock_credentials.access_key_secret = "sts-access-key-secret"
            mock_credentials.security_token = "sts-security-token"
            mock_credentials.expiration = "2025-12-31T23:59:59Z"
            
            mock_response_body = Mock()
            mock_response_body.credentials = mock_credentials
            
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            with patch.object(client.data_client, 'assume_role_for_workload_identity', return_value=mock_response):
                result = await client.assume_role_for_workload_identity(
                    workload_token="workload-token",
                    role_session_name="test-session",
                    duration_seconds="7200",
                    policy='{"Version": "1", "Statement": []}'
                )
                
                assert isinstance(result, STSCredential)
                assert result.access_key_id == "sts-access-key-id"

    @pytest.mark.asyncio
    async def test_assume_role_for_workload_identity_error_handling(self):
        """Test error handling when assuming role for workload identity fails."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            with patch.object(client.data_client, 'assume_role_for_workload_identity', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    await client.assume_role_for_workload_identity(
                        workload_token="workload-token",
                        role_session_name="test-session"
                    )


class TestPollForOAuth2Token:
    """Test cases for poll_for_oauth2_token method."""

    @pytest.mark.asyncio
    async def test_poll_for_oauth2_token_success_on_first_attempt(self):
        """Test polling for OAuth2 token that succeeds on the first attempt."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            mock_response_body = Mock()
            mock_response_body.access_token = "poll-token"
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            request = Mock()
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                result = await client.poll_for_oauth2_token(request, max_retries=3, delay_sec=0.1)
                
                assert result == "poll-token"
                client.data_client.get_resource_oauth2_token.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_poll_for_oauth2_token_success_on_second_attempt(self):
        """Test polling for OAuth2 token that succeeds on the second attempt."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            # First call returns no token, second call returns token
            mock_response_body_no_token = Mock()
            mock_response_body_no_token.access_token = None
            mock_response_no_token = Mock()
            mock_response_no_token.body = mock_response_body_no_token
            
            mock_response_body_with_token = Mock()
            mock_response_body_with_token.access_token = "poll-token"
            mock_response_with_token = Mock()
            mock_response_with_token.body = mock_response_body_with_token
            
            request = Mock()
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', side_effect=[
                mock_response_no_token, 
                mock_response_with_token
            ]):
                with patch('asyncio.sleep', return_value=None):  # Mock sleep to avoid actual delays
                    result = await client.poll_for_oauth2_token(request, max_retries=3, delay_sec=0.1)
                    
                    assert result == "poll-token"
                    assert client.data_client.get_resource_oauth2_token.call_count == 2

    @pytest.mark.asyncio
    async def test_poll_for_oauth2_token_max_retries_exceeded(self):
        """Test polling for OAuth2 token that fails after max retries."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            # Always return response without token
            mock_response_body = Mock()
            mock_response_body.access_token = None
            mock_response = Mock()
            mock_response.body = mock_response_body
            
            request = Mock()
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', return_value=mock_response):
                with patch('asyncio.sleep', return_value=None):  # Mock sleep to avoid actual delays
                    with pytest.raises(RuntimeError, match="Failed to get OAuth2 token after 2 attempts"):
                        await client.poll_for_oauth2_token(request, max_retries=2, delay_sec=0.1)

    @pytest.mark.asyncio
    async def test_poll_for_oauth2_token_with_exception(self):
        """Test polling for OAuth2 token when API call raises an exception."""
        with patch('agent_identity_python_sdk.core.identity.CredentialClient') as mock_credential_client, \
             patch('agent_identity_python_sdk.core.identity.ControlClient') as mock_control_client_class, \
             patch('agent_identity_python_sdk.core.identity.DataClient') as mock_data_client_class:
            
            mock_credential_instance = Mock()
            mock_credential_client.return_value = mock_credential_instance
            
            mock_control_client = Mock()
            mock_control_client_class.return_value = mock_control_client
            
            mock_data_client = Mock()
            mock_data_client_class.return_value = mock_data_client
            
            client = IdentityClient(region_id="cn-beijing")
            
            request = Mock()
            
            with patch.object(client.data_client, 'get_resource_oauth2_token', side_effect=Exception("API Error")):
                with patch('asyncio.sleep', return_value=None):  # Mock sleep to avoid actual delays
                    with pytest.raises(RuntimeError, match="Failed to get OAuth2 token after 2 attempts"):
                        await client.poll_for_oauth2_token(request, max_retries=2, delay_sec=0.1)