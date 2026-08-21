# Agent Identity SDK for Go

[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8?logo=go)](https://golang.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Go SDK for Alibaba Cloud Agent Identity — enables agents to securely access external resources via OAuth2, API keys, and STS credentials.

## Installation

```bash
go get github.com/aliyun/agent-identity-dev-kit/agent-identity-sdk-go
```

## Quick Start

### 1. Create a Client

```go
import agentidentity "github.com/aliyun/agent-identity-dev-kit/agent-identity-sdk-go"

client, err := agentidentity.NewIdentityClient("cn-beijing")
if err != nil {
    log.Fatal(err)
}
```

The SDK uses the default Alibaba Cloud credential chain (environment variables, ECS instance role, etc.). Optional customizations:

```go
client, err := agentidentity.NewIdentityClient("cn-hangzhou",
    agentidentity.WithDataApiEndpoint("custom-data.example.com"),
    agentidentity.WithProtocol("HTTPS"),
)
```

### 2. Get API Key

```go
ctx := context.Background()
apiKey, err := agentidentity.GetAPIKey(ctx, client, "my-provider")
```

### 3. Get STS Credential

```go
sts, err := agentidentity.GetSTSCredential(ctx, client)
fmt.Println(sts.AccessKeyId, sts.AccessKeySecret, sts.SecurityToken)
```

With custom options:

```go
sts, err := agentidentity.GetSTSCredential(ctx, client, agentidentity.AssumeRoleOptions{
    RoleSessionName: "my-session",
    DurationSeconds: 3600,
    Policy:          `{"Version":"1","Statement":[]}`,
})
```

### 4. Get OAuth2 Token

```go
token, err := agentidentity.GetOAuth2Token(ctx, client, "my-provider")
```

With user authorization (OAuth2 3LO):

```go
ctx := agentidentity.WithUserId(context.Background(), "user-123")

token, err := agentidentity.GetOAuth2Token(ctx, client, "my-provider", agentidentity.GetTokenOptions{
    CallbackUrl: "http://127.0.0.1:8443/callback",
    OnAuthUrl: func(authURL string) {
        fmt.Println("Please authorize:", authURL)
    },
})
```

The OAuth2 3LO flow:

1. SDK gets an authorization URL and calls `OnAuthUrl`
2. User opens the URL in their browser to authorize
3. Authorization server redirects to your `CallbackUrl` with `session_uri`
4. Your server calls `client.ConfirmUserAuth(ctx, sessionURI)` to confirm
5. SDK polls until the token is ready

### 5. User Context

Pass user identity through context for user-scoped tokens:

```go
ctx := agentidentity.WithUserId(context.Background(), "user-123")
ctx = agentidentity.WithUserToken(ctx, "user-jwt-token")

token, _ := agentidentity.GetOAuth2Token(ctx, client, "my-provider")
```

### 6. Workload Identity Management (Low-Level)

For advanced use cases, you can manage workload identities directly:

```go
// Create a workload identity
workloadName, err := client.CreateWorkloadIdentity(ctx, agentidentity.CreateWorkloadIdentityOption{
    WorkloadName:                   "my-workload",
    RoleArn:                        "acs:ram::123456:role/MyRole",
    AllowedResourceOAuth2ReturnUrls: []string{"http://127.0.0.1:8443/callback"},
    IdentityProviderName:           "my-provider",
})

// Get a workload access token
token, err := client.GetWorkloadAccessToken(ctx, workloadName)

// Assume role for STS credentials
sts, err := client.AssumeRoleForWorkloadIdentity(ctx, agentidentity.AssumeRoleOptions{
    WorkloadToken:   token,
    RoleSessionName: "my-session",
    DurationSeconds: 3600,
})
```

## API Reference

### Functional API (Recommended)

| Function | Description |
|----------|-------------|
| `GetOAuth2Token(ctx, client, providerName, opts)` | Get OAuth2 token with automatic workload/STS handling |
| `GetAPIKey(ctx, client, providerName)` | Get API key with automatic workload/STS handling |
| `GetSTSCredential(ctx, client, opts)` | Get STS credential with automatic workload handling |

### Core Client

| Method | Description |
|--------|-------------|
| `NewIdentityClient(region, opts...)` | Create a new client |
| `client.GetToken(ctx, opts)` | Get OAuth2 token (low-level) |
| `client.GetApiKey(ctx, opts)` | Get API key (low-level) |
| `client.GetWorkloadAccessToken(ctx, name, opts...)` | Get workload access token |
| `client.CreateWorkloadIdentity(ctx, opts...)` | Create a workload identity |
| `client.AssumeRoleForWorkloadIdentity(ctx, opts)` | Assume role for STS credentials |
| `client.ConfirmUserAuth(ctx, sessionUri, opts)` | Confirm user OAuth2 authorization |
| `client.GetStsCredentialClient(ctx, workloadToken, userId, userToken)` | Get STS-backed credential client |

### Context Helpers

| Function | Description |
|----------|-------------|
| `WithUserId(ctx, userId)` | Set user ID in context |
| `WithUserToken(ctx, token)` | Set user JWT token in context |
| `WithWorkloadAccessToken(ctx, token)` | Set workload access token in context |
| `WithCustomState(ctx, state)` | Set custom state in context |
| `GetUserId(ctx)` / `GetUserToken(ctx)` / ... | Get values from context |
| `ClearContext(ctx)` | Clear all Agent Identity values from context |

### Cache

| Function | Description |
|----------|-------------|
| `StoreCredentialInCache(key, credential, ttl?)` | Store STS credential in LRU cache (default TTL: 600s) |
| `GetCachedCredential(key)` | Get cached credential (returns nil if expired) |
| `SetMaxCacheSize(maxSize)` | Set maximum cache size (default: 100) |

### Options

```go
type GetTokenOptions struct {
    ProviderName        string
    AuthFlow            string
    Scopes              []string
    OnAuthUrl           func(url string)
    CallbackUrl         string
    ForceAuthentication bool
    CustomState         string
    CustomParameters    map[string]string
    Credential          credential.Credential
}

type AssumeRoleOptions struct {
    RoleSessionName string
    DurationSeconds int64
    Policy          string
}
```

### Data Models

```go
type STSCredential struct {
    AccessKeyId     string
    AccessKeySecret string
    SecurityToken   string
    Expiration      string
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | Alibaba Cloud access key | — |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | Alibaba Cloud access key secret | — |
| `AGENT_IDENTITY_REGION_ID` | Region for API endpoints | `cn-beijing` |
| `AGENT_IDENTITY_USE_STS` | Whether to use STS for API calls | `true` |
| `AGENT_IDENTITY_USER_ID` | User ID for OAuth2 3LO | — |
| `AGENT_IDENTITY_USER_TOKEN` | User JWT for OAuth2 3LO | — |
| `AGENT_IDENTITY_CALLBACK_PORT` | OAuth2 callback port | `8443` |

## Architecture

```
┌─────────────────────────────────────────────┐
│              Your Application               │
│                                             │
│  GetOAuth2Token / GetAPIKey / GetSTSCredential
│         │              │              │     │
│         ▼              ▼              ▼     │
│  ┌──────────────────────────────────┐       │
│  │        IdentityClient            │       │
│  │  ┌──────────┐  ┌──────────────┐  │       │
│  │  │ Ctrl     │  │  Data Plane  │  │       │
│  │  │ Plane    │  │  Client      │  │       │
│  │  └──────────┘  └──────────────┘  │       │
│  │  ┌────────────────────────────┐  │       │
│  │  │  LRU Cache (STS Creds)     │  │       │
│  │  └────────────────────────────┘  │       │
│  └──────────────────────────────────┘       │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │  Alibaba Cloud Agent    │
        │      Identity Service   │
        └─────────────────────────┘
```

## Examples

See the [`examples/quickstart/`](examples/quickstart/) directory for a complete working example demonstrating all three credential types.

```bash
cd examples/quickstart

# Get STS credential
go run main.go

# Get API key
go run main.go apikey <provider-name>

# Get OAuth2 token
export AGENT_IDENTITY_USER_ID=<user-id>
go run main.go oauth <provider-name>

# Get all three
export AGENT_IDENTITY_USER_ID=<user-id>
go run main.go all <provider-name>
```

## Testing

```bash
# Run unit tests
go test -v

# Run tests with coverage
go test -coverprofile=coverage.out && go tool cover -html=coverage.out

# Run end-to-end tests (requires real credentials)
go test -v -tags=e2e
```

## License

Apache License 2.0 — see [LICENSE](../../LICENSE).
