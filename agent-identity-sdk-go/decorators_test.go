package agentidentity

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"testing"
)

// ============================================================================
// decorators.go tests
// ============================================================================

func TestGetRegion_Default(t *testing.T) {
	os.Unsetenv("AGENT_IDENTITY_REGION_ID")
	region := getRegion()
	if region != "cn-beijing" {
		t.Fatalf("expected cn-beijing, got %s", region)
	}
}

func TestGetRegion_FromEnv(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_REGION_ID", "cn-shanghai")
	defer os.Unsetenv("AGENT_IDENTITY_REGION_ID")
	region := getRegion()
	if region != "cn-shanghai" {
		t.Fatalf("expected cn-shanghai, got %s", region)
	}
}

func TestGetOAuth2Token_FromContext(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	uniqueToken := "wl-token-ctx-" + generateUUID()
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
		} else {
			w.Write([]byte(`{"AccessToken":"oauth2-result"}`))
		}
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), uniqueToken)

	token, err := GetOAuth2Token(ctx, client, "my-provider", GetTokenOptions{
		Scopes: []string{"scope1"},
	})
	if err != nil {
		t.Fatalf("GetOAuth2Token failed: %v", err)
	}
	if token != "oauth2-result" {
		t.Fatalf("expected oauth2-result, got %s", token)
	}
}

func TestGetOAuth2Token_WithAllContextValues(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	uniqueToken := "wl-token-allctx-" + generateUUID()
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
		} else {
			w.Write([]byte(`{"AccessToken":"full-context-token"}`))
		}
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), uniqueToken)
	ctx = WithUserId(ctx, "user-456")
	ctx = WithUserToken(ctx, "jwt-user")
	ctx = WithCustomState(ctx, "custom-state-value")

	token, err := GetOAuth2Token(ctx, client, "my-provider")
	if err != nil {
		t.Fatalf("GetOAuth2Token failed: %v", err)
	}
	if token != "full-context-token" {
		t.Fatalf("expected full-context-token, got %s", token)
	}
}

func TestGetOAuth2Token_WithOptions(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	uniqueToken := "wl-token-opts-" + generateUUID()
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
		} else {
			w.Write([]byte(`{"AccessToken":"optioned-token"}`))
		}
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), uniqueToken)
	var onAuthUrlCalled bool
	token, err := GetOAuth2Token(ctx, client, "my-provider", GetTokenOptions{
		Scopes:              []string{"read", "write"},
		AuthFlow:            "authorization_code",
		CallbackUrl:         "https://cb.example.com",
		ForceAuthentication: true,
		CustomParameters:    map[string]string{"key": "val"},
		OnAuthUrl: func(url string) {
			onAuthUrlCalled = true
		},
	})
	if err != nil {
		t.Fatalf("GetOAuth2Token failed: %v", err)
	}
	if token != "optioned-token" {
		t.Fatalf("expected optioned-token, got %s", token)
	}
	if onAuthUrlCalled {
		t.Fatal("OnAuthUrl should not be called for direct token response")
	}
}

func TestGetAPIKey_Functional(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	uniqueToken := "wl-token-apikey-" + generateUUID()
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
		} else {
			w.Write([]byte(`{"APIKey":"func-api-key"}`))
		}
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), uniqueToken)
	ctx = WithUserId(ctx, "user-789")
	ctx = WithUserToken(ctx, "jwt-func")

	apiKey, err := GetAPIKey(ctx, client, "my-provider")
	if err != nil {
		t.Fatalf("GetAPIKey failed: %v", err)
	}
	if apiKey != "func-api-key" {
		t.Fatalf("expected func-api-key, got %s", apiKey)
	}
}

func TestGetSTSCredential_Functional(t *testing.T) {
	uniqueToken := "wl-token-sts-" + generateUUID()
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-func-ak","AccessKeySecret":"STS-func-sk","SecurityToken":"STS-func-token","Expiration":"2099-01-01T00:00:00Z"}}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), uniqueToken)

	cred, err := GetSTSCredential(ctx, client)
	if err != nil {
		t.Fatalf("GetSTSCredential failed: %v", err)
	}
	if cred.AccessKeyId != "STS-func-ak" {
		t.Fatalf("expected STS-func-ak, got %s", cred.AccessKeyId)
	}

	cred2, err := GetSTSCredential(ctx, client, AssumeRoleOptions{
		RoleSessionName: "test-session",
		DurationSeconds: 1800,
		Policy:          `{"Version":"1"}`,
	})
	if err != nil {
		t.Fatalf("GetSTSCredential with options failed: %v", err)
	}
	if cred2.AccessKeyId != "STS-func-ak" {
		t.Fatalf("expected STS-func-ak, got %s", cred2.AccessKeyId)
	}
}

