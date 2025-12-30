# -*- coding: utf-8 -*-
"""Utilities module for Agent Identity CLI."""

from .credentials import (
    get_credential_client,
    get_openapi_config,
    get_account_id,
    build_role_arn,
)
from .constants import (
    DEFAULT_REGION,
    AGENT_IDENTITY_ENDPOINT,
    OAUTH2_CREDENTIAL_PROVIDER,
    APIKEY_CREDENTIAL_PROVIDER,
)

__all__ = [
    # Credential functions
    "get_credential_client",
    "get_openapi_config",
    "get_account_id",
    "build_role_arn",
    # Constants
    "DEFAULT_REGION",
    "AGENT_IDENTITY_ENDPOINT",
    "OAUTH2_CREDENTIAL_PROVIDER",
    "APIKEY_CREDENTIAL_PROVIDER",
]

