# Agent Identity Local Service Automation Demo

An Agent Identity local service automation demo for one-click cloud resource creation, local Agent/frontend/backend startup, and MCP tool invocation permission control through Agent Identity.

## 🚀 Overview

This sample demonstrates how to automate resource initialization and local service startup for an LLM Agent service based on the [AgentScope](https://github.com/alibaba/agentscope) runtime framework and integrated with Agent Identity.
It includes Inbound authentication, Outbound credential acquisition and tool invocation, session management, user identity management, cloud credential acquisition, MCP integration, and MCP tool invocation permission control through Agent Identity policy sets. The deployment structure consists of three modules: AI Agent service, frontend application, and backend application.

The frontend and backend applications constitute a complete inbound application that integrates Alibaba Cloud OAuth2.0 authentication flow, allowing browser-based authentication and retrieval of Alibaba Cloud ID Tokens. After obtaining credentials, the frontend can interact with the Agent through the backend application, using Agent Identity's credential hosting capabilities for tool usage.

Key features include:

- Integration of Alibaba Cloud OAuth 2.0 flow for user authentication
- Acquisition of Alibaba Cloud OAuth2.0 user identity tokens as Agent inbound identity
- Integration of AgentScope Runtime framework and QwenLLM Agent services
- Registration and publishing of an MCP service on AI Gateway, with access controlled by an Agent Identity policy set
- Access to multiple tools with different credential types, including:
  - Alibaba Cloud MCP service (OAuth2 token)
  - Reading files from Alibaba Cloud OSS (STS Token)
  - Getting system time (simulated: OAuth2 token)
  - Simulating weather retrieval (simulated: API Key)
  - Simulating today's schedule retrieval (simulated: STS Token)

## 🏗️ Architecture
![framework.png](images/framework.png)

### Core Components

- **Identity Client**: Manages user authentication and token lifecycle
- **Credential Management**: OAuth2, API key, and STS credential management
- **Workload Identity**: Agent identity management based on Agent Identity service
- **AI Gateway MCP Publishing**: Publishes an MCP service on AI Gateway and controls Agent access through an Agent Identity policy set
- **MCP/Tool Integration**: Streamable HTTP endpoints for real-time tool execution
- **Session Management**: Memory state persistence across interactions

## ⚙️ Prerequisites

### System Requirements
- Python ≥ 3.10
- pip package manager

### Required Cloud Resources

#### 1. RAM Identity Setup
Prepare a RAM user with administrator permissions and create an AccessKey for that RAM user.

The AccessKey is used by the demo scripts to create and clean up Agent Identity, APIG, VPC, IMS, RAM, and related cloud resources. Use administrator credentials only in a test account or controlled environment, and run the cleanup script after the demo.

#### 2. DashScope API Key
Obtain a [DashScope API key](https://bailian.console.aliyun.com/?tab=model#/api-key) with model calling permissions.

#### 3. AI Gateway Service
Enable the AI Gateway service first: [AI Gateway Console](https://apig.console.aliyun.com/#/ai-gateway-overview).

This demo creates an AI Gateway instance during setup. The instance is a paid resource. Run `./clear_services.sh` after the demo to clean up resources.

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/end-to-end_sample_local_automation
```

### 2. One-click Bootstrap
For first-time setup, run the bootstrap script. It creates a virtual environment, installs dependencies, validates required credentials, and creates the cloud resources required by the demo.

```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-admin-access-key-id>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-admin-access-key-secret>
export DASHSCOPE_API_KEY=<your-dashscope-api-key>
./bootstrap.sh
```

## 🔧 Resource Initialization

`bootstrap.sh` performs the following operations:

1. **Create Identity Provider**
   - Discovery URL: `https://oauth.aliyun.com/.well-known/openid-configuration`
   - Audience: `12345678`

2. **Create Alibaba Cloud OAuth 2.1 Inbound Application**
   - Scopes: `aliuid;profile;openid`

3. **Create OAuth 2.1 Native Application for Alibaba Cloud MCP Service**
   - Scopes: `aliuid;profile;openid;/acs/mcp-server`

4. **Create Workload Identity and Role**
   - Workload Identity Name: `workload-${UUID}`
   - Role Name: `AgentIdentityRole-${workloadIdentityName}`
   - Role Trust Policy: Allows assume role requests from this workload identity
   - Role Permission Policy: Allows this role to call Agent Identity data plane APIs

5. **Configure Credential Providers**
   - OAuth2 provider for MCP server integration and simulated tools
   - API key provider for model calls and simulated tools

6. **Configure AI Gateway Resources**
   - Create APIG gateway, service, policy, plugin, and MCP server
   - Register and publish the MCP service on AI Gateway
   - Create an Agent Identity policy set and attach it to the gateway to control MCP invocation permissions

### Agent Identity MCP Permission Control Example

`bootstrap.sh` registers and publishes a sample MCP service on AI Gateway. The MCP service contains a `maps-geo` geocoding tool, and the initial permission policy is configured to deny all requests. This setup demonstrates how an Agent Identity policy set controls both MCP tool discovery and tool invocation.

The example has three stages:

1. **Initial state: deny all**
   - After `bootstrap.sh` completes, the MCP service containing the `maps-geo` tool has been registered and published on AI Gateway.
   - The policy set denies all requests by default.
   - Behavior: the Agent cannot discover tools from this MCP.

2. **Update the policy to allow all**
   - Change the policy to allow all requests.
   - Behavior: the Agent can discover the `maps-geo` tool and invoke it without input restrictions. Any `address` value can be used.

3. **Update the policy for input-level control**
   - Change the policy to allow only requests where `address` is `杭州西湖`.
   - Behavior: requests for `杭州西湖` can invoke the `maps-geo` tool successfully; requests with any other `address` are blocked with a `403` error.

Demo videos:

- [Phase 1: deny all by default](video/demo_phase1.mp4)
- [Phase 2: allow all requests](video/demo_phase2.mp4)
- [Phase 3: input-level control by `address`](video/demo_phase3.mp4)

> **Note**: The script outputs created resource information to .config.json in the root directory, which contains "mcp_app_name" for subsequent use.

> **Note**: If abnormal failures occur during execution (such as network issues, resource quota exceeded, etc.), clear the created resources before re-running the setup. Use the same bash-entry style as `bootstrap.sh` and `deploy_services.sh`:
> ```bash
> ./clear_services.sh
> ```
> The script reads `.config.json`, stops local services, deletes MCP services, AI Gateway bindings, policies/policy sets, APIG/VPC resources, Agent Identity resources, IMS applications, and demo-created RAM roles/users/policies in dependency order, then archives `.config.json` as `.config.json.cleared.<timestamp>`.

## ▶️ Running the Agent

### One-click Local Startup

After bootstrap completes, run the following command in the sample root directory:
```bash
./deploy_services.sh
```

The script reads `.config.json`, resolves MCP service endpoints, and starts:

- Agent service: `http://localhost:8080`
- Backend and frontend service: `http://localhost:8090`

After startup succeeds, open `http://localhost:8090` to try the demo.

### Interacting with the Agent

#### Tool Function Summary

| Command | Function | Credential Type |
|--------|----------|-----------------|
| Query today's weather | Weather API query | API Key |
| Query today's schedule | Calendar/Schedule access | STS Token |
| Query current system time | System time retrieval | OAuth Token |
| Call Alibaba Cloud MCP service to query owned resource types | Alibaba Cloud resource query | OAuth Token |
| Read Alibaba Cloud OSS files | OSS file query | STS Token |

#### Acquiring User Identity Tokens

Navigate to the frontend page (http://localhost:8090) and click the "Login" button, which will guide you through the Alibaba Cloud OAuth authorization process (the authorized user must be under the same Alibaba Cloud account as the created OAuth application).

#### Sending Requests to the Agent

After completing OAuth authorization, you can interact with the Agent through the chat box on the frontend page.

### Example Prompts

Here are some simple examples that can be used to test different tool functionalities:

- "How is the weather today?" - Testing weather API (API key authentication)
- "What is my schedule for today?" - Testing calendar/schedule tool (STS token authentication)
- "What time is it now?" - Testing system time retrieval (OAuth token authentication)
- "Help me query what resource types my account owns" - Testing Alibaba Cloud MCP service (OAuth token authentication)
- "Read my OSS file" - Testing OSS file query (STS token authentication)

## 🤝 Support

For questions or concerns about the Agent Identity SDK:
- Refer to [official documentation](https://help.aliyun.com/product/agent-identity)
- Contact Alibaba Cloud support
- Submit issues in the repository

---
