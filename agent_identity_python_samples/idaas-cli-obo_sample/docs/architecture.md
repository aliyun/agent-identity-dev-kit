# Architecture: Agent Identity × IDaaS Inbound Login + OBO Outbound

This document explains how the sample is wired: the split between the control
plane and the data plane, the end-to-end token sequence, the mapping from CLI
subcommands to cloud APIs, the on-behalf-of (OBO) delegation semantics, the
dual-domain pitfall, and how the zero-dependency RPC V1 signing works.

## Control plane vs. data plane

The sample separates everything it does into two planes with different
lifecycles:

| Plane | Owns | Endpoints | API version | Subcommands |
|---|---|---|---|---|
| **Control plane** (one-time) | User pool, IDaaS identity-source binding, pool OAuth client, IdentityProvider, WorkloadIdentity, OAuth2 credential provider | `agentidentity.<region>.aliyuncs.com` | `2025-09-01` | `setup`, `cleanup` |
| **Data plane** (per run) | Browser login (authorize / token), WAT exchange, OBO token minting, JWKS-based verification | `https://signin.<region>.aliyuncs.com` (OAuth endpoints) and `agentidentitydata.<region>.aliyuncs.com` (RPC) | OAuth2 + `2025-11-27` | `login`, `exchange-wat`, `obo`, `serve-orders`, `demo` |

Responsibilities:

- **Control plane** creates and destroys the long-lived resources the data
  plane depends on. `setup` is idempotent: it queries by name before every
  create (`Get*` / `List*`) and logs `[CREATE]` or `[REUSE]` per resource.
  `cleanup` deletes in reverse order and treats `EntityNotExists.*` as `[SKIP]`.
- **Data plane** executes one full identity journey at runtime:
  an employee federates into the user pool through IDaaS (inbound), the CLI
  lifts that human identity into a workload identity (WAT), then exchanges it
  for a downstream OAuth2 token issued **on behalf of** the employee (outbound),
  and a local mock order service consumes that token and returns data scoped
  to the caller's identity.

## Token sequence

```mermaid
sequenceDiagram
    autonumber
    actor Emp as Employee (browser)
    participant CLI as sample.py (loopback 127.0.0.1)
    participant Pool as Pool OAuth (signin domain)
    participant EIAM as IDaaS (EIAM) instance
    participant DP as Agent Identity data plane
    participant OS as Mock order service (local)

    CLI->>Pool: GET /{poolId}/oauth2/authorize (code, PKCE S256, state, nonce)
    Pool->>Emp: pool login page → IDaaS SSO entry
    Emp->>EIAM: federated login (first login: JIT provisioning; optional email OTP)
    EIAM-->>Pool: authenticated (hosted inbound credential bound to session)
    Pool-->>CLI: 302 redirect → 127.0.0.1:8765/callback?code=...&state=...
    CLI->>Pool: POST /{poolId}/oauth2/token (code, code_verifier, client_id/secret)
    Pool-->>CLI: ID Token (sub, session_id, nonce, iss, aud)
    CLI->>DP: GetWorkloadAccessTokenForJWT(WorkloadIdentityName, UserToken)
    DP-->>CLI: WAT (JWE, ~5 min TTL)
    CLI->>DP: GetResourceOAuth2Token(ON_BEHALF_OF, WAT, provider, audience, scopes)
    DP->>EIAM: upstream token request via the credential provider
    EIAM-->>DP: access token (sub = employee, act.sub = WI ARN)
    DP-->>CLI: OBO access token (+ refresh token)
    CLI->>OS: GET /orders with Authorization: Bearer <AT>
    OS->>EIAM: fetch JWKS (cached 300s) and verify RS256 / iss / aud / exp
    EIAM-->>OS: public keys
    OS-->>CLI: 200 — orders filtered by sub and scope
```

Key points:

1. **Inbound (steps 1–6)**: the CLI starts a loopback HTTP server
   (`http://127.0.0.1:8765/callback`, RFC 8252 style) and opens the system
   browser at the pool authorize endpoint with PKCE S256, a random `state`
   and a `nonce`. The browser walks the federation path (pool login page →
   IDaaS SSO → IDaaS authentication → JIT provisioning on first login →
   consent, implicit or via a consent page). The authorization code is redeemed
   at the pool token endpoint; the CLI decodes the ID Token, prints its claims
   as teaching assertions (`sub`, `iss`, `aud`, `session_id`, `nonce` echo) and
   saves it under `.tokens/`.
