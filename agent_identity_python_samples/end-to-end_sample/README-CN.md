# Agent Identity Python SDK 示例

Agent Identity Python SDK 的完整演示，用于构建安全的、具备身份感知能力的AI代理。同时支持 UF（用户在场）和 M2M（无用户参与）两种凭据获取模式。

## 🚀 概述

本示例展示了如何构建一个基于[AgentScope](https://github.com/alibaba/agentscope)运行时框架，并集成Agent Identity SDK的LLM Agent服务。
包括Inbound认证，Outbound凭据获取和工具调用，会话管理，用户身份管理，云凭证获取，MCP集成等功能。部署结构上包括AI Agent服务，前端应用以及后端应用三个模块。

本示例演示两种凭据获取模式：
- **UF（用户在场）模式**：用户登录后，Agent 代表用户获取凭据并调用工具。例如：用户通过聊天框让 Agent 查询 ECS 实例、读取 OSS 文件、写入钉钉文档等。
- **M2M（无用户参与）模式**：无需用户登录，外部系统通过 API 触发 Agent，Agent 使用机器身份凭证自主执行任务。例如：CI/CD 系统触发 Agent 发送钉钉工作通知。

前端应用与后端应用构成了一个完整的入站应用，集成了阿里云OAuth2.0认证流程，可以通过浏览器进行身份验证，并获取阿里云ID Token。在获得凭据之后，前端应用可通过后端应用与Agent进行交互，使用Agent Identity的凭据托管能力进行工具使用。

整体功能点包括：

- 集成了阿里云OAuth 2.0流程对用户进行身份验证
- 获取阿里云OAuth2.0用户身份令牌作为Agent入站身份
- 集成了AgentScope Runtime框架和QwenLLM的Agent服务
- 接入了多个不同的凭证类型的工具，包括
  - 阿里云MCP服务（OAuth2令牌）
  - 写入钉钉文档（OAuth2令牌）
  - 阿里云OSS读取文件（STS Token）
  - 获取系统时间（模拟：OAuth2令牌）
  - 模拟获取天气（模拟：API Key）
  - 模拟获取今日日程（模拟：STS Token）
- 支持 M2M 模式，Agent 使用机器凭证自动获取钉钉 M2M 令牌并发送工作通知

## 🏗️ 架构
![framework.png](images/framework.png)

### 核心组件

- **身份客户端**：管理用户身份验证和令牌生命周期
- **凭证管理**：OAuth2、API密钥和STS凭证管理
- **工作负载身份**：基于Agent Identity服务的Agent身份管理
- **MCP/工具集成**：用于实时工具执行的可流式HTTP端点
- **会话管理**：跨交互的内存状态持久化

## ⚙️ 先决条件

### 系统要求
- Python ≥ 3.10
- pip包管理器

### 所需云资源

#### 1. RAM身份设置
创建一个具有以下权限的RAM子账户：

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

#### 2. DashScope API密钥
获取具有模型调用权限的[DashScope API密钥](https://bailian.console.aliyun.com/?tab=model#/api-key)。

#### 3. 钉钉企业内部应用（M2M 模式所需）

使用 M2M 模式发送钉钉工作通知，需要先在钉钉开发者平台创建钉钉应用：

1. 登录[钉钉开发者后台](https://open-dev.dingtalk.com/)
2. 进入**应用开发** → **企业内部应用** → **创建应用**
3. 填写应用名称和描述，创建应用
4. 在**基础信息**页面，记录以下三个值：
   - **AppKey**（即 client_id）
   - **AppSecret**（即 client_secret）
   - **AgentId**（应用 ID，数字类型）
5. 在**权限管理**页面，搜索并添加以下权限：
   - `企业机器人消息发送`（用于发送工作通知）
   - `通讯录个人信息读权限`（用于查询用户 ID）
6. 在**开发管理**页面，填写**服务器出口 IP**（不限制可填 `*`）
7. 在**版本管理与发布**页面，创建版本并发布应用
> **注意**：权限开通后必须发布应用才能生效。如果权限已开通但 API 返回 403，请检查是否已发布最新版本。

## 📦 安装

### 1. 克隆仓库
```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/end-to-end_sample
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

为前文中创建的RAM用户创建Access Key，并在控制台创建Dashscope API Key后，注入到环境变量中：

```bash
# 阿里云凭证
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-access-key-id>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-access-key-secret>
export AGENT_IDENTITY_REGION_ID=cn-beijing # 当前Agent Identity仅开放北京地域
# DashScope API
export DASHSCOPE_API_KEY=<your-api-key>
# M2M
export DINGTALK_APP_KEY=<your-dingtalk-app-key>
export DINGTALK_APP_SECRET=<your-dingtalk-app-secret>
export DINGTALK_AGENT_ID=<your-dingtalk-agent-id>
export DINGTALK_CORP_ID=<your-dingtalk-corp-id>
#https://open-dev.dingtalk.com/，登陆开发者平台获取CorpId
```

## 🔧 资源初始化

### 自动化设置脚本
运行准备脚本来自动创建所需的云资源：

```bash
python -m prepare
```

此脚本执行以下操作：

1. **创建身份提供者**
   - 发现URL：`https://oauth.aliyun.com/.well-known/openid-configuration`
   - 受众：`12345678`

2. **创建阿里云OAuth 2.1入站应用**
   - 作用域：`aliuid;profile;openid`

3. **创建阿里云MCP服务所需的OAuth 2.1 Native应用**
   - 作用域：`aliuid;profile;openid;/acs/mcp-server`

4. **创建工作负载身份和角色**
   - 工作负载身份名称：`workload-${UUID}`
   - 角色名称：`AgentIdentityRole-${workloadIdentityName}`
   - 角色信任策略：允许来自该工作负载身份的扮演请求
   - 角色权限策略：允许该角色调用Agent Identity数据面API

5. **配置凭证提供者**
   - 用于MCP服务器集成/获取系统时间的OAuth2提供者
   - 用于天气工具的API密钥提供者
   - 用于钉钉 M2M 工作通知的 M2M 凭证提供者（提供商名称：`dingtalk-m2m-sample`，vendor：`DingTalkOAuth2`，oauthType：`M2M`）

> **注意**：脚本会输出创建的资源信息到根目录下的.config.json中，其中包含"mcp_app_name"，需要在后续使用到。

> **注意**：如果执行过程中出现异常失败（如网络问题、资源超过quota等）需要清除创建的资源后再重新运行prepare，清除创建的资源请运行：
> ```bash
> python -m clear
> ```
> 脚本会将.config.json中的Agent Identity相关的资源进行删除。
> 
> **为避免对账号下的RAM资源造成影响，清理逻辑不会删除角色/自定义策略，需要手动删除**。

### MCP服务器配置

1. 导航到[阿里云MCP服务器](https://api.aliyun.com/mcp)
2. 选择"Core"官方MCP服务
3. 用您创建的`${mcp_app_name}`替换默认的OAuth应用（该值在执行prepare之后会输出在".config.json"文件中）
4. 使用您的MCP服务器可流式HTTP端点更新`config.yml`：
5. 开启AI网关的权限能力的时候，需要额外配置MCP服务器，参考`tools/mcp/demo_apig_mcp`的实现以及`fetch-workload-access-token_sample/README-CN.md`，并在`main.py`中`register_mcp_and_invoke`函数中启用MCP

```yaml
MCP_SERVER: "<your-mcp-server-endpoint>"
DEMO_MCP_SERVER: "<your-demo-mcp-server-endpoint>"
```

![MCP配置](images/get_mcp_endpoint.png)

## ▶️ 运行代理

### 启动代理服务

#### 本地启动

在根目录下执行：
```bash
python -m deploy_starter.main
```

代理在`http://localhost:8080`上运行，包含以下端点：
- `/process` - 主要代理交互端点
- `/health` - 健康检查端点

#### 部署为百炼高代码应用

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

4. 使用CLI工具将打包出来的whl文件部署到百炼(可选，或直接上传whl包)：
```bash
runtime-fc-deploy --deploy-name agent-identity-sample  --whl-path <PATH_TO_YOUR_NEW_WHL_FILE> --telemetry enable
```

5. 进入[百炼控制台](https://bailian.console.aliyun.com/?tab=app#/app-center)，在控制台上为高代码应用配置环境变量，需要配置如下两个环境变量，其中`AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME`为前文中执行prepare操作时创建的workload identity的名称，输出在项目根目录.config.json中，key为`workload_identity_name`。
```bash
export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME=<your-workload-identity-name>
export DASHSCOPE_API_KEY=<your-api-key>
```

6. 在高代码应用控制台上，点击查看详情，进入高代码应用所在函数计算实例的控制台。
![images/go_to_fc.png](images/go_to_fc.png)

7. 在函数计算控制台上为高代码应用对应的函数计算实例创建并配置实例角色（需要选择"阿里云服务"，并且"受信服务"需要选择"函数计算"），为角色赋予`AliyunAgentIdentityDataFullAccess`系统策略。

8. 检查函数启动命令`python3 -m deploy_starter.main`


### 启动前后端服务

#### 代理服务部署在本地的情况
检查前端服务配置文件，在当前根目录下创建`.config.json`文件，并配置以下内容：
```json
{
 "workload_identity_name":"your workload identity name",
 "inbound_app_id":"your login oauth native client id"
}
```
检查后端服务配置
在`backend`目录下的`app.yml`文件中配置以下内容：
```yaml
INBOUND_REDIRECT_URI: "your frontend redirect uri, e.g. http://localhost:8090"
AGENT_FRAMEWORK: "agent framework: agentScope or agentRun"
AGENT_BEARER_TOKEN: "your agent api access token. For local deployments, the accessToken configuration is not applicable."
AGENT_ENDPOINT: "your agent api endpoint, e.g. http://localhost:8080/process depends on your agent deployment config"
```

在根目录下执行启动服务：
```bash
python -m application.backend.app
```
后端服务在`http://localhost:8090`上运行，包含以下端点：
- `/chat` - 主要交互端点，与代理的process连接，并增加了入站身份
- `/callback` - 用于接收Agent Identity服务确认获取OAuth令牌时的回调 
- `/callback_for_oauth` - 用于入站身份获取OAuth令牌时的回调

#### 代理服务部署在百炼平台的情况

如果在上一步中选择将代理服务部署到百炼，则需要在启动服务前配置代理服务的地址和访问Token。

进入[百炼控制台](https://bailian.console.aliyun.com/?tab=app#/app-center)，找到刚才部署的高代码应用，找到触发器的公网访问地址和鉴权Token，如图所示：
![images/get_deploy_info.png](images/get_deploy_info.png)

将公网访问地址和鉴权Token配置到config.yml中：
```bash
AGENT_BEARER_TOKEN: "<鉴权Token>"
AGENT_ENDPOINT: "<公网地址>/process"
```

启动服务：

```bash
python -m application.backend.app
```

### 与代理交互

#### 工具功能汇总

| 命令 | 功能 | 凭证类型 | 模式 |
|------|------|--------|------|
| 查询今天的天气 | 天气API查询 | API密钥 | UF |
| 查询今日日程 | 日历/日程访问 | STS令牌 | UF |
| 查询当前系统时间 | 系统时间获取 | OAuth令牌 | UF |
| 调用阿里云MCP服务，查询全部ECS实例 | 阿里云资源查询 | OAuth令牌 | UF |
| 读取阿里云OSS文件 | OSS文件查询 | STS令牌 | UF |
| 读取钉钉文档中的文件 | 钉钉文档读取 | OAuth令牌 | UF |
| 发送钉钉工作通知 | 钉钉M2M通知 | M2M令牌 | M2M |


#### 获取用户身份令牌

进入前端页面（http://localhost:8090），点击"登录"按钮，将引导您完成阿里云OAuth授权流程（授权用户需要与创建的OAuth应用在同一阿里云账号下）。

#### 向代理发送请求

完成OAuth授权后，可以通过前端页面聊天框与Agent进行交互。


### 测试

本示例支持两种模式的测试。UF 模式通过前端聊天框交互（需登录），M2M 模式通过 API 调用触发（无需登录）。

#### UF 模式（用户在场）

1. 进入前端页面（http://localhost:8090），点击"登录"按钮完成阿里云 OAuth 授权
2. 在聊天框中输入指令，Agent 会根据意图自动选择对应工具

示例 Prompt：

- "今天天气怎么样？" - 测试天气API（API密钥认证）
- "我今天的日程安排是什么？" - 测试日历/日程工具（STS令牌认证）
- "现在几点了？" - 测试系统时间获取（OAuth令牌认证）
- "帮我查询我的ECS实例列表" - 测试阿里云MCP服务（OAuth令牌认证）
- "读取我的OSS文件" - 测试OSS文件查询（STS令牌认证）

#### M2M 模式（无用户参与）

M2M 模式模拟外部系统（如 CI/CD）通过 API 触发 Agent，无需用户登录。通过 curl 向 `/process` 接口发送自然语言指令，Agent 会自动分析意图并调用 M2M 工具。

> curl 中的 `input` 字段就是你在聊天框里输入的内容，只是包装成了 JSON 格式。UF 用聊天框，M2M 用 curl——区别仅在于触发方式。

**前置步骤：查询钉钉用户 ID**

发送工作通知需要钉钉用户 ID（不是手机号或工号）。可以通过以下方式获取：
1. 在钉钉管理后台 → 通讯录 → 点击成员 → 查看用户 ID

**调用示例**

将下面的 `<你的钉钉用户ID>` 替换为实际值，复制到终端运行：

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
        "content": [{"type": "text", "text": "通知钉钉用户 <你的钉钉用户ID> 提交今天的日报"}]
      }
    ]
  }'
```

Agent 收到指令后，LLM 会提取用户 ID 和消息内容，自动调用钉钉工作通知工具发送通知。目标员工的钉钉 APP 将收到工作通知消息。

> **注意**：M2M 请求不携带用户身份信息，Agent 使用机器身份获取凭据。在生产环境中，请为 `/process` 端点添加认证保护。

## 🤝 支持

关于Agent Identity SDK的问题或疑问：
- 参考[官方文档](https://help.aliyun.com/product/agent-identity)
- 联系阿里云支持
- 在仓库中提交问题

---
