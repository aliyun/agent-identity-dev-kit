//go:build integration

package agentidentity

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"fmt"
	"math/big"
	"net"
	"net/http"
	"os"
	"sync"
	"testing"
	"time"
)

// ---------------------------------------------------------------------------
// Self-signed certificate helpers
// ---------------------------------------------------------------------------

func generateSelfSignedCert() (tls.Certificate, error) {
	priv, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return tls.Certificate{}, err
	}

	serialNumber, err := rand.Int(rand.Reader, new(big.Int).Lsh(big.NewInt(1), 128))
	if err != nil {
		return tls.Certificate{}, err
	}

	now := time.Now()
	template := x509.Certificate{
		SerialNumber: serialNumber,
		Subject:      pkix.Name{CommonName: "localhost"},
		NotBefore:    now.Add(-time.Hour),
		NotAfter:     now.Add(24 * time.Hour),
		KeyUsage:     x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		DNSNames:     []string{"localhost"},
		IPAddresses:  []net.IP{net.ParseIP("127.0.0.1")},
	}

	derBytes, err := x509.CreateCertificate(rand.Reader, &template, &template, &priv.PublicKey, priv)
	if err != nil {
		return tls.Certificate{}, err
	}

	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: derBytes})
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(priv)})

	return tls.X509KeyPair(certPEM, keyPEM)
}

// ---------------------------------------------------------------------------
// Callback server: listens for the OAuth2 redirect with session_uri
// ---------------------------------------------------------------------------

type callbackServer struct {
	server     *http.Server
	mu         sync.Mutex
	sessionUri string
	done       chan struct{}
}

func newCallbackServer(t *testing.T) *callbackServer {
	cs := &callbackServer{done: make(chan struct{})}

	mux := http.NewServeMux()
	mux.HandleFunc("/callback", func(w http.ResponseWriter, r *http.Request) {
		sessionUri := r.URL.Query().Get("session_uri")
		if sessionUri == "" {
			t.Logf("[Callback Server] Received callback without session_uri: %s", r.URL.RawQuery)
			http.Error(w, "missing session_uri", http.StatusBadRequest)
			return
		}

		cs.mu.Lock()
		cs.sessionUri = sessionUri
		cs.mu.Unlock()
		t.Logf("[Callback Server] Received session_uri: %s", sessionUri)
		close(cs.done)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Authorization received. You may close this window."))
	})

	cs.server = &http.Server{Addr: ":8443", Handler: mux}

	cert, err := generateSelfSignedCert()
	if err != nil {
		t.Fatalf("Failed to generate self-signed cert: %v", err)
	}

	// Use tlsConfig to avoid TLS handshake errors in browsers
	cs.server.TLSConfig = &tls.Config{
		Certificates: []tls.Certificate{cert},
	}

	go func() {
		if err := cs.server.ListenAndServeTLS("", ""); err != nil && err != http.ErrServerClosed {
			t.Logf("[Callback Server] Error: %v", err)
		}
	}()

	return cs
}

func (cs *callbackServer) waitForCallback(timeout time.Duration) (string, bool) {
	select {
	case <-cs.done:
		cs.mu.Lock()
		defer cs.mu.Unlock()
		return cs.sessionUri, true
	case <-time.After(timeout):
		return "", false
	}
}

func (cs *callbackServer) stop() {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	_ = cs.server.Shutdown(ctx)
}

// ---------------------------------------------------------------------------
// TestFullChain — complete end-to-end flow with OAuth2 callback handling
// ---------------------------------------------------------------------------

