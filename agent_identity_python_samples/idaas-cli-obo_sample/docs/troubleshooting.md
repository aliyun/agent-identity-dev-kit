# Troubleshooting / 常见问题排查

Error codes in English, root causes and remedies in Chinese. Every entry below
comes from real integration testing (design reviews + pre-release
verification). When the CLI fails, it prints the error together with a
next-step hint — this table gives the full background.

错误码保持英文原样，根因与处置用中文说明。以下条目全部来自真实联调沉淀
（设计评审 + 预发实测）。CLI 出错时会附带下一步指引，本表提供完整背景。
通用排查第一步永远是：`python3 sample.py --check`。

---

## 1. Login / 登录链路（数据面第 1 步）

| 错误码 / 现象 | 根因 | 处置 |
|---|---|---|
| `invalid_request`（token 兑换被拒） | EIAM token 端点对 `private_key_jwt` 分支也**强制要求 `client_id`**，缺了即拒 | 兑换请求表单里必须带 `client_id`（机密客户端同时带 `client_secret`）；sample 已内置，手工复现时注意 |
| `nonce` 回显校验失败（login 打印「未回显 nonce」） | authorize 带了 `nonce` 而 id_token 未回显，严格校验会拒绝（可能是响应被替换或端点行为不符） | 重跑 `python3 sample.py login`；若持续失败，确认走的是池 OAuth 正常链路而非缓存页 |
| `state_mismatch`（回调页显示「state 校验未通过」） | 回调的 `state` 与发起时不一致：常见为浏览器里残留的**陈旧回调页**被再次触发，或回调被篡改 | 关闭旧的回调标签页，重跑 `login` |
| `invalid_grant`（兑换授权码失败） | 授权码**一次性**且有效期短；或兑换时 `redirect_uri` 与 authorize 时**不是逐字符一致** | 重跑 `login` 重新取码；sample 会按实际绑定端口动态构造两侧 URI，手工复现时保持完全一致 |
| 登录页出现**邮箱 OTP / MFA 二次验证**（预发实测新发现） | EIAM 侧策略变更：kit 早前验证成功后，EIAM 对测试账号新增了 step2 邮箱 OTP 要求（`ia_otp_email` enable=true） | 属预期交互，不是故障：在**浏览器内**按页面引导输入邮箱验证码完成登录；纯 REST/无头自动化会被此步骤阻塞 |
| 无法监听 `127.0.0.1:8765`（端口占用） | 本机常驻进程（如 IDE collector）占用 8765 | `python3 sample.py login --port 8766` 换端口即可：用户池客户端 redirect_uri 白名单含任意一条 loopback 条目即放行且**忽略端口**，无需回控制台改白名单 |

## 2. WAT / OBO（数据面第 2、3 步）

