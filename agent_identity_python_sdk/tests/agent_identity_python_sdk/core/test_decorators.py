"""Tests for the decorators module."""
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock

import pytest

from agent_identity_python_sdk.core.decorators import (
    get_region,
    requires_access_token,
    requires_api_key,
    requires_sts_token,
    requires_workload_access_token,
    _get_workload_access_token,
    _get_workload_access_token_local,
    _has_running_loop
)
from agent_identity_python_sdk.model.stscredential import STSCredential

os.environ.setdefault("AGENT_IDENTITY_REGION_ID", "cn-beijing")
os.environ.setdefault("ALIBABA_CLOUD_ACCESS_KEY_ID", "mock-akid")
os.environ.setdefault("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "mock-aksecret")
print(os.environ.get("AGENT_IDENTITY_REGION_ID"))
class TestGetRegion:
    """Test cases for get_region function."""

    def test_get_region_from_env(self):
        """Test get_region function with environment variable set."""
        with patch.dict(os.environ, {"AGENT_IDENTITY_REGION_ID": "us-west-1"}):
            assert get_region() == "us-west-1"

    def test_get_region_default(self):
        """Test get_region function with no environment variable set."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_region() == "cn-beijing"


class TestHasRunningLoop:
    """Test cases for _has_running_loop function."""

    def test_has_running_loop_false(self):
        """Test _has_running_loop when no event loop is running."""
        # This test runs in a thread without an event loop
        assert _has_running_loop() is False

    @pytest.mark.asyncio
    async def test_has_running_loop_true(self):
        """Test _has_running_loop when event loop is running."""
        # This test runs in an async context with an event loop
        assert _has_running_loop() is True


class TestRequiresAccessToken:
    """Test cases for requires_access_token decorator."""

    @pytest.mark.asyncio
    async def test_requires_access_token_async_function(self):
        """Test requires_access_token decorator with async function."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_token = AsyncMock(return_value="access-token")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                mock_get_token.return_value = "workload-token"

                @requires_access_token(
                    credential_provider_name="test-provider",
                    inject_param_name="access_token",
                    auth_flow="USER_FEDERATION"
                )
                async def sample_async_function(access_token):
                    return f"Token: {access_token}"

                os.environ.setdefault("AGENT_IDENTITY_REGION_ID", "cn-beijing")
                os.environ.setdefault("ALIBABA_CLOUD_ACCESS_KEY_ID", "mock-akid")
                os.environ.setdefault("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "mock-aksecret")
                # Execute
                result = await sample_async_function()

                # Verify
                assert result == "Token: access-token"
                mock_identity_client.get_token.assert_called_once()

    def test_requires_access_token_sync_function(self):
        """Test requires_access_token decorator with sync function."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_token = AsyncMock(return_value="access-token")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_access_token(
                        credential_provider_name="test-provider",
                        inject_param_name="access_token",
                        auth_flow="USER_FEDERATION"
                    )
                    def sample_function(access_token):
                        return f"Token: {access_token}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "Token: access-token"
                    mock_identity_client.get_token.assert_called_once()

    def test_requires_access_token_with_scopes(self):
        """Test requires_access_token decorator with scopes."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_token = AsyncMock(return_value="access-token")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_access_token(
                        credential_provider_name="test-provider",
                        inject_param_name="access_token",
                        scopes=["read", "write"],
                        auth_flow="USER_FEDERATION"
                    )
                    def sample_function(access_token):
                        return f"Token: {access_token}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "Token: access-token"
                    mock_identity_client.get_token.assert_called_once()
                    # Verify that scopes were passed to get_token
                    call_args = mock_identity_client.get_token.call_args
                    assert call_args.kwargs['scopes'] == ["read", "write"]

    def test_requires_access_token_with_custom_parameters(self):
        """Test requires_access_token decorator with custom parameters."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_token = AsyncMock(return_value="access-token")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_access_token(
                        credential_provider_name="test-provider",
                        inject_param_name="access_token",
                        auth_flow="USER_FEDERATION",
                        custom_parameters={"param1": "value1"}
                    )
                    def sample_function(access_token):
                        return f"Token: {access_token}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "Token: access-token"
                    mock_identity_client.get_token.assert_called_once()
                    # Verify that custom_parameters were passed to get_token
                    call_args = mock_identity_client.get_token.call_args
                    assert call_args.kwargs['custom_parameters'] == {"param1": "value1"}

    def test_requires_access_token_async_in_async_env(self):
        """Test requires_access_token decorator with sync function in async environment."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_token = AsyncMock(return_value="access-token")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=True):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
                        mock_future = MagicMock()
                        mock_future.result.return_value = "access-token"
                        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future

                        @requires_access_token(
                            credential_provider_name="test-provider",
                            inject_param_name="access_token",
                            auth_flow="USER_FEDERATION"
                        )
                        def sample_function(access_token):
                            return f"Token: {access_token}"

                        # Execute
                        result = sample_function()

                        # Verify
                        assert result == "Token: access-token"
                        mock_executor.return_value.__enter__.return_value.submit.assert_called_once()


class TestRequiresApiKey:
    """Test cases for requires_api_key decorator."""

    @pytest.mark.asyncio
    async def test_requires_api_key_async_function(self):
        """Test requires_api_key decorator with async function."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_api_key = AsyncMock(return_value="api-key")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                mock_get_token.return_value = "workload-token"

                @requires_api_key(
                    credential_provider_name="test-provider",
                    inject_param_name="api_key"
                )
                async def sample_async_function(api_key):
                    return f"API Key: {api_key}"

                # Execute
                result = await sample_async_function()

                # Verify
                assert result == "API Key: api-key"
                mock_identity_client.get_api_key.assert_called_once()

    def test_requires_api_key_sync_function(self):
        """Test requires_api_key decorator with sync function."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_api_key = AsyncMock(return_value="api-key")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_api_key(
                        credential_provider_name="test-provider",
                        inject_param_name="api_key"
                    )
                    def sample_function(api_key):
                        return f"API Key: {api_key}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "API Key: api-key"
                    mock_identity_client.get_api_key.assert_called_once()

    def test_requires_api_key_async_in_async_env(self):
        """Test requires_api_key decorator with sync function in async environment."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_api_key = AsyncMock(return_value="api-key")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=True):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
                        mock_future = MagicMock()
                        mock_future.result.return_value = "api-key"
                        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future

                        @requires_api_key(
                            credential_provider_name="test-provider",
                            inject_param_name="api_key"
                        )
                        def sample_function(api_key):
                            return f"API Key: {api_key}"

                        # Execute
                        result = sample_function()

                        # Verify
                        assert result == "API Key: api-key"
                        mock_executor.return_value.__enter__.return_value.submit.assert_called_once()


class TestRequiresStsToken:
    """Test cases for requires_sts_token decorator."""

    @pytest.mark.asyncio
    async def test_requires_sts_token_async_function(self):
        """Test requires_sts_token decorator with async function."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_sts_credential = STSCredential(
            access_key_id="test-access-key-id",
            access_key_secret="test-access-key-secret",
            security_token="test-security-token",
            expiration="2025-12-31T23:59:59Z"
        )
        mock_identity_client.assume_role_for_workload_identity = AsyncMock(return_value=mock_sts_credential)

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                mock_get_token.return_value = "workload-token"

                @requires_sts_token(
                    inject_param_name="sts_credential"
                )
                async def sample_async_function(sts_credential):
                    return f"STS Credential: {sts_credential.access_key_id}"

                # Execute
                result = await sample_async_function()

                # Verify
                assert result == "STS Credential: test-access-key-id"
                mock_identity_client.assume_role_for_workload_identity.assert_called_once()

    def test_requires_sts_token_sync_function(self):
        """Test requires_sts_token decorator with sync function."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_sts_credential = STSCredential(
            access_key_id="test-access-key-id",
            access_key_secret="test-access-key-secret",
            security_token="test-security-token",
            expiration="2025-12-31T23:59:59Z"
        )
        mock_identity_client.assume_role_for_workload_identity = AsyncMock(return_value=mock_sts_credential)

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_sts_token(
                        inject_param_name="sts_credential"
                    )
                    def sample_function(sts_credential):
                        return f"STS Credential: {sts_credential.access_key_id}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "STS Credential: test-access-key-id"
                    mock_identity_client.assume_role_for_workload_identity.assert_called_once()

    def test_requires_sts_token_with_session_duration(self):
        """Test requires_sts_token decorator with custom session duration."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_sts_credential = STSCredential(
            access_key_id="test-access-key-id",
            access_key_secret="test-access-key-secret",
            security_token="test-security-token",
            expiration="2025-12-31T23:59:59Z"
        )
        mock_identity_client.assume_role_for_workload_identity = AsyncMock(return_value=mock_sts_credential)

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_sts_token(
                        inject_param_name="sts_credential",
                        session_duration=7200  # 2 hours
                    )
                    def sample_function(sts_credential):
                        return f"STS Credential: {sts_credential.access_key_id}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "STS Credential: test-access-key-id"
                    call_args = mock_identity_client.assume_role_for_workload_identity.call_args
                    assert call_args.kwargs['duration_seconds'] == 7200

    def test_requires_sts_token_with_policy(self):
        """Test requires_sts_token decorator with custom policy."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_sts_credential = STSCredential(
            access_key_id="test-access-key-id",
            access_key_secret="test-access-key-secret",
            security_token="test-security-token",
            expiration="2025-12-31T23:59:59Z"
        )
        mock_identity_client.assume_role_for_workload_identity = AsyncMock(return_value=mock_sts_credential)

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_sts_token(
                        inject_param_name="sts_credential",
                        policy='{"Version": "1"}'
                    )
                    def sample_function(sts_credential):
                        return f"STS Credential: {sts_credential.access_key_id}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "STS Credential: test-access-key-id"
                    call_args = mock_identity_client.assume_role_for_workload_identity.call_args
                    assert call_args.kwargs['policy'] == '{"Version": "1"}'

    def test_requires_sts_token_async_in_async_env(self):
        """Test requires_sts_token decorator with sync function in async environment."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_sts_credential = STSCredential(
            access_key_id="test-access-key-id",
            access_key_secret="test-access-key-secret",
            security_token="test-security-token",
            expiration="2025-12-31T23:59:59Z"
        )
        mock_identity_client.assume_role_for_workload_identity = AsyncMock(return_value=mock_sts_credential)

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=True):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
                        mock_future = MagicMock()
                        mock_future.result.return_value = mock_sts_credential
                        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future

                        @requires_sts_token(
                            inject_param_name="sts_credential"
                        )
                        def sample_function(sts_credential):
                            return f"STS Credential: {sts_credential.access_key_id}"

                        # Execute
                        result = sample_function()

                        # Verify
                        assert result == "STS Credential: test-access-key-id"
                        mock_executor.return_value.__enter__.return_value.submit.assert_called_once()