2. **Identity lift (steps 7–8)**: `GetWorkloadAccessTokenForJWT` turns the
   pool ID Token into a **Workload Access Token (WAT)** — the moment the
   identity transitions from "a human in a browser session" to "a workload
   bound to that human's session". In a real product this call is made by an
   Agent framework transparently; the CLI only does it explicitly for
   demonstration. The WAT is a JWE-encrypted token (not locally decodable) and
   is short-lived (~5 minutes measured).
3. **Outbound OBO (steps 9–11)**: `GetResourceOAuth2Token` with
   `OAuth2Flow=ON_BEHALF_OF` exchanges the WAT for a downstream token minted
   by IDaaS for the order-service application. The token's `sub` is still the
   employee; the actor is the workload identity (see below).
4. **Consumption (steps 12–15)**: the local mock order service pulls the JWKS
   from the IDaaS discovery endpoint (memory-cached 300 s) and verifies the
   bearer token — RS256 signature, `iss`, `aud`, `exp` (60 s clock skew
   tolerance) — then returns all orders for `read.all`, only the caller's own
   orders otherwise, and accepts new orders only with `write.all`.

## Subcommand → API mapping

| Subcommand | Target | API / route | Style | Notes |
|---|---|---|---|---|
| `login` | `{SIGNIN_BASE_URL}/{USER_POOL_ID}/oauth2/authorize` | OAuth2 authorize (browser) | GET query | `response_type=code`, PKCE `S256`, `state`, `nonce`, `scope=openid` |
| `login` | `{SIGNIN_BASE_URL}/{USER_POOL_ID}/oauth2/token` | OAuth2 token | POST form | `grant_type=authorization_code`, `code`, `redirect_uri` (must match authorize char-for-char), `client_id`, `client_secret`, `code_verifier`. `client_id` is required even for the private-key-JWT branch |
| `exchange-wat` | `agentidentitydata.<region>.aliyuncs.com` | `GetWorkloadAccessTokenForJWT` (`2025-11-27`) | RPC **query** | `WorkloadIdentityName` + `UserToken` (the pool ID Token) |
| `obo` | `agentidentitydata.<region>.aliyuncs.com` | `GetResourceOAuth2Token` (`2025-11-27`) | RPC **formData** | `OAuth2Flow=ON_BEHALF_OF`, `WorkloadAccessToken`, `ResourceCredentialProviderName`, `Audience`, `Scopes` as a **JSON array string**. Business parameters must all go in the form body — query-string or JSON-body calls fail with `MissingParameter.*` |
| `setup --mode=script` | `agentidentity.<region>.aliyuncs.com` | `ListUserPools`, `CreateUserPool`, `SetSpecificIdentityProvider`, `GetSpecificIdentityProvider`, `GetUserPoolClient`, `CreateUserPoolClient`, `UpdateUserPoolClient`, `CreateClientSecret`, `GetIdentityProvider`/`CreateIdentityProvider`, `GetWorkloadIdentity`/`CreateWorkloadIdentity`, `GetOAuth2CredentialProvider`/`CreateOAuth2CredentialProvider` (`2025-09-01`) | RPC query / formData | Query-before-create, `[CREATE]`/`[REUSE]` per step; the SSO orchestration (binding → SCIM → SSO) is polled until `SSOStatus=Enabled` |
| `cleanup` | `agentidentity.<region>.aliyuncs.com` | `DeleteOAuth2CredentialProvider`, `DeleteWorkloadIdentity`, `DeleteIdentityProvider`, `DeleteUserPoolClient`, `DeleteUserPool` (`2025-09-01`) | RPC query | Reverse order; `EntityNotExists.*` → `[SKIP]` |
| `serve-orders` / `demo` | `127.0.0.1:9090` (or ephemeral) | local HTTP: `GET /health`, `GET /orders`, `POST /orders` | — | Bearer verification against `ORDER_SERVICE_JWKS_URI`; no cloud API |

## On-behalf-of delegation semantics

The OBO access token is where the delegation is expressed. The sample prints
the relevant claims after `obo`:

- `sub` — **the federated employee** (the human who logged in via IDaaS). The
  order service uses it to decide whose orders to return.
- `iss` / `aud` — the token is **issued by the IDaaS instance** and addressed
  to the **order-service application** (the audience configured as
  `ORDER_SERVICE_AUDIENCE`, shaped `agent-<outbound-app-clientId>`).
- `act.sub` — **the actual actor: the Workload Identity ARN**. The token says
  "the workload identity (the agent) is acting on behalf of the user in
  `sub`". This is the core of on-behalf-of: an agent can call downstream
  services in the user's name without ever holding the user's password or a
  long-lived user token.
