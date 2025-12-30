# Agent Identity Python SDK

The Agent Identity Python SDK is a Python development toolkit for accessing Agent Identity services. This SDK provides identity authentication, token management, API key acquisition, and more, supporting both synchronous and asynchronous invocation modes.

## Features

- **OAuth2 Access Token Acquisition**: Supports multiple OAuth2 flows for access token retrieval
- **API Key Acquisition**: Programmatic API key retrieval
- **STS Credential Acquisition**: Obtain temporary security token service credentials
- **Context Management**: Thread-safe context variable management
- **Caching Mechanism**: Built-in credential caching for improved performance
- **Decorator Support**: Simplified authentication flow integration via decorators
- **Concurrency Safety**: Supports multi-threading and asynchronous environments

## Installation

```bash
pip install agent-identity-python-sdk
```

## Quick Start

### Basic Configuration

Before using the SDK, ensure you have set the correct environment variables:

```bash
export AGENT_IDENTITY_REGION_ID="cn-beijing"  # Optional, set your Region ID, default is cn-beijing
export AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN="<your-workload-access-token>" # Optional, set your workload access token, if not specified, the Agent Identity service will be automatically called to obtain it
export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME="<your-workload-identity-name>" # Optional, set your workload identity name, if specified, the workload identity will be used as the agent's identity, otherwise a random workload identity will be generated
export AGENT_IDENTITY_USE_STS="true/false" # Optional, set whether to use the agent identity associated role for resource credential acquisition, default is true
```

### Using Decorators to Automatically Obtain Tokens

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
    # Use access_token here
    print(f"Access token: {access_token}")
    # Your business logic

# Call the function
my_function()
```

### Using Decorators to Obtain API Keys

```python
from agent_identity_python_sdk.core.decorators import requires_api_key

@requires_api_key(credential_provider_name="your-provider-name", inject_param_name="api_key")
def my_function(api_key: str):
    # Use api_key here
    print(f"API key: {api_key}")
    # Your business logic

# Call the function
my_function()
```

### Using Decorators to Obtain STS Credentials

```python
from agent_identity_python_sdk.core.decorators import requires_sts_token
from agent_identity_python_sdk.model.stscredential import STSCredential

@requires_sts_token(inject_param_name="sts_credential")
def my_function(sts_credential: STSCredential):
    # Use sts_credential here
    print(f"STS Access Key ID: {sts_credential.access_key_id}")
    # Your business logic

# Call the function
my_function()
```

## Core Modules

### IdentityClient

IdentityClient is the core identity management client that provides methods for creating and managing identities and acquiring various types of credentials.

```python
from agent_identity_python_sdk.core.identity import IdentityClient

client = IdentityClient(region_id="cn-beijing")

# Create workload identity
workload_identity_name = client.create_workload_identity(
    workload_identity_name="my-workload",
    allowed_resource_oauth2_return_urls=["https://example.com/callback"],
    role_arn="acs:ram::12****:role/example-role",
)

# Get workload access token
token = client.get_workload_access_token(
    workload_name=workload_identity_name,
    user_token="ejwyJ9***",
    user_id="example-user"
) # Prioritizes using user_token to obtain workload access token; if not available, uses user_id to obtain workload access token; if both are absent, obtains workload access token without end-user information
```

### Context Management

The SDK provides context managers for storing thread/async task isolated data:

#### AgentIdentityContext

Used to manage workload access tokens, user ID, user tokens, session ID, etc. The SDK will read the current thread's context variables to obtain the workload access token when acquiring workload access tokens.

```python
from agent_identity_python_sdk.context.context import AgentIdentityContext

# Set workload access token
AgentIdentityContext.set_workload_access_token("your-token")

# Get workload access token
token = AgentIdentityContext.get_workload_access_token()

# Set user token
AgentIdentityContext.set_user_token("your-token")

# Set user ID
AgentIdentityContext.set_user_id("user-123")

# Set custom state
AgentIdentityContext.set_custom_state("your-state")

# Clear current thread context, needs to be actively cleared at the end of a single session, otherwise permission leakage may occur due to thread sharing
AgentIdentityContext.clear()
```

If a workload access token is set in the context, it will be prioritized when acquiring workload access tokens from the current thread context variables.

If no workload access token is set, when the SDK automatically acquires a workload access token, it will retrieve user ID/user token information from the current thread context variables, following the **user token/user ID/none** priority to acquire the workload access token.

If a custom state is set, during OAuth2 authorization, the custom state will be passed along. User applications can use the custom state to handle authorization callbacks and perform verification. It is recommended that applications use custom state for session verification to prevent malicious sharing of authorization links to obtain other users' permissions.

⚠️ **Note**: After the current workflow execution is completed, you need to actively clear the current thread context, otherwise permission leakage may occur due to thread sharing.

## Environment Variables Configuration

| Variable Name | Description | Default Value |
|---------------|-------------|---------------|
| AGENT_IDENTITY_REGION_ID | Region identifier | cn-beijing |
| AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN | Workload identity token | None |
| AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME | Workload identity name | None |
| AGENT_IDENTITY_USE_STS | Whether to use STS for resource credential acquisition | true |

## Contributing

Issues and Pull Requests are welcome to help improve this SDK.

## License

This project is licensed under the Apache-2.0 License. See the [LICENSE](../LICENSE) file for details.