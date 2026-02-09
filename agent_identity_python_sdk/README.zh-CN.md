# Agent Identity Python SDK

Agent Identity Python SDK 是一个用于接入 Agent Identity 服务的 Python 开发工具包。该 SDK 提供了身份认证、令牌管理、API 密钥获取等功能，支持同步和异步调用模式。

## 功能特性

- **OAuth2 访问令牌获取**：支持多种 OAuth2 流程获取访问令牌
- **API 密钥获取**：程序化获取 API 密钥
- **STS 凭据获取**：获取临时安全令牌服务凭据
- **上下文管理**：线程安全的上下文变量管理
- **缓存机制**：内置凭据缓存提高性能
- **装饰器支持**：通过装饰器简化认证流程集成
- **并发安全**：支持多线程和异步环境

## 安装

```bash
pip install agent-identity-python-sdk
```

## 快速开始

### 基本配置

在使用 SDK 之前，请确保设置了正确的环境变量：

```bash
export AGENT_IDENTITY_REGION_ID="cn-beijing"  # 可选，设置您的Region ID，默认为cn-beijing
export AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN="<your-workload-access-token>" # 可选，设置您的工作负载访问令牌，如果不指定，则会自动调用Agent Identity服务获取 
export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME="<your-workload-identity-name>" # 可选，设置您工作负载身份名称，如果指定，则使用该工作负载身份作为智能体的身份，否则会生成一个随机的工作负载身份
export AGENT_IDENTITY_USE_STS="true/false" # 可选，设置是否使用智能体身份关联的角色进行资源凭据的获取，默认为true
```

### 使用装饰器自动获取令牌

```python
from agent_identity_python_sdk.core import requires_access_token

@requires_access_token(
    credential_provider_name="your-provider-name",
    inject_param_name="access_token",
    auth_flow="USER_FEDERATION",
    on_auth_url= lambda url: print(f"Please visit {url} to authenticate."),
    scopes=["openid", "profile", "email"],
    force_authentication=False,
    callback_url="http://localhost:8080",
    custom_parameters={
        "custom_param_1": "value_1",
        "custom_param_2": "value_2"
    }
)
def my_function(access_token: str):
    # 在这里使用 access_token
    print(f"Access token: {access_token}")
    # 您的业务逻辑

# 调用函数
my_function()
```

### 使用装饰器获取 API 密钥

```python
from agent_identity_python_sdk.core.decorators import requires_api_key

@requires_api_key(credential_provider_name="your-provider-name", inject_param_name="api_key")
def my_function(api_key: str):
    # 在这里使用 api_key
    print(f"API key: {api_key}")
    # 您的业务逻辑

# 调用函数
my_function()
```

### 使用装饰器获取 STS 凭据

```python
from agent_identity_python_sdk.core.decorators import requires_sts_token
from agent_identity_python_sdk.model.stscredential import STSCredential

@requires_sts_token(inject_param_name="sts_credential")
def my_function(sts_credential: STSCredential):
    # 在这里使用 sts_credential
    print(f"STS Access Key ID: {sts_credential.access_key_id}")
    # 您的业务逻辑

# 调用函数
my_function()
```

### 使用装饰器获取 Workload 凭据

```python
from agent_identity_python_sdk.core.decorators import requires_workload_access_token
@requires_workload_access_token(inject_param_name="workload_access_token")
def my_function(workload_access_token: str):
    # 在这里使用 workload_access_token
    print(f"Workload Access Token: {workload_access_token}")
    # 您的业务逻辑

# 调用函数
my_function()
```

## 核心模块

### IdentityClient

IdentityClient 是核心的身份管理客户端，提供了创建和管理身份、获取各种类型凭据的方法。

```python
from agent_identity_python_sdk.core.identity import IdentityClient

client = IdentityClient(region_id="cn-beijing")

# 创建工作负载身份
workload_identity_name = client.create_workload_identity(
    workload_identity_name="my-workload",
    allowed_resource_oauth2_return_urls=["https://example.com/callback"],
    role_arn="acs:ram::12****:role/example-role",
)

# 获取工作负载访问令牌
token = client.get_workload_access_token(
    workload_name=workload_identity_name,
    user_token="ejwyJ9***",
    user_id="example-user"
) # 优先使用user_token获取workload access token，如果没有则使用user_id获取workload access token，如果都不存在则获取不含终端用户信息的workload access token
```

### 上下文管理

SDK 提供了上下文管理器用于存储线程/异步任务隔离的数据：

#### AgentIdentityContext

用于管理工作负载访问令牌、用户ID、用户Token、会话ID等。SDK会在获取工作负载访问令牌时读取当前线程的上下文变量来获取工作负载访问令牌。

```python
from agent_identity_python_sdk.context.context import AgentIdentityContext

# 设置工作负载访问令牌
AgentIdentityContext.set_workload_access_token("your-token")

# 获取工作负载访问令牌
token = AgentIdentityContext.get_workload_access_token()

# 设置用户Token
AgentIdentityContext.set_user_token("your-token")

# 设置用户ID
AgentIdentityContext.set_user_id("user-123")

# 设置custom state
AgentIdentityContext.set_custom_state("your-state")

# 清除当前线程上下文，在单次会话结束时需要主动清除，否则可能会因为线程共享导致权限泄漏
AgentIdentityContext.clear()
```

如果context中设置了工作负载访问令牌，在获取工作负载访问令牌时将优先使用当前线程上下文变量。

如果未设置工作负载访问令牌，当SDK自动获取工作负载访问令牌时，SDK会从当前线程上下文变量中获取用户ID/用户令牌信息，按照**用户令牌/用户ID/无**的优先级获取工作负载访问令牌。

如果设置了custom state，则当发生OAuth2授权时，custom state会被传递，用户应用程序可以使用custom state来处理授权回调，进行校验等操作。推荐应用程序使用custom state来进行session校验，来规避恶意分享授权链接来获取其他用户权限的行为。

⚠️ **注意**：在当前工作流执行完成后，需要主动清除当前线程上下文，否则可能会因为线程共享导致权限泄漏。

## 环境变量配置

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| AGENT_IDENTITY_REGION_ID | 区域标识 | cn-beijing |
| AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN | 工作负载身份令牌 | 无 |
| AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME | 工作负载身份名称 | 无 |
| AGENT_IDENTITY_USE_STS | 是否使用 STS 获取资源凭据 | true |

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个 SDK。

## 许可证

本项目采用 Apache-2.0 许可证。详情请见 [LICENSE](../LICENSE) 文件。