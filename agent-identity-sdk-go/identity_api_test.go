package agentidentity

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"testing"
	"time"

	dataclient "github.com/alibabacloud-go/agentidentitydata-20251127/client"
)

// ============================================================================
// identity_api.go tests — HTTP server mocking
// ============================================================================

func TestGetWorkloadAccessToken_ForJWT(t *testing.T) {
	server := newMockServer(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadAccessToken":"jwt-wl-token"}`))
	})
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	token, err := client.GetWorkloadAccessToken(context.Background(), "my-workload", GetWorkloadAccessTokenOption{
		UserToken: "user-jwt",
	})
	if err != nil {
		t.Fatalf("GetWorkloadAccessToken failed: %v", err)
	}
	if token != "jwt-wl-token" {
		t.Fatalf("expected jwt-wl-token, got %s", token)
	}
}

func TestGetWorkloadAccessToken_ForUserId(t *testing.T) {
	server := newMockServer(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadAccessToken":"user-wl-token"}`))
	})
	defer server.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	token, err := client.GetWorkloadAccessToken(context.Background(), "my-workload", GetWorkloadAccessTokenOption{
		UserId: "user-123",
	})
	if err != nil {
		t.Fatalf("GetWorkloadAccessToken failed: %v", err)
	}
	if token != "user-wl-token" {
		t.Fatalf("expected user-wl-token, got %s", token)
	}
}

func TestGetWorkloadAccessToken_NoUser(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadAccessToken":"generic-wl-token"}`))
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

	token, err := client.GetWorkloadAccessToken(context.Background(), "my-workload")
	if err != nil {
		t.Fatalf("GetWorkloadAccessToken failed: %v", err)
	}
	if token != "generic-wl-token" {
		t.Fatalf("expected generic-wl-token, got %s", token)
	}
}

func TestGetWorkloadAccessToken_Error(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"message":"internal error"}`))
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

	_, err = client.GetWorkloadAccessToken(context.Background(), "my-workload")
	if err == nil {
		t.Fatal("expected error from server error")
	}
}

func TestGetWorkloadAccessToken_ForUserToken(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadAccessToken":"user-token-wl"}`))
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

	token, err := client.GetWorkloadAccessToken(context.Background(), "my-workload", GetWorkloadAccessTokenOption{
		UserToken: "user-jwt-token",
	})
	if err != nil {
		t.Fatalf("GetWorkloadAccessToken failed: %v", err)
	}
	if token != "user-token-wl" {
		t.Fatalf("expected user-token-wl, got %s", token)
	}
}

func TestGetWorkloadAccessToken_ForJWT_Error(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte(`{"message":"bad request"}`))
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

	_, err = client.GetWorkloadAccessToken(context.Background(), "my-workload", GetWorkloadAccessTokenOption{
		UserToken: "invalid-jwt",
	})
	if err == nil {
		t.Fatal("expected error from bad JWT")
	}
}

func TestGetWorkloadAccessToken_ForUserId_Error(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		w.Write([]byte(`{"message":"not found"}`))
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

	_, err = client.GetWorkloadAccessToken(context.Background(), "nonexistent-workload", GetWorkloadAccessTokenOption{
		UserId: "user-123",
	})
	if err == nil {
		t.Fatal("expected error from not found")
	}
}

func TestConfirmUserAuth_WithUserId(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{}`))
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

	err = client.ConfirmUserAuth(context.Background(), "https://session-uri", ConfirmUserAuthOption{
		UserId: "user-123",
	})
	if err != nil {
		t.Fatalf("ConfirmUserAuth failed: %v", err)
	}
}

func TestConfirmUserAuth_WithoutUserId(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{}`))
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

	err = client.ConfirmUserAuth(context.Background(), "https://session-uri")
	if err != nil {
		t.Fatalf("ConfirmUserAuth failed: %v", err)
	}
}