class TestGetWorkloadAccessToken:
    """Test cases for _get_workload_access_token and related functions."""

    @pytest.mark.asyncio
    async def test_get_workload_access_token_from_context(self):
        """Test _get_workload_access_token when token is available in context."""
        # Setup mocks
        mock_identity_client = Mock()

        with patch('agent_identity_python_sdk.core.decorators.AgentIdentityContext') as mock_context:
            mock_context.get_workload_access_token.return_value = "cached-token"

            # Execute
            token = await _get_workload_access_token(mock_identity_client)

            # Verify
            assert token == "cached-token"
            mock_context.get_workload_access_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workload_access_token_not_in_context(self):
        """Test _get_workload_access_token when token is not in context."""
        # Setup mocks
        mock_identity_client = Mock()

        with patch('agent_identity_python_sdk.core.decorators.AgentIdentityContext') as mock_context:
            mock_context.get_workload_access_token.return_value = None

            with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token_local') as mock_local:
                mock_local.return_value = "new-token"

                # Execute
                token = await _get_workload_access_token(mock_identity_client)

                # Verify
                assert token == "new-token"
                mock_context.get_workload_access_token.assert_called_once()
                mock_local.assert_called_once()


class TestRequriesWorkloadAccessToken:
    """Test cases for requires_workload_access_token decorator."""

    @pytest.mark.asyncio
    async def test_requires_workload_access_token_async_function(self):
        """Test requires_workload_access_token decorator with async function."""
        # Setup mocks
        mock_identity_client = Mock()
        
        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client
            
            with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                mock_get_token.return_value = "workload-access-token"

                @requires_workload_access_token(inject_param_name="workload_token")
                async def sample_async_function(workload_token):
                    return f"Workload Token: {workload_token}"

                # Execute
                result = await sample_async_function()

                # Verify
                assert result == "Workload Token: workload-access-token"
                mock_get_token.assert_called_once()

    def test_requires_workload_access_token_sync_function(self):
        """Test requires_workload_access_token decorator with sync function."""

        # Setup mocks
        mock_identity_client = Mock()
        
        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client
            
            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-access-token"

                    @requires_workload_access_token(inject_param_name="workload_token")
                    def sample_function(workload_token):
                        return f"Workload Token: {workload_token}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "Workload Token: workload-access-token"
                    mock_get_token.assert_called_once()

    def test_requires_workload_access_token_default_param_name(self):
        """Test requires_workload_access_token decorator with default parameter name."""
        # Setup mocks
        mock_identity_client = Mock()
        
        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client
            
            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-access-token"

                    @requires_workload_access_token()
                    def sample_function(workload_access_token):
                        return f"Workload Token: {workload_access_token}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "Workload Token: workload-access-token"
                    mock_get_token.assert_called_once()

    def test_requires_workload_access_token_async_in_async_env(self):
        """Test requires_workload_access_token decorator with sync function in async environment."""



