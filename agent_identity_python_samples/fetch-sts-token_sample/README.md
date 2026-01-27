# Agent Identity Python SDK Sample

Sample demonstrating STS token acquisition with Agent Identity Python SDK for BAILIAN.

## 🚀 Overview

This example demonstrates how to build a simple Agent based on the [AgentScope](https://github.com/alibaba/agentscope) runtime framework with integrated Agent Identity SDK, which is granted the ability to create Alibaba Cloud VPCs. When the Agent needs to invoke the create Alibaba Cloud VPC tool, it will use the Agent Identity SDK to obtain the corresponding Agent role through the workload identity, and then use that role to make Alibaba Cloud Open API calls to create the VPC.

## ⚙️ Prerequisites

### System Requirements
- Python ≥ 3.10
- pip package manager

### Required Cloud Resources

#### 1. RAM Identity Setup
Create a RAM user with full access permissions for Agent Identity:
```
AliyunAgentIdentityFullAccess
```

#### 2. DashScope API Key
Obtain a [DashScope API key](https://bailian.console.aliyun.com/?tab=model#/api-key) with model invocation permissions.

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/fetch-sts-token_sample
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create Access Key for the RAM user created earlier, and inject them into environment variables:

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
   - Role trust policy: Allows assume requests from this workload identity
   - Role permission policy: Allows the role to call Agent Identity data plane APIs

### Grant VPC Permissions to the RAM Role

Go to [Alibaba Cloud RAM Console](https://ram.console.aliyun.com/roles), grant VPC permissions to the RAM role created above: AliyunVPCFullAccess.

## ▶️ Run Agent

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

Can be invoked via curl command:
```bash
curl -N \
  -X POST "http://localhost:8080/process" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [
      {
        "role": "user",
        "content": [
          { "type": "text", "text": "帮我创建我的VPC调用工具帮我创建一个VPC，网段为192.168.0.0/16，name为test-vpc+随机字符串，region为cn-hangzhou" }
        ]
      }
    ],
    "session_id": "<your-session-id>",
    "user_id": "<your-user-id>"
  }'
```

Where `<your-session-id>` and `<your-user-id>` are session ID and user ID respectively, which can be customized.

## 🤝 Support

For questions or inquiries about Agent Identity SDK:
- Refer to [Official Documentation](https://help.aliyun.com/product/agent-identity)
- Contact Alibaba Cloud support
- Submit issues in the repository

---