- `_idaas_imp` — the IDaaS **impersonation chain**, recording the
  "user → workload" delegation path on the IDaaS side. Together with
  `act.sub` it gives auditors a complete picture of who is really calling.
- `session_id` — the key the Agent Identity region uses to **locate the
  inbound hosted credential**: the region looks up the federated callback
  credential by the `(pool, user, sessionId)` triple. Without a matching
  `session_id` the OBO call fails with `Forbidden.InboundCredentialMissing`
  (see [troubleshooting.md](./troubleshooting.md)).

Two design consequences worth internalizing:

1. The inbound credential is hosted **only on the federation callback path**.
   Password logins directly against the pool do not host a credential, and a
   browser that reuses a stale pool session produces a token whose
   `session_id` no longer matches the hosted credential — both surface as
   `InboundCredentialMissing` at OBO time.
2. The WorkloadIdentity must be created with `SessionBindingEnabled=true`.
   Session binding is what ties the WAT to the user's login session; without
   it the same `InboundCredentialMissing` error appears.

## The dual-domain pitfall

The pool's OAuth surfaces do **not** live on a single domain. Mixing them up
is the most common configuration error:

| Surface | Correct domain | Wrong-but-tempting alternative |
|---|---|---|
| authorize / token exchange | `https://signin.<region>.aliyuncs.com/{USER_POOL_ID}/oauth2/authorize` and `/oauth2/token` (`SIGNIN_BASE_URL`) | `agentidentitydata` domain (no OAuth endpoints there) |
| Pool discovery / JWKS | `https://{DATA_ENDPOINT}/{USER_POOL_ID}/.well-known/openid-configuration` and `https://{DATA_ENDPOINT}/{USER_POOL_ID}/oauth2/jwks` | the signin domain |
| WAT / OBO RPC | `agentidentitydata.<region>.aliyuncs.com` | the control-plane `agentidentity` domain |
| Control-plane RPC (setup/cleanup) | `agentidentity.<region>.aliyuncs.com` | the data-plane domain |

Additional gotchas confirmed in pre-release testing:

- The pool discovery document may return `issuer` / `jwks_uri` pointing at a
  **VPC-only domain** (e.g. a `vpc`-suffixed host). Such domains are **not
  resolvable from the public internet** (NXDOMAIN). For public-internet use,
  take the equivalent public JWKS path instead:
  `https://{DATA_ENDPOINT}/{USER_POOL_ID}/oauth2/jwks`.
- The order-service verification keys (`ORDER_SERVICE_ISSUER` /
  `ORDER_SERVICE_JWKS_URI`) come from the **IDaaS (EIAM) discovery document**,
  not from the pool discovery: `GET {IDAAS_ORIGIN}/api/v2/iauths_system/oauth2/.well-known/openid-configuration`
  and use its `issuer` / `jwks_uri` fields (both publicly reachable).

## Zero-dependency RPC V1 signing

The sample calls the Alibaba Cloud RPC APIs with **only the Python standard
library** (`urllib` + `hmac` + `hashlib` + `base64`). The implementation
mirrors `alibabacloud_tea_openapi` / `alibabacloud_openapi_util` and was
verified in pre-release testing (control-plane and data-plane probe calls all
passed server-side AK authentication and signature validation; only
deliberate business-layer errors were returned).

How it works:

1. **Common (meta) parameters**: `Action`, `Format=json`, `Version`,
   `Timestamp` (UTC, `%Y-%m-%dT%H:%M:%SZ`), `SignatureNonce` (md5-based unique
   value), `SignatureMethod=HMAC-SHA1`, `SignatureVersion=1.0`,
   `AccessKeyId`. With STS credentials the `SecurityToken` is appended and
   **included in the signed set**.
2. **Percent-encoding**: all keys and values are encoded with
   `urllib.parse.quote(value, safe="~")` — note that `/` and other reserved
   characters *are* encoded, only `~` is not. Using a different `safe` set is
   the classic cause of `SignatureDoesNotMatch`.
3. **Canonical query string**: sort all signed parameters by key, join as
   `k1=v1&k2=v2` (percent-encoded).
4. **String to sign**: `"{METHOD}&%2F&{quote_plus(canonical_query, safe='~')}"`.
5. **Signature**: `base64(HMAC-SHA1(secret + "&", string_to_sign))`, placed in
   the query string as `Signature`.
6. **`query` style** (e.g. `GetWorkloadAccessTokenForJWT`): business
   parameters go into the query string alongside the meta parameters.
