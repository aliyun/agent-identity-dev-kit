package agentidentity

import (
	"context"
	"fmt"
	"os"
)

// getRegion returns the region from environment variable or defaults to cn-beijing.
func getRegion() string {
	region := os.Getenv("AGENT_IDENTITY_REGION_ID")
	if region != "" {
		return region
	}
	return "cn-beijing"
}

// getWorkloadAccessTokenMiddleware gets workload access token from context or local configuration.
// Priority: context > environment variable > local config > auto-create
func getWorkloadAccessTokenMiddleware(client *IdentityClient, ctx context.Context) (string, error) {
	token, ok := GetWorkloadAccessToken(ctx)
	if ok && token != "" {
		return token, nil
	}
	return getWorkloadAccessTokenLocal(client, ctx)
}

// getWorkloadAccessTokenLocal gets workload access token from local config or auto-creates a new workload identity.
func getWorkloadAccessTokenLocal(client *IdentityClient, ctx context.Context) (string, error) {
	workloadIdentityName := os.Getenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")
	if workloadIdentityName == "" {
		name, _ := ReadLocalConfig("workload_identity_name")
		workloadIdentityName = name
	}

	if workloadIdentityName == "" {
		var err error
		workloadIdentityName, err = client.CreateWorkloadIdentity(ctx)
		if err != nil {
			return "", fmt.Errorf("failed to create workload identity: %w", err)
		}
	}

	if err := WriteLocalConfig("workload_identity_name", workloadIdentityName); err != nil {
		return "", fmt.Errorf("failed to write workload identity name to config: %w", err)
	}

	// Extract user info from context
	userId, _ := GetUserId(ctx)
	userToken, _ := GetUserToken(ctx)

	return client.GetWorkloadAccessToken(ctx, workloadIdentityName, GetWorkloadAccessTokenOption{
		UserId:    userId,
		UserToken: userToken,
	})
}

// ===========================================================================
// Functional API — simple token-returning functions
// ===========================================================================

// GetOAuth2Token fetches an OAuth2 access token for the given provider.
// This is the recommended way to get credentials — no function wrapping needed.
func GetOAuth2Token(ctx context.Context, client *IdentityClient, providerName string, opts ...GetTokenOptions) (string, error) {
	var options GetTokenOptions
	if len(opts) > 0 {
		options = opts[0]
	}

	userId, _ := GetUserId(ctx)
	idToken, _ := GetUserToken(ctx)
	state, _ := GetCustomState(ctx)

	workloadAccessToken, err := getWorkloadAccessTokenMiddleware(client, ctx)
	if err != nil {
		return "", fmt.Errorf("failed to get workload access token: %w", err)
	}

	credentialClient, err := client.GetStsCredentialClient(ctx, workloadAccessToken, userId, idToken)
	if err != nil {
		return "", fmt.Errorf("failed to get STS credential client: %w", err)
	}

	tokenOpts := GetTokenOptions{
		ProviderName:        providerName,
		AgentIdentityToken:  workloadAccessToken,
		Scopes:              options.Scopes,
		OnAuthUrl:           options.OnAuthUrl,
		AuthFlow:            options.AuthFlow,
		CallbackUrl:         options.CallbackUrl,
		ForceAuthentication: options.ForceAuthentication,
		CustomState:         state,
		CustomParameters:    options.CustomParameters,
		Credential:          credentialClient,
	}

	return client.GetToken(ctx, tokenOpts)
}

// GetAPIKey fetches an API key for the given provider.
func GetAPIKey(ctx context.Context, client *IdentityClient, providerName string) (string, error) {
	userId, _ := GetUserId(ctx)
	idToken, _ := GetUserToken(ctx)

	workloadAccessToken, err := getWorkloadAccessTokenMiddleware(client, ctx)
	if err != nil {
		return "", fmt.Errorf("failed to get workload access token: %w", err)
	}

	credentialClient, err := client.GetStsCredentialClient(ctx, workloadAccessToken, userId, idToken)
	if err != nil {
		return "", fmt.Errorf("failed to get STS credential client: %w", err)
	}

	return client.GetApiKey(ctx, GetApiKeyOptions{
		ProviderName:       providerName,
		AgentIdentityToken: workloadAccessToken,
		Credential:         credentialClient,
	})
}

// GetSTSCredential fetches an STS credential for the current session.
func GetSTSCredential(ctx context.Context, client *IdentityClient, opts ...AssumeRoleOptions) (*STSCredential, error) {
	var options AssumeRoleOptions
	if len(opts) > 0 {
		options = opts[0]
	}

	workloadAccessToken, err := getWorkloadAccessTokenMiddleware(client, ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get workload access token: %w", err)
	}

	sessionDuration := options.DurationSeconds
	if sessionDuration == 0 {
		sessionDuration = 3600
	}

	sessionName := options.RoleSessionName
	if sessionName == "" {
		sessionName = fmt.Sprintf("AgentIdentitySessionRole-%s", generateUUID())
	}

	return client.AssumeRoleForWorkloadIdentity(ctx, AssumeRoleOptions{
		WorkloadToken:   workloadAccessToken,
		RoleSessionName: sessionName,
		DurationSeconds: sessionDuration,
		Policy:          options.Policy,
	})
}

// ===========================================================================
// Middleware wrappers (backward compatible — prefer functional API above)
// ===========================================================================

// AccessTokenFunc is the type of function that receives an access token.
type AccessTokenFunc func(ctx context.Context, accessToken string) error

// ApiKeyFunc is the type of function that receives an API key.
type ApiKeyFunc func(ctx context.Context, apiKey string) error

