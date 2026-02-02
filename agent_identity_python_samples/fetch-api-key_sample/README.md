# Agent Identity Python SDK Sample

Sample demonstrating API Key hosting with Agent Identity Python SDK for BAILIAN.

## 🚀 Overview

This example demonstrates how to build an LLM Agent service based on the [AgentScope](https://github.com/alibaba/agentscope) runtime framework with integrated Agent Identity SDK, hosting API Keys on Agent Identity service, and dynamically acquiring API Keys at runtime.

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
cd agent_identity_python_samples/fetch-api-key_sample
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

### Create Credential Provider
Run the preparation script to automatically create required cloud resources:

```bash
python -m prepare --api-key <your-api-key>
```

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

### (Optional) Deploy as BAILIAN High-Code Application

If deploying to BAILIAN high-code application, follow the specific deployment process according to [BAILIAN High-Code Deployment Instructions](https://bailian.console.aliyun.com/?tab=api#/api/?type=app&url=2983030).

1. First execute the following command to install dependencies:
```bash
pip install rich
pip install alibabacloud-bailian20231229
```

2. Execute the following command in the project root directory for packaging:
```bash
python setup.py bdist_wheel
```
This will generate a whl file in the dist directory under the root directory.

3. Before deployment, ensure environment variables for access keys with appropriate permissions are configured:
```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-access-key-id>      
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-access-key-secret>
export MODELSTUDIO_WORKSPACE_ID=<your-workspace-id>                 # Optional, replace with BAILIAN business space ID where the high-code application will be deployed, if not set, the default business space will be used
```

4. Use CLI tool to deploy the packaged whl file to BAILIAN:
```bash
runtime-fc-deploy --deploy-name agent-identity-sample  --whl-path <PATH_TO_YOUR_NEW_WHL_FILE> --telemetry enable
```

5. Enter [BAILIAN Console](https://bailian.console.aliyun.com/?tab=app#/app-center), and configure environment variables for the high-code application on the console. Configure the following environment variables:
```bash
export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME=<your-workload-identity-name>
```

6. On the high-code application console, click "View Details" to enter the console of the function compute instance where the high-code application resides.

7. On the function compute console, create and configure an instance role for the corresponding function compute instance of the high-code application (need to select "Alibaba Cloud Service", and "Trusted Service" needs to select "Function Compute"), and assign the `AliyunAgentIdentityDataFullAccess` system policy to the role.

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
          { "type": "text", "text": "Hello" }
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