7. **`formData` style** (required by `GetResourceOAuth2Token`): the business
   parameter dict is flattened (nested dict → `k.sub` recursion, list →
   `k.1`, `k.2`, … starting at 1, scalars → `str()`), serialized as a
   key-sorted `application/x-www-form-urlencoded` body, and — crucially —
   **the flattened body parameters join the signed set** while the signature
   itself stays in the query string, not the body.
8. **TLS**: the default verified SSL context is used; if the system has no CA
   store the client tries `certifi` (an optional, non-required dependency).

Retry policy: network errors / HTTP 5xx / `Throttling*` are retried with
exponential backoff (max 3); `wait_window=True` (used by `obo`) additionally
retries `MissingParameter.*` up to 30 times × 5 s to ride out rolling-release
window switches; deterministic errors (`SignatureDoesNotMatch`,
`InvalidParameter*`, `Forbidden.*`, …) are never retried.

## Replacing lib/rpc.py with the official SDK

`lib/rpc.py` exists solely to keep the sample **zero-dependency**. If you
prefer the official SDK (a Tea-based client generated from the
`agentidentity` API meta files), there are exactly **three call sites** to
swap:

| Call site | APIs | Version | Style |
|---|---|---|---|
| `lib/flow.py` → `run_exchange_wat` | `GetWorkloadAccessTokenForJWT` | `2025-11-27` | `query` |
| `lib/flow.py` → `run_obo` | `GetResourceOAuth2Token` | `2025-11-27` | `formData` |
| `lib/control_plane.py` → `_call` | all setup / cleanup APIs (`ListUserPools`, `CreateUserPool`, …) | `2025-09-01` | `query` / `formData` |

The behavioral contract to preserve when swapping:

1. **Two wire styles**: `GetWorkloadAccessTokenForJWT` and the control-plane
   APIs use the `query` style (business parameters in the query string);
   `GetResourceOAuth2Token` **requires** the `formData` style (business
   parameters as an `application/x-www-form-urlencoded` body). Mixing them
   up fails with `MissingParameter.*`.
2. **`Scopes` is a JSON array string** — `["read","write.all"]` passed as a
   single parameter; the `Scopes.1` / `Scopes.2` fan-out form is rejected.
3. **API versions differ per plane**: `2025-11-27` for the data plane,
   `2025-09-01` for the control plane.
4. Keep the error semantics the sample relies on: retry `Throttling*` / 5xx /
   network errors with backoff; the `wait_window` handling of
   `MissingParameter.*` (see the retry policy above); surface deterministic
   errors immediately; and consult `err_code(resp)` when a 200 response is
   missing expected fields (the server reports business errors as
   `Code` / `Message` inside an otherwise successful response).

## SCIM positioning

SCIM provisioning is **out of scope for v1 of this sample**: there is no CLI
command that automates it and it has not been verified in pre-release
testing. `setup --with-scim` only prints guidance.

The main line does not need SCIM: on **first federated login the user is
provisioned just-in-time (JIT)** into the user pool automatically, which is
enough for the demo.

SCIM pre-provisioning (creating directory users ahead of time with
`externalId` set to the IDaaS `sub`) is the advanced option when you want to
control group membership or account state before the first login — JIT then
matches by `externalId` instead of creating a fresh profile. See step 3 of
[control-plane-console.md](./control-plane-console.md) if you want to enable
it manually in the console.

## Deviations from the original design

Where the implementation consciously deviates from the initial design
notes, and the pre-release findings that motivated each:

1. **SCIM provisioning is not automated.** Pre-release testing showed the
   federated-login JIT provisioning covers the demo main line fully, and the
   `SetSpecificIdentityProvider` API currently lists **DingTalk only** as a
   supported identity-source type (binding IDaaS via the API returned
   `InvalidParameter`). SCIM therefore stays manual (console) plus
   guidance-only (`setup --with-scim` prints instructions, performs no
   writes).
2. **`POOL_ISSUER` evolved into `SIGNIN_BASE_URL` + `DATA_ENDPOINT`.** The
   original single "pool issuer" notion splits across two domains in
   production: OAuth authorize/token live on `signin.<region>.aliyuncs.com`
   while pool discovery / JWKS live on the data endpoint (see the dual-domain
   pitfall above). Two explicit `.env` keys reflect that reality better than
   one combined value.
3. **The refresh-token flow is not implemented.** The OBO response does
   include a refresh token, and the sample persists it under `.tokens/` for
   inspection — but never refreshes. The upstream WAT expires in ~5 minutes
   (measured), long before the downstream AT, so refreshing the AT cannot
   rescue a stale WAT; re-running `login` → `exchange-wat` → `obo` is the
   documented path.