func TestConfirmUserAuth_WithUserToken(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{}`))
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

	err = client.ConfirmUserAuth(context.Background(), "https://session-uri", ConfirmUserAuthOption{
		UserToken: "jwt-token",
	})
	if err != nil {
		t.Fatalf("ConfirmUserAuth failed: %v", err)
	}
}

func TestConfirmUserAuth_Error(t *testing.T) {
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

	err = client.ConfirmUserAuth(context.Background(), "https://session-uri")
	if err == nil {
		t.Fatal("expected error from server error")
	}
}

func TestGetToken_Direct(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"AccessToken":"oauth2-access-token"}`))
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

	token, err := client.GetToken(context.Background(), GetTokenOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
	})
	if err != nil {
		t.Fatalf("GetToken failed: %v", err)
	}
	if token != "oauth2-access-token" {
		t.Fatalf("expected oauth2-access-token, got %s", token)
	}
}

func TestGetToken_WithAuthUrlAndPolling(t *testing.T) {
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"AuthorizationURL":"https://auth.example.com/authorize","SessionURI":"https://session-uri.example.com"}`))
		} else {
			w.Write([]byte(`{"AccessToken":"polled-oauth2-token"}`))
		}
	}))
	defer server.Close()

	var authURLReceived string
	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(server.endpoint),
		WithControlApiEndpoint(server.endpoint),
		WithProtocol("HTTP"),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	token, err := client.GetToken(context.Background(), GetTokenOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
		OnAuthUrl: func(url string) {
			authURLReceived = url
		},
	})
	if err != nil {
		t.Fatalf("GetToken failed: %v", err)
	}
	if authURLReceived != "https://auth.example.com/authorize" {
		t.Fatalf("expected auth URL callback, got %s", authURLReceived)
	}
	if token != "polled-oauth2-token" {
		t.Fatalf("expected polled-oauth2-token, got %s", token)
	}
}

func TestGetToken_WithCustomParameters(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"AccessToken":"custom-params-token"}`))
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

	token, err := client.GetToken(context.Background(), GetTokenOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
		CustomParameters:   map[string]string{"param1": "value1", "param2": "value2"},
	})
	if err != nil {
		t.Fatalf("GetToken with CustomParameters failed: %v", err)
	}
	if token != "custom-params-token" {
		t.Fatalf("expected custom-params-token, got %s", token)
	}
}

func TestGetToken_ForceAuth(t *testing.T) {
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"AuthorizationURL":"https://auth.example.com/force","SessionURI":"https://session-uri"}`))
		} else {
			w.Write([]byte(`{"AccessToken":"force-auth-token"}`))
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

	token, err := client.GetToken(context.Background(), GetTokenOptions{
		ProviderName:        "my-provider",
		AgentIdentityToken:  "wl-token",
		ForceAuthentication: true,
	})
	if err != nil {
		t.Fatalf("GetToken with ForceAuth failed: %v", err)
	}
	if token != "force-auth-token" {
		t.Fatalf("expected force-auth-token, got %s", token)
	}
}

func TestGetToken_NeitherTokenNorAuthUrl(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{}`))
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

	_, err = client.GetToken(context.Background(), GetTokenOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
	})
	if err == nil {
		t.Fatal("expected error when neither token nor auth URL returned")
	}
}

func TestGetToken_ContextCancellation(t *testing.T) {
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount == 1 {
			w.Write([]byte(`{"AuthorizationURL":"https://auth.example.com","SessionURI":"https://session-uri"}`))
		} else {
			time.Sleep(100 * time.Millisecond)
			w.Write([]byte(`{}`))
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

	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	_, err = client.GetToken(ctx, GetTokenOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
		OnAuthUrl:          func(url string) {},
	})
	if err == nil {
		t.Fatal("expected error from context cancellation")
	}
}

