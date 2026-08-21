# AI Gateway MCP Auth & Credential Injection Sample

An end-to-end sample demonstrating **AI Gateway MCP authentication and credential injection** powered by the latest AI Gateway plugin (AgentIdentity WASM plugin): a user logs in via OIDC, chats with an MCP-backed order service through an AI Gateway, and the gateway plugin verifies the workload access token, enforces Cedar policies, and transparently injects downstream OAuth2 credentials into forwarded requests.

> 📖 The complete step-by-step deployment guide is available in [DEPLOY_GUIDE.md](./DEPLOY_GUIDE.md).

## 🚀 Overview

This sample demonstrates an end-to-end **gateway-side credential injection** flow based on the Agent Identity service and the Alibaba Cloud AI Gateway (APIG):

1. The end user logs in through **OIDC Authorization Code + PKCE** (via an Agent Identity user pool) and obtains an ID Token.
2. The chatbot exchanges the ID Token for a **Workload Access Token (WAT)** through the Agent Identity SDK.
3. The chatbot connects to the **MCP Server hosted by the AI Gateway** with `Authorization: Bearer <WAT>`.
4. The **AgentIdentity WASM plugin** on the gateway verifies the WAT, evaluates **Cedar policies**, and performs **credential injection** — fetching a downstream OAuth2 token from Agent Identity (`USER_FEDERATION` flow) and injecting it into the forwarded request as `Authorization: Bearer <downstream-token>`.
5. The request is forwarded to the upstream **order service** (FastAPI with built-in OAuth2 endpoints) running on ECS. Denied requests get `403`.

The key value: **the chatbot never sees or holds downstream service credentials**. All downstream OAuth2 token acquisition and injection happens inside the gateway plugin, governed by Cedar policies.

## 🏗️ Architecture

```
┌─────────┐     ┌─────────────────────────┐     ┌──────────────────┐
│ Chatbot │────>│  AI Gateway (APIG)      │────>│  Order Service   │
│ (local) │     │       (in VPC)          │     │  (order_service/ │
│         │     │                         │     │   FastAPI on ECS)│
│  OIDC   │     │  AgentIdentity WASM     │     │                  │
│  login  │     │  plugin:                │     │  ├─ OAuth2       │
│         │     │  authn + Cedar authz +  │     │  │   endpoints   │
│         │     │  credential injection   │     │  └─ Order CRUD   │
└─────────┘     └─────────────────────────┘     └──────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │  Agent Identity  │
                │ (user pool +     │
                │  policy sets)    │
                └──────────────────┘
```

**Request flow (5 steps):**

1. The user logs in via OIDC and obtains an ID Token.
2. The chatbot exchanges the ID Token for a Workload Access Token (WAT).
3. The chatbot calls the AI Gateway with `Authorization: Bearer <WAT>`.
4. The AgentIdentity WASM plugin on the gateway:
   - Verifies the WAT (authentication).
   - Evaluates Cedar policies in the policy set bound to the gateway (authorization). Unauthorized tools are also filtered out of `tools/list`.
   - **Credential injection**: obtains a downstream OAuth2 token from Agent Identity (using the `USER_FEDERATION` OAuth2 credential provider) and injects it into the forwarded request header.
5. On success the request is forwarded to the order service on ECS; otherwise the gateway returns `403`.

**How credential injection works:**

The plugin is configured with the ARN of an OAuth2 credential provider created in Agent Identity (authorization type `USER_FEDERATION`). On each authorized request, the plugin asks Agent Identity to mint a downstream OAuth2 token bound to the federated user identity, then injects it into the upstream request as `{injectHeaderPrefix} {token}` on `{injectHeaderName}` (by default `Authorization: Bearer <token>`). The downstream service validates this token like any regular OAuth2 Bearer token.

## ⚙️ Prerequisites

