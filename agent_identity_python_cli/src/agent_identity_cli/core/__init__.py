# -*- coding: utf-8 -*-
"""Core module for Agent Identity CLI."""

from .deployer import create_role, create_workload_identity
from .models import (
    CreateRoleConfig,
    CreateRoleResult,
    CreateWorkloadIdentityConfig,
    CreateWorkloadIdentityResult,
)

__all__ = [
    "create_role",
    "create_workload_identity",
    "CreateRoleConfig",
    "CreateRoleResult",
    "CreateWorkloadIdentityConfig",
    "CreateWorkloadIdentityResult",
]
