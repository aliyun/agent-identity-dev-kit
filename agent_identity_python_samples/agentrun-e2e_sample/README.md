# Agent Identity Python SDK Sample

End-to-end example of AgentRun integrated with Agent Identity: OIDC inbound identity, OAuth2 credential hosting for hosted MCP tools, Cedar fine-grained authorization, and agent-side credential fetching (API Key / STS / OAuth2).

## 🚀 Overview

This sample demonstrates a LangChain agent deployed on AgentRun Runtime that:

1. Authenticates end users with an OIDC ID Token (inbound, validated by the AgentRun gateway);
2. Calls an AgentRun-hosted MCP tool on behalf of the user — the Workload Access Token (WAT) injected by the gateway is forwarded to the tool, where the AgentIdentity hook performs Cedar authorization and OAuth2 credential injection;
3. Fetches credentials for local tools through the Agent Identity SDK (API Key, OSS STS, OAuth2).

Built-in tools:

| Capability | Tool | Enable via env |
|---|---|---|
| Hosted MCP tool calls (OAuth2 hosting + Cedar) | loaded via `tool_resource(TOOL_NAME)` | always on |
| API Key credential hosting | `weather_search` | `ENABLE_WEATHER_TOOL=1` |
| OSS STS temporary credentials | `get_object_from_oss` | `ENABLE_OSS_TOOL=1` |
| OAuth2 user-federation token injection | `get_current_time` | `ENABLE_TIME_TOOL=1` |
| STS temporary credential injection | `get_schedule` | `ENABLE_SCHEDULE_TOOL=1` |

## ⚙️ Prerequisites

### System Requirements
- Python ≥ 3.10
- pip package manager

### Resource Preparation

#### 1. OIDC Identity Provider
Prepare an OIDC identity provider as the inbound credential issuer. You need its
Discovery URL (`.../.well-known/openid-configuration`) and a way to issue test
ID Tokens for end users.

#### 2. Create AgentRun Language Model
Create a large language model in the AgentRun console (Model Management). Record
the **service name** (card title) and the **model name** (tag inside the card).

#### 3. OAuth2 Credential Chain
1. RAM console → Applications → create a Web application (OAuth 2.1); scopes:
   `openid`, `aliuid`, `profile`, plus what the upstream MCP requires;
2. AgentIdentity console → Credential Providers → create an OAuth2 provider
   linked to that application. Name it **`test-provider-for-mcp-oauth`** — the
   sample's time tool references this name (see `get_current_time.py`; rename
   there if you prefer your own). Copy the callback URL from the provider page;
3. Back-fill the callback URL into the RAM application.

#### 4. API Key Credential Provider
AgentIdentity console → Credential Providers → create an **API Key** provider
named **`test-provider-api-key`** (referenced by `weather_search.py`). The key
value can be any non-empty string — the mock tool only verifies injection.

#### 5. Create the Remote MCP Tool
AgentRun console → Tools & Skills → create a remote MCP tool with your upstream
MCP server URL, enable AgentIdentity authentication, and bind the OAuth2
provider from step 3.

## 📦 Installation and Deployment to AgentRun

### 1. Clone Repository
```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/agentrun-e2e_sample
```

### 2. Install Dependencies Locally
```bash
pip install -r requirements.txt -t ./python
```
Note: the build environment must match the AgentRun runtime (linux/amd64,
Python 3.12). On macOS add
`--platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:`.
This layout matches the runtime `PYTHONPATH=/opt/python:/code/python`, so
dependencies installed into `python/` are importable after deployment.

### 3. Package as zip
Package the current directory (including the `python/` subdirectory) as a zip
file for creating an agent via zip package:
```bash
zip -r agentrun-e2e-sample.zip . -x "*__pycache__*"
```

### 4. Create Agent
Create the Agent in the AgentRun console via code package. Environment variables:

| Variable | Required | Notes |
|---|---|---|
| `MODEL_SERVICE_NAME` | yes | Model service name (card title) |
| `MODEL_NAME` | yes | Model name |
| `TOOL_NAME` | yes | Hosted MCP tool name(s), comma-separated for multiple |
| `AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME` | for OSS and other local tools | Workload identity name (created via agent-identity-cli) |
| `AGENT_IDENTITY_REGION_ID` | for local tools | AgentIdentity data-plane region (SDK defaults to cn-beijing; set explicitly) |

Credential configuration: select **AgentIdentity identity provider
authentication** and choose the OIDC provider registered in Prerequisites.

### Invocation

```bash
curl <agent-endpoint>/openai/v1/chat/completions -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <id-token-from-your-idp>" \
  -d '{"messages":[{"role":"user","content":"你有什么工具？"}],"stream":false}'
```

The first call to a credential-hosted MCP tool returns an OAuth2 authorization
link; open it in a browser, authorize, and invoke again.

## 🤝 Support

For questions or inquiries about Agent Identity SDK:
- Refer to [Official Documentation](https://help.aliyun.com/product/agent-identity)
- Contact Alibaba Cloud support
- Submit an issue in the repository
