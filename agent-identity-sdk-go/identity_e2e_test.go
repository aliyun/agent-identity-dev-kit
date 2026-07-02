//go:build e2e

package agentidentity

import (
	"context"
	"fmt"
	"os"
	"regexp"
	"testing"
)

// ---------------------------------------------------------------------------
// Shared state – initialised in TestMain
// ---------------------------------------------------------------------------
var (
	e2eClient              *IdentityClient
	e2eWorkloadName        string
	e2eWorkloadAccessToken string
	e2eProviderName        string
)

func TestMain(m *testing.M) {
	ak := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
	sk := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
	e2eProviderName = os.Getenv("AGENT_IDENTITY_E2E_PROVIDER_NAME")
	region := os.Getenv("AGENT_IDENTITY_REGION_ID")
	if region == "" {
		region = "cn-beijing"
	}

	if ak == "" || sk == "" || e2eProviderName == "" {
		fmt.Println("[E2E] Skipping E2E tests: required environment variables not set. " +
			"Need ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET, AGENT_IDENTITY_E2E_PROVIDER_NAME.")
		os.Exit(0)
	}

	var err error
	e2eClient, err = NewIdentityClient(region)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[E2E Setup] Failed to create IdentityClient: %v\n", err)
		os.Exit(1)
	}

	ctx := context.Background()

	e2eWorkloadName, err = e2eClient.CreateWorkloadIdentity(ctx)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[E2E Setup] Failed to create workload identity: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("[E2E Setup] Created workload identity: %s\n", e2eWorkloadName)

	e2eWorkloadAccessToken, err = e2eClient.GetWorkloadAccessToken(ctx, e2eWorkloadName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[E2E Setup] Failed to get workload access token: %v\n", err)
		os.Exit(1)
	}

	code := m.Run()

	fmt.Printf("[E2E Cleanup] Workload Identity created during tests: %s (manual cleanup may be required)\n", e2eWorkloadName)
	os.Exit(code)
}

// ===========================================================================
// Workload Identity Lifecycle
// ===========================================================================

// AC1 – CreateWorkloadIdentity with custom name
func TestCreateWorkloadIdentity_WithCustomName(t *testing.T) {
	ctx := context.Background()
	customName := fmt.Sprintf("e2e-custom-%d", os.Getpid())
	result, err := e2eClient.CreateWorkloadIdentity(ctx, CreateWorkloadIdentityOption{
		WorkloadName: customName,
	})
	if err != nil {
		t.Fatalf("CreateWorkloadIdentity with custom name failed: %v", err)
	}
	if result != customName {
		t.Fatalf("expected workload name %q, got %q", customName, result)
	}
	t.Logf("[E2E Cleanup] Extra workload identity created: %s", result)
}

// AC2 – CreateWorkloadIdentity without name → auto-generated
func TestCreateWorkloadIdentity_WithoutName(t *testing.T) {
	ctx := context.Background()
	result, err := e2eClient.CreateWorkloadIdentity(ctx)
	if err != nil {
		t.Fatalf("CreateWorkloadIdentity without name failed: %v", err)
	}
	matched, _ := regexp.MatchString(`^workload-[0-9a-f]{8}$`, result)
	if !matched {
		t.Fatalf("expected auto-generated name matching workload-{8hex}, got %q", result)
	}
	t.Logf("[E2E Cleanup] Extra workload identity created: %s", result)
}

// AC3 – GetWorkloadAccessToken without user info
func TestGetWorkloadAccessToken_NoUserInfo(t *testing.T) {
	ctx := context.Background()
	token, err := e2eClient.GetWorkloadAccessToken(ctx, e2eWorkloadName)
	if err != nil {
		t.Fatalf("GetWorkloadAccessToken failed: %v", err)
	}
	if token == "" {
		t.Fatal("expected non-empty workload access token")
	}
}

// AC4 – GetWorkloadAccessToken with UserId
func TestGetWorkloadAccessToken_WithUserId(t *testing.T) {
	ctx := context.Background()
	token, err := e2eClient.GetWorkloadAccessToken(ctx, e2eWorkloadName, GetWorkloadAccessTokenOption{
		UserId: "e2e-test-user",
	})
	if err != nil {
		t.Fatalf("GetWorkloadAccessToken with userId failed: %v", err)
	}
	if token == "" {
		t.Fatal("expected non-empty workload access token")
	}
}