func TestGetToken_MaxRetriesExhausted(t *testing.T) {
	listener := newMockNetListener()
	endpoint := listener.Addr().String()
	listener.Close()

	client, err := NewIdentityClient("cn-beijing",
		WithDataApiEndpoint(endpoint),
		WithControlApiEndpoint(endpoint),
	)
	if err != nil {
		t.Fatalf("NewIdentityClient failed: %v", err)
	}

	ctx := context.Background()
	_, err = client.pollForOAuth2Token(ctx, client.dataClient,
		&dataclient.GetResourceOAuth2TokenRequest{},
		2, 10*time.Millisecond)
	if err == nil {
		t.Fatal("expected error from max retries exhausted")
	}
}

func TestGetToken_WithScopesAndCallbackUrl(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"AccessToken":"scoped-token"}`))
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

	token, err := client.GetToken(context.Background(), GetTokenOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
		Scopes:             []string{"scope1", "scope2"},
		CallbackUrl:        "https://callback.example.com",
		AuthFlow:           "authorization_code",
		CustomState:        "state-123",
	})
	if err != nil {
		t.Fatalf("GetToken failed: %v", err)
	}
	if token != "scoped-token" {
		t.Fatalf("expected scoped-token, got %s", token)
	}
}

func TestGetToken_ErrorFromInitialCall(t *testing.T) {
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

	_, err = client.GetToken(context.Background(), GetTokenOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
	})
	if err == nil {
		t.Fatal("expected error from failed API call")
	}
}

func TestGetToken_WithSTSClient(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"AccessToken":"sts-token-result"}`))
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

	token, err := client.GetToken(context.Background(), GetTokenOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
	})
	if err != nil {
		t.Fatalf("GetToken failed: %v", err)
	}
	if token != "sts-token-result" {
		t.Fatalf("expected sts-token-result, got %s", token)
	}
}

func TestGetApiKey_Direct(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"APIKey":"my-api-key-123"}`))
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

	apiKey, err := client.GetApiKey(context.Background(), GetApiKeyOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
	})
	if err != nil {
		t.Fatalf("GetApiKey failed: %v", err)
	}
	if apiKey != "my-api-key-123" {
		t.Fatalf("expected my-api-key-123, got %s", apiKey)
	}
}

func TestGetApiKey_EmptyResponse(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{}`))
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

	_, err = client.GetApiKey(context.Background(), GetApiKeyOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
	})
	if err == nil {
		t.Fatal("expected error for empty API key response")
	}
}

