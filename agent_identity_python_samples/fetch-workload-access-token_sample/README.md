# Agent Identity Python SDK Sample

A sample demonstrating DashScope API Key hosting based on the Agent Identity Python SDK.

## 🚀 Overview

This sample demonstrates how to build a simple Agent based on the [AgentScope](https://github.com/alibaba/agentscope) runtime framework and integrated with the Agent Identity SDK. The Agent uses the Agent Identity SDK to obtain the corresponding user WorkloadAccessToken through workload identity, and uses the workloadAccessToken as credentials to access MCP services configured on the AI Gateway. The MCP services on the API Gateway integrate permissions configured in AgentIdentity through plugins, allowing or restricting user access to services defined on the AI Gateway.

## ⚙️ Prerequisites

### System Requirements
- Python ≥ 3.10
- pip package manager

### Required Cloud Resources

#### 1. RAM Identity Setup
Create a RAM user and grant it full access permissions to Agent Identity:
```
AliyunAgentIdentityFullAccess
```

#### 2. DashScope API Key
Obtain a [DashScope API Key](https://bailian.console.aliyun.com/?tab=model#/api-key) with model invocation permissions.

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/fetch-workload-access-token_sample
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create an Access Key for the RAM user created earlier and inject it into environment variables:

```bash
# Alibaba Cloud Credentials
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-access-key-id>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-access-key-secret>
export AGENT_IDENTITY_REGION_ID=cn-beijing # Agent Identity is currently only available in Beijing region
export DASHSCOPE_API_KEY=<your-api-key>
```

## 🔧 Resource Initialization

### Create RAM Role and Workload Identity

Run the Agent Identity CLI to create workload identity and role:

```bash
agent-identity-cli create-workload-identity --workload-identity-name <your-workload-identity-name>
```

The CLI will **create the following workload identity and role**:
   - Workload Identity Name: `<your-workload-identity-name>`
   - Role Name: `AgentIdentityRole-${workloadIdentityName}`
   - Role Trust Policy: Allows assume requests from this workload identity
   - Role Permission Policy: Allows this role to call Agent Identity data plane APIs

In scenarios that support gateway authentication, additional role permissions need to be configured as follows:
```
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "agentidentitydata:SearchAuthorizedActions",
        "agentidentitydata:EvaluatePolicy"
      ],
      "Resource": "*"
    }
  ]
}
```

### AI Gateway Configuration

Go to the [Alibaba Cloud AI Gateway Console](https://apig.console.aliyun.com/) to configure MCP services.
For example, we configured an MCP service named `get-utc-time`, which defines two tools: `getutctime` and `helloworld`.

### Configure Agent User Permissions
Go to the [Alibaba Cloud AgentIdentity Policy Set Console](https://agentidentity.console.aliyun.com/policy-sets)
* Create a policy set named `apig_call_whitelist` and add the following policies:
* Associate the gateway in the same region, and authorize the corresponding MCP services and tools through visual editing. After creation, it will trigger gateway plugin installation and permission distribution.
> Special Note: After installing the plugin, authentication and authorization operations will begin. In interception mode, it will affect existing business.
* After completing the configuration, users can only use tools they have permissions for.

## ▶️ Running the Agent

Inject the workload identity name created earlier into environment variables:
```bash
export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME=<your-workload-identity-name>
```

Run the agent service:
```bash
python -m deploy_starter.main
```

The agent runs on `http://localhost:8080` with the following endpoints:
- `/process` - Main agent interaction endpoint
- `/health` - Health check endpoint

### Invocation

You can invoke it using curl commands:
```bash
curl -N \
  -X POST "http://localhost:8080/process" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [
      {
        "role": "user",
        "content": [
          { "type": "text", "text": "Tell me the time in UTC" }
        ]
      }
    ],
    "session_id": "<your-session-id>",
    "user_id": "<your-user-id>"
  }'
```

Where `<your-session-id>` and `<your-user-id>` are the session ID and user ID, which can be customized.

## 🤝 Support

For questions or inquiries about the Agent Identity SDK:
- Refer to the [official documentation](https://help.aliyun.com/product/agent-identity)
- Contact Alibaba Cloud support
- Submit issues in the repository

---