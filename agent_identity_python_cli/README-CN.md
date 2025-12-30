[English](README.md) | 简体中文

![](https://aliyunsdk-pages.alicdn.com/icons/AlibabaCloud.svg)

## Alibaba Cloud Agent Identity CLI for Python

阿里云 AI Agent 身份管理命令行工具，提供创建 RAM Role、权限策略和 Workload Identity 的能力。

## 要求

- Python >= 3.8

## 安装

```bash
pip install agent-identity-cli
```

本地开发安装：

```bash
git clone <repository-url>
cd agent-identity-python-cli
pip install -e .
```

## 配置

使用 CLI 前需设置以下环境变量：

```bash
# 必需：阿里云凭据
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your_access_key_id>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your_access_key_secret>

# 可选：Agent Identity 区域，默认 cn-beijing
export AGENT_IDENTITY_REGION_ID=cn-beijing

# 可选：自定义 Agent Identity API 端点（用于预发测试）
export AGENT_IDENTITY_ENDPOINT=agentidentity.cn-beijing.aliyuncs.com
```

## CLI 使用方式

### create-role

创建 RAM Role，包含 Agent Identity 信任策略和权限策略。

```bash
# 基本用法：自动生成 role name，信任策略允许所有 workload identity
agent-identity-cli create-role

# 指定 role name
agent-identity-cli create-role --role-name my-agent-role

# 指定 workload identity name（用于构建信任策略）
agent-identity-cli create-role --workload-identity-name my-identity

# 完整参数
agent-identity-cli create-role \
  --role-name my-agent-role \
  --workload-identity-name my-identity
```

**参数说明：**

| 参数 | 必填 | 说明 |
|------|------|------|
| `--role-name` | 否 | Role 名称。默认为 `AgentIdentityRole-{workload-identity-name}` 或 `AgentIdentityRole-{随机}` |
| `--workload-identity-name` | 否 | 用于构建信任策略的 Workload Identity 名称。不传则允许所有 |

**输出：**

- Role ARN
- Role 名称
- Policy 名称
- 信任策略 (JSON)
- 权限策略 (JSON)

### create-workload-identity

创建 Workload Identity，可自动创建关联的 Role。

```bash
# 自动创建关联的 Role
agent-identity-cli create-workload-identity --workload-identity-name my-identity

# 使用已有的 Role
agent-identity-cli create-workload-identity \
  --workload-identity-name my-identity \
  --associated-role-arn acs:ram::123456789:role/my-role

# 完整参数
agent-identity-cli create-workload-identity \
  --workload-identity-name my-identity \
  --associated-role-arn acs:ram::123456789:role/my-role \
  --identity-provider-name my-idp \
  --allowed-resource-oauth2-return-urls "https://example.com/callback,https://app.example.com/oauth"
```

**参数说明：**

| 参数 | 必填 | 说明 |
|------|------|------|
| `--workload-identity-name` | 是 | Workload Identity 名称 |
| `--associated-role-arn` | 否 | 关联的 Role ARN。不传则自动创建新 Role |
| `--identity-provider-name` | 否 | Identity Provider 名称 |
| `--allowed-resource-oauth2-return-urls` | 否 | OAuth2 回调 URL 列表，逗号分隔 |

**输出：**

- Workload Identity ARN
- Workload Identity 名称
- Role 信息（如果创建了新 Role）

## Python 模块使用方式

CLI 也可以作为 Python 模块使用，便于与其他工具集成。

### create_role

```python
from agent_identity_cli import create_role, CreateRoleConfig

# 创建 Role（信任策略允许所有 workload identity）
result = create_role(CreateRoleConfig())
print(f"Role ARN: {result.role_arn}")
print(f"Trust Policy: {result.trust_policy}")
print(f"Permission Policy: {result.permission_policy}")

# 指定 workload identity name
result = create_role(CreateRoleConfig(
    role_name="my-agent-role",
    workload_identity_name="my-identity",
))
print(f"Role ARN: {result.role_arn}")
```

### create_workload_identity

```python
from agent_identity_cli import create_workload_identity, CreateWorkloadIdentityConfig

# 自动创建 Role
result = create_workload_identity(CreateWorkloadIdentityConfig(
    workload_identity_name="my-identity",
))
print(f"Workload Identity ARN: {result.workload_identity_arn}")
print(f"Role ARN: {result.role_result.role_arn}")

# 使用已有 Role
result = create_workload_identity(CreateWorkloadIdentityConfig(
    workload_identity_name="my-identity",
    associated_role_arn="acs:ram::123456789:role/my-role",
))
```

### 数据模型

**CreateRoleConfig：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `role_name` | str | 否 | Role 名称，不传则自动生成 |
| `workload_identity_name` | str | 否 | 用于信任策略的 Workload Identity 名称 |

**CreateRoleResult：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `role_arn` | str | 创建的 Role ARN |
| `role_name` | str | 创建的 Role 名称 |
| `trust_policy` | dict | 信任策略内容 |
| `policy_name` | str | 创建的权限策略名称 |
| `permission_policy` | dict | 权限策略内容 |

**CreateWorkloadIdentityConfig：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `workload_identity_name` | str | 是 | Workload Identity 名称 |
| `associated_role_arn` | str | 否 | 关联的 Role ARN |
| `identity_provider_name` | str | 否 | Identity Provider 名称 |
| `allowed_resource_oauth2_return_urls` | List[str] | 否 | OAuth2 回调 URL 列表 |

**CreateWorkloadIdentityResult：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `workload_identity_arn` | str | 创建的 Workload Identity ARN |
| `workload_identity_name` | str | 创建的 Workload Identity 名称 |
| `role_result` | CreateRoleResult | Role 信息（如果创建了新 Role） |

## 策略格式

### 信任策略

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

- 如果不指定 `--workload-identity-name`，则不包含 `Condition` 块，允许所有 Workload Identity

### 权限策略

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

## 许可证

[Apache-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Copyright (c) 2009-present, Alibaba Cloud All rights reserved.