class TestConcurrency:
    """Test cases for concurrent access scenarios."""

    def test_concurrent_requires_access_token_calls(self):
        """Test concurrent calls to requires_access_token decorated function."""
        # Setup
        mock_identity_client = Mock()
        mock_identity_client.get_token = AsyncMock(return_value="access-token")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_access_token(
                        credential_provider_name="test-provider",
                        inject_param_name="access_token",
                        auth_flow="USER_FEDERATION"
                    )
                    def sample_function(access_token):
                        return f"Token: {access_token}"

                    # Execute multiple calls
                    results = []
                    for _ in range(3):
                        result = sample_function()
                        results.append(result)

                    # Verify
                    assert all(r == "Token: access-token" for r in results)
                    assert mock_identity_client.get_token.call_count == 3

    def test_concurrent_requires_api_key_calls(self):
        """Test concurrent calls to requires_api_key decorated function."""
        # Setup
        mock_identity_client = Mock()
        mock_identity_client.get_api_key = AsyncMock(return_value="api-key")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_api_key(
                        credential_provider_name="test-provider",
                        inject_param_name="api_key"
                    )
                    def sample_function(api_key):
                        return f"API Key: {api_key}"

                    # Execute multiple calls
                    results = []
                    for _ in range(3):
                        result = sample_function()
                        results.append(result)

                    # Verify
                    assert all(r == "API Key: api-key" for r in results)
                    assert mock_identity_client.get_api_key.call_count == 3

    def test_concurrent_requires_sts_token_calls(self):
        """Test concurrent calls to requires_sts_token decorated function."""
        # Setup
        mock_identity_client = Mock()
        mock_sts_credential = STSCredential(
            access_key_id="test-access-key-id",
            access_key_secret="test-access-key-secret",
            security_token="test-security-token",
            expiration="2025-12-31T23:59:59Z"
        )
        mock_identity_client.assume_role_for_workload_identity = AsyncMock(return_value=mock_sts_credential)

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_sts_token(
                        inject_param_name="sts_credential"
                    )
                    def sample_function(sts_credential):
                        return f"STS Credential: {sts_credential.access_key_id}"

                    # Execute multiple calls
                    results = []
                    for _ in range(3):
                        result = sample_function()
                        results.append(result)

                    # Verify
                    assert all(r == "STS Credential: test-access-key-id" for r in results)
                    assert mock_identity_client.assume_role_for_workload_identity.call_count == 3


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_decorator_with_different_into_parameter(self):
        """Test decorators with different 'into' parameter values."""
        # Test requires_access_token with custom 'into' parameter
        mock_identity_client = Mock()
        mock_identity_client.get_token = AsyncMock(return_value="access-token")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_access_token(
                        credential_provider_name="test-provider",
                        inject_param_name="custom_token_name",
                        auth_flow="USER_FEDERATION"
                    )
                    def sample_function(custom_token_name):
                        return f"Token: {custom_token_name}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "Token: access-token"

    def test_requires_api_key_with_different_into_parameter(self):
        """Test requires_api_key with different 'into' parameter."""
        # Setup
        mock_identity_client = Mock()
        mock_identity_client.get_api_key = AsyncMock(return_value="api-key")
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_api_key(
                        credential_provider_name="test-provider",
                        inject_param_name="custom_api_key_name"
                    )
                    def sample_function(custom_api_key_name):
                        return f"API Key: {custom_api_key_name}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "API Key: api-key"

    def test_requires_sts_token_with_different_into_parameter(self):
        """Test requires_sts_token with different 'into' parameter."""
        # Setup
        mock_identity_client = Mock()
        mock_sts_credential = STSCredential(
            access_key_id="test-access-key-id",
            access_key_secret="test-access-key-secret",
            security_token="test-security-token",
            expiration="2025-12-31T23:59:59Z"
        )
        mock_identity_client.assume_role_for_workload_identity = AsyncMock(return_value=mock_sts_credential)

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_sts_token(
                        inject_param_name="custom_credential_name"
                    )
                    def sample_function(custom_credential_name):
                        return f"STS Credential: {custom_credential_name.access_key_id}"

                    # Execute
                    result = sample_function()

                    # Verify
                    assert result == "STS Credential: test-access-key-id"


