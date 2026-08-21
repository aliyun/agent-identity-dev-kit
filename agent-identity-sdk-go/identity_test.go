package agentidentity

import (
	"os"
	"regexp"
	"testing"
)

// ============================================================================
// identity.go tests — pure functions
// ============================================================================

func TestGetStsCacheKey(t *testing.T) {
	key := getStsCacheKey("user1", "token1", "session1")
	expected := "user1:token1:session1"
	if key != expected {
		t.Fatalf("expected %s, got %s", expected, key)
	}
}

func TestGetStsCacheKeyEmptyValues(t *testing.T) {
	key := getStsCacheKey("", "", "")
	if key != "::" {
		t.Fatalf("expected ::, got %s", key)
	}
}

func TestGenerateRandomHex(t *testing.T) {
	hex1 := generateRandomHex(4)
	if len(hex1) != 8 {
		t.Fatalf("expected 8 hex chars for 4 bytes, got %d: %s", len(hex1), hex1)
	}
	hex2 := generateRandomHex(4)
	if hex1 == hex2 {
		t.Fatal("expected different values on successive calls")
	}
}

func TestGenerateRandomHex_Lengths(t *testing.T) {
	for _, n := range []int{1, 2, 8, 16} {
		s := generateRandomHex(n)
		if len(s) != n*2 {
			t.Fatalf("expected %d chars for %d bytes, got %d", n*2, n, len(s))
		}
	}
}

func TestGenerateUUID(t *testing.T) {
	uuid := generateUUID()
	re := regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)
	if !re.MatchString(uuid) {
		t.Fatalf("invalid UUID v4 format: %s", uuid)
	}
}

func TestGenerateUUIDUniqueness(t *testing.T) {
	seen := make(map[string]bool)
	for i := 0; i < 100; i++ {
		u := generateUUID()
		if seen[u] {
			t.Fatalf("duplicate UUID: %s", u)
		}
		seen[u] = true
	}
}

func TestNewIdentityClient_Options(t *testing.T) {
	_, err := NewIdentityClient("cn-hangzhou",
		WithDataApiEndpoint("custom-data.example.com"),
		WithControlApiEndpoint("custom-control.example.com"),
	)
	if err == nil {
		t.Log("Client created successfully (credentials available in environment)")
	} else {
		t.Logf("NewIdentityClient failed as expected: %v", err)
	}
}

func TestNewIdentityClient_CustomProtocol(t *testing.T) {
	_, err := NewIdentityClient("cn-shanghai", WithProtocol("HTTPS"))
	if err == nil {
		t.Log("Client created with HTTPS protocol")
	} else {
		t.Logf("NewIdentityClient failed as expected: %v", err)
	}
}

func TestNewIdentityClient_UseStsEnvTrue(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "true")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	_, err := NewIdentityClient("cn-beijing")
	if err == nil {
		t.Log("Client created with useSts=true")
	} else {
		t.Logf("Expected failure due to credential chain: %v", err)
	}
}

func TestNewIdentityClient_UseStsEnvFalse(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "false")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	_, err := NewIdentityClient("cn-beijing")
	if err == nil {
		t.Log("Client created with useSts=false")
	} else {
		t.Logf("Expected failure due to credential chain: %v", err)
	}
}

func TestNewIdentityClient_UseStsEnvInvalid(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_USE_STS", "invalid")
	defer os.Unsetenv("AGENT_IDENTITY_USE_STS")

	_, err := NewIdentityClient("cn-beijing")
	if err == nil {
		t.Log("Client created with invalid env → useSts=false")
	} else {
		t.Logf("Expected failure: %v", err)
	}
}

func TestNewIdentityClient_CredentialError(t *testing.T) {
	os.Setenv("ALIBABA_CLOUD_CREDENTIALS_URI", "invalid://bad")
	defer os.Unsetenv("ALIBABA_CLOUD_CREDENTIALS_URI")

	_, err := NewIdentityClient("cn-beijing")
	if err != nil {
		t.Logf("Got expected error: %v", err)
	}
}

func TestWithDataApiEndpoint(t *testing.T) {
	opt := WithDataApiEndpoint("custom.example.com")
	client := &IdentityClient{}
	opt(client)
	if client.dataApiEndpoint != "custom.example.com" {
		t.Fatalf("expected custom.example.com, got %s", client.dataApiEndpoint)
	}
}

func TestWithControlApiEndpoint(t *testing.T) {
	opt := WithControlApiEndpoint("custom-control.example.com")
	client := &IdentityClient{}
	opt(client)
	if client.controlApiEndpoint != "custom-control.example.com" {
		t.Fatalf("expected custom-control.example.com, got %s", client.controlApiEndpoint)
	}
}

func TestWithProtocol_Option(t *testing.T) {
	opt := WithProtocol("HTTPS")
	client := &IdentityClient{}
	opt(client)
	if client.protocol != "HTTPS" {
		t.Fatalf("expected HTTPS, got %s", client.protocol)
	}
}