func TestGetWorkloadAccessTokenMiddleware_FromContext(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadAccessToken":"middleware-wl-token"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), "ctx-wl-token")
	token, err := getWorkloadAccessTokenMiddleware(client, ctx)
	if err != nil {
		t.Fatalf("getWorkloadAccessTokenMiddleware failed: %v", err)
	}
	if token != "ctx-wl-token" {
		t.Fatalf("expected ctx-wl-token, got %s", token)
	}
}

func TestGetWorkloadAccessTokenMiddleware_EmptyTokenInContext(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadAccessToken":"fallback-wl-token"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	os.Setenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME", "existing-workload")
	defer os.Unsetenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")

	ctx := WithWorkloadAccessToken(context.Background(), "")
	token, err := getWorkloadAccessTokenMiddleware(client, ctx)
	if err != nil {
		t.Fatalf("getWorkloadAccessTokenMiddleware failed: %v", err)
	}
	if token != "fallback-wl-token" {
		t.Fatalf("expected fallback-wl-token, got %s", token)
	}
}

func TestGetWorkloadAccessTokenMiddleware_FromEnv(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadAccessToken":"env-middleware-token"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	os.Setenv("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN", "env-wl-token-mw")
	defer os.Unsetenv("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN")

	ctx := context.Background()
	token, err := getWorkloadAccessTokenMiddleware(client, ctx)
	if err != nil {
		t.Fatalf("getWorkloadAccessTokenMiddleware failed: %v", err)
	}
	if token != "env-wl-token-mw" {
		t.Fatalf("expected env-wl-token-mw, got %s", token)
	}
}

func TestGetWorkloadAccessTokenLocal_FromEnv(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadAccessToken":"local-wl-token"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	os.Setenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME", "env-workload")
	defer os.Unsetenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")

	ctx := context.Background()
	token, err := getWorkloadAccessTokenLocal(client, ctx)
	if err != nil {
		t.Fatalf("getWorkloadAccessTokenLocal failed: %v", err)
	}
	if token != "local-wl-token" {
		t.Fatalf("expected local-wl-token, got %s", token)
	}
}

func TestGetWorkloadAccessTokenLocal_FromLocalConfig(t *testing.T) {
	dir := t.TempDir()
	oldCwd, _ := os.Getwd()
	os.Chdir(dir)
	defer os.Chdir(oldCwd)

	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadAccessToken":"config-wl-token"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	WriteLocalConfig("workload_identity_name", "config-workload")

	os.Unsetenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")
	ctx := context.Background()
	token, err := getWorkloadAccessTokenLocal(client, ctx)
	if err != nil {
		t.Fatalf("getWorkloadAccessTokenLocal failed: %v", err)
	}
	if token != "config-wl-token" {
		t.Fatalf("expected config-wl-token, got %s", token)
	}
	os.Remove(".config.json")
}

func TestGetWorkloadAccessTokenLocal_AutoCreate(t *testing.T) {
	dir := t.TempDir()
	oldCwd, _ := os.Getwd()
	os.Chdir(dir)
	defer os.Chdir(oldCwd)

	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		t.Logf("Request %d: %s %s", callCount, r.Method, r.URL.Path)
		if callCount == 1 {
			w.Write([]byte(`{"WorkloadIdentity":{"WorkloadIdentityName":"auto-created-workload"}}`))
		} else {
			w.Write([]byte(`{"WorkloadAccessToken":"auto-wl-token"}`))
		}
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	os.Unsetenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")

	ctx := context.Background()
	token, err := getWorkloadAccessTokenLocal(client, ctx)
	if err != nil {
		t.Fatalf("getWorkloadAccessTokenLocal failed: %v", err)
	}
	if token != "auto-wl-token" {
		t.Fatalf("expected auto-wl-token, got %s", token)
	}
}

