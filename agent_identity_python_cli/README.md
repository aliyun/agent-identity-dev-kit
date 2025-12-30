English | [简体中文](README-CN.md)

![](https://aliyunsdk-pages.alicdn.com/icons/AlibabaCloud.svg)

## Alibaba Cloud Agent Identity CLI for Python

A command-line tool for managing AI Agent identities on Alibaba Cloud. It provides capabilities to create RAM Roles, Permission Policies, and Workload Identities.

## Requirements

- Python >= 3.8

## Installation

```bash
pip install agent-identity-cli
```

For local development:

```bash
git clone <repository-url>
cd agent-identity-python-cli
pip install -e .
```

## Configuration

Set the following environment variables before using the CLI:

```bash
# Required: Alibaba Cloud credentials
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your_access_key_id>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your_access_key_secret>

# Optional: Agent Identity region, defaults to cn-beijing
export AGENT_IDENTITY_REGION_ID=cn-beijing

# Optional: Custom endpoint for Agent Identity API (for pre-release testing)
export AGENT_IDENTITY_ENDPOINT=agentidentity.cn-beijing.aliyuncs.com
```

## CLI Usage

### create-role

Create a RAM Role with Agent Identity trust policy and permission policy.

```bash
# Basic usage: auto-generate role name, trust policy allows all workload identities
agent-identity-cli create-role

# Specify role name
agent-identity-cli create-role --role-name my-agent-role

# Specify workload identity name (for trust policy)
agent-identity-cli create-role --workload-identity-name my-identity

# Full parameters
agent-identity-cli create-role \
  --role-name my-agent-role \
  --workload-identity-name my-identity
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--role-name` | No | Role name. Defaults to `AgentIdentityRole-{workload-identity-name}` or `AgentIdentityRole-{random}` |
| `--workload-identity-name` | No | Workload Identity name for building trust policy. If not specified, allows all workload identities |

**Output:**

- Role ARN
- Role Name
- Policy Name
- Trust Policy (JSON)
- Permission Policy (JSON)

### create-workload-identity

Create a Workload Identity with optional automatic Role creation.

```bash
# Auto-create associated Role
agent-identity-cli create-workload-identity --workload-identity-name my-identity

# Use existing Role
agent-identity-cli create-workload-identity \
  --workload-identity-name my-identity \
  --associated-role-arn acs:ram::123456789:role/my-role

# Full parameters
agent-identity-cli create-workload-identity \
  --workload-identity-name my-identity \
  --associated-role-arn acs:ram::123456789:role/my-role \
  --identity-provider-name my-idp \
  --allowed-resource-oauth2-return-urls "https://example.com/callback,https://app.example.com/oauth"
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--workload-identity-name` | Yes | Workload Identity name |
| `--associated-role-arn` | No | Associated Role ARN. If not specified, auto-creates a new Role |
| `--identity-provider-name` | No | Identity Provider name |
| `--allowed-resource-oauth2-return-urls` | No | OAuth2 callback URL list, comma-separated |

**Output:**

- Workload Identity ARN
- Workload Identity Name
- Role information (if a new Role was created)

## Python SDK Usage

The CLI can also be used as a Python module for integration with other tools.

### create_role

```python
from agent_identity_cli import create_role, CreateRoleConfig

# Create Role (trust policy allows all workload identities)
result = create_role(CreateRoleConfig())
print(f"Role ARN: {result.role_arn}")
print(f"Trust Policy: {result.trust_policy}")
print(f"Permission Policy: {result.permission_policy}")

# Specify workload identity name
result = create_role(CreateRoleConfig(
    role_name="my-agent-role",
    workload_identity_name="my-identity",
))
print(f"Role ARN: {result.role_arn}")
```

### create_workload_identity

```python
from agent_identity_cli import create_workload_identity, CreateWorkloadIdentityConfig

# Auto-create Role
result = create_workload_identity(CreateWorkloadIdentityConfig(
    workload_identity_name="my-identity",
))
print(f"Workload Identity ARN: {result.workload_identity_arn}")
print(f"Role ARN: {result.role_result.role_arn}")

# Use existing Role
result = create_workload_identity(CreateWorkloadIdentityConfig(
    workload_identity_name="my-identity",
    associated_role_arn="acs:ram::123456789:role/my-role",
))
```

### Data Models

**CreateRoleConfig:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role_name` | str | No | Role name, auto-generated if not specified |
| `workload_identity_name` | str | No | Workload Identity name for trust policy |

**CreateRoleResult:**

| Field | Type | Description |
|-------|------|-------------|
| `role_arn` | str | Created Role ARN |
| `role_name` | str | Created Role name |
| `trust_policy` | dict | Trust policy content |
| `policy_name` | str | Created permission policy name |
| `permission_policy` | dict | Permission policy content |

**CreateWorkloadIdentityConfig:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workload_identity_name` | str | Yes | Workload Identity name |
| `associated_role_arn` | str | No | Associated Role ARN |
| `identity_provider_name` | str | No | Identity Provider name |
| `allowed_resource_oauth2_return_urls` | List[str] | No | OAuth2 callback URL list |

**CreateWorkloadIdentityResult:**

| Field | Type | Description |
|-------|------|-------------|
| `workload_identity_arn` | str | Created Workload Identity ARN |
| `workload_identity_name` | str | Created Workload Identity name |
| `role_result` | CreateRoleResult | Role information (if a new Role was created) |

## Policy Formats

### Trust Policy

```json
{
  "Version": "1",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "workload.agentidentity.aliyuncs.com"
    },
    "Action": ["sts:AssumeRole", "sts:SetContext"],
    "Condition": {
      "StringEquals": {
        "sts:RequestContext/agentidentity:WorkloadIdentityArn": 
          "acs:agentidentity:{regionId}:{accountId}:workloadidentitydirectory/default/workloadidentity/{name}"
      }
    }
  }]
}
```

- If `--workload-identity-name` is not specified, the `Condition` block is omitted, allowing all Workload Identities.

### Permission Policy

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["agentidentitydata:GetResourceOAuth2Token"],
      "Resource": ["acs:agentidentity:{regionId}:{accountId}:workloadidentitydirectory/default/workloadidentity/{name}"]
    },
    {
      "Effect": "Allow",
      "Action": ["agentidentitydata:GetResourceAPIKey"],
      "Resource": ["acs:agentidentity:{regionId}:{accountId}:workloadidentitydirectory/default/workloadidentity/{name}"]
    }
  ]
}
```

## License

[Apache-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Copyright (c) 2009-present, Alibaba Cloud All rights reserved.