// AC5 – GetWorkloadAccessToken with non-existent workload name
func TestGetWorkloadAccessToken_NotExist(t *testing.T) {
	ctx := context.Background()
	_, err := e2eClient.GetWorkloadAccessToken(ctx, "non-existent-workload-identity")
	if err == nil {
		t.Fatal("expected error for non-existent workload identity, got nil")
	}
}

// AC6 – GetWorkloadAccessToken with UserToken (JWT path)
func TestGetWorkloadAccessToken_WithUserToken(t *testing.T) {
	userToken := os.Getenv("AGENT_IDENTITY_E2E_USER_TOKEN")
	if userToken == "" {
		t.Skip("Skipping: AGENT_IDENTITY_E2E_USER_TOKEN not set")
	}
	ctx := context.Background()
	token, err := e2eClient.GetWorkloadAccessToken(ctx, e2eWorkloadName, GetWorkloadAccessTokenOption{
		UserToken: userToken,
	})
	if err != nil {
		t.Fatalf("GetWorkloadAccessToken with userToken failed: %v", err)
	}
	if token == "" {
		t.Fatal("expected non-empty workload access token")
	}
}

// ===========================================================================
// Resource Credential Acquisition
// ===========================================================================

// AC1, AC2 – GetToken (OAuth2 3LO)
func TestGetToken_OAuth2(t *testing.T) {
	ctx := context.Background()
	token, err := e2eClient.GetToken(ctx, GetTokenOptions{
		ProviderName:       e2eProviderName,
		AgentIdentityToken: e2eWorkloadAccessToken,
		AuthFlow:           "USER_FEDERATION",
		OnAuthUrl: func(url string) {
			fmt.Printf("[E2E OAuth2] Authorization URL (open in browser to authorise): %s\n", url)
		},
	})
	if err != nil {
		t.Fatalf("GetToken failed: %v", err)
	}
	if token == "" {
		t.Fatal("expected non-empty OAuth2 token")
	}
}

// AC3 – GetApiKey with valid provider
func TestGetApiKey_Valid(t *testing.T) {
	ctx := context.Background()
	apiKey, err := e2eClient.GetApiKey(ctx, GetApiKeyOptions{
		ProviderName:       e2eProviderName,
		AgentIdentityToken: e2eWorkloadAccessToken,
	})
	if err != nil {
		t.Fatalf("GetApiKey failed: %v", err)
	}
	if apiKey == "" {
		t.Fatal("expected non-empty API key")
	}
}

// AC7 – GetApiKey with invalid provider
func TestGetApiKey_InvalidProvider(t *testing.T) {
	ctx := context.Background()
	_, err := e2eClient.GetApiKey(ctx, GetApiKeyOptions{
		ProviderName:       "non-existent-provider-name",
		AgentIdentityToken: e2eWorkloadAccessToken,
	})
	if err == nil {
		t.Fatal("expected error for invalid provider, got nil")
	}
}

// AC4 – AssumeRoleForWorkloadIdentity
func TestAssumeRoleForWorkloadIdentity(t *testing.T) {
	ctx := context.Background()
	stsCred, err := e2eClient.AssumeRoleForWorkloadIdentity(ctx, AssumeRoleOptions{
		WorkloadToken:   e2eWorkloadAccessToken,
		RoleSessionName: "e2e-test-session",
	})
	if err != nil {
		t.Fatalf("AssumeRoleForWorkloadIdentity failed: %v", err)
	}
	if stsCred == nil {
		t.Fatal("expected non-nil STSCredential")
	}
	if stsCred.AccessKeyId == "" {
		t.Error("expected non-empty AccessKeyId")
	}
	if stsCred.AccessKeySecret == "" {
		t.Error("expected non-empty AccessKeySecret")
	}
	if stsCred.SecurityToken == "" {
		t.Error("expected non-empty SecurityToken")
	}
	if stsCred.Expiration == "" {
		t.Error("expected non-empty Expiration")
	}
}