// StsTokenFunc is the type of function that receives an STS credential.
type StsTokenFunc func(ctx context.Context, stsCredential *STSCredential) error

// RequiresAccessTokenConfig configures RequiresAccessToken middleware.
type RequiresAccessTokenConfig struct {
	ProviderName        string
	Scopes              []string
	OnAuthUrl           func(url string)
	AuthFlow            string
	CallbackUrl         string
	ForceAuthentication bool
	CustomParameters    map[string]string
	Client              *IdentityClient
}

// RequiresApiKeyConfig configures RequiresApiKey middleware.
type RequiresApiKeyConfig struct {
	ProviderName string
	Client       *IdentityClient
}

// RequiresStsTokenConfig configures RequiresStsToken middleware.
type RequiresStsTokenConfig struct {
	SessionDuration int64
	Policy          string
	Client          *IdentityClient
}

// RequiresAccessToken is a middleware function that fetches an OAuth2 access token
// and passes it to the wrapped function.
// Deprecated: prefer GetOAuth2Token(ctx, client, providerName, opts) for simpler usage.
func RequiresAccessToken(config RequiresAccessTokenConfig, fn AccessTokenFunc) func(ctx context.Context) error {
	return func(ctx context.Context) error {
		var client *IdentityClient
		if config.Client != nil {
			client = config.Client
		} else {
			var err error
			client, err = NewIdentityClient(getRegion())
			if err != nil {
				return fmt.Errorf("failed to create identity client: %w", err)
			}
		}

		userId, _ := GetUserId(ctx)
		idToken, _ := GetUserToken(ctx)
		state, _ := GetCustomState(ctx)

		workloadAccessToken, err := getWorkloadAccessTokenMiddleware(client, ctx)
		if err != nil {
			return fmt.Errorf("failed to get workload access token: %w", err)
		}

		credentialClient, err := client.GetStsCredentialClient(ctx, workloadAccessToken, userId, idToken)
		if err != nil {
			return fmt.Errorf("failed to get STS credential client: %w", err)
		}

		token, err := client.GetToken(ctx, GetTokenOptions{
			ProviderName:        config.ProviderName,
			AgentIdentityToken:  workloadAccessToken,
			Scopes:              config.Scopes,
			OnAuthUrl:           config.OnAuthUrl,
			AuthFlow:            config.AuthFlow,
			CallbackUrl:         config.CallbackUrl,
			ForceAuthentication: config.ForceAuthentication,
			CustomState:         state,
			CustomParameters:    config.CustomParameters,
			Credential:          credentialClient,
		})
		if err != nil {
			return fmt.Errorf("failed to get access token: %w", err)
		}

		return fn(ctx, token)
	}
}

// RequiresApiKey is a middleware function that fetches an API key
// and passes it to the wrapped function.
// Deprecated: prefer GetAPIKey(ctx, client, providerName) for simpler usage.
func RequiresApiKey(config RequiresApiKeyConfig, fn ApiKeyFunc) func(ctx context.Context) error {
	return func(ctx context.Context) error {
		var client *IdentityClient
		if config.Client != nil {
			client = config.Client
		} else {
			var err error
			client, err = NewIdentityClient(getRegion())
			if err != nil {
				return fmt.Errorf("failed to create identity client: %w", err)
			}
		}

		userId, _ := GetUserId(ctx)
		idToken, _ := GetUserToken(ctx)

		workloadAccessToken, err := getWorkloadAccessTokenMiddleware(client, ctx)
		if err != nil {
			return fmt.Errorf("failed to get workload access token: %w", err)
		}

		credentialClient, err := client.GetStsCredentialClient(ctx, workloadAccessToken, userId, idToken)
		if err != nil {
			return fmt.Errorf("failed to get STS credential client: %w", err)
		}

		apiKey, err := client.GetApiKey(ctx, GetApiKeyOptions{
			ProviderName:       config.ProviderName,
			AgentIdentityToken: workloadAccessToken,
			Credential:         credentialClient,
		})
		if err != nil {
			return fmt.Errorf("failed to get API key: %w", err)
		}

		return fn(ctx, apiKey)
	}
}

// RequiresStsToken is a middleware function that fetches an STS credential
// and passes it to the wrapped function.
// Deprecated: prefer GetSTSCredential(ctx, client, opts) for simpler usage.
func RequiresStsToken(config RequiresStsTokenConfig, fn StsTokenFunc) func(ctx context.Context) error {
	return func(ctx context.Context) error {
		var client *IdentityClient
		if config.Client != nil {
			client = config.Client
		} else {
			var err error
			client, err = NewIdentityClient(getRegion())
			if err != nil {
				return fmt.Errorf("failed to create identity client: %w", err)
			}
		}

		workloadAccessToken, err := getWorkloadAccessTokenMiddleware(client, ctx)
		if err != nil {
			return fmt.Errorf("failed to get workload access token: %w", err)
		}

		sessionDuration := config.SessionDuration
		if sessionDuration == 0 {
			sessionDuration = 3600
		}

		stsCredential, err := client.AssumeRoleForWorkloadIdentity(ctx, AssumeRoleOptions{
			WorkloadToken:   workloadAccessToken,
			RoleSessionName: fmt.Sprintf("AgentIdentitySessionRole-%s", generateUUID()),
			DurationSeconds: sessionDuration,
			Policy:          config.Policy,
		})
		if err != nil {
			return fmt.Errorf("failed to get STS credential: %w", err)
		}

		return fn(ctx, stsCredential)
	}
}
