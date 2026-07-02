# Quickstart Example

This example shows the simplest way to use the Agent Identity SDK.

## Prerequisites

1. Go 1.21 or later
2. Alibaba Cloud credentials configured (env vars, credentials file, or ECS role)
3. Credential provider(s) configured in the Agent Identity service

## Usage

```bash
# Get STS credential (default)
go run main.go

# Get API key
go run main.go apikey <provider-name>

# Get OAuth2 token (callback port defaults to 8443)
export AGENT_IDENTITY_USER_ID=<user-id>
go run main.go oauth <provider-name>

# Get all three
export AGENT_IDENTITY_USER_ID=<user-id>
go run main.go all <provider-name>
```

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_IDENTITY_REGION_ID` | Alibaba Cloud region | `cn-beijing` |
| `AGENT_IDENTITY_USER_ID` | User ID for OAuth2 3LO | — |
| `AGENT_IDENTITY_USER_TOKEN` | User JWT for OAuth2 3LO | — |
| `AGENT_IDENTITY_CALLBACK_PORT` | OAuth2 callback port | `8443` |

Provider names are passed via command line arguments.

## How It Works

The OAuth2 flow:
1. SDK starts a local HTTP server on the configured port
2. SDK gets an authorization URL and prints it
3. User opens the URL in browser to authorize
4. Authorization server redirects to `http://127.0.0.1:<port>/callback?session_uri=...`
5. The callback handler calls `ConfirmUserAuth` to complete the flow
6. SDK polls until the token is ready