// AC5 – GetStsCredentialClient
func TestGetStsCredentialClient(t *testing.T) {
	ctx := context.Background()
	cred, err := e2eClient.GetStsCredentialClient(ctx, e2eWorkloadAccessToken, "", "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient failed: %v", err)
	}
	if cred == nil {
		t.Fatal("expected non-nil Credential instance")
	}
}

// AC6 – GetStsCredentialClient cache hit
func TestGetStsCredentialClient_Cache(t *testing.T) {
	ctx := context.Background()
	// Use a unique token-like key so we don't collide with previous test's cache
	uniqueToken := e2eWorkloadAccessToken

	cred1, err := e2eClient.GetStsCredentialClient(ctx, uniqueToken, "cache-test-user", "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient (1st call) failed: %v", err)
	}
	cred2, err := e2eClient.GetStsCredentialClient(ctx, uniqueToken, "cache-test-user", "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient (2nd call) failed: %v", err)
	}

	// With caching, the underlying STS credential should be the same, producing
	// the same Credential reference (Go credentials-go returns a new instance
	// each time, so we compare the access key IDs to verify the same STS cred was used).
	ak1, _ := cred1.GetAccessKeyId()
	ak2, _ := cred2.GetAccessKeyId()
	if ak1 == nil || ak2 == nil {
		t.Fatal("expected non-nil access key IDs from cached credentials")
	}
	if *ak1 != *ak2 {
		t.Fatalf("expected same access key ID from cache, got %q and %q", *ak1, *ak2)
	}
}

// ===========================================================================
// Credential Middleware Functions
// ===========================================================================

// AC1 – RequiresAccessToken
func TestRequiresAccessToken(t *testing.T) {
	var receivedToken string
	handler := RequiresAccessToken(
		RequiresAccessTokenConfig{
			ProviderName: e2eProviderName,
			AuthFlow:     "USER_FEDERATION",
			OnAuthUrl: func(url string) {
				fmt.Printf("[E2E Middleware OAuth2] Authorization URL: %s\n", url)
			},
		},
		func(ctx context.Context, accessToken string) error {
			receivedToken = accessToken
			return nil
		},
	)

	ctx := WithWorkloadAccessToken(context.Background(), e2eWorkloadAccessToken)
	if err := handler(ctx); err != nil {
		t.Fatalf("RequiresAccessToken handler failed: %v", err)
	}
	if receivedToken == "" {
		t.Fatal("expected non-empty access token in handler")
	}
}

// AC2 – RequiresApiKey
func TestRequiresApiKey(t *testing.T) {
	var receivedKey string
	handler := RequiresApiKey(
		RequiresApiKeyConfig{
			ProviderName: e2eProviderName,
		},
		func(ctx context.Context, apiKey string) error {
			receivedKey = apiKey
			return nil
		},
	)

	ctx := WithWorkloadAccessToken(context.Background(), e2eWorkloadAccessToken)
	if err := handler(ctx); err != nil {
		t.Fatalf("RequiresApiKey handler failed: %v", err)
	}
	if receivedKey == "" {
		t.Fatal("expected non-empty API key in handler")
	}
}

// AC3, AC4 – RequiresStsToken
func TestRequiresStsToken(t *testing.T) {
	var receivedCred *STSCredential
	handler := RequiresStsToken(
		RequiresStsTokenConfig{},
		func(ctx context.Context, stsCredential *STSCredential) error {
			receivedCred = stsCredential
			return nil
		},
	)

	ctx := WithWorkloadAccessToken(context.Background(), e2eWorkloadAccessToken)
	if err := handler(ctx); err != nil {
		t.Fatalf("RequiresStsToken handler failed: %v", err)
	}
	if receivedCred == nil {
		t.Fatal("expected non-nil STSCredential in handler")
	}
	if receivedCred.AccessKeyId == "" {
		t.Error("expected non-empty AccessKeyId")
	}
	if receivedCred.AccessKeySecret == "" {
		t.Error("expected non-empty AccessKeySecret")
	}
	if receivedCred.SecurityToken == "" {
		t.Error("expected non-empty SecurityToken")
	}
	if receivedCred.Expiration == "" {
		t.Error("expected non-empty Expiration")
	}
}
