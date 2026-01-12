# Agent Identity Python SDK 示例

基于Agent Identity Python SDK进行百炼API Key托管的示例。

## 🚀 概述

本示例展示了如何构建一个基于[AgentScope](https://github.com/alibaba/agentscope)运行时框架，并集成了Agent Identity SDK并将API Key托管在Agent Identity的服务上，在运行时动态获取API Key的LLM Agent服务。

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
cd agent_identity_python_samples/fetch-api-key_sample
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

### 创建凭据提供商
运行准备脚本来自动创建所需的云资源：

```bash
python -m prepare --api-key <your-api-key>
```

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
          { "type": "text", "text": "Hello" }
        ]
      }
    ],
    "session_id": "<your-session-id>",
    "user_id": "<your-user-id>"
  }'
```

其中`<your-session-id>`和`<your-user-id>`为会话ID和用户ID，可自定义。

### （可选）部署为百炼高代码应用

如果需要部署到百炼高代码应用，这里参照[百炼高代码部署说明](https://bailian.console.aliyun.com/?tab=api#/api/?type=app&url=2983030)给出具体的部署流程。

1. 首先请执行以下命令安装依赖：
```bash
pip install rich
pip install alibabacloud-bailian20231229
```

2. 在项目根目录执行下面命令进行打包：
```bash
python setup.py bdist_wheel
```
这将会在根目录的dist目录下生成一个whl文件。

3. 部署前请确保已配置对应账号有权限的access key等必要的环境变量：
```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-access-key-id>      
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-access-key-secret>
export MODELSTUDIO_WORKSPACE_ID=<your-workspace-id>                 #可选，替换为百炼的业务空间ID，该空间将部署高代码应用，不设置将使用默认业务空间
```

4. 使用CLI工具将打包出来的whl文件部署到百炼：
```bash
runtime-fc-deploy --deploy-name agent-identity-sample  --whl-path <PATH_TO_YOUR_NEW_WHL_FILE> --telemetry enable
```

5. 进入[百炼控制台](https://bailian.console.aliyun.com/?tab=app#/app-center)，在控制台上为高代码应用配置环境变量，需要配置如下环境变量：
```bash
export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME=<your-workload-identity-name>
```

6. 在高代码应用控制台上，点击查看详情，进入高代码应用所在函数计算实例的控制台。
![images/go_to_fc.png](images/go_to_fc.png)

7. 在函数计算控制台上为高代码应用对应的函数计算实例创建并配置实例角色（需要选择"阿里云服务"，并且"受信服务"需要选择"函数计算"），为角色赋予`AliyunAgentIdentityDataFullAccess`系统策略。


## 🤝 支持

关于Agent Identity SDK的问题或疑问：
- 参考[官方文档](https://help.aliyun.com/product/agent-identity)
- 联系阿里云支持
- 在仓库中提交问题

---