| Requirement | Description |
|------|------|
| Python 3.11+ | Chatbot runtime |
| Alibaba Cloud account | Agent Identity and AI Gateway (APIG) services activated |
| Alibaba Cloud VPC | A VPC (recommended: `cn-beijing`) to host the AI Gateway instance |
| Alibaba Cloud ECS | One ECS instance with a public IP (recommended: Ubuntu 24.04) to host the order service |
| DashScope API Key | From the [Alibaba Cloud Model Studio console](https://bailian.console.aliyun.com/?tab=model#/api-key), or any OpenAI-compatible LLM endpoint |
| RAM permission | Attach `AliyunAgentIdentityFullAccess` to the RAM identity used by the chatbot |

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/ai-gateway-mcp-auth-credential-injection_sample
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env` with your actual values:

| Variable | Source | Description |
|------|------|------|
| `OIDC_DISCOVERY_URL` | Agent Identity console → User pool | OIDC discovery document URL of the user pool |
| `OIDC_CLIENT_ID` | Agent Identity console → Client management | Client ID of the user pool client |
| `OIDC_CLIENT_SECRET` | Agent Identity console → Client secret | Client secret created for the client |
| `AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME` | Agent Identity console → Workload identities | Name of the workload identity created in the Agent Identity console, used to exchange the ID Token for a WAT |
| `LLM_API_KEY` | [Alibaba Cloud Model Studio console](https://bailian.console.aliyun.com) | DashScope API key |
| `LLM_BASE_URL` | Model Studio console | OpenAI-compatible endpoint, e.g. `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `MCP_SERVER_URL` | AI Gateway console → MCP management | MCP service entrypoint, e.g. `http://{gateway-entry}/mcp-servers/test-order-agent-identity` |
| `AGENT_IDENTITY_REGION_ID` | — (optional, default `cn-beijing`) | Agent Identity region |
| `LLM_MODEL` | — (optional, default `qwen-max`) | LLM model name |

## 🔧 Resource Setup

All cloud resources are configured manually in the consoles. The detailed instructions — with screenshots — live in [DEPLOY_GUIDE.md](./DEPLOY_GUIDE.md). **Read [DEPLOY_GUIDE.md §十 Troubleshooting](./DEPLOY_GUIDE.md) first** — it collects every known pitfall of the full chain. Estimated time: 2–4 hours; some steps have strict ordering (notably Step 3 ↔ Step 4 "placeholder first, backfill later"). Overview:

### Step 1 — Deploy the order service (`order_service/`)

If you don't have one yet, create an ECS instance (Ubuntu 24.04, same VPC as the future AI Gateway, public IP, ESSD system disk) with a security group allowing TCP **22** and **8001** (DEPLOY_GUIDE §1.1). Then deploy `order_service/` (a FastAPI order CRUD service with built-in OAuth2 endpoints, for testing purposes only) onto the ECS and start it on port `8001` with `OAUTH_BASE_URL` pointing to the ECS public address (append `</dev/null` to the nohup command to avoid the SSH session hanging). See [DEPLOY_GUIDE.md §一](./DEPLOY_GUIDE.md), and run `order_service/test_oauth.sh` on the ECS to verify the full OAuth flow.

### Step 2 — Agent Identity inbound configuration

Create a user pool (`mcp-chatbot-demo`) and an OIDC client (`mcp-chatbot`, redirect URI `http://localhost:18080/callback`), create the client secret, and configure the login method. **Blocking pitfall:** new user pools default to `EnablePasswordLogin=false` — enable password login via the SDK `UpdateLoginPreference` (aliyun CLI force mode silently ignores the nested parameter), otherwise OIDC login fails with `NO_LOGIN_METHOD_ENABLED`. Then create a test user, an inbound OIDC identity provider (discovery URL = user pool discovery, allowed audience = client ID), a RAM role (trust `workload.agentidentity.aliyuncs.com` with a WI-ARN condition), and the Workload Identity.

> Note: it is recommended to create the Workload Identity with **session binding disabled (`SessionBindingEnabled=false`)** — then the plugin does not need `oauthReturnURL` and no return-URL whitelist (AllowedResourceOAuth2ReturnURLs) is required. Only when session binding is enabled must the Workload Identity's **allowed OAuth2 return-URL whitelist** include the plugin's `oauthReturnURL` (see Step 6). The RAM role bound to the Workload Identity needs **policy-evaluation permission** (`agentidentitydata:EvaluatePolicy`, e.g. `AliyunAgentIdentityDataFullAccess`) **plus** credential-access permission (`agentidentitydata:GetCredential`) — otherwise every `tools/call` fails with 403 (empty reasons) while `tools/list` works. Also: bind the policy set to the gateway via the console (the console auto-creates the TLS-enabled data-plane service; the CLI/API path requires enabling TLS in the console manually, otherwise `InvalidProtocol.NeedSsl`). Note the Agent Identity CLI product name is **`agentidentity`** (API version `2025-09-01`), not `agentidentitycontrol`. See [DEPLOY_GUIDE.md §二](./DEPLOY_GUIDE.md).

![User pool info](images/01-user-pool-info.png)
![Client secret](images/02-client-secret.png)
![SAML SSO configuration](images/03-saml-sso-config.png)

### Step 3 — Agent Identity outbound OAuth2 credential provider

Create an OAuth2 credential provider (name `mcp-order-oauth2`, authorization type `USER_FEDERATION`) whose client ID/secret and token endpoints point to the order service's OAuth2 endpoints, and record its ARN. The issuer/authorization/token endpoints must be reachable by the **Agent Identity data plane** — it cannot reach an ECS public IP directly (error `InvalidOAuthDiscoveryURL: Unreachable`), so the endpoints must be exposed through the AI Gateway. **Ordering note:** the gateway does not exist yet at this point — first create the provider with the ECS direct address (`http://<ECS-public-IP>:8001`) as a placeholder, and after the gateway + OAuth passthrough routes (Step 4) are ready, **backfill** the provider's Issuer/DiscoveryURL/endpoints with the gateway entry domain and restart the order service with the same `OAUTH_BASE_URL`. See [DEPLOY_GUIDE.md §三](./DEPLOY_GUIDE.md).

![OAuth2 credential provider](images/04-oauth2-provider-config.png)

### Step 4 — AI Gateway setup (NAT/EIP, backend service, hosted MCP, tool YAML, OAuth passthrough)

Create an AI Gateway instance in your VPC, enable public network access via a NAT gateway + EIP + SNAT entry, create a backend service pointing to the ECS **private IP** on port `8001` (the gateway cannot reach the ECS public IP; use the IP-address/VIP source type for `IP:port` addresses), create an HTTP-to-MCP service on top of it (then **deploy** it so the entry domain takes effect), edit the MCP tool metadata YAML (tools: `createOrder`, `deleteOrder`, `getOrder`, `listOrders`), verify connectivity with curl, and create the `/.well-known` + `/oauth` passthrough routes needed by Step 3's backfill. See [DEPLOY_GUIDE.md §四](./DEPLOY_GUIDE.md).

![NAT gateway in VPC](images/05-vpc-nat-gateway.png)
![Create NAT gateway and bind EIP](images/06-create-nat-gateway.png)
![SNAT entry](images/07-snat-entry.png)
![Create backend service](images/08-create-service.png)
![Create MCP service](images/09-create-mcp-service.png)
![Edit MCP tool YAML](images/10-create-tool-yaml.png)

### Step 5 — Bind a policy set to the gateway

Create a policy set (`mcp-gateway-policies`) in Agent Identity and bind it to the AI Gateway instance (`AIGateway::Gateway`). Console binding auto-creates the TLS-enabled `agentidentitydata` data-plane service; on the CLI/API path you must create it yourself — the service **name must be `agentidentitydata` without the `.dns` suffix** (the FQDN gets `.dns` appended automatically; naming it `agentidentitydata.dns` yields `.dns.dns` and every request fails with a generic 401), and upstream TLS can only be enabled via the console. See [DEPLOY_GUIDE.md §五](./DEPLOY_GUIDE.md).

![Bind policy set to gateway](images/11-policy-bind-resource.png)

### Step 6 — Plugin configuration (credential injection YAML)

Install the official **agent-identity-oauth** plugin (HigressOfficial, version **1.0.1 or later**) on the gateway from the plugin marketplace (or via CLI), and add an MCP-level rule. The key part for credential injection:

```yaml
credential:
  enabled: true            # enable credential injection
  type: oauth2
  arn: <OAuth2 credential provider ARN from Step 3>
  oauthFlow: USER_FEDERATION
  # Recommended (when the WI has session binding disabled): omit oauthReturnURL.
  # Only required when session binding is enabled, and must be in the WI return-URL whitelist.
  # oauthReturnURL: <OAuth callback URL>
  injectHeaderName: Authorization
  injectHeaderPrefix: Bearer
  injectHeaderPrefixEnabled: true
```

The plugin injects the downstream OAuth2 token as `Bearer <token>` into the `Authorization` header of the request forwarded to the order service. On the CLI/API path, plugin attachments cannot target `McpServer` directly (`attach-resource-type` only supports `GatewayRoute`/`Gateway`/`GatewayDomain`/`HttpApi`/`Operation`) — attach the rule to the MCP service's underlying gateway route as a `GatewayRoute` instead. See [DEPLOY_GUIDE.md §六](./DEPLOY_GUIDE.md) for the full YAML and field reference; see the appendix of [DEPLOY_GUIDE.md](./DEPLOY_GUIDE.md#附录配置参考) for the complete plugin configuration reference and FAQ (common issues).

![Plugin configuration page](images/12-plugin-config-page.png)
![MCP-level plugin rule](images/13-plugin-rule-config.png)

### Step 7 — Cedar policies

Edit Cedar policies in the policy set to control per-user, per-tool access (optionally with `when` conditions on `principal has actor` or `context.input`). Note: for OIDC-federated users the entity type is `AgentIdentity::OAuthUser`, and the available attributes are `Issuer`/`actor` (there is no `iss`/`sub` attribute) — `actor` must be the **full directory form** WI ARN (`acs:agentidentity:{region}:{accountId}:workloadidentitydirectory/default/workloadidentity/{name}`) or the `when` clause is always false. **The entity-ID form varies by environment/product version** (confirmed): it can be either the short `user_id` (`user_xxxx`) or the full user ARN, and a wrong form silently yields 403 with empty reasons plus an empty `tools/list` — probe with a permit-all policy first, then determine the form via LOG_ONLY evaluation logs or by trying both forms once each. See [DEPLOY_GUIDE.md §七](./DEPLOY_GUIDE.md) for both example forms and the full determination method.

![Cedar policy editor](images/14-cedar-policy-editor.png)

### Installing the official gateway plugin

The gateway plugin is officially released in the AI Gateway plugin marketplace as **agent-identity-oauth** (publisher: HigressOfficial; minimum version **1.0.1**). Install it directly from the marketplace in the console, or via CLI:

```bash
aliyun apig list-plugin-classes --gateway-type AI --name-like agent   # look up the plugin class ID
aliyun apig install-plugin --gateway-ids <gateway-id> --plugin-class-id <plugin-class-id>
```

No manual build/upload is required. See [DEPLOY_GUIDE.md §六](./DEPLOY_GUIDE.md) for details.

## ▶️ Running

```bash
./run_chatbot.sh
```

The script loads `.env` from its own directory, validates the required variables, and then:

1. Runs `oidc_login.py` — opens a browser for OIDC login and captures the ID Token via a local callback server (`http://localhost:18080/callback`).
2. Launches `mcp_chatbot.py` with the ID Token, which exchanges it for a Workload Access Token, connects to the gateway-hosted MCP Server, loads only the tools you are authorized for, and enters the interactive chat.

You can also run the components directly with `--help` (e.g. `python3 mcp_chatbot.py --help`) to pass tokens or endpoints manually.

## ✅ End-to-End Verification

Follow [DEPLOY_GUIDE.md §九](./DEPLOY_GUIDE.md) and test these scenarios in the chat:

1. **Plain chat** — say "hello"; the LLM replies without any MCP call.
2. **Authorized tool** — "list all orders"; the chatbot calls `listOrders`, the gateway authorizes and injects credentials, and the order list is returned.
3. **Denied tool (ENFORCE mode)** — "delete order order-001"; if `deleteOrder` is not permitted by your Cedar policy, the gateway returns `403`.
4. **Tool filtering** — at startup, unauthorized tools are automatically filtered out of `tools/list` by the plugin.

For diagnostics, use [test_mcp.py](./test_mcp.py): it performs OIDC login → ID Token → WAT → MCP connect → list tools, printing each step's status:

```bash
python3 test_mcp.py                      # uses .env in the same (or parent) directory
python3 test_mcp.py --mcp-url "http://..." --region cn-beijing
python3 test_mcp.py --bearer-token "eyJ..."   # skip OIDC login, pass an ID Token directly
```

The order service's own OAuth flow can be verified on the ECS with `bash order_service/test_oauth.sh` (authorize → token → create order → list orders → 401 without token → refresh).

## 🤝 Support

For questions or inquiries about the Agent Identity SDK:
- Refer to the [official documentation](https://help.aliyun.com/product/agent-identity)
- Contact Alibaba Cloud support
- Submit issues in the repository

---

## 📄 License

This project is licensed under the Apache License 2.0 — see the [LICENSE](../../LICENSE) file at the repository root for details.