func TestFullChain(t *testing.T) {
	ctx := context.Background()

	ak := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
	sk := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
	providerName := os.Getenv("AGENT_IDENTITY_E2E_PROVIDER_NAME")
	region := os.Getenv("AGENT_IDENTITY_REGION_ID")
	if region == "" {
		region = "cn-beijing"
	}

	if ak == "" || sk == "" || providerName == "" {
		t.Skip("Skipping integration test: need ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET, AGENT_IDENTITY_E2E_PROVIDER_NAME")
	}

	// ---- Step 0 — Start local callback server ----
	t.Log("=== Step 0: Start local HTTPS callback server on :8443 ===")
	callbackSrv := newCallbackServer(t)
	defer callbackSrv.stop()

	// ---- Step 1 — Create IdentityClient + Workload Identity ----
	t.Log("=== Step 1: Create IdentityClient & Workload Identity ===")
	client, err := NewIdentityClient(region)
	if err != nil {
		t.Fatalf("Failed to create IdentityClient: %v", err)
	}

	// Try to reuse existing workload identity from local config
	configFile := fmt.Sprintf("/tmp/agent-identity-test-config-%s.json", region)
	workloadName, err := ReadLocalConfig("workload_identity_name", configFile)
	if err != nil || workloadName == "" {
		// No existing identity, create a new one
		workloadName = fmt.Sprintf("integration-chain-%d", os.Getpid())
		result, err := client.CreateWorkloadIdentity(ctx, CreateWorkloadIdentityOption{
			WorkloadName: workloadName,
		})
		if err != nil {
			t.Fatalf("Failed to create WorkloadIdentity: %v", err)
		}
		if result != workloadName {
			t.Fatalf("expected workload name %q, got %q", workloadName, result)
		}
		// Persist for next run
		if err := WriteLocalConfig("workload_identity_name", workloadName, configFile); err != nil {
			t.Logf("Warning: failed to persist workload identity name: %v", err)
		}
		t.Logf("Workload identity created (new): %s", workloadName)
	} else {
		t.Logf("Workload identity reused (from config): %s", workloadName)
	}

	// ---- Step 2 — Get Workload Access Token (three paths) ----
	t.Log("=== Step 2a: Get WAT without user info ===")
	workloadAccessToken, err := client.GetWorkloadAccessToken(ctx, workloadName)
	if err != nil {
		t.Fatalf("Failed to get WorkloadAccessToken (no user info): %v", err)
	}
	if workloadAccessToken == "" {
		t.Fatal("expected non-empty WorkloadAccessToken")
	}
	t.Log("WAT (no user info) obtained")

	// UserId path (optional — only if env is set)
	userId := os.Getenv("AGENT_IDENTITY_E2E_USER_ID")
	if userId != "" {
		t.Log("=== Step 2b: Get WAT with UserId ===")
		watForUserId, err := client.GetWorkloadAccessToken(ctx, workloadName, GetWorkloadAccessTokenOption{
			UserId: userId,
		})
		if err != nil {
			t.Fatalf("Failed to get WorkloadAccessToken (with userId): %v", err)
		}
		if watForUserId == "" {
			t.Fatal("expected non-empty WorkloadAccessToken for userId")
		}
		t.Logf("WAT (with userId=%s) obtained", userId)
	} else {
		t.Log("=== Step 2b: Skipped (AGENT_IDENTITY_E2E_USER_ID not set) ===")
	}

	// UserToken (JWT) path (optional — only if env is set)
	userToken := os.Getenv("AGENT_IDENTITY_E2E_USER_TOKEN")
	if userToken != "" {
		t.Log("=== Step 2c: Get WAT with UserToken (JWT) ===")
		watForUserToken, err := client.GetWorkloadAccessToken(ctx, workloadName, GetWorkloadAccessTokenOption{
			UserToken: userToken,
		})
		if err != nil {
			t.Fatalf("Failed to get WorkloadAccessToken (with userToken): %v", err)
		}
		if watForUserToken == "" {
			t.Fatal("expected non-empty WorkloadAccessToken for userToken")
		}
		t.Log("WAT (with userToken/JWT) obtained")
	} else {
		t.Log("=== Step 2c: Skipped (AGENT_IDENTITY_E2E_USER_TOKEN not set) ===")
	}

	// ---- Step 3a — Get OAuth2 Access Token (with callback + ConfirmUserAuth) ----
	t.Log("=== Step 3a: Get OAuth2 Access Token ===")
	var authUrlCalled bool
	var authUrlReceived string

	authUrlCh := make(chan string, 1)

	oauth2Token, err := client.GetToken(ctx, GetTokenOptions{
		ProviderName:       providerName,
		AgentIdentityToken: workloadAccessToken,
		AuthFlow:           "USER_FEDERATION",
		CallbackUrl:        "https://localhost:8443/callback",
		OnAuthUrl: func(url string) {
			authUrlCalled = true
			authUrlReceived = url
			t.Logf("Authorization URL received: %s", url)
			authUrlCh <- url
		},
	})
	// If GetToken returns an error, it may be because the OAuth2 flow needs
	// manual confirmation. Try the callback flow manually.
	if err != nil {
		t.Logf("GetToken returned error: %v, attempting manual callback flow...", err)

		// Wait for the auth URL callback to fire
		select {
		case authUrlReceived = <-authUrlCh:
		case <-time.After(60 * time.Second):
			t.Fatalf("Timeout waiting for authorization URL")
		}
	}

	if authUrlCalled {
		t.Logf("Auth URL callback fired: %v", authUrlCalled)
	}

	// Parse the authorization URL to check if we got a session_uri from it
	// The GetToken API returns an authorization URL that the user must visit.
	// After visiting, the IdP redirects to our callback with session_uri.
	if oauth2Token == "" {
		t.Log("Opening authorization URL in browser... (you may need to authorise manually)")

		// Open in browser (best effort)
		openBrowser(authUrlReceived)

		// Wait for callback to receive session_uri
		sessionUri, ok := callbackSrv.waitForCallback(120 * time.Second)
		if !ok {
			t.Fatal("Timeout waiting for OAuth2 callback on :8443. " +
				"Please visit the authorization URL manually and ensure the redirect goes to https://localhost:8443/callback")
		}

		t.Logf("Callback received, calling ConfirmUserAuth with session_uri...")

		// Call ConfirmUserAuth to complete the OAuth2 flow
		err = client.ConfirmUserAuth(ctx, sessionUri, ConfirmUserAuthOption{
			UserId:    "",
			UserToken: "",
		})
		if err != nil {
			t.Fatalf("ConfirmUserAuth failed: %v", err)
		}
		t.Log("ConfirmUserAuth succeeded, polling for token...")

		// Now retry GetToken — the polling inside GetToken should succeed
		oauth2Token, err = client.GetToken(ctx, GetTokenOptions{
			ProviderName:       providerName,
			AgentIdentityToken: workloadAccessToken,
			AuthFlow:           "USER_FEDERATION",
			CallbackUrl:        "https://localhost:8443/callback",
		})
		if err != nil {
			t.Fatalf("GetToken retry after ConfirmUserAuth failed: %v", err)
		}
	}

	if oauth2Token == "" {
		t.Fatal("expected non-empty OAuth2 token")
	}
	t.Logf("OAuth2 token obtained")

	// ---- Step 3b — Get API Key ----
	t.Log("=== Step 3b: Get API Key ===")
	apiKey, err := client.GetApiKey(ctx, GetApiKeyOptions{
		ProviderName:       providerName,
		AgentIdentityToken: workloadAccessToken,
	})
	if err != nil {
		t.Fatalf("GetApiKey failed: %v", err)
	}
	if apiKey == "" {
		t.Fatal("expected non-empty API key")
	}
	t.Logf("API key obtained (prefix: %s...)", apiKey[:min(8, len(apiKey))])

	// ---- Step 3c — Assume Role for STS Token ----
	t.Log("=== Step 3c: Assume Role for STS Token ===")
	stsCred, err := client.AssumeRoleForWorkloadIdentity(ctx, AssumeRoleOptions{
		WorkloadToken:   workloadAccessToken,
		RoleSessionName: "integration-test-session",
	})
	if err != nil {
		t.Fatalf("AssumeRoleForWorkloadIdentity failed: %v", err)
	}
	if stsCred.AccessKeyId == "" || stsCred.AccessKeySecret == "" || stsCred.SecurityToken == "" {
		t.Fatal("expected non-empty STS credential fields")
	}
	t.Logf("STS credential obtained: AccessKeyId=%s, Expiration=%s",
		stsCred.AccessKeyId, stsCred.Expiration)

	// ---- Step 3d — Get STS Credential Client (with cache verification) ----
	t.Log("=== Step 3d: Get STS Credential Client (with cache) ===")
	credClient1, err := client.GetStsCredentialClient(ctx, workloadAccessToken, "chain-user", "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient (1st) failed: %v", err)
	}
	credClient2, err := client.GetStsCredentialClient(ctx, workloadAccessToken, "chain-user", "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient (2nd) failed: %v", err)
	}
	ak1, _ := credClient1.GetAccessKeyId()
	ak2, _ := credClient2.GetAccessKeyId()
	if ak1 == nil || ak2 == nil {
		t.Fatal("expected non-nil access key IDs")
	}
	if *ak1 != *ak2 {
		t.Fatalf("cache not working: different access keys %q vs %q", *ak1, *ak2)
	}
	t.Logf("STS credential cache working: AccessKeyId=%s", *ak1)

	// ---- Step 4 — Middleware Decorators ----
	t.Log("=== Step 4a: RequiresAccessToken middleware ===")
	var receivedOAuth2Token string
	handler1 := RequiresAccessToken(
		RequiresAccessTokenConfig{
			ProviderName: providerName,
			AuthFlow:     "USER_FEDERATION",
			CallbackUrl:  "https://localhost:8443/callback",
		},
		func(ctx context.Context, accessToken string) error {
			receivedOAuth2Token = accessToken
			return nil
		},
	)
	ctxWithToken := WithWorkloadAccessToken(ctx, workloadAccessToken)
	if err := handler1(ctxWithToken); err != nil {
		t.Fatalf("RequiresAccessToken middleware failed: %v", err)
	}
	if receivedOAuth2Token == "" {
		t.Fatal("expected non-empty OAuth2 token from middleware")
	}
	t.Log("RequiresAccessToken middleware succeeded")

	t.Log("=== Step 4b: RequiresApiKey middleware ===")
	var receivedApiKey string
	handler2 := RequiresApiKey(
		RequiresApiKeyConfig{
			ProviderName: providerName,
		},
		func(ctx context.Context, key string) error {
			receivedApiKey = key
			return nil
		},
	)
	if err := handler2(ctxWithToken); err != nil {
		t.Fatalf("RequiresApiKey middleware failed: %v", err)
	}
	if receivedApiKey == "" {
		t.Fatal("expected non-empty API key from middleware")
	}
	t.Log("RequiresApiKey middleware succeeded")

	t.Log("=== Step 4c: RequiresStsToken middleware ===")
	var receivedStsCred *STSCredential
	handler3 := RequiresStsToken(
		RequiresStsTokenConfig{},
		func(ctx context.Context, cred *STSCredential) error {
			receivedStsCred = cred
			return nil
		},
	)
	if err := handler3(ctxWithToken); err != nil {
		t.Fatalf("RequiresStsToken middleware failed: %v", err)
	}
	if receivedStsCred == nil || receivedStsCred.AccessKeyId == "" {
		t.Fatal("expected non-empty STS credential from middleware")
	}
	t.Logf("RequiresStsToken middleware succeeded: AccessKeyId=%s", receivedStsCred.AccessKeyId)

	// ---- Step 5 — Local Config Persistence ----
	t.Log("=== Step 5: Local Config Persistence ===")
	err = WriteLocalConfig("workload_identity_name", workloadName, configFile)
	if err != nil {
		t.Fatalf("WriteLocalConfig failed: %v", err)
	}
	readValue, err := ReadLocalConfig("workload_identity_name", configFile)
	if err != nil {
		t.Fatalf("ReadLocalConfig failed: %v", err)
	}
	if readValue != workloadName {
		t.Fatalf("expected config value %q, got %q", workloadName, readValue)
	}
	_ = os.Remove(configFile) // cleanup
	t.Log("Local config read/write succeeded")

	t.Log("=== Full Chain Integration Test PASSED ===")
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func openBrowser(authUrl string) {
	// Try to open browser on macOS
	if _, err := os.Stat("/System/Library/CoreServices/Finder.app"); err == nil {
		fmt.Fprintf(os.Stderr, "\n\n  >>> Please open: %s\n\n", authUrl)
	}
}

