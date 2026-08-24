# Agent Identity Python SDK 示例

AgentRun 集成 Agent Identity 的端到端示例：OIDC 入站身份、托管 MCP 工具的 OAuth2 凭据托管、Cedar 细粒度权限管控，以及 Agent 侧凭据获取（API Key / STS / OAuth2）。

## 🚀 概述

本示例演示了一个部署在 AgentRun Runtime 上的 LangChain Agent：

1. 通过 OIDC ID Token 认证终端用户（入站，由 AgentRun 网关校验）；
2. 代表用户调用 AgentRun 托管的 MCP 工具——网关注入的 Workload Access Token（WAT）被转发给工具，由 AgentIdentity Hook 完成 Cedar 鉴权与 OAuth2 凭据注入；
3. 通过 Agent Identity SDK 为本地工具获取凭据（API Key、OSS STS、OAuth2）。

内置工具：

| 能力 | 工具 | 开启方式（env） |
|---|---|---|
| 托管 MCP 工具调用（OAuth2 托管 + Cedar） | `tool_resource(TOOL_NAME)` 加载 | 默认开启 |
| API Key 凭据托管 | `weather_search` | `ENABLE_WEATHER_TOOL=1` |
| OSS STS 临时凭据 | `get_object_from_oss` | `ENABLE_OSS_TOOL=1` |
| OAuth2 用户授权凭据注入 | `get_current_time` | `ENABLE_TIME_TOOL=1` |
| STS 临时凭据注入 | `get_schedule` | `ENABLE_SCHEDULE_TOOL=1` |

## ⚙️ 先决条件

### 系统要求
- Python ≥ 3.10
- pip 包管理器

### 资源准备

#### 1. OIDC 身份提供商
准备一个 OIDC 身份提供商作为入站身份签发方。需要它的 Discovery URL
（`.../.well-known/openid-configuration`），以及为终端用户签发测试 ID Token 的途径。

#### 2. 创建 AgentRun 大语言模型
在 AgentRun 控制台（模型管理）创建一个模型。记录**服务名**（卡片标题）和
**模型名**（卡片内的模型标签）。

#### 3. OAuth2 凭据链
1. RAM 控制台 → 应用管理 → 创建 Web 应用（OAuth 2.1）；授权范围勾选
   `openid`、`aliuid`、`profile`，以及上游 MCP 要求的 scope；
2. AgentIdentity 控制台 → 凭证提供商 → 创建 OAuth2 Provider 并关联该应用。
   名称固定为 **`test-provider-for-mcp-oauth`**（样例的时间工具按此名引用，
   见 `get_current_time.py`；如需自定义请同步修改代码）。复制 Provider 页展示的回调地址；
3. 回到 RAM 应用，回填该回调地址。

#### 4. API Key 凭证提供商
AgentIdentity 控制台 → 凭证提供商 → 创建 **API Key** 型提供商，名称固定为
**`test-provider-api-key`**（`weather_search.py` 按此名引用）。Key 值任意非空字符串
即可——mock 工具只验证注入，不校验真伪。

#### 5. 创建远程 MCP 工具
AgentRun 控制台 → 工具与Skills → 创建远程 MCP 工具，填入上游 MCP 地址，
开启 AgentIdentity 身份认证并绑定第 3 步的 OAuth2 Provider。

## 📦 安装和部署到 AgentRun

### 1. 克隆仓库
```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/agentrun-e2e_sample
```

### 2. 安装依赖到本地
```bash
pip install -r requirements.txt -t ./python
```
注意：构建环境需与 AgentRun 部署环境一致（linux/amd64、Python 3.12）。
在 macOS 上请追加 `--platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:`。
该目录布局与运行时的 `PYTHONPATH=/opt/python:/code/python` 一致，安装到
`python/` 的依赖在部署后可直接导入。

### 3. 打包为 zip
将当前目录（包含 `python/` 子目录）打包为 zip 文件，用于通过代码包创建 Agent：
```bash
zip -r agentrun-e2e-sample.zip . -x "*__pycache__*"
```

### 4. 创建 Agent
在 AgentRun 控制台通过代码包创建 Agent。环境变量：

| 变量 | 必填 | 说明 |
|---|---|---|
| `MODEL_SERVICE_NAME` | 是 | 模型服务名（卡片标题） |
| `MODEL_NAME` | 是 | 模型名 |
| `TOOL_NAME` | 是 | 托管 MCP 工具名，多个用英文逗号分隔 |
| `AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME` | 使用 OSS 等本地工具时必填 | 工作负载身份名（agent-identity-cli 创建） |
| `AGENT_IDENTITY_REGION_ID` | 使用本地工具时必填 | AgentIdentity 数据面地域（SDK 默认 cn-beijing，须显式指定） |

凭证配置：选择「AgentIdentity 身份提供商认证」，选取资源准备中注册的 OIDC IdP。

### 调用

```bash
curl <agent-endpoint>/openai/v1/chat/completions -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <你的IdP签发的ID-Token>" \
  -d '{"messages":[{"role":"user","content":"你有什么工具？"}],"stream":false}'
```

首次调用托管 MCP 工具会返回 OAuth2 授权链接，在浏览器中完成授权后再次调用即可。

## 🤝 支持

关于 Agent Identity SDK 的问题或疑问：
- 参考[官方文档](https://help.aliyun.com/product/agent-identity)
- 联系阿里云支持
- 在仓库中提交 issue
