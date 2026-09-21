# Architecture: Agent Identity × IDaaS Inbound Login + OBO Outbound

This document explains how the sample is wired: the split between the control
plane and the data plane, the end-to-end token sequence, the mapping from CLI
subcommands to cloud APIs, the on-behalf-of (OBO) delegation semantics, the
dual-domain pitfall, the credential chain and configuration derivation, and how
the standard-library RPC V1 signing works.

## Control plane vs. data plane

The sample separates everything it does into two planes with different
lifecycles:

| Plane | Owns | Endpoints | API version | Subcommands |
|---|---|---|---|---|
| **Control plane** (one-time) | User pool, IDaaS identity-source binding, pool OAuth client, IdentityProvider, WorkloadIdentity, OAuth2 credential provider | `agentidentity.<region>.aliyuncs.com` | `2025-09-01` | `setup`, `cleanup` |
| **Data plane** (per run) | Browser login (authorize / token), WAT exchange, OBO token minting, JWKS-based verification | `https://signin.<region>.aliyuncs.com` (pre-release OAuth endpoints; production uses the sign-in login domain) and `agentidentitydata.<region>.aliyuncs.com` (RPC) | OAuth2 + `2025-11-27` | `login`, `exchange-wat`, `obo`, `serve-orders`, `demo` |

