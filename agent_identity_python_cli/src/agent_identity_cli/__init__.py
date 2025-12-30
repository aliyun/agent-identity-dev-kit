# -*- coding: utf-8 -*-
"""
Agent Identity CLI - A toolkit for managing AI Agent identities.

This module provides both CLI and programmatic interfaces for:
- Creating RAM Roles with Agent Identity trust policy
- Creating Workload Identities
"""

__version__ = "0.1.0"

from .core.deployer import create_role, create_workload_identity
from .core.models import (
    CreateRoleConfig,
    CreateRoleResult,
    CreateWorkloadIdentityConfig,
    CreateWorkloadIdentityResult,
)

__all__ = [
    # Functions
    "create_role",
    "create_workload_identity",
    # Config classes
    "CreateRoleConfig",
    "CreateWorkloadIdentityConfig",
    # Result classes
    "CreateRoleResult",
    "CreateWorkloadIdentityResult",
]