class TestErrorConditions:
    """Test error conditions and exception handling."""

    @pytest.mark.asyncio
    async def test_requires_access_token_exception_handling(self):
        """Test exception handling in requires_access_token decorator."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_token = AsyncMock(side_effect=Exception("API Error"))
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                mock_get_token.return_value = "workload-token"

                @requires_access_token(
                    credential_provider_name="test-provider",
                    inject_param_name="access_token",
                    auth_flow="USER_FEDERATION"
                )
                async def sample_async_function(access_token):
                    return f"Token: {access_token}"

                # Execute and expect exception
                with pytest.raises(Exception, match="API Error"):
                    await sample_async_function()

    def test_requires_api_key_exception_handling(self):
        """Test exception handling in requires_api_key decorator."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.get_api_key = AsyncMock(side_effect=Exception("API Error"))
        mock_identity_client.get_sts_credential_client = AsyncMock(return_value=Mock())

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_api_key(
                        credential_provider_name="test-provider",
                        inject_param_name="api_key"
                    )
                    def sample_function(api_key):
                        return f"API Key: {api_key}"

                    # Execute and expect exception
                    with pytest.raises(Exception, match="API Error"):
                        sample_function()

    def test_requires_sts_token_exception_handling(self):
        """Test exception handling in requires_sts_token decorator."""
        # Setup mocks
        mock_identity_client = Mock()
        mock_identity_client.assume_role_for_workload_identity = AsyncMock(side_effect=Exception("API Error"))

        with patch('agent_identity_python_sdk.core.decorators.IdentityClient') as mock_client_class:
            mock_client_class.return_value = mock_identity_client

            with patch('agent_identity_python_sdk.core.decorators._has_running_loop', return_value=False):
                with patch('agent_identity_python_sdk.core.decorators._get_workload_access_token') as mock_get_token:
                    mock_get_token.return_value = "workload-token"

                    @requires_sts_token(
                        inject_param_name="sts_credential"
                    )
                    def sample_function(sts_credential):
                        return f"STS Credential: {sts_credential.access_key_id}"

                    # Execute and expect exception
                    with pytest.raises(Exception, match="API Error"):
                        sample_function()