func TestRequiresAccessToken_CreatesClient(t *testing.T) {
	fn := func(ctx context.Context, token string) error {
		return nil
	}
	wrapped := RequiresAccessToken(RequiresAccessTokenConfig{
		ProviderName: "test-provider",
	}, fn)
	if wrapped == nil {
		t.Fatal("RequiresAccessToken returned nil")
	}
}

func TestRequiresApiKey_CreatesClient(t *testing.T) {
	fn := func(ctx context.Context, apiKey string) error {
		return nil
	}
	wrapped := RequiresApiKey(RequiresApiKeyConfig{
		ProviderName: "test-provider",
	}, fn)
	if wrapped == nil {
		t.Fatal("RequiresApiKey returned nil")
	}
}

func TestRequiresStsToken_CreatesClient(t *testing.T) {
	fn := func(ctx context.Context, cred *STSCredential) error {
		return nil
	}
	wrapped := RequiresStsToken(RequiresStsTokenConfig{}, fn)
	if wrapped == nil {
		t.Fatal("RequiresStsToken returned nil")
	}
}

func TestRequiresStsToken_WithConfig(t *testing.T) {
	fn := func(ctx context.Context, cred *STSCredential) error {
		if cred.AccessKeyId != "test-ak" {
			return nil
		}
		return nil
	}
	wrapped := RequiresStsToken(RequiresStsTokenConfig{
		SessionDuration: 7200,
		Policy:          `{"Version":"1"}`,
	}, fn)
	if wrapped == nil {
		t.Fatal("RequiresStsToken returned nil")
	}
}

func TestRequiresAccessToken_MockEndpoints(t *testing.T) {
	setupMockCredentials()
	defer cleanupMockCredentials()

	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"WorkloadAccessToken":"wl-token-req"}`))
		} else if callCount == 2 {
			w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
		} else {
			w.Write([]byte(`{"AccessToken":"middleware-token"}`))
		}
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatal(err)
	}

	called := false
	var receivedToken string
	fn := func(ctx context.Context, token string) error {
		called = true
		receivedToken = token
		return nil
	}

	os.Setenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME", "test-workload")
	defer os.Unsetenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")

	wrapped := RequiresAccessToken(RequiresAccessTokenConfig{
		ProviderName: "test-provider",
		Client:       client,
	}, fn)

	err = wrapped(context.Background())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !called {
		t.Fatal("inner function was not called")
	}
	if receivedToken != "middleware-token" {
		t.Fatalf("expected middleware-token, got %s", receivedToken)
	}
}

func TestRequiresApiKey_MockEndpoints(t *testing.T) {
	setupMockCredentials()
	defer cleanupMockCredentials()

	uniqueToken := "wl-token-apikey-" + generateUUID()
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(fmt.Sprintf(`{"WorkloadAccessToken":"%s"}`, uniqueToken)))
		} else if callCount == 2 {
			w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
		} else {
			w.Write([]byte(`{"APIKey":"middleware-api-key"}`))
		}
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatal(err)
	}

	os.Setenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME", "test-workload")
	defer os.Unsetenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")

	called := false
	var receivedKey string
	fn := func(ctx context.Context, key string) error {
		called = true
		receivedKey = key
		return nil
	}

	wrapped := RequiresApiKey(RequiresApiKeyConfig{
		ProviderName: "test-provider",
		Client:       client,
	}, fn)

	err = wrapped(context.Background())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !called {
		t.Fatal("inner function was not called")
	}
	if receivedKey != "middleware-api-key" {
		t.Fatalf("expected middleware-api-key, got %s", receivedKey)
	}
}

func TestRequiresStsToken_MockEndpoints(t *testing.T) {
	setupMockCredentials()
	defer cleanupMockCredentials()

	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"WorkloadAccessToken":"wl-token-req"}`))
		} else {
			w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-mid-ak","AccessKeySecret":"STS-mid-sk","SecurityToken":"STS-mid-token","Expiration":"2099-01-01T00:00:00Z"}}`))
		}
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatal(err)
	}

	os.Setenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME", "test-workload")
	defer os.Unsetenv("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")

	called := false
	var receivedCred *STSCredential
	fn := func(ctx context.Context, cred *STSCredential) error {
		called = true
		receivedCred = cred
		return nil
	}

	wrapped := RequiresStsToken(RequiresStsTokenConfig{
		SessionDuration: 1800,
		Policy:          `{"Version":"1"}`,
		Client:          client,
	}, fn)

	err = wrapped(context.Background())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !called {
		t.Fatal("inner function was not called")
	}
	if receivedCred.AccessKeyId != "STS-mid-ak" {
		t.Fatalf("expected STS-mid-ak, got %s", receivedCred.AccessKeyId)
	}
}

