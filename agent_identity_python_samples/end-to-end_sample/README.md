# Agent Identity Python SDK Sample

A complete demonstration of the Agent Identity Python SDK for building secure, identity-aware AI agents. Supports both UF (User-present) and M2M (Machine-to-Machine) credential acquisition modes.

## 🚀 Overview

This sample demonstrates how to build an LLM Agent service based on the [AgentScope](https://github.com/alibaba/agentscope) runtime framework, integrated with the Agent Identity SDK.
It includes Inbound authentication, Outbound credential acquisition and tool invocation, session management, user identity management, cloud credential acquisition, MCP integration, and other functions. The deployment structure consists of three modules: AI Agent service, frontend application, and backend application.

This sample demonstrates two credential acquisition modes:
- **UF (User-present) mode**: After user login, the Agent obtains credentials on behalf of the user and invokes tools. For example: user asks the Agent via chat to query ECS instances, read OSS files, or write DingTalk documents.
- **M2M (Machine-to-Machine) mode**: No user login required. External systems trigger the Agent via API, and the Agent autonomously executes tasks using machine identity credentials. For example: CI/CD system triggers the Agent to send DingTalk work notifications.

Both modes share the same Agent pipeline (natural language input → LLM analysis → tool decision → credential injection → execution). The difference lies only in the trigger source and credential origin.

The frontend and backend applications constitute a complete inbound application that integrates Alibaba Cloud OAuth2.0 authentication flow, allowing browser-based authentication and retrieval of Alibaba Cloud ID Tokens. After obtaining credentials, the frontend can interact with the Agent through the backend application, using Agent Identity's credential hosting capabilities for tool usage.

Key features include:

- Integration of Alibaba Cloud OAuth 2.0 flow for user authentication
- Acquisition of Alibaba Cloud OAuth2.0 user identity tokens as Agent inbound identity
- Integration of AgentScope Runtime framework and QwenLLM Agent services
- Access to multiple tools with different credential types, including:
  - Alibaba Cloud MCP service (OAuth2 token)
  - Writing DingTalk documents (OAuth2 token)
  - Reading files from Alibaba Cloud OSS (STS Token)
  - Getting system time (simulated: OAuth2 token)
  - Simulating weather retrieval (simulated: API Key)
  - Simulating today's schedule retrieval (simulated: STS Token)
- M2M mode: External systems trigger the Agent via `/process`, and the Agent uses machine credentials to automatically obtain DingTalk M2M tokens and send work notifications

## 🏗️ Architecture
![framework.png](images/framework.png)

### Core Components

- **Identity Client**: Manages user authentication and token lifecycle
- **Credential Management**: OAuth2, API key, and STS credential management
- **Workload Identity**: Agent identity management based on Agent Identity service
- **MCP/Tool Integration**: Streamable HTTP endpoints for real-time tool execution
- **Session Management**: Memory state persistence across interactions

## ⚙️ Prerequisites

### System Requirements
- Python ≥ 3.10
- pip package manager

### Required Cloud Resources

#### 1. RAM Identity Setup
Create a RAM sub-account with the following permissions:

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "agentidentity:*",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "agentidentitydata:*",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "ram:CreateServiceLinkedRole",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ram:ServiceName": ["agentidentity.aliyuncs.com"]
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ram:CreateApplication",
        "ram:CreateRole", 
        "ram:CreatePolicy",
        "ram:AttachPolicyToRole", 
        "ram:CreateAppSecret",
        "ram:DeleteApplication"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 2. DashScope API Key
Obtain a [DashScope API key](https://bailian.console.aliyun.com/?tab=model#/api-key) with model calling permissions.

#### 3. DingTalk Enterprise Internal Application (Required for M2M Mode)

To send DingTalk work notifications in M2M mode, you need to create an enterprise internal application on the DingTalk Open Platform:

1. Log in to the [DingTalk Developer Console](https://open-dev.dingtalk.com/)
2. Go to **App Development** → **Enterprise Internal Development** → **Create Application**
3. Fill in the application name and description, create an H5 micro-application
4. On the **Basic Information** page, record the following three values:
   - **AppKey** (i.e., client_id)
   - **AppSecret** (i.e., client_secret)
   - **AgentId** (application ID, numeric type)
5. On the **Permission Management** page, search and add the following permissions:
   - `Enterprise robot message sending` (for sending work notifications)
   - `Contact personal info read permission` (for querying user IDs)
6. On the **Development Management** page, fill in **Server Outbound IP** (you can fill `*` for no restrictions)
7. On the **Version Management & Release** page, create a version and publish the application

> **Note**: Permissions only take effect after the application is published. If permissions are granted but the API returns 403, check whether the latest version has been published.

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/end-to-end_sample
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

After creating an Access Key for the RAM user mentioned above and creating a Dashscope API Key in the console, inject them into environment variables:

```bash
# Alibaba Cloud Credentials
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-access-key-id>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-access-key-secret>
export AGENT_IDENTITY_REGION_ID=cn-beijing # Currently, Agent Identity is only available in Beijing region
# DashScope API
export DASHSCOPE_API_KEY=<your-api-key>
# M2M (DingTalk Work Notification)
export DINGTALK_APP_KEY=<your-dingtalk-app-key>
export DINGTALK_APP_SECRET=<your-dingtalk-app-secret>
export DINGTALK_AGENT_ID=<your-dingtalk-agent-id>
export DINGTALK_CORP_ID=<your-dingtalk-corp-id>
```

## 🔧 Resource Initialization

### Automated Setup Script
Run the preparation script to automatically create required cloud resources:

```bash
python -m prepare
```

This script performs the following operations:

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
   - OAuth2 provider for MCP server integration/system time retrieval
   - API key provider for weather tools
   - M2M credential provider for DingTalk work notifications (provider name: `dingtalk-m2m-sample`, vendor: `DingTalkOAuth2`, oauthType: `M2M`)

> **Note**: The script outputs created resource information to .config.json in the root directory, which contains "mcp_app_name" for subsequent use.

> **Note**: If abnormal failures occur during execution (such as network issues, resource quota exceeded, etc.), you need to clear the created resources before re-running prepare. To clear created resources, run:
> ```bash
> python -m clear
> ```
> The script will delete Agent Identity-related resources from .config.json.
> 
> **To avoid impacting RAM resources under your account, the cleanup logic does not delete roles/custom policies, which need to be manually deleted**.

### MCP Server Configuration

1. Navigate to [Alibaba Cloud MCP Server](https://api.aliyun.com/mcp/servers)
2. Select the "resourcecenter" official MCP service
3. Replace the default OAuth application with your created `${mcp_app_name}` (this value will be output in the ".config.json" file after executing prepare)
5. When enabling permission capabilities on AI Gateway, additional MCP server configuration is required. Please refer to the implementation in `tools/mcp/demo_apig_mcp` and `fetch-workload-access-token_sample/README-CN.md`. Enable MCP config in function `register_mcp_and_invoke` in `main.py`.

```yaml
MCP_SERVER: "<your-mcp-server-endpoint>"
DEMO_MCP_SERVER: "<your-demo-mcp-server-endpoint>"
```

![MCP Configuration](images/get_mcp_endpoint.png)

## ▶️ Running the Agent

### Starting the Agent Service

#### Local Startup

In the root directory, execute:
```bash
python -m deploy_starter.main
```

The agent runs on `http://localhost:8080` with the following endpoints:
- `/process` - Main agent interaction endpoint
- `/health` - Health check endpoint

#### Deployment as Bailian High-Code Application

If deploying to Bailian high-code application, refer to the [Bailian High-Code Deployment Guide](https://bailian.console.aliyun.com/?tab=api#/api/?type=app&url=2983030) for specific deployment procedures.

1. First, execute the following commands to install dependencies:
```bash
pip install rich
pip install alibabacloud-bailian20231229
```

2. Execute the following command in the project root directory to package:
```bash
python setup.py bdist_wheel
```
This will generate a whl file in the dist directory under the root directory.

3. Before deployment, ensure necessary environment variables with appropriate account permissions are configured:
```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-access-key-id>      
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-access-key-secret>
export MODELSTUDIO_WORKSPACE_ID=<your-workspace-id>                 # Optional, replace with Bailian business space ID where the high-code application will be deployed, otherwise the default business space will be used
```

4. Use the CLI tool to deploy the packaged whl file to Bailian(Optional, or you can upload whl package in Bailian high-code application console):
```bash
runtime-fc-deploy --deploy-name agent-identity-sample  --whl-path <PATH_TO_YOUR_NEW_WHL_FILE> --telemetry enable
```

5. Enter the [Bailian Console](https://bailian.console.aliyun.com/?tab=app#/app-center) and configure environment variables for the high-code application on the console. Two environment variables need to be configured, where `AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME` is the name of the workload identity created during the prepare operation, output in the project root directory .config.json with key `workload_identity_name`.
```bash
export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME=<your-workload-identity-name>
export DASHSCOPE_API_KEY=<your-api-key>
```

6. On the high-code application console, click View Details to enter the Function Compute instance console where the high-code application resides.
![images/go_to_fc.png](images/go_to_fc.png)

7. Create and configure an instance role for the Function Compute instance corresponding to the high-code application on the Function Compute console (need to select "Alibaba Cloud Services", and "Trusted Services" needs to select "Function Compute"), and assign the `AliyunAgentIdentityDataFullAccess` system policy to the role.

8. check the function run commond: `python3 -m deploy_starter.main`
### Start Frontend and Backend Services

#### When Agent Service is Deployed Locally
Check the frontend service configuration file, in the current root directory create a `.config.json` file, and configure the following content:
```json
{
 "workload_identity_name":"your workload identity name",
 "inbound_app_id":"your login oauth native client id"
}
```
Check backend service configuration
Configure the following content in the `app.yml` file under the `backend` directory:
```yaml
INBOUND_REDIRECT_URI: "your frontend redirect uri, e.g. http://localhost:8090"
AGENT_FRAMEWORK: "agent framework: agentScope or agentRun"
AGENT_BEARER_TOKEN: "your agent api access token. For local deployments, the accessToken configuration is not applicable."
AGENT_ENDPOINT: "your agent api endpoint, e.g. http://localhost:8080/process depends on your agent deployment config"
```

In the root directory, execute to start services:
```bash
python -m application.backend.app
```
Backend service runs on `http://localhost:8090` with the following endpoints:
- `/chat` - Main interaction endpoint, connected to agent's process with added inbound identity
- `/callback` - Callback for receiving confirmation when Agent Identity service acquires OAuth tokens
- `/callback_for_oauth` - Callback for inbound identity acquiring OAuth tokens

#### When Agent Service is Deployed on Bailian Platform

If in the previous step you chose to deploy the agent service to Bailian, you need to configure the agent service address and access token before starting services.

Enter the [Bailian Console](https://bailian.console.aliyun.com/?tab=app#/app-center), find the high-code application just deployed, and locate the public network access address and authentication token of the trigger, as shown in the figure:
![images/get_deploy_info.png](images/get_deploy_info.png)

Configure the public network access address and authentication token in config.yml:
```bash
AGENT_BEARER_TOKEN: "<Authentication Token>"
AGENT_ENDPOINT: "<Public Address>/process"
```

Start services:

```bash
python -m application.backend.app
```

### Interacting with the Agent

#### Tool Function Summary

| Command | Function | Credential Type | Mode |
|--------|----------|-----------------|------|
| Query today's weather | Weather API query | API Key | UF |
| Query today's schedule | Calendar/Schedule access | STS Token | UF |
| Query current system time | System time retrieval | OAuth Token | UF |
| Call Alibaba Cloud MCP service to query all ECS instances | Alibaba Cloud resource query | OAuth Token | UF |
| Read Alibaba Cloud OSS files | OSS file query | STS Token | UF |
| Read files from DingTalk documents | DingTalk document reading | OAuth Token | UF |
| Send DingTalk work notification | DingTalk M2M notification | M2M Token | M2M |

#### Acquiring User Identity Tokens

Navigate to the frontend page (http://localhost:8090) and click the "Login" button, which will guide you through the Alibaba Cloud OAuth authorization process (the authorized user must be under the same Alibaba Cloud account as the created OAuth application).

#### Sending Requests to the Agent

After completing OAuth authorization, you can interact with the Agent through the chat box on the frontend page.

### Testing

This sample supports two testing modes. UF mode interacts through the frontend chat box (login required), M2M mode is triggered via API call (no login required). Both modes share the same Agent workflow: receive natural language → LLM analyzes intent → invoke tool → return result.

#### UF Mode (User-present)

1. Open the frontend page (http://localhost:8090), click "Login" to complete Alibaba Cloud OAuth authorization
2. Type instructions in the chat box, the Agent will automatically select the appropriate tool based on intent

Example prompts:

- "How is the weather today?" - Testing weather API (API key authentication)
- "What is my schedule for today?" - Testing calendar/schedule tool (STS token authentication)
- "What time is it now?" - Testing system time retrieval (OAuth token authentication)
- "Help me query my ECS instance list" - Testing Alibaba Cloud MCP service (OAuth token authentication)
- "Read my OSS file" - Testing OSS file query (STS token authentication)

#### M2M Mode (Machine-to-Machine)

M2M mode simulates an external system (e.g., CI/CD) triggering the Agent via API, without user login. Send natural language instructions to the `/process` endpoint via curl, and the Agent will automatically analyze the intent and invoke M2M tools.

> The `input` field in curl is the same text you would type in the chat box, just wrapped in JSON format. UF uses the chat box, M2M uses curl — the difference is only in how the Agent is triggered.

**Prerequisite: Get DingTalk User ID**

Sending work notifications requires DingTalk user IDs (not phone numbers or employee IDs). You can obtain them by:
1. DingTalk Admin Console → Contacts → Click member → View User ID
2. Or via DingTalk API `topapi/v2/user/getbymobile` using phone number

**Example Call**

Replace `<your-dingtalk-user-id>` with the actual value, then run in terminal:

```bash
curl -X POST "http://localhost:8080/process" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "m2m-demo",
    "user_id": "m2m-demo",
    "input": [
      {
        "role": "user",
        "type": "message",
        "content": [{"type": "text", "text": "Send a DingTalk notification to user <your-dingtalk-user-id> to submit their daily report"}]
      }
    ]
  }'
```

After receiving the instruction, the LLM will extract the user ID and message content, then automatically invoke the DingTalk work notification tool. The target employee will receive a work notification in their DingTalk app.

> **Note**: M2M requests do not carry user identity information. The Agent uses machine identity to obtain credentials. In production environments, add authentication protection to the `/process` endpoint.

## 🤝 Support

For questions or concerns about the Agent Identity SDK:
- Refer to [official documentation](https://help.aliyun.com/product/agent-identity)
- Contact Alibaba Cloud support
- Submit issues in the repository

---