// ---------------------------------------------------------------------------
// TestFullChainWithUserId — UserId-based WAT end-to-end flow
// ---------------------------------------------------------------------------

// TestFullChainWithUserId verifies the complete flow using UserId path:
//
//  1. Create Workload Identity
//  2. Get WAT via UserId → GetWorkloadAccessTokenForUserId
//  3. Use this WAT for: GetToken (OAuth2), GetApiKey, AssumeRole, GetStsCredentialClient
//  4. Middleware decorators with UserId injected into context
func TestFullChainWithUserId(t *testing.T) {
	ctx := context.Background()

	ak := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
	sk := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
	providerName := os.Getenv("AGENT_IDENTITY_E2E_PROVIDER_NAME")
	userId := os.Getenv("AGENT_IDENTITY_E2E_USER_ID")
	region := os.Getenv("AGENT_IDENTITY_REGION_ID")
	if region == "" {
		region = "cn-beijing"
	}

	if ak == "" || sk == "" || providerName == "" {
		t.Skip("Skipping: need ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET, AGENT_IDENTITY_E2E_PROVIDER_NAME")
	}
	if userId == "" {
		t.Skip("Skipping: AGENT_IDENTITY_E2E_USER_ID not set")
	}

	// ---- Step 0 — Start local callback server ----
	t.Log("=== Step 0: Start local HTTPS callback server on :8443 ===")
	callbackSrv := newCallbackServer(t)
	defer callbackSrv.stop()

	// ---- Step 1 — Create IdentityClient + Workload Identity ----
	t.Log("=== Step 1: Create IdentityClient & Workload Identity ===")
	client, err := NewIdentityClient(region)
	if err != nil {
		t.Fatalf("Failed to create IdentityClient: %v", err)
	}

	configFile := fmt.Sprintf("/tmp/agent-identity-test-config-%s.json", region)
	workloadName, err := ReadLocalConfig("workload_identity_name", configFile)
	if err != nil || workloadName == "" {
		workloadName = fmt.Sprintf("integration-userid-%d", os.Getpid())
		result, err := client.CreateWorkloadIdentity(ctx, CreateWorkloadIdentityOption{
			WorkloadName: workloadName,
		})
		if err != nil {
			t.Fatalf("Failed to create WorkloadIdentity: %v", err)
		}
		if result != workloadName {
			t.Fatalf("expected workload name %q, got %q", workloadName, result)
		}
		if err := WriteLocalConfig("workload_identity_name", workloadName, configFile); err != nil {
			t.Logf("Warning: failed to persist workload identity name: %v", err)
		}
		t.Logf("Workload identity created: %s", workloadName)
	} else {
		t.Logf("Workload identity reused: %s", workloadName)
	}

	// ---- Step 2 — Get WAT via UserId ----
	t.Log("=== Step 2: Get WAT via UserId ===")
	workloadAccessToken, err := client.GetWorkloadAccessToken(ctx, workloadName, GetWorkloadAccessTokenOption{
		UserId: userId,
	})
	if err != nil {
		t.Fatalf("Failed to get WAT (with userId=%s): %v", userId, err)
	}
	if workloadAccessToken == "" {
		t.Fatal("expected non-empty WAT")
	}
	t.Logf("WAT (userId=%s) obtained", userId)

	// ---- Step 3a — Get OAuth2 Access Token ----
	t.Log("=== Step 3a: Get OAuth2 Access Token ===")
	authUrlCh := make(chan string, 1)
	var authUrlCalled bool

	oauth2Token, err := client.GetToken(ctx, GetTokenOptions{
		ProviderName:       providerName,
		AgentIdentityToken: workloadAccessToken,
		AuthFlow:           "USER_FEDERATION",
		CallbackUrl:        "https://localhost:8443/callback",
		OnAuthUrl: func(url string) {
			authUrlCalled = true
			t.Logf("Authorization URL received: %s", url)
			authUrlCh <- url
		},
	})
	if err != nil {
		t.Logf("GetToken returned error: %v, attempting manual callback flow...", err)
		select {
		case <-authUrlCh:
		case <-time.After(60 * time.Second):
			t.Fatalf("Timeout waiting for authorization URL")
		}
	}

	if oauth2Token == "" {
		sessionUri, ok := callbackSrv.waitForCallback(120 * time.Second)
		if !ok {
			t.Fatal("Timeout waiting for OAuth2 callback. Open the auth URL manually.")
		}

		err = client.ConfirmUserAuth(ctx, sessionUri, ConfirmUserAuthOption{
			UserId:    userId,
			UserToken: "",
		})
		if err != nil {
			t.Fatalf("ConfirmUserAuth failed: %v", err)
		}
		t.Log("ConfirmUserAuth succeeded")

		oauth2Token, err = client.GetToken(ctx, GetTokenOptions{
			ProviderName:       providerName,
			AgentIdentityToken: workloadAccessToken,
			AuthFlow:           "USER_FEDERATION",
			CallbackUrl:        "https://localhost:8443/callback",
		})
		if err != nil {
			t.Fatalf("GetToken retry after ConfirmUserAuth failed: %v", err)
		}
	}

	if oauth2Token == "" {
		t.Fatal("expected non-empty OAuth2 token")
	}
	t.Logf("OAuth2 token obtained (authUrlCalled=%v)", authUrlCalled)

	// ---- Step 3b — Get API Key ----
	t.Log("=== Step 3b: Get API Key ===")
	apiKey, err := client.GetApiKey(ctx, GetApiKeyOptions{
		ProviderName:       providerName,
		AgentIdentityToken: workloadAccessToken,
	})
	if err != nil {
		t.Fatalf("GetApiKey failed: %v", err)
	}
	if apiKey == "" {
		t.Fatal("expected non-empty API key")
	}
	t.Logf("API key obtained")

	// ---- Step 3c — Assume Role for STS Token ----
	t.Log("=== Step 3c: Assume Role for STS Token ===")
	stsCred, err := client.AssumeRoleForWorkloadIdentity(ctx, AssumeRoleOptions{
		WorkloadToken:   workloadAccessToken,
		RoleSessionName: "integration-userid-session",
	})
	if err != nil {
		t.Fatalf("AssumeRoleForWorkloadIdentity failed: %v", err)
	}
	if stsCred.AccessKeyId == "" {
		t.Fatal("expected non-empty AccessKeyId")
	}
	t.Logf("STS credential obtained: AccessKeyId=%s", stsCred.AccessKeyId)

	// ---- Step 3d — Get STS Credential Client (with cache) ----
	t.Log("=== Step 3d: Get STS Credential Client (with cache) ===")
	credClient1, err := client.GetStsCredentialClient(ctx, workloadAccessToken, userId, "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient (1st) failed: %v", err)
	}
	credClient2, err := client.GetStsCredentialClient(ctx, workloadAccessToken, userId, "")
	if err != nil {
		t.Fatalf("GetStsCredentialClient (2nd) failed: %v", err)
	}
	ak1, _ := credClient1.GetAccessKeyId()
	ak2, _ := credClient2.GetAccessKeyId()
	if ak1 == nil || ak2 == nil {
		t.Fatal("expected non-nil access key IDs")
	}
	if *ak1 != *ak2 {
		t.Fatalf("cache not working: different access keys %q vs %q", *ak1, *ak2)
	}
	t.Logf("STS credential cache working: AccessKeyId=%s", *ak1)

	// ---- Step 4 — Middleware Decorators (with UserId in context) ----
	ctxWithUserId := WithUserId(context.Background(), userId)
	ctxWithToken := WithWorkloadAccessToken(ctxWithUserId, workloadAccessToken)

	t.Log("=== Step 4a: RequiresAccessToken middleware (with UserId) ===")
	var receivedOAuth2Token string
	handler1 := RequiresAccessToken(
		RequiresAccessTokenConfig{
			ProviderName: providerName,
			AuthFlow:     "USER_FEDERATION",
			CallbackUrl:  "https://localhost:8443/callback",
		},
		func(ctx context.Context, accessToken string) error {
			receivedOAuth2Token = accessToken
			return nil
		},
	)
	if err := handler1(ctxWithToken); err != nil {
		t.Fatalf("RequiresAccessToken middleware failed: %v", err)
	}
	if receivedOAuth2Token == "" {
		t.Fatal("expected non-empty OAuth2 token from middleware")
	}
	t.Log("RequiresAccessToken middleware succeeded")

	t.Log("=== Step 4b: RequiresApiKey middleware (with UserId) ===")
	var receivedApiKey string
	handler2 := RequiresApiKey(
		RequiresApiKeyConfig{
			ProviderName: providerName,
		},
		func(ctx context.Context, key string) error {
			receivedApiKey = key
			return nil
		},
	)
	if err := handler2(ctxWithToken); err != nil {
		t.Fatalf("RequiresApiKey middleware failed: %v", err)
	}
	if receivedApiKey == "" {
		t.Fatal("expected non-empty API key from middleware")
	}
	t.Log("RequiresApiKey middleware succeeded")

	t.Log("=== Step 4c: RequiresStsToken middleware (with UserId) ===")
	var receivedStsCred *STSCredential
	handler3 := RequiresStsToken(
		RequiresStsTokenConfig{},
		func(ctx context.Context, cred *STSCredential) error {
			receivedStsCred = cred
			return nil
		},
	)
	if err := handler3(ctxWithToken); err != nil {
		t.Fatalf("RequiresStsToken middleware failed: %v", err)
	}
	if receivedStsCred == nil || receivedStsCred.AccessKeyId == "" {
		t.Fatal("expected non-empty STS credential from middleware")
	}
	t.Logf("RequiresStsToken middleware succeeded: AccessKeyId=%s", receivedStsCred.AccessKeyId)

	t.Log("=== UserId Chain Integration Test PASSED ===")
}