func TestGetOAuth2Token_ErrorPath(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	uniqueToken := "wl-token-oauth2err-" + generateUUID()
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"message":"error"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), uniqueToken)
	_, err = GetOAuth2Token(ctx, client, "my-provider")
	if err == nil {
		t.Fatal("expected error from failed OAuth2 flow")
	}
}

func TestGetAPIKey_ErrorPath(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	uniqueToken := "wl-token-apikeyerr-" + generateUUID()
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"message":"error"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), uniqueToken)
	_, err = GetAPIKey(ctx, client, "my-provider")
	if err == nil {
		t.Fatal("expected error from failed API key flow")
	}
}

func TestGetSTSCredential_ErrorPath(t *testing.T) {
	uniqueToken := "wl-token-stserr-" + generateUUID()
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"message":"error"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), uniqueToken)
	_, err = GetSTSCredential(ctx, client)
	if err == nil {
		t.Fatal("expected error from failed STS credential flow")
	}
}

func TestGetOAuth2Token_WorkloadTokenError(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"message":"error"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := context.Background()
	_, err = GetOAuth2Token(ctx, client, "my-provider")
	if err == nil {
		t.Fatal("expected error from failed OAuth2 flow")
	}
}

func TestGetAPIKey_WorkloadTokenError(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"message":"error"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := context.Background()
	_, err = GetAPIKey(ctx, client, "my-provider")
	if err == nil {
		t.Fatal("expected error from failed API key flow")
	}
}

func TestGetSTSCredential_WorkloadTokenError(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"message":"error"}`))
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := context.Background()
	_, err = GetSTSCredential(ctx, client)
	if err == nil {
		t.Fatal("expected error from failed STS credential flow")
	}
}

func TestGetOAuth2Token_WithAuthURLNoCallback(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
		} else if callCount == 2 {
			w.Write([]byte(`{"AuthorizationURL":"https://auth.example.com","SessionURI":"https://session-uri"}`))
		} else {
			w.Write([]byte(`{"AccessToken":"no-callback-token"}`))
		}
	}))
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := WithWorkloadAccessToken(context.Background(), "wl-token-nocb-"+generateUUID())
	token, err := GetOAuth2Token(ctx, client, "my-provider")
	if err != nil {
		t.Fatalf("GetOAuth2Token failed: %v", err)
	}
	if token != "no-callback-token" {
		t.Fatalf("expected no-callback-token, got %s", token)
	}
}

func TestRequiresAccessToken_CalledWithoutCredentials(t *testing.T) {
	called := false
	fn := func(ctx context.Context, token string) error {
		called = true
		return nil
	}

	wrapped := RequiresAccessToken(RequiresAccessTokenConfig{
		ProviderName: "test-provider",
	}, fn)

	err := wrapped(context.Background())
	if err != nil {
		t.Logf("Expected error without real credentials: %v", err)
	}
	t.Logf("Inner function called: %v", called)
}

func TestRequiresApiKey_CalledWithoutCredentials(t *testing.T) {
	called := false
	fn := func(ctx context.Context, apiKey string) error {
		called = true
		return nil
	}

	wrapped := RequiresApiKey(RequiresApiKeyConfig{
		ProviderName: "test-provider",
	}, fn)

	err := wrapped(context.Background())
	if err != nil {
		t.Logf("Expected error: %v", err)
	}
	t.Logf("Inner function called: %v", called)
}

func TestRequiresStsToken_CalledWithoutCredentials(t *testing.T) {
	called := false
	fn := func(ctx context.Context, cred *STSCredential) error {
		called = true
		return nil
	}

	wrapped := RequiresStsToken(RequiresStsTokenConfig{
		SessionDuration: 7200,
	}, fn)

	err := wrapped(context.Background())
	if err != nil {
		t.Logf("Expected error: %v", err)
	}
	t.Logf("Inner function called: %v", called)
}