class TestCoverage:
    """Additional tests to ensure full coverage."""
    
    def test_logger_setup(self):
        """Test logger setup which should cover the logger.setLevel line."""
        import logging
        from agent_identity_python_sdk.core.decorators import logger
        assert logger.level == logging.INFO
    
    @pytest.mark.asyncio
    async def test_get_workload_access_token_local_with_env_var(self):
        """Test _get_workload_access_token_local with environment variable set."""
        mock_client = Mock()
        mock_client.get_workload_access_token.return_value = "mock-token"
        
        with patch.dict(os.environ, {"AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME": "test-workload-identity"}):
            with patch('agent_identity_python_sdk.core.decorators.write_local_config') as mock_write:
                token = await _get_workload_access_token_local(mock_client, user_id="test-user", id_token="test-token")
                
                assert token == "mock-token"
                mock_client.get_workload_access_token.assert_called_once_with(
                    "test-workload-identity", user_id="test-user", user_token="test-token"
                )
                mock_write.assert_called_once_with("workload_identity_name", "test-workload-identity")
    
    @pytest.mark.asyncio
    async def test_get_workload_access_token_local_with_config(self):
        """Test _get_workload_access_token_local with config file value."""
        mock_client = Mock()
        mock_client.get_workload_access_token.return_value = "mock-token"
        
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('agent_identity_python_sdk.core.decorators.read_local_config', return_value="config-workload-identity"):
                with patch('agent_identity_python_sdk.core.decorators.write_local_config') as mock_write:
                    token = await _get_workload_access_token_local(mock_client, user_id="test-user", id_token="test-token")
                    
                    assert token == "mock-token"
                    mock_client.get_workload_access_token.assert_called_once_with(
                        "config-workload-identity", user_id="test-user", user_token="test-token"
                    )
                    mock_write.assert_called_once_with("workload_identity_name", "config-workload-identity")
    
    @pytest.mark.asyncio
    async def test_get_workload_access_token_local_create_workload_identity(self):
        """Test _get_workload_access_token_local creating new workload identity."""
        mock_client = Mock()
        mock_client.get_workload_access_token.return_value = "mock-token"
        mock_client.create_workload_identity.return_value = "new-workload-identity"
        
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('agent_identity_python_sdk.core.decorators.read_local_config', return_value=None):  # Return None instead of exception
                with patch('agent_identity_python_sdk.core.decorators.write_local_config') as mock_write:
                    token = await _get_workload_access_token_local(mock_client, user_id="test-user", id_token="test-token")
                    
                    assert token == "mock-token"
                    mock_client.create_workload_identity.assert_called_once()
                    mock_client.get_workload_access_token.assert_called_once_with(
                        "new-workload-identity", user_id="test-user", user_token="test-token"
                    )
                    mock_write.assert_called_once_with("workload_identity_name", "new-workload-identity")