| 错误码 / 现象 | 根因 | 处置 |
|---|---|---|
| `Forbidden.InboundCredentialMissing` | **`session_id` 是 OBO 的定位键**：region 按 `(pool, user, session_id)` 三元组查入站托管凭证，查不到即报此错。常见原因：① 浏览器复用了旧的池登录会话（session_id 不匹配）；② 登录未走联邦入口；③ WorkloadIdentity 未开启会话绑定 | 用**无痕窗口**（或先清理浏览器会话）重跑 `login` 走联邦入口；确认 WI 的 `SessionBindingEnabled=true`（步骤 6） |
| `InvalidParameter.JsonWebToken` | 传给 `GetWorkloadAccessTokenForJWT` 的 ID Token 过期或 issuer 不匹配 | 重跑 `login`，成功后**立即**执行后续步骤 |
| `InvalidParameter.WorkloadAccessToken` / 报错含 "Workload access token is expired" | **WAT 有效期极短（实测约 5 分钟）**，超窗使用 | 重跑 `exchange-wat` 后立即 `obo`；分步调试建议直接用 `demo`（第 2→3 步自动衔接，不等待输入） |
| WAT 无法本地解码（5 段 JWE 结构，`decode_jwt_payload` 抛段数≠3） | **设计行为**：WAT 是 JWE 加密令牌，本地只应看长度与 RequestId | 无需处置；sample 只打印 `eyJ…(len=N)` 脱敏形态 |
| `MissingParameter.Scopes` | `Scopes` 传参格式不合法：**逐个传参（`--Scopes.N` 形态）不被接受**，必须是 **JSON 数组字符串** | 传 `["read","write.all"]` 单参数；sample 的 `serialize_scopes` 已按此契约处理 |
| `MissingParameter.*` 偶发出现且 sample 自动重试（30 次 × 5s） | 预发**滚动发布窗口**抖动：新旧实例对参数绑定短暂不一致 | 等待自动重试完成；重试仍失败说明不是窗口抖动，按具体缺失参数排查（如 Scopes 格式） |
| `ServiceUnavailable.UpstreamTokenEndpoint` | region 调上游 IDaaS token 端点失败：通常是**出站 provider 侧（IDaaS 订单服务应用）密钥缺失/失效**或授权边不齐 | 检查 `OBO_PROVIDER_NAME` 对应 provider 的配置：IDaaS 侧订单服务应用的密钥、认证方式与应用授权 |
| 订单服务 401（`aud` 不符）或 OBO 报 audience 相关错误 | `Audience` 没有指向订单服务应用：audience 必须是 `agent-<出站应用clientId>` 形态 | 修正 `.env` 的 `ORDER_SERVICE_AUDIENCE`（IDaaS 控制台订单服务应用详情页取值） |
| `EntityNotExists.OAuth2CredentialProvider` 等 | 资源不存在：名称与控制台不一致，或**资产被清理**（预发实测：provider 曾被环境清理；且**配额=1** 被占用） | 核对 `.env` 的 `WI_NAME` / `OBO_PROVIDER_NAME`；重建 provider 前需先删除旧 provider（注意会影响引用它的既有链路） |
| `EntityAlreadyExists.*` | setup 重跑时资源已存在 | sample 按名复用即可，无需处置；provider 场景如需重建先删旧再建 |

## 3. Setup / Cleanup（管控面）

