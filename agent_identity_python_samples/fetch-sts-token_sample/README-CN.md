# Agent Identity Python SDK 示例

基于Agent Identity Python SDK进行百炼API Key托管的示例。

## 🚀 概述

本示例展示了如何构建一个基于[AgentScope](https://github.com/alibaba/agentscope)运行时框架，并集成了Agent Identity SDK的简单的Agent，并为Agent赋予了创建创建阿里云VPC的功能。在需要调用创建阿里云VPC工具时，Agent会通过Agent Identity
 SDK，利用工作负载身份获取对应的Agent角色，再使用该角色进行阿里云Open API调用，完成VPC的创建。
## ⚙️ 先决条件

### 系统要求
- Python ≥ 3.10
- pip包管理器

### 所需云资源

#### 1. RAM身份设置
创建一个RAM用户，赋予其Agent Identity的full access权限：
```
AliyunAgentIdentityFullAccess
```

#### 2. DashScope API密钥
获取具有模型调用权限的[DashScope API密钥](https://bailian.console.aliyun.com/?tab=model#/api-key)。

## 📦 安装

### 1. 克隆仓库
```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/fetch-sts-token_sample
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

为前文中创建的RAM用户创建Access Key，注入到环境变量中：

```bash
# 阿里云凭证
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-access-key-id>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-access-key-secret>
export AGENT_IDENTITY_REGION_ID=cn-beijing # 当前Agent Identity仅开放北京地域
export DASHSCOPE_API_KEY=<your-api-key>
```

## 🔧 资源初始化

### 创建RAM角色和工作负载身份

运行Agent Identity CLI，创建工作负载身份和角色：

```bash
agent-identity-cli create-workload-identity --workload-identity-name <your-workload-identity-name>
```

CLI将**创建如下工作负载身份和角色**：
   - 工作负载身份名称：`<your-workload-identity-name>`
   - 角色名称：`AgentIdentityRole-${workloadIdentityName}`
   - 角色信任策略：允许来自该工作负载身份的扮演请求
   - 角色权限策略：允许该角色调用Agent Identity数据面API

### 为RAM角色赋予VPC权限

进入[阿里云RAM控制台](https://ram.console.aliyun.com/roles)，为上面创建的RAM角色赋予VPC权限：AliyunVPCFullAccess。

## ▶️ 运行代理


将前面创建出来的工作负载身份名称注入到环境变量：
```bash
export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME=<your-workload-identity-name>
```

运行代理服务：
```bash
python -m deploy_starter.main
```

代理在`http://localhost:8080`上运行，包含以下端点：
- `/process` - 主要代理交互端点
- `/health` - 健康检查端点

### 调用

可以通过curl命令进行调用：
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

其中`<your-session-id>`和`<your-user-id>`为会话ID和用户ID，可自定义。

## 🤝 支持

关于Agent Identity SDK的问题或疑问：
- 参考[官方文档](https://help.aliyun.com/product/agent-identity)
- 联系阿里云支持
- 在仓库中提交问题

---
