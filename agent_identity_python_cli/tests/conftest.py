# -*- coding: utf-8 -*-
"""Shared fixtures for unit tests."""

import pytest
from unittest.mock import MagicMock, patch


# Test constants
TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "cn-beijing"
TEST_ROLE_NAME = "TestRole"
TEST_POLICY_NAME = "TestPolicy"
TEST_WORKLOAD_IDENTITY_NAME = "test-identity"


@pytest.fixture
def mock_account_id():
    """Mock account ID for testing."""
    return TEST_ACCOUNT_ID


@pytest.fixture
def mock_region():
    """Mock region for testing."""
    return TEST_REGION


@pytest.fixture
def mock_credential_client():
    """Mock CredentialClient for testing."""
    with patch("agent_identity_cli.utils.credentials.CredentialClient") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ram_client():
    """Mock RAM Client for testing."""
    mock_client = MagicMock()
    
    # Mock create_role response
    mock_role_response = MagicMock()
    mock_role_response.body.role.arn = f"acs:ram::{TEST_ACCOUNT_ID}:role/{TEST_ROLE_NAME}"
    mock_client.create_role.return_value = mock_role_response
    
    # Mock create_policy response
    mock_policy_response = MagicMock()
    mock_policy_response.body.policy.policy_name = TEST_POLICY_NAME
    mock_client.create_policy.return_value = mock_policy_response
    
    # Mock attach_policy_to_role (no return value needed)
    mock_client.attach_policy_to_role.return_value = None
    
    return mock_client


@pytest.fixture
def mock_identity_client():
    """Mock Agent Identity Client for testing."""
    mock_client = MagicMock()
    
    # Mock create_workload_identity response
    mock_response = MagicMock()
    mock_response.body.workload_identity.workload_identity_arn = (
        f"acs:agentidentity:{TEST_REGION}:{TEST_ACCOUNT_ID}:"
        f"workloadidentitydirectory/default/workloadidentity/{TEST_WORKLOAD_IDENTITY_NAME}"
    )
    mock_client.create_workload_identity.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_sts_client():
    """Mock STS Client for testing."""
    mock_client = MagicMock()
    
    # Mock get_caller_identity response
    mock_response = MagicMock()
    mock_response.body.account_id = TEST_ACCOUNT_ID
    mock_client.get_caller_identity.return_value = mock_response
    
    return mock_client

