# MCP Chatbot + Agent Identity 部署指南

从零开始部署一个基于 Agent Identity 鉴权的 MCP Chatbot Demo。

---

## 目录

- [架构概览](#架构概览)
- [前置条件](#前置条件)
- [一、部署测试 HTTP 服务（Order Service）](#一部署测试-http-服务order-service)
- [二、Agent Identity 入站配置](#二agent-identity-入站配置)
- [三、Agent Identity 出站配置](#三agent-identity-出站配置)
- [四、AI 网关托管 MCP 配置](#四ai-网关托管-mcp-配置)
- [五、Agent Identity 策略集](#五agent-identity-策略集)
- [六、AI 网关插件配置](#六ai-网关插件配置)
- [七、Agent Identity 策略集编辑](#七agent-identity-策略集编辑)
- [八、Chatbot 部署](#八chatbot-部署)
- [九、端到端验证](#九端到端验证)
- [十、Troubleshooting（常见问题排查）](#十troubleshooting常见问题排查)
- [附录：配置参考](#附录配置参考)

---

## 架构概览

```
┌─────────┐     ┌─────────────────────────┐     ┌──────────────────┐
│ Chatbot │────>│  AI 网关 (APIG)         │────>│  ECS 订单服务     │
│ (本地)  │     │       (VPC 内)          │     │ (order-service-  │
│         │     │                         │     │  oauth, FastAPI) │
│  OIDC   │     │  WASM 插件:              │     │                  │
│  登录   │     │  AgentIdentity 插件     │     │  ├─ OAuth2 端点  │
│         │     │  (认证+Cedar鉴权+凭据注入)│     │  └─ 订单 CRUD    │
└─────────┘     └─────────────────────────┘     └──────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ Agent Identity   │
                │ (用户池 + 策略集)│
                └──────────────────┘
```

本 Demo 包含一个完整的 MCP 后端服务（本 sample 的 `order_service/` 目录），提供：
- **order-service-oauth**：带 OAuth2 的订单 CRUD 服务（FastAPI，仅限测试），部署在 ECS 上

**请求流程：**

1. 用户通过 OIDC 登录获取 ID Token
2. Chatbot 用 ID Token 换取 Workload Access Token (WAT)
3. Chatbot 将 WAT 放在 `Authorization: Bearer <WAT>` 头中请求 AI 网关
4. AI 网关上的 AgentIdentity WASM 插件处理请求：
   - 身份认证（验证 WAT）
   - Cedar 策略鉴权
   - 凭据注入（OAuth2 Token 获取并注入到下游请求）
5. 鉴权通过则转发到 ECS 上的订单服务；拒绝则返回 403

---

## 前置条件

| 条件 | 说明 |
|------|------|
| 阿里云账号 | 开通 Agent Identity 和 AI 网关服务 |
| 阿里云 VPC | 一个 VPC（推荐 `cn-beijing`），用于部署 AI 网关 |
| 阿里云 ECS | 一台带公网 IP 的 ECS 实例（推荐 Ubuntu 24.04），用于部署订单服务（创建步骤见 §1.1） |
| Python 3.11+ | Chatbot 运行环境 |
| pip 依赖 | 以本 sample 目录的 `requirements.txt` 为准（`mcp`、`langchain-core`、`langgraph`、`httpx`、`pydantic`、`agent-identity-python-sdk`、`certifi`） |
| LLM API | 阿里云百炼 DashScope API 或兼容端点 |

### 前置检查清单

开始部署前，请逐项确认：

- [ ] **产品开通**：Agent Identity、AI 网关（APIG）、ECS、VPC/NAT 网关、RAM、百炼（Model Studio）均已开通
- [ ] **操作权限**：操作者（RAM 用户/角色）具备上述产品的管理权限；Chatbot 运行时使用的 RAM 身份需附加 `AliyunAgentIdentityFullAccess`（用于换取 WAT）
- [ ] **CLI 配置**（若使用 aliyun CLI）：已安装 aliyun CLI 并通过 `aliyun configure` 配置好 profile。**注意：Agent Identity 的 CLI 产品名为 `agentidentity`（API 版本 `2025-09-01`）**，不存在 `agentidentitycontrol` 这个产品名
- [ ] **SDK/CLI 凭据与目标账号一致**：SDK 默认凭据链与 aliyun CLI 默认 profile 可能解析到其他账号。请确认 `ALIBABA_CLOUD_ACCESS_KEY_ID`/`ALIBABA_CLOUD_ACCESS_KEY_SECRET`（或 CLI 的 `--profile`/`--region`）与所部署资源属于同一账号，否则会出现误导性的 `EntityNotExists.WorkloadIdentity` 报错（见 §10.1-④）
- [ ] **本地环境**：Python 3.11+、可打开浏览器的桌面环境（OIDC 登录需要）、SSH 客户端
- [ ] **Region 一致性**：推荐所有资源（ECS、VPC、AI 网关、Agent Identity 资源）统一使用 `cn-beijing`
- [ ] **记录习惯**：全程会产生大量 ID/ARN（用户池 ID、Client ID、网关 ID、网关 GatewayArn、provider ARN、RAM 角色 ARN、WI ARN 等），建议边做边记录

### 预计耗时与难度提示

- **预计耗时**：2～4 小时（AI 网关、NAT 网关等资源的创建需要等待数分钟到十余分钟）
- **难度**：中高。涉及 6 个以上云产品的协同，且部分步骤存在严格顺序依赖（尤其 §三与 §四之间的"先占位、后回填"），建议一次性连续完成
- **跳坑建议**：部署前先通读 [§十 Troubleshooting](#十troubleshooting常见问题排查)，其中汇总了全部已知坑位

---

## 一、部署测试 HTTP 服务（Order Service）

> **如果你已有支持 OAuth2 鉴权的 HTTP 后端服务，可跳过此步骤**，直接使用你的服务地址。

Demo 包中包含一个带 OAuth2 的订单 CRUD 服务（本 sample 的 `order_service/` 目录），部署在 ECS 上作为 AI 网关的上游。

### 1.1 创建 ECS 实例与安全组（已有可跳过）

1. 登录 [ECS 控制台](https://ecs.console.aliyun.com) → **创建实例**：
   - **地域**：`cn-beijing`（推荐与 AI 网关同地域）
   - **镜像**：Ubuntu 24.04 64 位
   - **规格**：2 vCPU/4 GiB 及以上（如 `ecs.e-c1m2.large`，按量付费即可）
   - **系统盘**：ESSD 云盘（`cloud_essd`）。注意：部分入门级规格**不支持**高效云盘（`cloud_efficiency`，会报 `InvalidSystemDiskCategory.ValueNotSupported`）
   - **网络**：选择后续部署 AI 网关所用的 **同一 VPC** 及其交换机（网关后端需通过私网 IP 访问本实例）
   - **公网 IP**：勾选"分配公网 IPv4 地址"，按使用流量计费
   - **登录凭证**：设置自定义密码（用于 SSH），并妥善保管
2. 创建/选择**安全组**，添加入方向规则：
   - TCP **22**（SSH 部署操作）
   - TCP **8001**（订单服务，外网验证用；授权对象按需收紧）
3. 创建完成后记录：**公网 IP**（SSH 与初期验证）、**私网 IP**（§四网关后端地址）

### 1.2 上传代码到 ECS

```bash
# 在本 sample 目录（agent_identity_python_samples/ai-gateway-mcp-auth-credential-injection_sample）下执行
# 上传到 ECS
ECS_IP=<你的 ECS 公网 IP>

ssh root@$ECS_IP "mkdir -p /opt/order-service-oauth"
cat order_service/main.py | ssh root@$ECS_IP "cat > /opt/order-service-oauth/main.py"
cat order_service/requirements.txt | ssh root@$ECS_IP "cat > /opt/order-service-oauth/requirements.txt"
cat order_service/test_oauth.sh | ssh root@$ECS_IP "cat > /opt/order-service-oauth/test_oauth.sh"
```

### 1.3 安装 Python 环境和依赖

```bash
ssh root@$ECS_IP

# Ubuntu 24.04 需要 venv
apt update && apt install -y python3.12-venv

cd /opt/order-service-oauth
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 1.4 启动订单服务

```bash
cd /opt/order-service-oauth

# 默认端口 8001，OAUTH_BASE_URL 设为 ECS 公网地址 + 端口
OAUTH_BASE_URL=http://$ECS_IP:8001 nohup .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/order-service.log 2>&1 </dev/null &
```

> **重要**：后台启动命令末尾的 `</dev/null` 不可省略。通过 SSH 会话执行 nohup 时若不重定向 stdin，会话可能挂起不返回（服务本身正常，但终端被卡住）。
>
> **端口说明**：服务默认监听 8001 端口，需在阿里云安全组中放行该端口（连同 22 端口，见 §1.1）。
>
> **提示**：此处 `OAUTH_BASE_URL` 暂用 ECS 地址便于本地验证；待 AI 网关就绪并按步骤四的"OAuth 端点透传"（§4.7）配置完成后，需将 `OAUTH_BASE_URL` 改为网关入口域名并重启服务（须与 provider 的 Issuer 一致，见 §三的回填说明）。

验证启动成功：

```bash
# 本机测试
curl http://127.0.0.1:8001/.well-known/oauth-authorization-server
# 应返回 JSON，包含 issuer、authorization_endpoint、token_endpoint

# 外网测试（需安全组放行 8001）
curl http://$ECS_IP:8001/.well-known/oauth-authorization-server
```

### 1.5 测试 OAuth 全流程

```bash
ssh root@$ECS_IP
cd /opt/order-service-oauth && chmod +x test_oauth.sh && bash test_oauth.sh
```

脚本自动完成：授权获取 code → 换 token → 创建订单 → 列出订单 → 无 token 401 → refresh 续期。

---

## 二、Agent Identity 入站配置

入站配置用于认证用户身份，包括创建用户池、客户端、客户端密钥、配置登录方式、创建测试用户、创建入站身份提供商（IdP）、创建 RAM 角色与 Workload Identity。本节所有资源均在 [Agent Identity 控制台](https://agentidentity.console.aliyun.com)（Region `cn-beijing`）创建。

> **CLI 产品名说明**：若使用 aliyun CLI 操作 Agent Identity，产品名为 **`agentidentity`**（API 版本 **`2025-09-01`**），不存在 `agentidentitycontrol` 这个产品名（执行会报 `not a valid command or product`）。

### 2.1 创建用户池

1. 登录 [Agent Identity 控制台](https://agentidentity.console.aliyun.com)
2. 左侧菜单选择 **用户池管理** → **创建用户池**
3. 填写基本信息：
   - **用户池名称**：`mcp-chatbot-demo`
   - **Region**：选择 `cn-beijing`
4. 创建完成后记录：
   - **用户池 ID**：`up_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **OIDC Discovery 地址**：`https://signin-{region}.aliyunagentid.com/{用户池ID}/.well-known/openid-configuration`

![用户池基本信息与元数据配置](images/01-user-pool-info.png)

### 2.2 创建客户端

在用户池中创建客户端，用于用户 OIDC 登录获取 ID Token。

1. 进入用户池详情 → **客户端管理** → **创建客户端**
2. 填写客户端配置：
   - **名称**：`mcp-chatbot`
   - **回调地址**：`http://localhost:18080/callback`
   - 其他配置保持默认
3. 创建完成后，进入客户端详情 → **客户端密钥** → **创建密钥**（注意：新建客户端默认 `SecretRequired=false` 即无密钥模式，本 Demo 需要显式创建密钥）
4. 记录以下信息：
   - **Client ID**：`client_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Client Secret**：创建密钥时获得的密钥值

![创建客户端密钥](images/02-client-secret.png)

### 2.3 启用密码登录（内置账号密码方式，推荐）

> **⚠️ 阻断级坑位**：新建用户池默认 **`EnablePasswordLogin=false`**。若不显式启用密码登录，OIDC 登录页会报 **`NO_LOGIN_METHOD_ENABLED`**，登录流程无法开始。

**推荐通过 SDK 启用**（Python SDK，`agent-identity-python-sdk`）：

```python
# 示例：启用用户池内置密码登录
client.update_login_preference(enable_password_login=True)  # 具体方法名以 SDK 版本为准（UpdateLoginPreference）
```

> **已知坑**：通过 aliyun CLI 的 force 模式（`--force`）传嵌套的 `LoginPreference` 参数会被**静默忽略**（命令返回成功但实际未生效），请不要依赖 CLI 完成此步，改用 SDK 或控制台。启用后建议回读确认 `EnablePasswordLogin=true`。

启用后即可使用用户池内置的账号密码登录（配合 §2.5 创建的测试用户）。如果你的企业环境要求走 SAML SSO，见下一小节。

### 2.4 配置用户池登录方式（SAML SSO，可选）

配置用户池的登录方式，使终端用户可以通过 SAML SSO 登录。

1. 进入用户池详情 → **登录方式** → **添加登录方式**
2. 选择 **SAML SSO**
3. 上传你的 IdP 的 SAML Metadata（或手动填写 IdP Entity ID、SSO URL、证书）
4. 保存后，**下载用户池的 SP Metadata**，上传到你的 IdP 侧完成配置
5. 配置完成后，用户登录时将通过 SAML SSO 完成身份认证

> **提示**：如果仅用于测试，无需配置 SSO，使用 §2.3 的内置账号密码登录即可。

![配置 SAML SSO 身份提供商](images/03-saml-sso-config.png)

### 2.5 创建测试用户

后续 OIDC 登录与端到端验证需要一个真实用户：

1. 进入用户池详情 → **用户管理** → **创建用户**
2. 填写用户名（如 `demo-user`），并**设置密码**（对应 SDK/CLI 的 CreateUser + SetUserPassword）
3. 记录用户名与密码（后续 §八 Chatbot 登录时使用）

### 2.6 创建入站身份提供商（Inbound IdP）

Workload Identity 需要关联一个入站 IdP 才能信任用户池签发的 ID Token：

1. 左侧菜单选择 **入站** → **身份提供商** → **创建**，类型选 **OIDC**
2. 配置：
   - **名称**：`mcp-chatbot-inbound`
   - **Discovery URL**：用户池的 OIDC Discovery 地址（§2.1 记录的 `https://signin-{region}.aliyunagentid.com/{用户池ID}/.well-known/openid-configuration`）
   - **允许的 Audience（AllowedAudience）**：§2.2 创建的客户端 Client ID
3. 创建后记录 **入站 IdP 名称与 ARN**，§2.8 创建 Workload Identity 时需关联

### 2.7 创建 RAM 角色（供 Workload Identity 扮演）

Workload Identity 换取下游凭据时需要扮演一个 RAM 角色：

1. 登录 [RAM 控制台](https://ram.console.aliyun.com) → **角色** → **创建角色** → 信任实体类型选 **阿里云服务**
2. **受信服务**选择 Agent Identity 工作负载服务：`workload.agentidentity.aliyuncs.com`
3. 编辑角色**信任策略**，加上 Workload Identity ARN 条件（限制只有该 WI 可扮演）：

```json
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": { "Service": ["workload.agentidentity.aliyuncs.com"] },
      "Condition": {
        "StringEquals": {
          "acs:SourceArn": "acs:agentidentity:{region}:{accountId}:workloadidentitydirectory/default/workloadidentity/{你的WI名称}"
        }
      }
    }
  ],
  "Version": "1"
}
```

4. 为角色**附加权限策略**：
   - 最简做法：系统策略 **`AliyunAgentIdentityDataFullAccess`**（含凭据获取 + 策略评估全部权限）
   - 最小权限做法：至少包含 **`agentidentitydata:GetCredential`**（如 `AliyunAgentIdentityDataGetCredentialAccess`）**与 `agentidentitydata:EvaluatePolicy`** 两项权限

> **⚠️ 阻断级坑位**：缺少 `agentidentitydata:EvaluatePolicy` 时，会出现 **`tools/list` 正常但所有 `tools/call` 返回 403 AccessDenied 且 reasons 为空**，网关插件不会给出明确提示（策略评估被 RAM 隐式拒绝后 fail-closed）。详见 [§10.4](#十troubleshooting常见问题排查)。

5. 记录**角色 ARN**：`acs:ram::{accountId}:role/{角色名}`

### 2.8 创建 Workload Identity

1. 左侧菜单选择 **Workload Identity** → **创建**（或在控制台对应入口）：
   - **名称**：如 `mcp-chatbot-demo-wi`
   - **关联入站 IdP**：§2.6 创建的 `mcp-chatbot-inbound`
   - **RAM 角色（RoleArn）**：§2.7 创建的角色 ARN（未绑角色时换取下游凭据会报 `MissingRoleArn`）
   - **推荐关闭 session binding（`SessionBindingEnabled=false`）**：关闭后插件无需配置 `oauthReturnURL`，Workload Identity 也无需配置"允许的 OAuth2 回调地址（AllowedResourceOAuth2ReturnURLs）"白名单，配置最简
2. CLI 创建示例（产品名 `agentidentity`，版本 `2025-09-01`）：

   ```bash
   # <workloadIdentityName>、<roleArn>、<inboundIdpName> 替换为实际值；不传 AllowedResourceOAuth2ReturnURLs
   aliyun agentidentity CreateWorkloadIdentity \
     --WorkloadIdentityName <workloadIdentityName> \
     --RoleArn <roleArn> \
     --IdentityProviderName <inboundIdpName> \
     --SessionBindingEnabled false
   ```

   若通过 API 创建，对应请求字段为 `SessionBindingEnabled: false`（不填 `AllowedResourceOAuth2ReturnURLs`）。
3. 记录 **Workload Identity 名称与 ARN**（§八 `.env` 中的 `AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME` 即填名称）

> **仅当 Workload Identity 开启 session binding（`SessionBindingEnabled=true`）时**：才需要配置**允许的 OAuth2 回调地址（ReturnURLs）白名单**，使其包含插件配置中 `oauthReturnURL` 使用的地址（含 http/https 两种协议形式），且插件必须配置 `oauthReturnURL`，否则凭据获取会报 `MissingParameter.ResourceOAuth2ReturnURL` / `Missmatch.ResourceOAuth2ReturnURL`。

---

## 三、Agent Identity 出站配置

出站配置用于创建 OAuth2 凭据提供商，使 MCP 服务能够通过 OAuth2 协议访问下游资源（即步骤一中部署在 ECS 上的订单服务）。

> **⚠️ 执行顺序说明（先占位、后回填）**：OAuth2 provider 的 discovery/授权/令牌端点最终必须配置为 **AI 网关透传域名**（见下方"重要"），但 AI 网关要到步骤四才创建。推荐执行方式：
>
> 1. **本节先用 ECS 直连地址占位创建 provider**：`http://{ECS公网IP}:8001`（此时仅能验证 provider 创建成功，授权链路暂不可用）；
> 2. **完成 §四（网关 + OAuth 透传路由，见 §4.7）后回填**：通过控制台编辑或 `UpdateOAuth2CredentialProvider` API，将 Issuer/DiscoveryURL/授权端点/令牌端点统一改为网关入口域名 `http://{网关入口地址}`；
> 3. **同步重启订单服务**：将 ECS 上 `OAUTH_BASE_URL` 改为同一网关域名并重启（§1.4），保证 well-known 文档中的 issuer 与 provider 配置全程一致。
>
> 也可以选择在完成 §四之后再执行本节全部内容，效果等价。

### 3.1 创建 OAuth2 凭据提供商

1. 左侧菜单选择 **出站** → **凭据提供商** → **OAuth2**
2. 点击 **创建 OAuth2 凭据提供商**
3. 配置：
   - **名称**：`mcp-order-oauth2`
   - **授权类型**：`USER_FEDERATION`
   - **供应商**：自定义
   - **配置方法**：手动配置
   - **客户端 ID**：`order-client`（订单服务的 OAuth2 client_id）
   - **客户端密钥**：`order-secret`（订单服务的 OAuth2 client_secret）
   - **发现端点（Discovery URL）**：`http://{OAuth端点基地址}/.well-known/oauth-authorization-server`
   - **颁发者（Issuer）**：`http://{OAuth端点基地址}`（见下方端点可达性说明，最终必须为网关入口域名）
   - **授权端点（Authorization Endpoint）**：`http://{OAuth端点基地址}/oauth/authorize`
   - **令牌端点（Token Endpoint）**：`http://{OAuth端点基地址}/oauth/token`
   - **是否启用 PKCE**：视下游服务要求而定
4. 创建完成后记录：
   - **凭据提供商 ARN**：`acs:agentidentity:cn-beijing:{accountId}:tokenvault/default/oauth2credentialprovider/{providerName}`
   - 创建时返回的 **OAuth 回调地址（callback URL）**（若控制台展示），供排查使用

> **重要（端点可达性）**：颁发者/发现/授权/令牌等 OAuth 端点必须能被 **Agent Identity 数据面**访问（授权流程中数据面会拉取 discovery 文档并跳转授权端点）。实测数据面**无法直连 ECS 公网 IP**（报 `InvalidOAuthDiscoveryURL: Unreachable`），推荐做法：将 OAuth discovery/authorize/token 端点**经 AI 网关透传**（网关后端服务指向 ECS 同 VPC 私网地址，为 `/.well-known/*`、`/oauth/*` 前缀创建透传路由，见 §4.7），并将提供商的 Issuer/各端点配置为网关入口域名；同时订单服务的 `OAUTH_BASE_URL` 也需指向同一网关域名，保证 issuer 一致。若本步先以 ECS 地址占位创建，网关就绪后务必按本节开头说明完成**回填**。

![OAuth2 凭据提供商配置](images/04-oauth2-provider-config.png)

---

## 四、AI 网关托管 MCP 配置

在 VPC 内创建 AI 网关实例，并配置网络使其具备公网访问能力。

### 4.1 创建 AI 网关实例

1. 登录 [AI 网关控制台](https://apig.console.aliyun.com/#/cn-beijing/ai-gateway)
2. 选择 **AI 网关** → **创建实例**
3. 配置：
   - **实例名称**：`mcp-demo-gateway`
   - **Region**：`cn-beijing`
   - **VPC**：选择你用于部署的 VPC
   - **规格**：按需选择
4. 创建完成后记录：
   - **网关 ID**：`gw-xxxxxxxxxxxxxxxxxxxx`

> **注意**：创建 AI 网关实例时不会立即获得网关入口地址，入口地址在创建 MCP 服务后才会生成。

### 4.2 配置 VPC 网络（NAT 网关 + EIP）

AI 网关部署在 VPC 内，需要通过 NAT 网关 + EIP 访问公网（用于调用 Agent Identity API 和访问 ECS 上的订单服务）。

1. 进入 [VPC 控制台](https://vpc.console.aliyun.com) → 选择你的 VPC
2. **创建 NAT 网关**：
   - 在 VPC 内创建 NAT 网关
   - 选择与 AI 网关相同的可用区

![VPC 资源管理 - NAT 网关](images/05-vpc-nat-gateway.png)

3. **配置 EIP**：
   - 申请一个弹性公网 IP（EIP）
   - 将 EIP 绑定到 NAT 网关

![创建公网 NAT 网关并绑定 EIP](images/06-create-nat-gateway.png)

4. **配置 SNAT 规则**：
   - 创建 SNAT 条目，将 VPC 内网段（或 AI 网关所在交换机）的出站流量通过 NAT 网关转发
   - 确保 AI 网关所在子网的实例可以通过 NAT 访问公网

![创建 SNAT 条目](images/07-snat-entry.png)

> 如果你的 VPC 已经有 NAT 网关并配置了公网访问，可跳过此步骤。

### 4.3 创建后端服务

在 AI 网关中创建后端服务，指向 ECS 上的订单服务。

1. 进入 AI 网关实例 → **服务管理** → **创建服务**
2. 配置：
   - **服务来源**：**IP 地址（固定 IP/VIP 类型）**。注意：后端地址是 `IP:端口` 形式时必须选 IP 地址类型；选择"DNS 域名"类型会拒绝带端口的 IP 地址
   - **服务地址**：`{ECS私网IP}:8001`（§1.1 记录的私网 IP，步骤一中部署的订单服务）
   - **服务名称**：`order-service`
3. 保存

> **注意**：网关出网经 ENI/VPC 转发，**无法连通 ECS 公网 IP**（表现为 503 connection timeout），后端服务地址必须使用与网关同 VPC 的**私网 IP**。

![创建后端服务](images/08-create-service.png)

### 4.4 创建 MCP 服务

1. 进入 AI 网关实例 → **MCP 管理** → **创建 MCP**
2. 配置：
   - **类型**：HTTP 转 MCP
   - **后端服务**：选择上一步创建的 `order-service` 服务
   - **MCP 接入点**：添加一个域名（如 `mcp-demo.example.com`）。注意：该域名必须在你的账号内未被占用，若提示冲突请换一个（如 `mcp-demo-{随机后缀}.example.com`）
3. 保存，然后对该 MCP 服务执行 **部署/发布**（携带接入点域名）

![创建 MCP 服务](images/09-create-mcp-service.png)

> **注意**：MCP 服务创建后需**部署（Deploy）**才会生效并生成网关默认入口域名；未部署时入口地址不可用。保存/部署后即可获得 **MCP 服务地址**（网关入口地址），格式如：`http://{网关入口地址}/mcp-servers/{服务路径}`。记录此地址，后续作为 Chatbot 的 `MCP_SERVER_URL`。

### 4.5 编辑 MCP 工具

进入 MCP 服务详情 → **编辑工具**，输入以下元数据配置：

```yaml
server:
  name: test-order-agent-identity
  securitySchemes:
    - id: ""
      type: ""
  passthroughAuthHeader: true
tools:
  - name: createOrder
    description: 创建订单 - 创建新订单
    args:
      - name: customer_name
        description: 客户姓名
        type: string
        required: true
        position: body
      - name: items
        description: 订单明细（至少一项）
        type: array
        required: true
        items:
          description: ""
          properties:
            name:
              description: 商品名称
              type: string
            quantity:
              description: 数量（大于 0）
              type: integer
            unit_price:
              description: 单价（大于 0）
              type: number
          required:
            - name
            - quantity
            - unit_price
          type: object
        position: body
    requestTemplate:
      url: /orders
      method: POST
      headers:
        - key: Content-Type
          value: application/json
      security:
        id: ""
    responseTemplate:
      prependBody: |
        # API Response Information
        Below is the response from an API call.
        ## Response Structure
        > Content-Type: application/json
        - **created_at**: 创建时间 (Type: string)
        - **customer_name**: 客户姓名 (Type: string)
        - **id**: 订单 ID（8 位 hex） (Type: string)
        - **items**: 订单明细 (Type: array)
        - **status**: 订单状态 (Type: string)
        - **total_amount**: 订单总金额 (Type: number)
        - **updated_at**: 更新时间 (Type: string)
        ## Original Response
    outputSchema:
      description: 创建成功
      type: object
      properties:
        created_at:
          description: 创建时间
          type: string
        customer_name:
          description: 客户姓名
          type: string
        id:
          description: 订单 ID（8 位 hex）
          type: string
        items:
          description: 订单明细
          type: array
          items:
            type: object
            properties:
              name:
                description: 商品名称
                type: string
              quantity:
                description: 数量
                type: integer
              unit_price:
                description: 单价
                type: number
        status:
          description: 订单状态
          type: string
        total_amount:
          description: 订单总金额（自动计算）
          type: number
        updated_at:
          description: 更新时间
          type: string
  - name: deleteOrder
    description: 删除订单 - 根据 ID 删除订单
    args:
      - name: order_id
        description: 订单 ID
        type: string
        required: true
        position: path
    requestTemplate:
      url: /orders/{order_id}
      method: DELETE
      security:
        id: ""
    responseTemplate: {}
  - name: getOrder
    description: 查询单个订单 - 根据 ID 查询订单详情
    args:
      - name: order_id
        description: 订单 ID
        type: string
        required: true
        position: path
    requestTemplate:
      url: /orders/{order_id}
      method: GET
      security:
        id: ""
    responseTemplate:
      prependBody: |
        # API Response Information
        Below is the response from an API call.
        ## Response Structure
        > Content-Type: application/json
        - **created_at**: 创建时间 (Type: string)
        - **customer_name**: 客户姓名 (Type: string)
        - **id**: 订单 ID（8 位 hex） (Type: string)
        - **items**: 订单明细 (Type: array)
        - **status**: 订单状态 (Type: string)
        - **total_amount**: 订单总金额 (Type: number)
        - **updated_at**: 更新时间 (Type: string)
        ## Original Response
    outputSchema:
      description: 查询成功
      type: object
      properties:
        created_at:
          description: 创建时间
          type: string
        customer_name:
          description: 客户姓名
          type: string
        id:
          description: 订单 ID（8 位 hex）
          type: string
        items:
          description: 订单明细
          type: array
          items:
            type: object
            properties:
              name:
                description: 商品名称
                type: string
              quantity:
                description: 数量
                type: integer
              unit_price:
                description: 单价
                type: number
        status:
          description: 订单状态
          type: string
        total_amount:
          description: 订单总金额（自动计算）
          type: number
        updated_at:
          description: 更新时间
          type: string
  - name: listOrders
    description: 列出订单 - 查询订单列表，支持按客户名和状态筛选
    args:
      - name: customer_name
        description: 按客户姓名筛选
        type: string
        position: query
      - name: status
        description: 按订单状态筛选
        type: string
        enum:
          - pending
          - paid
          - cancelled
        position: query
    requestTemplate:
      url: /orders
      method: GET
      security:
        id: ""
    responseTemplate:
      prependBody: |
        # API Response Information
        Below is the response from an API call.
        ## Response Structure
        > Content-Type: application/json
        - **items**: Array of items (Type: array)
          - **items[].created_at**: 创建时间 (Type: string)
          - **items[].customer_name**: 客户姓名 (Type: string)
          - **items[].id**: 订单 ID (Type: string)
          - **items[].items**: 订单明细 (Type: array)
          - **items[].status**: 订单状态 (Type: string)
          - **items[].total_amount**: 订单总金额 (Type: number)
          - **items[].updated_at**: 更新时间 (Type: string)
        ## Original Response
```

![编辑 MCP 工具 - 自定义 YAML](images/10-create-tool-yaml.png)

### 4.6 验证网关连通性

使用 curl 测试网关连通性：

```bash
curl -X POST "http://{网关入口地址}/mcp-servers/{服务路径}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
```

**预期结果**：
- 此时插件尚未安装，网关应直接返回 MCP 初始化响应（无需认证）
- 如果返回 401 或其他错误，请检查 MCP 服务配置和后端服务连通性

### 4.7 创建 OAuth 端点透传路由（§三回填的前置条件）

Agent Identity 数据面无法直连 ECS 公网 IP，因此订单服务的 OAuth discovery/授权/令牌端点需经网关透传（后端仍指向 §4.3 的 `order-service` 私网服务）：

1. 在网关上创建一个 HTTP API（如 `oauth-passthrough`），并添加两条路由，后端均指向 `order-service` 服务：
   - **路由 1**：路径前缀 `/.well-known`
   - **路由 2**：路径前缀 `/oauth`
2. 验证透传生效：

   ```bash
   curl http://{网关入口地址}/.well-known/oauth-authorization-server
   ```

   应返回 JSON（此时 issuer 可能仍是 ECS 地址，下一步重启后变更）。
3. **回填与重启**（对应 §三开头的顺序说明）：
   - 更新 §三创建的 OAuth2 provider：Issuer/DiscoveryURL/授权端点/令牌端点统一改为 `http://{网关入口地址}`
   - 修改 ECS 订单服务的 `OAUTH_BASE_URL` 为同一网关域名并重启（先 kill 旧进程，再按 §1.4 命令启动）
   - 再次 curl 验证：well-known 文档中的 `issuer` 应已变为 `http://{网关入口地址}`

---

## 五、Agent Identity 策略集

创建策略集并将其绑定到 AI 网关实例上。策略集是 Cedar 鉴权策略的容器，绑定后网关上的 AgentIdentity 插件将使用该策略集进行鉴权。

### 5.1 创建策略集

1. 登录 [Agent Identity 控制台](https://agentidentity.console.aliyun.com)
2. 左侧菜单选择 **策略管理** → **策略集**
3. 点击 **创建策略集**
4. 配置：
   - **名称**：`mcp-gateway-policies`
   - **Region**：`cn-beijing`

### 5.2 绑定策略集到 AI 网关实例

1. 进入策略集详情 → **资源绑定**（或 **关联资源**）
2. 点击 **绑定资源**
3. 选择资源类型：**AI 网关**（`AIGateway::Gateway`）
4. 选择步骤四中创建的网关实例：`gw-xxxxxxxxxxxxxxxxxxxx`
5. 确认绑定

> 绑定后，网关的 `resourceId`（GatewayArn）为：`acs:apig:cn-beijing:{accountId}:gateway/{网关ID}`，后续插件配置需要使用。
>
> **关于 TLS（`agentidentitydata` 数据面服务）——强烈建议走控制台路径**：
>
> - **控制台绑定**：会自动为网关创建带 TLS 的 `agentidentitydata` 数据面服务，无需额外操作。
> - **CLI/API 绑定**：不会自动创建该服务，需手动创建。两个阻断级坑位：
>   1. **服务名不能带 `.dns` 后缀**：创建 DNS 类型服务时，服务名必须为 **`agentidentitydata`**。APIG 会自动在服务名后追加 `.dns` 生成 serviceFQDN；若把服务名写成 `agentidentitydata.dns`，实际 cluster 会变成 `agentidentitydata.dns.dns`，插件按 FQDN `agentidentitydata.dns` 找不到 Envoy cluster，导致**所有请求返回泛化 401**（body 中 requestId 为空、无错误码）。
>   2. **上游 TLS 必须在控制台开启**：实测通过 CLI/API 的 `CreateService`/`UpdateService` 无法复刻控制台的 TLS 渲染（`ports=443/HTTPS`、`protocol=TLS` 各种写法，甚至重启网关，上游仍是明文连接），数据面要求 TLS 时会报 `InvalidProtocol.NeedSsl`。该步骤**目前只能在控制台为 `agentidentitydata` 服务开启 TLS**，开启后回读服务应为 `protocol=HTTPS`、`healthStatus=Healthy`。

![策略集绑定资源](images/11-policy-bind-resource.png)

---

## 六、AI 网关插件配置

网关上需要安装官方 **agent-identity-oauth** 插件（HigressOfficial 发布，最低版本 **1.0.1**）并配置规则。该插件在认证阶段完成 WAT 验证、Cedar 策略鉴权与下游凭据注入。

### 6.1 安装官方 agent-identity-oauth 插件

**方式一：控制台插件市场**

1. 进入网关实例 → **插件市场**，搜索 `agent-identity-oauth`（发布者为 **HigressOfficial**）
2. 点击 **安装**，选择目标网关实例，版本选择 **1.0.1 及以上**

**方式二：CLI**

```bash
# 1. 查询插件类 ID（插件类 ID 因地域/账号而异，需自行查询）
aliyun apig list-plugin-classes --gateway-type AI --name-like agent

# 2. 安装官方插件到网关
aliyun apig install-plugin --gateway-ids <网关ID> --plugin-class-id <插件类ID>
```

> **提示**：CLI 操作时请显式指定目标账号对应的 `--profile` 与 `--region`，否则默认 profile 可能落到其他账号，出现查不到插件/资源（假 404）的情况（见 §10.1-④）。

**关于默认插件**：若策略集是通过**控制台**绑定的，网关上可能已自动安装了一个 agent-identity 鉴权插件——请确认其版本 ≥ 1.0.1；若是旧版本，先卸载再按上述方式安装。若通过 **CLI/API** 绑定策略集，则网关无默认插件，直接安装即可。避免同一路由上同时启用两个鉴权插件：插件会**无条件剥离原始 `Authorization` 头**，双插件会互相干扰。

![插件配置页面](images/12-plugin-config-page.png)

### 6.2 配置 agent-identity-oauth 插件规则

插件安装后，需要配置规则使其在指定的 MCP 服务上生效。

1. 进入网关实例 → **插件** → 找到已安装的 agent-identity-oauth 插件 → 点击 **规则配置**
2. 在左侧 **生效范围** 中选择 **MCP/路由级插件规则**
3. 点击 **添加规则**，生效目标选择你创建的 MCP 服务
4. 输入以下完整配置：

```yaml
agentIdentityService:
  serviceName: agentidentitydata.dns
  serviceUrl: https://agentidentitydata-vpc.cn-beijing.aliyuncs.com
  resourceId: acs:apig:cn-beijing:{你的账号ID}:gateway/{网关ID}
credential:
  enabled: true
  type: oauth2
  arn: >-
    acs:agentidentity:cn-beijing:{accountId}:tokenvault/default/oauth2credentialprovider/{步骤三创建的providerName}
  oauthForceAuth: false
  oauthFlow: USER_FEDERATION
  # 推荐：Workload Identity 已关闭 session binding（SessionBindingEnabled=false）时，不配置 oauthReturnURL
  # 仅当 Workload Identity 开启 session binding 时才需要填写：
  # oauthReturnURL: "https://{你的应用域名}/callback"  # 须在 WI 回调白名单内
  injectHeaderName: Authorization
  injectHeaderPrefix: Bearer
  injectHeaderPrefixEnabled: true
```

5. 点击 **保存**
6. 保存后，点击规则右侧的 **启用** 按钮，使规则生效

> **CLI/API 路径的挂载类型说明（McpServer）**：若通过 CLI/API 创建插件规则（plugin attachment），`attach-resource-type` 枚举仅支持 `GatewayRoute`/`Gateway`/`GatewayDomain`/`HttpApi`/`Operation`，**不支持 `McpServer`**。控制台的"生效目标选择 MCP 服务"对应到 CLI 时，需查出该 MCP 服务的**底层路由 ID**（MCP 服务详情可查），以 **`GatewayRoute`** 类型挂载，效果与 MCP 级规则等价。

> **关于 `oauthReturnURL`（条件性要求）**：该字段**仅在 Workload Identity 开启 session binding（`SessionBindingEnabled=true`）时需要**——此时若无已存凭据，数据面会生成授权 URL 并回跳到该地址，缺少 `oauthReturnURL` 会返回网关 500（`GetResourceOAuth2Token failed with status 400`，对应 `MissingParameter.ResourceOAuth2ReturnURL`），且该 URL 必须预先加入 Workload Identity 的“允许的 OAuth2 回调地址”白名单（否则报 `Missmatch.ResourceOAuth2ReturnURL`）。
>
> **推荐做法**：创建 Workload Identity 时关闭 session binding（`SessionBindingEnabled=false`），此时插件**无需配置 `oauthReturnURL`**、Workload Identity 也**无需配置回调地址白名单（AllowedResourceOAuth2ReturnURLs）**，授权完成后即可直接获取 token。

> **官方插件 schema 兼容性（已验证）**：官方 `agent-identity-oauth` 1.0.1 的 schema 覆盖上述全部字段，配置可**原样复用**（其中 `resourceId` 使用完整 ARN 形态 `acs:apig:{region}:{accountId}:gateway/{网关ID}` 已验证生效）。官方插件另新增 `authorizationEnabled`、`oauthScopes`、`tokenVaultName`、`allowRequestOverride` 等选填字段，本 Demo 保持默认不配置。
>
> **官方插件行为要点（已验证）**：
>
> 1. **无条件剥离原始 `Authorization` 头**：WAT 校验后原始 `Authorization` 头被剥离，转发给后端的只有注入的下游 OAuth2 token（后端不会看到 WAT）；
> 2. **initialize 阶段即同步获取资源 OAuth2 token**：此时若后端服务不健康或 OAuth 端点不可达，会直接返回 500（`GetResourceOAuth2Token failed`）——遇到该错误请**优先排查后端服务健康度与 OAuth 端点可达性**（见 §10.2-⑨）；
> 3. **无 token 时返回结构化 errorCode**：WAT 缺失/无效时返回带 requestId 的结构化错误（如 HTTP 401 + `MissingParameter.WorkloadAccessToken`），而非泛化 401。

![MCP/路由级插件规则配置](images/13-plugin-rule-config.png)

#### 配置字段说明

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `agentIdentityService.serviceName` | — | Agent Identity 数据面服务的 **serviceFQDN**，固定为 `agentidentitydata.dns`。注意：这是网关内 DNS 服务的 FQDN，对应的服务**名称必须是 `agentidentitydata`**（不带 `.dns` 后缀，见 §5.2） |
| `agentIdentityService.serviceUrl` | — | Agent Identity 数据面 API 的 HTTPS 地址（VPC 内网地址，`-vpc` 后缀） |
| `agentIdentityService.resourceId` | — | 网关资源标识（GatewayArn） |
| `credential.enabled` | `false` | 是否启用凭据注入。**必须设为 `true`** |
| `credential.type` | `""` | 凭据类型，填 `oauth2` |
| `credential.arn` | `""` | OAuth2 凭据提供商 ARN（步骤三中创建后获取） |
| `credential.oauthForceAuth` | `false` | 是否强制每次请求都走 OAuth 授权 |
| `credential.oauthFlow` | `USER_FEDERATION` | OAuth 授权流程类型 |
| `credential.oauthReturnURL` | `""` | OAuth 授权完成后的回跳地址。**仅当 Workload Identity 开启 session binding 时需要填写**（且须在 WI 回调地址白名单内）；推荐关闭 session binding 后不填 |
| `credential.injectHeaderName` | `Authorization` | 凭据注入到请求的 Header 名称 |
| `credential.injectHeaderPrefix` | `Bearer` | 注入 Header 的值前缀 |
| `credential.injectHeaderPrefixEnabled` | `true` | 是否在注入的 Header 值中添加前缀 |

> 插件会将获取到的 OAuth2 Token 以 `{injectHeaderPrefix} {token}` 格式注入到 `{injectHeaderName}` 请求头中，转发给下游 MCP 服务。

---

## 七、Agent Identity 策略集编辑

在步骤五创建的策略集上编辑 Cedar 鉴权策略，控制用户对 MCP 工具的访问权限。

### 7.1 进入策略编辑器

1. 进入 Agent Identity 控制台 → **策略管理** → 选择策略集 `mcp-gateway-policies`
2. 点击 **编辑策略**

### 7.2 编写 Cedar 策略

> **重要**：如果绑定了策略集到网关实例，但未编写任何策略，则相当于所有人都没有权限访问，`listTools` 也无法列出任何工具。建议先添加一个基础的全放开策略确认连通性，再逐步收紧权限。

Cedar 策略的基本格式：

- **Principal**：`AgentIdentity::OAuthUser::"{联邦用户实体ID}"`（指定用户）或 `principal`（所有已认证用户）。经 OIDC 联邦的用户实体类型为 `AgentIdentity::OAuthUser`；**实体 ID 形态存在环境差异**，可能出现两种形态：短 `user_id`（形如 `user_xxxx`）或完整用户 ARN（`acs:agentidentity:{region}:{accountId}:userpool/{用户池ID}/user/{user_id}`）；可用属性为 `Issuer`（颁发者）与 `actor`（工作负载身份 ARN），如何判定见下方说明
- **Action**：`AIGateway::Action::"mcp-servers.{服务名}.{工具名}"`（指定工具）
- **Resource**：`AIGateway::Gateway::"{网关GatewayArn}"`（指定网关实例）

**示例 0：基础全放开策略（建议先用此策略验证连通性）**

```cedar
permit (
  principal,
  action,
  resource == AIGateway::Gateway::"acs:apig:cn-beijing:{accountId}:gateway/{网关ID}"
);
```

**示例 1：仅允许特定联邦用户查询订单（注意实体 ID 的两种形态）**

**形态 A（完整用户 ARN）**：

```cedar
permit (
  principal == AgentIdentity::OAuthUser::"acs:agentidentity:{region}:{accountId}:userpool/{用户池ID}/user/{user_id}",
  action in
    [AIGateway::Action::"mcp-servers.test-order-agent-identity.deleteOrder",
     AIGateway::Action::"mcp-servers.test-order-agent-identity.getOrder",
     AIGateway::Action::"mcp-servers.test-order-agent-identity.listOrders"],
  resource == AIGateway::Gateway::"acs:apig:cn-beijing:{accountId}:gateway/{网关ID}"
)
when { principal has actor };
```

**形态 B（短 user_id）**：

```cedar
permit (
  principal == AgentIdentity::OAuthUser::"user_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  action in
    [AIGateway::Action::"mcp-servers.test-order-agent-identity.deleteOrder",
     AIGateway::Action::"mcp-servers.test-order-agent-identity.getOrder",
     AIGateway::Action::"mcp-servers.test-order-agent-identity.listOrders"],
  resource == AIGateway::Gateway::"acs:apig:cn-beijing:{accountId}:gateway/{网关ID}"
)
when { principal has actor };
```

> **注意（实体 ID 形态的环境差异，已确认）**：实测确认联邦 OAuthUser 实体的 ID 形态**可能随产品版本/环境不同而不同**，短 `user_id` 与完整用户 ARN 均可能出现：2026-08-12 从零重建环境的最终验证中，实体 ID 实际为**短 `user_id`**（形如 `user_xxxx`），按完整用户 ARN 书写会**静默 403（reasons 为空）且 `tools/list` 被过滤为空**；而更早一轮环境中完整用户 ARN 形态曾生效。客户无法凭空判断自己环境是哪种形态，需按下方判定方法探测。
>
> 其余已验证结论：属性键为大写的 `Issuer` 与 `actor`（**无** `iss`/`sub` 属性），其中 `actor` 为工作负载身份的**完整目录形式 ARN**（`acs:agentidentity:{region}:{accountId}:workloadidentitydirectory/default/workloadidentity/{名称}`）；按 `principal.iss` 或短形式 actor 值匹配会让 `when` 条款恒假。
>
> **实体 ID 形态判定方法**：
>
> 1. **先通链路**：部署示例 0 的最宽探针策略 `permit (principal, action, resource)`，确认 `tools/list`、`tools/call` 均能走通；
> 2. **再定形态**：用属性探针读取实体实际属性（如 LOG_ONLY 模式下观察策略评估日志中的 principal 实体 ID），或直接**两种形态各试一次**（示例 1 形态 A 与形态 B 轮换部署）；
> 3. **写错的症状很典型**：`tools/call` 返回 403 且 reasons 为空，同时 `tools/list` 被过滤为空——遇到这组症状优先怀疑实体 ID 形态不匹配（见 §10.4-⑬）。

**示例 2：允许所有用户创建订单，但限制输入参数**

```cedar
permit (
  principal,
  action == AIGateway::Action::"mcp-servers.test-order-agent-identity.createOrder",
  resource == AIGateway::Gateway::"acs:apig:cn-beijing:{accountId}:gateway/{网关ID}"
)
when { context.input.customer_name == "张三" };
```

> **说明**：`when` 子句可用于更细粒度的控制，如基于 `principal has actor`/`principal.Issuer`（工作负载身份与颁发者）或 `context.input`（请求参数）进行条件判断。

### 7.3 设置执行模式

- **LOG_ONLY**（观察模式）：鉴权结果仅记录日志，不拦截请求
- **ENFORCE**（强制模式）：鉴权拒绝时返回 403

> **建议**：先用 LOG_ONLY 模式验证策略正确性，确认无误后切换到 ENFORCE。

![Cedar 策略编辑器](images/14-cedar-policy-editor.png)

---

## 八、Chatbot 部署

### 8.1 环境准备

```bash
# 进入本 sample 目录（agent_identity_python_samples/ai-gateway-mcp-auth-credential-injection_sample）
cd agent_identity_python_samples/ai-gateway-mcp-auth-credential-injection_sample

# 安装依赖（与 requirements.txt 对齐：mcp、langchain-core、langgraph、httpx、pydantic、agent-identity-python-sdk、certifi）
pip install -r requirements.txt
```

### 8.2 配置文件

复制模板并填入你的实际配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# OIDC 配置（从 Agent Identity 控制台获取）
OIDC_DISCOVERY_URL=https://signin-{region}.aliyunagentid.com/{用户池ID}/.well-known/openid-configuration
OIDC_CLIENT_ID={Client ID}
OIDC_CLIENT_SECRET={Client Secret}

# Agent Identity Workload Identity（从 Agent Identity 控制台获取）
AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME={Workload Identity 名称}

# LLM 配置（阿里云百炼 DashScope）
LLM_API_KEY={你的 API Key}
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# MCP 配置（AI 网关的 MCP 路由地址）
MCP_SERVER_URL=http://{网关入口地址}/mcp-servers/test-order-agent-identity

# 可选配置
AGENT_IDENTITY_REGION_ID=cn-beijing
LLM_MODEL=qwen-max
```

| 变量 | 来源 | 说明 |
|------|------|------|
| `OIDC_DISCOVERY_URL` | Agent Identity 控制台 → 用户池 | OIDC 发现文档地址 |
| `OIDC_CLIENT_ID` | Agent Identity 控制台 → 客户端管理 | 客户端 Client ID |
| `OIDC_CLIENT_SECRET` | Agent Identity 控制台 → 客户端密钥 | 客户端 Client Secret |
| `LLM_API_KEY` | [百炼控制台](https://bailian.console.aliyun.com) | DashScope API Key |
| `LLM_BASE_URL` | 百炼控制台 | API 兼容端点地址 |
| `MCP_SERVER_URL` | AI 网关控制台 → MCP 管理 | MCP 服务接入地址（§4.4 创建并部署后生成） |

### 8.3 启动

```bash
chmod +x run_chatbot.sh   # 首次执行时
./run_chatbot.sh
```

`run_chatbot.sh` 是一体化串联脚本，实际分两步执行（与手动分步执行完全等价）：

1. **Step 1 — OIDC 登录获取 ID Token**：调用 `oidc_login.py`（传入 `.env` 中的 discovery URL / Client ID / Client Secret），自动打开浏览器进入用户池登录页（使用 §2.5 的测试用户账号密码），通过本地回调服务（`http://localhost:18080/callback`）捕获 ID Token
2. **Step 2 — 启动 Chatbot**：以 `--bearer-token <ID Token>` 启动 `mcp_chatbot.py`，自动用 ID Token 换取 Workload Access Token（WAT），连接网关托管的 MCP Server，仅加载已授权的工具，进入交互式对话

启动前脚本会自动加载同目录 `.env` 并校验必需变量（缺失会逐项提示）。

> **手动分步执行（可选）**：若需调试单步，可直接运行：
>
> ```bash
> # Step 1：登录并把 ID Token 保存到文件
> python3 oidc_login.py --discovery-url "$OIDC_DISCOVERY_URL" --client-id "$OIDC_CLIENT_ID" --client-secret "$OIDC_CLIENT_SECRET" > /tmp/id_token.txt
> # Step 2：用 ID Token 启动 chatbot
> python3 mcp_chatbot.py --bearer-token "$(cat /tmp/id_token.txt)" --mcp-url "$MCP_SERVER_URL" --api-key "$LLM_API_KEY" --base-url "$LLM_BASE_URL"
> ```
>
> 也可用 `python3 test_mcp.py` 做分步诊断（OIDC 登录 → ID Token → WAT → MCP 连接 → 列工具，逐步打印状态）。

---

## 九、端到端验证

启动后依次测试以下场景：

### 场景 1：基础对话（不涉及工具）

```
你: 你好
```
预期：LLM 正常回复，无 MCP 调用。

### 场景 2：查询订单（已授权工具）

```
你: 帮我列出所有订单
```
预期：
- Chatbot 调用 `listOrders` 工具
- 网关鉴权通过（假设 listOrders 在策略中允许）
- 返回订单列表

### 场景 3：鉴权拒绝（ENFORCE 模式）

```
你: 帮我删除订单 order-001
```
预期（如果 deleteOrder 未在策略中授权）：
- Chatbot 调用 `deleteOrder` 工具
- 网关返回 403 Forbidden
- Chatbot 显示"操作被拒绝"

### 场景 4：工具列表过滤

观察启动时的工具加载列表。如果策略中某些工具未授权，AgentIdentity 插件会自动从 `tools/list` 响应中过滤掉，Chatbot 只会加载已授权的工具。

---

## 十、Troubleshooting（常见问题排查）

本节汇总全链路部署中已验证的坑位，按阶段组织，每条按 **症状 → 根因 → 解决方案** 描述。建议部署前先通读本节。

### 10.1 登录与换取凭据阶段

**① OIDC 登录页报 `NO_LOGIN_METHOD_ENABLED`**

- **根因**：新建用户池默认 `EnablePasswordLogin=false`，未启用任何登录方式。
- **解决**：通过 SDK 调用 `UpdateLoginPreference`（`enable_password_login=True`）启用密码登录，或在控制台开启。**不要用 aliyun CLI force 模式**——嵌套的 `LoginPreference` 参数会被静默忽略（命令返回成功但未生效）。启用后回读确认。详见 §2.3。

**② 换取下游凭据/工具调用报 `MissingRoleArn`**

- **根因**：Workload Identity 未绑定 RAM 角色（RoleArn 为空）。
- **解决**：按 §2.7 创建 RAM 角色（信任 `workload.agentidentity.aliyuncs.com` + WI ARN 条件），再通过 `UpdateWorkloadIdentity` 或控制台把 RoleArn 绑到 Workload Identity。

**③ 网关 500：`GetResourceOAuth2Token failed with status 400`（`MissingParameter.ResourceOAuth2ReturnURL`）**

- **根因**：Workload Identity 开启了 session binding，但插件未配置 `oauthReturnURL`。
- **解决（推荐配置）**：创建/更新 Workload Identity 时**关闭 `SessionBindingEnabled`、清空 AllowedResourceOAuth2ReturnURLs 白名单，同时插件不配置 `oauthReturnURL`**——此形态下无需传 return URL 即可成功获取 token，配置最简。仅当确需开启 session binding 时，才需同时配置插件 `oauthReturnURL` 并将该地址（含 http/https 两种形式）加入 WI 回调白名单（否则报 `Missmatch.ResourceOAuth2ReturnURL`）。详见 §2.8、§6.2。

**④ 换取 WAT 报 `EntityNotExists.WorkloadIdentity`（404），但 Workload Identity 在控制台确实存在**

- **根因**：SDK 默认凭据链（或 aliyun CLI 默认 profile）解析到了**另一个阿里云账号**——凭据属于账号 A，而 Workload Identity 在账号 B 下，数据面自然查不到。该报错极具误导性，容易误判为“WI 被误删”。
- **解决**：显式设置 `ALIBABA_CLOUD_ACCESS_KEY_ID` / `ALIBABA_CLOUD_ACCESS_KEY_SECRET` 环境变量（或确认凭据 profile 所用账号与资源一致）；CLI 同理需显式指定目标账号的 `--profile` 与 `--region`。修正后重试即可；也可先通过控制面 `GetWorkloadIdentity` 确认 WI 确实存在。见前置检查清单。

### 10.2 网关与插件阶段

**⑤ 所有请求返回泛化 401（body 仅 `{"code":"Unauthorized","message":"Authentication failed"}`，requestId 为空、无错误码）**

- **根因**：网关 DNS 服务命名陷阱。CLI/API 创建 DNS 类型服务时，服务名会被自动追加 `.dns` 生成 serviceFQDN；若把数据面服务命名为 `agentidentitydata.dns`，实际 cluster 变成 `agentidentitydata.dns.dns`，插件按 `agentIdentityService.serviceName=agentidentitydata.dns` 找不到 Envoy cluster，在极早期失败并返回泛化 401。
- **解决**：删除错误服务，重新创建 DNS 服务，**服务名必须为 `agentidentitydata`（不带 `.dns` 后缀）**，回读确认 `serviceFQDN=agentidentitydata.dns`。详见 §5.2。
- **区分**：若 401 带明确 errorCode（如 `MissingParameter.WorkloadAccessToken`、`InvalidParameter.WorkloadAccessToken`）且 requestId 非空，说明插件已正常触达数据面，按对应错误处理（如重新登录换新 WAT）。

**⑥ 插件报 `InvalidProtocol.NeedSsl`**

- **根因**：`agentidentitydata` 数据面服务的上游 TLS 未生效，Envoy 以明文连接 443 端口。
- **解决**：**该步骤必须走控制台**。实测 CLI/API 的 `UpdateService` 无法复刻控制台的 TLS 渲染（`ports=443/HTTPS`、`protocol=TLS` 各种写法，乃至重启网关，均无效）；在控制台为 `agentidentitydata` 服务开启 TLS 后才生效，回读应为 `protocol=HTTPS`、`healthStatus=Healthy`。或改由控制台绑定策略集（自动创建带 TLS 的服务）。详见 §5.2。

**⑦ 网关转发后端报 503 connection timeout**

- **根因**：后端服务地址使用了 ECS 公网 IP（网关经 ENI/VPC 转发，无法连通公网 VIP）。
- **解决**：后端服务必须使用与网关同 VPC 的 **ECS 私网 IP**（§4.3）。

**⑧ 此前可用的 WAT 突然全部 401 Unauthorized（插件切换/卸载/配置重载后）**

- **根因**：插件卸载/切换或配置重载会使旧会话失效，此前签发的 WAT 无法继续使用（属预期行为）。
- **解决**：重新登录获取 ID Token 并换取新的 WAT。

**⑨ initialize 阶段网关报 500：`GetResourceOAuth2Token failed`**

- **根因**：官方插件在 MCP initialize 阶段即同步获取资源 OAuth2 token；此时若后端订单服务不健康（如 ECS 被释放、重建后私网 IP 变化未同步到网关服务），或 OAuth discovery/端点不可达，会直接返回 500（数据面可查到 `InvalidOAuthDiscoveryURL: Unreachable`）。
- **解决**：**优先检查后端服务健康度**（网关服务管理 → healthStatus 应为 Healthy；确认 ECS 进程存活、私网 IP 未变化，见 §10.5-⑱），再确认网关 `/.well-known/oauth-authorization-server` 透传路由可达（见 §4.7、§10.3-⑩）。

### 10.3 OAuth 授权阶段

**⑩ 授权环节报 `InvalidOAuthDiscoveryURL: Unreachable`**

- **根因**：OAuth provider 的 discovery/授权/令牌端点指向了 ECS 公网 IP，而 Agent Identity 数据面无法直连 ECS 公网 IP。
- **解决**：OAuth 端点必须**经网关透传**：网关后端指向 ECS 私网 IP，创建 `/.well-known`、`/oauth` 前缀的透传路由（§4.7），然后把 provider 的 Issuer/DiscoveryURL/各端点**回填为网关入口域名**，并同步把 ECS 订单服务的 `OAUTH_BASE_URL` 改为同一网关域名后重启（issuer 必须一致）。

**⑪ 回填网关域名后授权仍失败（issuer 不匹配）**

- **根因**：provider 已回填网关域名，但 ECS 订单服务的 `OAUTH_BASE_URL` 未同步修改/重启，well-known 文档中的 issuer 与 provider 配置不一致。
- **解决**：按 §4.7 步骤 3 同步重启订单服务，curl 验证 well-known 的 issuer 已变为网关域名。

### 10.4 鉴权与工具调用阶段

**⑬ `tools/call` 返回 403 且 reasons 为空（可能伴随 `tools/list` 被过滤为空）**

- **根因①**：WI 绑定的 RAM 角色缺 `agentidentitydata:EvaluatePolicy` 权限（策略评估被 RAM 隐式拒绝后 fail-closed）。
  - **解决**：为角色附加 `AliyunAgentIdentityDataFullAccess`，或至少同时包含 `agentidentitydata:GetCredential` 与 `agentidentitydata:EvaluatePolicy`（§2.7）。
- **根因②**：Cedar 策略的 principal 形态与当前环境的实体 ID 形态不匹配。已确认实体 ID 形态**存在环境差异**：可能是短 `user_id`（形如 `user_xxxx`，2026-08-12 重建环境实测为此形态），也可能是完整用户 ARN（更早环境实测生效）——按错误形态书写会静默 403（reasons 为空）且 `tools/list` 被过滤为空。
  - **判定方法**：先部署最宽探针策略 `permit (principal, action, resource)` 确认链路通；再用属性探针（如 LOG_ONLY 模式下观察评估日志中的实体 ID）读取实体实际形态，或直接把完整 ARN / 短 user_id 两种写法各试一次（§7.2 示例 1 形态 A/B）。
- **根因③**：principal 属性写法错误。属性键为大写的 `Issuer` / `actor`（**无** `iss`/`sub` 属性）；`actor` 必须为**完整目录形式** WI ARN：`acs:agentidentity:{region}:{accountId}:workloadidentitydirectory/default/workloadidentity/{名称}`——用短形式会让 `when { ... }` 条款恒假。
  - **解决**：按 §7.2 示例修正策略。

**⑭ 工具列表为空 / listTools 无任何工具**

- **根因**：绑定了策略集但未写任何策略（等价于所有人无权限）、策略全部 deny，或 Cedar 策略的实体 ID 形态与当前环境不匹配（见 §10.4-⑬根因②）。
- **解决**：先加示例 0 的全放开策略验证连通性，再按 §7.2 的判定方法确认实体 ID 形态，逐步收紧。

### 10.5 部署与运维杂项

**⑮ SSH 会话中后台启动订单服务后会话挂起**

- **根因**：nohup 命令未重定向 stdin。
- **解决**：启动命令末尾加 `</dev/null`（§1.4 命令已包含）；若已卡住，服务本身正常，另开一个 SSH 会话验证即可。

**⑯ 创建 ECS 报 `InvalidSystemDiskCategory.ValueNotSupported`**

- **根因**：所选实例规格不支持高效云盘（`cloud_efficiency`）。
- **解决**：系统盘改用 ESSD 云盘（`cloud_essd`），见 §1.1。

**⑰ MCP 服务创建后无入口地址 / 不生效**

- **根因**：MCP 服务未执行部署（Deploy）；或接入点域名在账号内已被占用。
- **解决**：对 MCP 服务执行部署（携带接入点域名）；域名冲突时换一个未被占用的域名（§4.4）。

**⑱ ECS 重建后旧私网 IP 无法沿用 / 网关后端 Unhealthy**

- **根因**：ECS 释放重建后，旧私网 IP 可能已被网关的 Member ENI 占用而无法沿用，新实例会获得新的私网 IP；网关后端服务仍指向旧地址，healthStatus 变为 Unhealthy，链路报 503/500（见 §10.2-⑨）。
- **解决**：同步更新网关后端服务的 addresses 为新私网 IP:端口（控制台服务管理或 CLI `UpdateService`），完成后确认 `healthStatus=Healthy`。

**⑲ 订单服务重建/重启后 `tools/call` 报 -32042 要求重新授权**

- **根因**：Demo 订单服务将 OAuth access_token/授权码存于**内存**，ECS 重建或服务重启后旧凭据全部丢失，Agent Identity 数据面缓存的资源 token 也随之失效。
- **解决**：属 Demo 设计行为（生产环境的下游服务通常会持久化 token）。客户端需按 -32042（elicitation）提示重新走一次出站 OAuth 授权流程（打开授权 URL → 同意授权 → 回调），之后工具调用即恢复。

**⑳ `createOrder` 工具调用报 422 校验错误**

- **根因**：参数名错误——`createOrder` 必填 **`customer_name`**，价格字段名为 **`unit_price`**（不是 `price`），且 `items` 中每项的 `name`/`quantity`/`unit_price` 均必填。
- **解决**：按 §4.5 的工具定义填写。LLM 自动传参时可能先因 422 被拒再自行纠正重试，属正常现象。

---

## 附录：配置参考

### WASM 插件完整配置

```yaml
agentIdentityService:
  serviceName: agentidentitydata.dns
  serviceUrl: https://agentidentitydata-vpc.cn-beijing.aliyuncs.com
  resourceId: acs:apig:cn-beijing:{accountId}:gateway/{网关ID}
credential:
  enabled: true
  type: oauth2
  arn: >-
    acs:agentidentity:cn-beijing:{accountId}:tokenvault/default/oauth2credentialprovider/mcp-order-oauth2
  oauthForceAuth: false
  oauthFlow: USER_FEDERATION
  # 推荐：Workload Identity 已关闭 session binding 时，不配置 oauthReturnURL；开启 session binding 时填写并加入 WI 白名单
  # oauthReturnURL: "https://{你的应用域名}/callback"
  injectHeaderName: Authorization
  injectHeaderPrefix: Bearer
  injectHeaderPrefixEnabled: true
```

### 插件固定参数

| 参数 | 值 | 说明 |
|------|------|------|
| 执行阶段 | `authn` | 认证阶段 |
| 优先级 | `100` | 在认证阶段最先执行 |
| 检测 Header | `authorization` | 固定检测请求头 |
| ResourceType | `AIGateway::Gateway` | 资源类型 |
| 服务端口 | `443` | HTTPS |
| 请求超时 | `3000ms` | 调 Agent Identity 超时 |

### 常见问题

完整的问题排查指南见 [§十 Troubleshooting](#十troubleshooting常见问题排查)，下表为速查版：

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| OIDC 登录报 `NO_LOGIN_METHOD_ENABLED` | 新用户池默认未启用密码登录 | SDK `UpdateLoginPreference` 启用（CLI force 模式会静默忽略嵌套参数），见 §10.1-① |
| 换取 WAT 报 `EntityNotExists.WorkloadIdentity`（404） | SDK/CLI 凭据解析到了错误账号 | 显式设置 `ALIBABA_CLOUD_ACCESS_KEY_ID`/`SECRET`，或确认 profile 与资源同账号；CLI 显式 `--profile`/`--region`，见 §10.1-④ |
| 所有请求返回泛化 401（requestId 为空） | 数据面 DNS 服务名带了 `.dns` 后缀（FQDN 变成 `.dns.dns`） | 服务名改为 `agentidentitydata`（不带后缀），见 §10.2-⑤ |
| 请求返回 401 且带明确 errorCode | WAT 无效或已过期 | 重新登录获取 ID Token 换新 WAT，检查 region 配置 |
| 插件切换/卸载后原可用 WAT 全部 401 | 配置重载使旧会话失效（预期行为） | 重新登录换取新 WAT，见 §10.2-⑧ |
| initialize 阶段 500：`GetResourceOAuth2Token failed` | 官方插件 initialize 阶段即同步取资源 token，后端不健康或 OAuth 端点不可达 | 优先检查网关后端服务健康度与 OAuth 透传路由，见 §10.2-⑨ |
| 工具调用返回 403 | Cedar 策略拒绝 | 在 Agent Identity 控制台检查策略，确认 EnforcementMode |
| 工具调用 403 且 reasons 为空（可能伴随 `tools/list` 为空） | ① RAM 角色缺 `agentidentitydata:EvaluatePolicy`；② Cedar principal 实体 ID 形态与环境不匹配（短 user_id 与完整 ARN 均可能出现）；③ 大写 Issuer/actor + 完整目录形式 actor 写法错误 | 见 §10.4-⑬（含实体 ID 形态判定方法） |
| 网关 500：`GetResourceOAuth2Token failed with status 400`（`MissingParameter.ResourceOAuth2ReturnURL`） | Workload Identity 开启了 session binding，但插件未配置 `oauthReturnURL` | 推荐：关闭 `SessionBindingEnabled` + 清空白名单 + 插件不配 `oauthReturnURL`；仅开启 session binding 时才需配置两者，见 §10.1-③ |
| 凭据获取报 `Missmatch.ResourceOAuth2ReturnURL` | Workload Identity 开启 session binding 时，`oauthReturnURL` 不在回调地址白名单内 | 将该 URL（含 http/https 两种形式）加入 WI 的 AllowedResourceOAuth2ReturnURLs，或关闭 session binding |
| 插件报 `InvalidProtocol.NeedSsl` | `agentidentitydata` 服务上游 TLS 未生效（CLI/API 无法复刻） | **必须走控制台**为该服务开启 TLS，或改用控制台绑定策略集，见 §10.2-⑥ |
| 授权环节报 `InvalidOAuthDiscoveryURL: Unreachable` | OAuth 端点对 Agent Identity 数据面不可达（如直连 ECS 公网 IP） | 将 OAuth 端点经 AI 网关透传，provider 各端点回填网关域名，见 §10.3-⑩ |
| 网关转发后端 503 connection timeout | 后端服务地址使用了 ECS 公网 IP | 改用与网关同 VPC 的 ECS 私网 IP，见 §10.2-⑦ |
| 工具列表为空 | 策略集无策略或全部 deny | 先加全放开策略验证连通性，见 §10.4-⑭ |
| ECS 重建后网关后端 Unhealthy | 重建后私网 IP 变化（旧 IP 可能被网关 ENI 占用） | 更新网关后端服务 addresses 为新私网 IP，见 §10.5-⑱ |
| 订单服务重启后 `tools/call` 报 -32042 | Demo 订单服务 token 存内存，重启后凭据失效 | 重新走出站 OAuth 授权流程，见 §10.5-⑲ |
| `createOrder` 报 422 | 缺 `customer_name`，或价格字段误用 `price`（应为 `unit_price`） | 按工具定义填写，见 §10.5-⑳ |
| SSL 证书错误 | macOS Python 未安装证书 | 运行 `open /Applications/Python\ 3.x/Install\ Certificates.command` |
| LLM 返回 `choices is null` | API 端点返回非标准格式 | `mcp_chatbot.py` 已内置 `CompatibleChatOpenAI` 自动适配 |
| WASM 插件报 `bad argument` | `serviceName` 在网关中无对应 cluster | 检查服务名/FQDN（同泛化 401 条），确认 Agent Identity 服务已创建且已开 TLS |