func TestGetApiKey_WithSTSClient(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"APIKey":"sts-api-key"}`))
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

	apiKey, err := client.GetApiKey(context.Background(), GetApiKeyOptions{
		ProviderName:       "my-provider",
		AgentIdentityToken: "wl-token",
	})
	if err != nil {
		t.Fatalf("GetApiKey failed: %v", err)
	}
	if apiKey != "sts-api-key" {
		t.Fatalf("expected sts-api-key, got %s", apiKey)
	}
}

func TestAssumeRoleForWorkloadIdentity(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
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

	sts, err := client.AssumeRoleForWorkloadIdentity(context.Background(), AssumeRoleOptions{
		WorkloadToken:   "wl-token",
		RoleSessionName: "test-session",
	})
	if err != nil {
		t.Fatalf("AssumeRoleForWorkloadIdentity failed: %v", err)
	}
	if sts.AccessKeyId != "STS-ak" {
		t.Fatalf("expected STS-ak, got %s", sts.AccessKeyId)
	}
	if sts.AccessKeySecret != "STS-sk" {
		t.Fatalf("expected STS-sk, got %s", sts.AccessKeySecret)
	}
	if sts.SecurityToken != "STS-token" {
		t.Fatalf("expected STS-token, got %s", sts.SecurityToken)
	}
	if sts.Expiration != "2099-01-01T00:00:00Z" {
		t.Fatalf("expected 2099-01-01T00:00:00Z, got %s", sts.Expiration)
	}
}

func TestAssumeRoleForWorkloadIdentity_WithPolicy(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak-policy","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
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

	sts, err := client.AssumeRoleForWorkloadIdentity(context.Background(), AssumeRoleOptions{
		WorkloadToken:   "wl-token",
		RoleSessionName: "test-session",
		DurationSeconds: 1800,
		Policy:          `{"Version":"1"}`,
	})
	if err != nil {
		t.Fatalf("AssumeRoleForWorkloadIdentity with policy failed: %v", err)
	}
	if sts.AccessKeyId != "STS-ak-policy" {
		t.Fatalf("expected STS-ak-policy, got %s", sts.AccessKeyId)
	}
}

func TestAssumeRoleForWorkloadIdentity_DefaultDuration(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
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

	_, err = client.AssumeRoleForWorkloadIdentity(context.Background(), AssumeRoleOptions{
		WorkloadToken:   "wl-token",
		RoleSessionName: "test-session",
	})
	if err != nil {
		t.Fatalf("AssumeRoleForWorkloadIdentity failed: %v", err)
	}
}

func TestAssumeRoleForWorkloadIdentity_Error(t *testing.T) {
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

	_, err = client.AssumeRoleForWorkloadIdentity(context.Background(), AssumeRoleOptions{
		WorkloadToken:   "wl-token",
		RoleSessionName: "test-session",
	})
	if err == nil {
		t.Fatal("expected error from server error")
	}
}

func TestGetStsCredentialClient_CacheHit(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak-cached","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
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
	cred1, err := client.GetStsCredentialClient(ctx, "wl-token", "user1", "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient failed: %v", err)
	}
	if cred1 == nil {
		t.Fatal("expected credential, got nil")
	}

	cred2, err := client.GetStsCredentialClient(ctx, "wl-token", "user1", "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient (cached) failed: %v", err)
	}
	if cred2 == nil {
		t.Fatal("expected cached credential, got nil")
	}
}

func TestGetStsCredentialClient_CacheMiss(t *testing.T) {
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"Credentials":{"AccessKeyId":"STS-ak-`+fmt.Sprintf("%d", callCount)+`","AccessKeySecret":"STS-sk","SecurityToken":"STS-token","Expiration":"2099-01-01T00:00:00Z"}}`))
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
	cred1, err := client.GetStsCredentialClient(ctx, "wl-token-miss", "user1", "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient failed: %v", err)
	}
	if cred1 == nil {
		t.Fatal("expected credential")
	}

	cred2, err := client.GetStsCredentialClient(ctx, "wl-token-miss", "user2", "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient (miss) failed: %v", err)
	}
	if cred2 == nil {
		t.Fatal("expected credential")
	}
}

func TestConvertToCredential(t *testing.T) {
	stsCred := &STSCredential{
		AccessKeyId:     "test-ak",
		AccessKeySecret: "test-sk",
		SecurityToken:   "test-token",
	}

	cred, err := convertToCredential(stsCred)
	if err != nil {
		t.Fatalf("convertToCredential failed: %v", err)
	}
	if cred == nil {
		t.Fatal("expected credential, got nil")
	}
}

func TestCreateWorkloadIdentity(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadIdentity":{"WorkloadIdentityName":"my-workload"}}`))
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

	name, err := client.CreateWorkloadIdentity(context.Background(), CreateWorkloadIdentityOption{
		WorkloadName: "my-workload",
	})
	if err != nil {
		t.Fatalf("CreateWorkloadIdentity failed: %v", err)
	}
	if name != "my-workload" {
		t.Fatalf("expected my-workload, got %s", name)
	}
}

func TestCreateWorkloadIdentity_AutoName(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadIdentity":{"WorkloadIdentityName":"auto-workload"}}`))
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

	name, err := client.CreateWorkloadIdentity(context.Background())
	if err != nil {
		t.Fatalf("CreateWorkloadIdentity failed: %v", err)
	}
	if name != "auto-workload" {
		t.Fatalf("expected auto-workload, got %s", name)
	}
}

