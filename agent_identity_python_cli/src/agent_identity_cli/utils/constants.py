# -*- coding: utf-8 -*-
"""Constants for Agent Identity CLI."""

import os


# Default region for Agent Identity service
DEFAULT_REGION = os.getenv("AGENT_IDENTITY_REGION_ID", "cn-beijing")

# Agent Identity endpoint from environment, or None to build from region
AGENT_IDENTITY_ENDPOINT = os.getenv("AGENT_IDENTITY_ENDPOINT")

# Credential provider types
OAUTH2_CREDENTIAL_PROVIDER = "oauth2credentialprovider"
APIKEY_CREDENTIAL_PROVIDER = "apikeycredentialprovider"