> The endpoints above are **auto-derived from `REGION` + `ENVIRONMENT`** by
> `derive_defaults` (see
> [Credentials & configuration loading](#credentials--configuration-loading));
> you normally don't set `CONTROL_ENDPOINT` / `DATA_ENDPOINT` / `SIGNIN_BASE_URL`
> by hand. `POOL_JWKS_BASE` is mirrored from `SIGNIN_BASE_URL` **only when
> `ENVIRONMENT=production` is explicitly declared** in `.env`; if that key is
> absent or set to `pre-release`, it stays empty and pool discovery/JWKS falls
> back to `DATA_ENDPOINT` (the legacy behavior).

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
  `ORDER_SERVICE_AUDIENCE`: the enterprise app's **own audience identifier**
  from its IDaaS detail page, e.g. `test-aud` — **not** the OBO provider's
  OutboundAudience, `agent-…` form; passing the latter fails with
  `Forbidden.IdaasRsNotAuthorized`, verified in Singapore production).
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
| authorize / token exchange | `https://signin.<region>.aliyuncs.com/{USER_POOL_ID}/oauth2/authorize` and `/oauth2/token` (`SIGNIN_BASE_URL`; production uses the sign-in login domain, e.g. `https://signin-<region>.aliyunagentid.com`) | `agentidentitydata` domain (no OAuth endpoints there) |
| Pool discovery / JWKS | pre-release: `https://{DATA_ENDPOINT}/{USER_POOL_ID}/.well-known/openid-configuration` and `.../oauth2/jwks`; production (Singapore `ap-southeast-1`): the **sign-in domain** with the same paths — but **only when `ENVIRONMENT=production` is explicitly declared** in `.env` (the gating condition for `POOL_JWKS_BASE` mirroring). If absent/pre-release, stays empty and uses `DATA_ENDPOINT` (backward-compat). A `[env]` warning is printed to stderr when mirroring occurs | assuming one host fits every environment |
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
  and use its `issuer` / `jwks_uri` fields (both publicly reachable). When
  `IDAAS_ORIGIN` is set the sample fetches these **automatically** via
  `apply_discovery` (see
  [Credentials & configuration loading](#credentials--configuration-loading)) —
  no manual copying; an explicit `.env` value always wins.
- Environment variance (verified in Singapore `ap-southeast-1` production,
  2026-08): the sign-in domain takes the form
  `https://signin-<region>.aliyunagentid.com` (pre-release:
  `pre-signin-<region>.alibabacloudagentid.com`), and pool discovery/JWKS are
  served on the sign-in domain rather than the data endpoint — hence the
  optional `POOL_JWKS_BASE` knob in `.env`. **Gating**: `POOL_JWKS_BASE` is
  only auto-mirrored from `SIGNIN_BASE_URL` when the user **explicitly
  declares** `ENVIRONMENT=production`; if the key is absent (the common
  legacy `.env` shape) or `pre-release`, it stays empty and falls back to
  `DATA_ENDPOINT`. The OBO `Audience` must be the enterprise app's own
  audience identifier (e.g. `test-aud`), not the provider's OutboundAudience.
  See the README section "Region/environment differences" for the full
  checklist and the token-lifetime table.

## Credentials & configuration loading

Two mechanisms keep the `.env` surface minimal — only **3 required** values
(`REGION`, `ORDER_SERVICE_AUDIENCE`, `IDAAS_ORIGIN`); everything else is
derived, auto-fetched, or written back by `setup`.

### Three-level credential chain

`lib/credentials.py` → `resolve_creds(config)` resolves the Alibaba Cloud RPC
triple `(access_key_id, access_key_secret, security_token|None)` through a
fallback chain; the first level that yields credentials wins:

1. **Explicit AK/SK** — `config`'s `ALIYUN_ACCESS_KEY_ID` /
   `ALIYUN_ACCESS_KEY_SECRET` are non-placeholder → used directly
   (`ALIYUN_SECURITY_TOKEN` appended when set). Top priority: backward-compat /
   CI / fixed teaching credentials. **Both must be filled or both empty** —
   filling only one raises `CredentialError` immediately (no silent fallback to
   level 2/3), because a silent fallback could execute control-plane operations
   under a different account.
2. **SDK default chain** — when the optional `alibabacloud_credentials` is
   installed, a lazily-built singleton `CredentialClient()` walks the default
   chain (reads `~/.aliyun/config.json`; an OAuth profile refreshes
   non-interactively in the background via refresh_token). One
   `get_credential()` call returns all three fields. Any exception → fall
   through to level 3.
3. **Standard-library fallback** — pure-stdlib parse of `~/.aliyun/config.json`
   (the `current` profile): `AK` / `StsToken` / `OAuth` modes. **OAuth is not
   refreshed here**: an expired STS raises a `CredentialError` with guidance
   ("install the SDK for auto-refresh, or re-run `aliyun configure`") rather
   than silently using an expired token.

Environment-variable naming differs by layer: the explicit branch reads the
sample's `ALIYUN_ACCESS_KEY_*`; the SDK chain internally reads
`ALIBABA_CLOUD_*`. `sample.py --check` (offline) reports each level's
*capability* via `probe_*` APIs; `--check --creds-live` resolves and reports
the exact winning level.

The SDK is an **optional enhancement** — the sample runs standalone on the
standard library (level 3) without it. The singleton mirrors `lib/rpc.py`'s
`ssl_context()` double-checked-lock pattern so `setup`'s ~10 `_call`s reuse one
client instead of rebuilding the provider chain each time.

### Config derivation (offline) + discovery (lazy)

`lib/env.py` → `derive_defaults(env)` is **pure offline** (dict operations only,
no network / file IO) so the offline unit tests stay deterministic:

- `REGION` → `CONTROL_ENDPOINT` / `DATA_ENDPOINT`.
- `REGION` + `ENVIRONMENT` (default `production`) → `SIGNIN_BASE_URL`:
  production `https://signin-<region>.aliyunagentid.com`;
  pre-release `https://signin.<region>.aliyuncs.com`.
- `POOL_JWKS_BASE` gating: **only when the user _explicitly declared_
  `ENVIRONMENT=production`** (i.e. the key exists in `.env` / env-var and is
  non-placeholder) is `POOL_JWKS_BASE` mirrored from `SIGNIN_BASE_URL`. If the
  key is absent or `pre-release`, `POOL_JWKS_BASE` stays empty and
  `control_plane._pool_wellknown_host()` falls back to `DATA_ENDPOINT` — the
  pre-existing behavior, unchanged. When mirroring occurs, a `[env]`-prefixed
  warning is printed to **stderr** explaining how to revert.
- `ENVIRONMENT` validation: legal values are only `production` / `pre-release`
  (case-insensitive, auto-trimmed via `strip().lower()`); any other value raises
  `EnvError` (inherits `RpcError` → caught by `sample.py`'s unified error exit)
  **before** any derivation runs. The error message includes the offending value,
  the valid set, the `.env` path, and correction guidance.
- Reverse fallbacks: `REGION` from an explicit endpoint; `IDAAS_ORIGIN` from an
  explicit `ORDER_SERVICE_ISSUER`.
- Explicit values always win — derivation only fills empty / placeholder keys.

`lib/discovery.py` → `apply_discovery(config)` is the **only** network-touching
step and is deliberately kept out of `derive_defaults`. It pulls
`{IDAAS_ORIGIN}/api/v2/iauths_system/oauth2/.well-known/openid-configuration`,
reads `issuer` / `jwks_uri`, and fills the empty `ORDER_SERVICE_ISSUER` /
`ORDER_SERVICE_JWKS_URI` (explicit values win). It is triggered **lazily** only
where those values are needed — `demo`, `serve-orders`, and the end of `setup`
(which writes them back to `.env`); `login`, `--check`, `exchange-wat`, `obo`
never call it. An in-memory TTL cache (3600 s, mirroring `orders/verify.py`'s
`JwksCache`) backs the long-running `serve-orders` process; there is no
persistent cache (over-engineering for short-lived CLI runs).

### Discovery security validation (trust boundary)

Before the credential-chain refactoring, `issuer` / `jwks_uri` were manually
copied from the console (human-in-the-loop). After automation, the program
trusts the remote document content — so `lib/discovery.py` now enforces
**five layers of validation**:

1. **Input URL validation** (`_build_discovery_url`): `urlsplit` checks
   scheme=https, non-empty netloc/hostname, numeric port if present, no path
   component. This fixes the old bug where `https://` was `rstrip("/")`-ed into
   `https:`.
2. **Fetch-function arity pre-check** (`inspect.signature`): determines whether
   the injected `fetch_func` accepts 1 or 2 args — never calls it twice;
   exceptions from the injected body propagate as-is.
3. **Exception whitelist**: catches `OSError`, `http.client.HTTPException`,
   `ValueError`, `UnicodeError` (the first is **not** an `OSError` subclass and
   would escape wrapping otherwise).
4. **HTTPS-only redirect handler** (`_HttpsOnlyRedirectHandler`): blocks
   https→http downgrades and validates the final URL is still https with host
   matching `IDAAS_ORIGIN`.
5. **Response same-origin check** (`get_issuer_jwks`): the returned `jwks_uri`
   must be https, and both `issuer` and `jwks_uri` must be **same-origin**
   (same scheme + same host) as `IDAAS_ORIGIN` — preventing SSRF and issuer
   confusion.

**Why not string-equality between `issuer` and `IDAAS_ORIGIN`?** Real
deployments may have an issuer with a path prefix (e.g.
`/api/v2/iauths_system/oauth2`). RFC 8414 §3.3 consistency is interpreted here
as "same scheme + same host"; full string equality would false-positive on
legitimate environments.

Response body decoding uses `decode("utf-8", errors="replace")`.
`DiscoveryCache` semantics are unchanged: TTL 3600 s, `force_refresh` support,
errors are **never** cached, no persistent storage.

### Credential freshness: `_CredsResolver` (replaces `_ACTIVE_CREDS`)

The old module-level global `_ACTIVE_CREDS` cached a **resolution snapshot**.
Because `setup` includes SSO polling up to `SSO_POLL_TIMEOUT=600 s` (a full run
can exceed 10 minutes), the SDK's OAuth auto-refresh and the stdlib's
`sts_expiration` re-check were both short-circuited during that window; the
global also lacked isolation — any other `_call` in the same process silently
reused setup's identity.

The replacement `_CredsResolver(config, ttl=300.0, clock=None,
resolve_func=None)`:

- **TTL-bounded reuse**: within TTL, returns the cached triple (avoiding ~10
  `resolve_creds` calls per setup round); on expiry, re-resolves (the SDK has
  `reuse_last_provider_enabled` internally, so re-resolution is cheap) — letting
  auto-refresh actually take effect.
- **Explicit pass-through, no module-level state**: `_run_setup_script_inner`
  and `_run_deletes` (cleanup) both receive the resolver as a parameter and
  pass `creds=resolver.get()` to each `_call(...)`.
- **Failure leaves no dirty cache**: if `resolve_creds` raises
  `CredentialError`, `_cached` stays `None`.
- **Injectable clock/resolve_func**: unit tests control TTL without real sleep.

`_delete_quiet` now also catches `credentials.CredentialError` (logs `[WARN]`,
returns "failed", entry stays in the manifest for the next cleanup retry) —
preserving the "best-effort reverse-order cleanup + incremental manifest
writeback" contract.

### Two-phase `.env` writeback in `setup`

`_run_setup_script_inner` now writes back in **two phases**:

1. **Phase 1 (core outputs)**: immediately after all resources are created —
   `writeback_env` persists `OAUTH_CLIENT_SECRET`, `USER_POOL_ID`,
   `OAUTH_CLIENT_ID`, `WI_NAME`, `OBO_PROVIDER_NAME`, etc. **Not** issuer/jwks.
2. **Phase 2 (discovery fill)**: `apply_discovery` is attempted; on success a
   **second** `writeback_env` writes only `ORDER_SERVICE_ISSUER` /
   `ORDER_SERVICE_JWKS_URI`, and **only when the value actually changed**
   relative to pre-discovery (avoids clobbering user inline comments on
   idempotent re-runs, reduces the atomic-replace window). Log branches:
   "已回填" vs "沿用显式值".

`DiscoveryError` in phase 2 is downgraded to a warning — it **never** affects
phase 1's already-persisted outputs.

**Design rationale**: `client_secret` is returned **only once** at creation
time. The old ordering (discovery before writeback) meant any discovery
exception caused "resource created, `.env` not written, `client_secret`
permanently lost" — an irreversible loss.

### Offline probe APIs (`probe_explicit` / `probe_sdk_installed` / `probe_stdlib`)

`sample.py --check` (offline mode) uses three **public read-only probe
functions** exposed by `lib/credentials.py` — it never touches private symbols:

| Function | Returns | Side effects |
|---|---|---|
| `probe_explicit(config)` | `Optional[ResolvedCreds]` — `level="explicit"`, `source=".env 显式 ALIYUN_ACCESS_KEY_*"` when both AK/SK present; `None` when both absent/placeholder; **raises `CredentialError`** on half-fill (message identical to `resolve_creds`) | None (dict read only) |
| `probe_sdk_installed()` | `bool` — whether `alibabacloud_credentials` is importable (`CredentialClient is not None`) | None (no client construction, no `get_credential()`, no ECS metadata probe, no module-level failure state) |
| `probe_stdlib()` | `ResolvedCreds` — `level="stdlib"`, `source="~/.aliyun/config.json(profile=<name>, mode=<mode>)"`; raises `CredentialError` on any failure (file missing / invalid JSON / unsupported mode / STS expired) | None (read-only file parse + expiry check) |

These three form the **offline boundary**: no network, no refresh, no disk
writes. In contrast, `resolve_creds` / `resolve_creds_detailed` perform real
resolution (may trigger network, OAuth renewal, write-back to
`~/.aliyun/config.json`). `--check` uses the former; `--check --creds-live`
uses the latter.

`--check` (offline) also folds the probe outcome into its **exit code**: it
returns `0` only when required keys are complete *and* no deterministic
misconfiguration is found — i.e. neither a half-filled explicit AK/SK
(`probe_explicit` raises) nor an expired stdlib STS credential (`probe_stdlib`
raises with an “已过期” message). Both-empty (the recommended chain posture),
“SDK installed but not called”, and a missing `~/.aliyun/config.json` all keep
the exit code at `0`; the report body is unchanged either way (only the exit
code reflects the credential verdict). `--creds-live` real-resolution failures
are out of this exit-code contract. See
[troubleshooting.md](./troubleshooting.md) for the full sample output.

### `serve-orders` fail-closed + discovery degradation

`orders/verify.py`'s `TokenVerifier.__init__` now **rejects empty/placeholder
issuer and audience** (raises `ValueError`), eliminating the old fail-open
where `if self.issuer:` skipped the entire `iss` check on an empty string —
which would accept any token signed by that JWKS with a matching `aud`
(issuer confusion / cross-tenant token replay).

`orders/server.py`'s `make_server` startup sequence:

1. `derive_defaults` — if it raises `EnvError`, a clear startup error is
   printed (not a raw stack trace; matters for standalone deployment without
   `sample.py`).
2. `apply_discovery` — if it raises `DiscoveryError`, a stderr `[orders][WARN]`
   is emitted and startup **continues** (aligned with `setup` semantics: the
   service must still come up so `/health` works; JWKS-unreachable requests
   degrade to 503 per-request).
3. **Fail-closed check**: if `ORDER_SERVICE_ISSUER` /
   `ORDER_SERVICE_JWKS_URI` / `ORDER_SERVICE_AUDIENCE` is still
   empty/placeholder after discovery, startup is **refused** with two exits:
   (A) fill `IDAAS_ORIGIN` so discovery can populate them, or (B) fill all
   three explicitly.

Defense-in-depth: when an explicitly configured `ORDER_SERVICE_JWKS_URI` is
**not same-origin** with the effective issuer, a `[verify][WARN]` line is
printed to stderr (does **not** hard-fail — legitimate deployments may have
JWKS and issuer on different domains). The https hard-check is preserved.

## Zero-dependency RPC V1 signing

The sample calls the Alibaba Cloud RPC APIs with **only the Python standard
library** (`urllib` + `hmac` + `hashlib` + `base64`) — the signing layer itself
has no third-party dependency (credential *resolution* is separate; see
[Credentials & configuration loading](#credentials--configuration-loading),
where the SDK is an optional enhancement). The implementation
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

`lib/rpc.py` exists solely to keep the sample's **RPC layer**
standard-library-only. If you
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