func TestCreateWorkloadIdentity_WithFullOptions(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"WorkloadIdentity":{"WorkloadIdentityName":"full-workload"}}`))
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

	name, err := client.CreateWorkloadIdentity(context.Background(), CreateWorkloadIdentityOption{
		WorkloadName:                   "full-workload",
		RoleArn:                        "acs:ram::123456:role/TestRole",
		AllowedResourceOAuth2ReturnUrls: []string{"https://callback.example.com"},
		IdentityProviderName:           "my-provider",
	})
	if err != nil {
		t.Fatalf("CreateWorkloadIdentity failed: %v", err)
	}
	if name != "full-workload" {
		t.Fatalf("expected full-workload, got %s", name)
	}
}

func TestCreateWorkloadIdentity_Error(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"message":"internal error"}`))
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

	_, err = client.CreateWorkloadIdentity(context.Background(), CreateWorkloadIdentityOption{
		WorkloadName: "error-workload",
	})
	if err == nil {
		t.Fatal("expected error from server error")
	}
}

// ============================================================================
// PollForOAuth2Token tests
// ============================================================================

func TestPollForOAuth2Token_SuccessOnFirstRetry(t *testing.T) {
	callCount := 0
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		w.Header().Set("Content-Type", "application/json")
		if callCount < 3 {
			w.Write([]byte(`{}`))
		} else {
			w.Write([]byte(`{"AccessToken":"delayed-token"}`))
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

	ctx := context.Background()
	token, err := client.pollForOAuth2Token(ctx, client.dataClient,
		&dataclient.GetResourceOAuth2TokenRequest{},
		5, 50*time.Millisecond)
	if err != nil {
		t.Fatalf("pollForOAuth2Token failed: %v", err)
	}
	if token != "delayed-token" {
		t.Fatalf("expected delayed-token, got %s", token)
	}
}

func TestPollForOAuth2Token_ErrorThenSuccess(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"AccessToken":"error-then-success"}`))
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
	token, err := client.pollForOAuth2Token(ctx, client.dataClient,
		&dataclient.GetResourceOAuth2TokenRequest{},
		3, 10*time.Millisecond)
	if err != nil {
		t.Fatalf("pollForOAuth2Token failed: %v", err)
	}
	if token != "error-then-success" {
		t.Fatalf("expected error-then-success, got %s", token)
	}
}

func TestPollForOAuth2Token_ContextCancelMidPoll(t *testing.T) {
	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{}`))
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

	ctx, cancel := context.WithCancel(context.Background())
	go func() {
		time.Sleep(30 * time.Millisecond)
		cancel()
	}()

	_, err = client.pollForOAuth2Token(ctx, client.dataClient,
		&dataclient.GetResourceOAuth2TokenRequest{},
		10, 10*time.Millisecond)
	if err == nil {
		t.Fatal("expected error from context cancellation")
	}
}

// STS client path tests (need mock credentials)
func TestGetToken_STSClientPath(t *testing.T) {
	setupMockCredentials()
	defer cleanupMockCredentials()

	os.Setenv("AGENT_IDENTITY_USE_STS", "true")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"AccessToken":"sts-oauth2-token"}`))
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

	token, err := client.GetToken(context.Background(), GetTokenOptions{
		ProviderName: "test-provider",
		Credential:   createMockCredential(),
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if token != "sts-oauth2-token" {
		t.Fatalf("expected sts-oauth2-token, got %s", token)
	}
}

func TestGetApiKey_STSClientPath(t *testing.T) {
	setupMockCredentials()
	defer cleanupMockCredentials()

	os.Setenv("AGENT_IDENTITY_USE_STS", "true")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	server := newMockServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"APIKey":"sts-api-key"}`))
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

	key, err := client.GetApiKey(context.Background(), GetApiKeyOptions{
		ProviderName: "test-provider",
		Credential:   createMockCredential(),
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if key != "sts-api-key" {
		t.Fatalf("expected sts-api-key, got %s", key)
	}
}