| 错误码 / 现象 | 根因 | 处置 |
|---|---|---|
| `SetSpecificIdentityProvider` 报 `InvalidParameter`（绑定 IDaaS 失败） | aliyun CLI 帮助标注该接口**当前仅支持 DingTalk** 类型（预发实测确认） | 改用**控制台**完成「绑定 IDaaS」（模式 A 第 2 步），完成后重跑 `setup --mode=script`（幂等，会跳过已完成步骤） |
| `ServiceUnavailable`（调 ListOAuth2CredentialProviders 时） | 该接口**带 PageNumber/PageSize 分页参数即报错**（预发实测 5 次重试一致） | List 调用**不带分页参数**；sample 已按此实现 |
| 白名单丢条目（redirect_uri 越改越少） | 两个叠加因素：① aliyun CLI 多值参数须传 **JSON 数组单参数**（`'["a","b"]'`），空格分隔只取第一个值（**静默截断**）；② `UpdateUserPoolClient` 是**整体替换**语义 | 任何白名单写操作前先留档原值，写后**必读校验**；sample 已实现「保留原有条目合并 + 写后必读」 |
| `SignatureDoesNotMatch` / `IncompleteSignature` | RPC V1 签名细节错误：percentEncode 的 `safe="~"` 用错、formData 展开规则不符（dict→`k.sub`、list→`k.N` 从 1 起）、STS 场景 `SecurityToken` 未并入签名集合、Timestamp 格式非 UTC `%Y-%m-%dT%H:%M:%SZ` | 对照 [architecture.md 的签名一节](./architecture.md#zero-dependency-rpc-v1-signing)逐项自查；sample 的 `lib/rpc.py` 已实测通过 |
| `InvalidAccessKeyId` / `InvalidSecurityToken` | AK 失效/无权限，或 STS 临时凭证过期 | 检查 `.env` 的 `ALIYUN_ACCESS_KEY_*`；STS 注意时效与 `ALIYUN_SECURITY_TOKEN` 是否填对 |
| `Throttling.*` | 触发限流 | sample 已自动指数退避重试；仍失败等 1 分钟后重跑 |
| SSO 编排等待超时（SSOStatus 长时间非 Enabled） | 绑定 → SCIM 配置 → SSO 配置三相位编排中，个别相位失败或卡住 | 到控制台查看身份源编排相位；完成后重跑 setup（幂等续跑） |

## 4. Order service / 订单服务（数据面第 4 步）

| 错误码 / 现象 | 根因 | 处置 |
|---|---|---|
| `401 invalid_token`（签名/`iss`/`aud`/`exp` 校验失败） | 令牌与 `.env` 三个验签配置不一致：`ORDER_SERVICE_ISSUER` / `ORDER_SERVICE_AUDIENCE` / `ORDER_SERVICE_JWKS_URI` | 三项取值一律来自 **IDaaS (EIAM) discovery**（`GET {IDAAS_ORIGIN}/api/v2/iauths_system/oauth2/.well-known/openid-configuration` 的 `issuer` / `jwks_uri`）；401 响应里的 `error_description` 会写明具体是哪项不符 |
| `401`：JWKS 中不存在 `kid` 的公钥 | JWKS 取错源（用了池 JWKS 而非 IDaaS JWKS），或密钥刚轮换 | 确认 `ORDER_SERVICE_JWKS_URI` 用的是 IDaaS 公网 discovery 值；sample 缓存 300s、未命中会强制刷新一次 |
| `403 insufficient_scope`（POST /orders 被拒） | 令牌 scope 不含 `write.all`（预期行为，演示权限差异） | 在 `.env` 的 `ORDER_SERVICE_SCOPES` 加上对应 scope 后重跑 `obo`；或用 GET /orders 验证读链路 |
| `GET /orders` 返回本人订单为空（`scope_view=own`、`count=0`） | 你的真实 `sub` 与内置示意身份（employee-alice 等）不同，属预期「未知用户」行为 | 把 login 打印的 `sub` 填进 `orders/mock_data.py` 的 `SUB_ALIAS`（如 `{"user_xxxxxxxx…": "employee-alice"}`），或换两个不同账号跑 demo 对比 |
| `503 temporarily_unavailable` | JWKS 端点拉取失败（服务端依赖故障，不是令牌问题） | 检查 `ORDER_SERVICE_JWKS_URI` 公网可达性（vpc 域名公网不可达，见下节） |

## 5. Local environment / 本地环境与域名

| 错误码 / 现象 | 根因 | 处置 |
|---|---|---|
| DNS 解析失败（NXDOMAIN），域名为 `vpc` 前缀/后缀形态 | **池 discovery 返回的 issuer/jwks_uri 指向 VPC 专用域名，公网不可解析**（预发实测 NXDOMAIN） | 公网场景改用等价公网路径：池 JWKS 用 `https://{DATA_ENDPOINT}/{USER_POOL_ID}/oauth2/jwks`；订单服务验签直接用 IDaaS 公网 discovery 值 |
| 请求打到错误域名（404 / MissingParameter 诡异出现） | **双域名坑**：token 兑换必须走 `SIGNIN_BASE_URL`（`signin.<region>` 域名）；discovery / JWKS 走 `DATA_ENDPOINT` 域名；WAT/OBO RPC 走数据面域名；setup/cleanup 走控制面域名 | 对照 [architecture.md 的双域名表](./architecture.md#the-dual-domain-pitfall)核对 `.env` 的三个端点配置 |
| Python 3.12+ 下 HTTPS 请求报证书错误 | `urllib` 无系统 CA 可用 | 安装可选依赖 `pip install certifi`（sample 检测到无系统 CA 时会自动尝试 certifi；不装也能跑通其余链路） |
| 终端长命令输出偶发丢失 | 环境抖动，非 sample 问题 | 关键输出 sample 已落盘 `.tokens/` 与 RequestId；可用 `python3 sample.py --check` 复查状态 |
| 远程/无 GUI 环境中浏览器打不开（login 卡在等待回调） | `webbrowser.open` 在 ssh 会话/无桌面环境没有可渲染的浏览器，回调服务仍在远程机上监听 loopback | 端口转发到本地：`ssh -L 8765:127.0.0.1:8765 <user>@<host>`（端口按实际 `--port` 调整），然后在**本地浏览器**手动打开 login 终端打印的 authorize URL——回调会经转发命中远程 CLI 的 loopback 服务 |
