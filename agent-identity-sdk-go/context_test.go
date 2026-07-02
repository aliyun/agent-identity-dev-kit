package agentidentity

import (
	"context"
	"os"
	"testing"
)

func TestWithUserId(t *testing.T) {
	ctx := context.Background()
	ctx = WithUserId(ctx, "user-123")

	val, ok := GetUserId(ctx)
	if !ok {
		t.Fatal("GetUserId returned ok=false")
	}
	if val != "user-123" {
		t.Fatalf("expected user-123, got %s", val)
	}
}

func TestGetUserIdNotFound(t *testing.T) {
	val, ok := GetUserId(context.Background())
	if ok {
		t.Fatal("expected ok=false for unset userId")
	}
	if val != "" {
		t.Fatalf("expected empty string, got %s", val)
	}
}

func TestWithUserToken(t *testing.T) {
	ctx := context.Background()
	ctx = WithUserToken(ctx, "jwt-token-abc")

	val, ok := GetUserToken(ctx)
	if !ok {
		t.Fatal("GetUserToken returned ok=false")
	}
	if val != "jwt-token-abc" {
		t.Fatalf("expected jwt-token-abc, got %s", val)
	}
}

func TestGetUserTokenNotFound(t *testing.T) {
	_, ok := GetUserToken(context.Background())
	if ok {
		t.Fatal("expected ok=false for unset userToken")
	}
}

func TestWithCustomState(t *testing.T) {
	ctx := context.Background()
	ctx = WithCustomState(ctx, "my-state")

	val, ok := GetCustomState(ctx)
	if !ok {
		t.Fatal("GetCustomState returned ok=false")
	}
	if val != "my-state" {
		t.Fatalf("expected my-state, got %s", val)
	}
}

func TestGetCustomStateNotFound(t *testing.T) {
	_, ok := GetCustomState(context.Background())
	if ok {
		t.Fatal("expected ok=false for unset customState")
	}
}

func TestWithWorkloadAccessToken(t *testing.T) {
	ctx := context.Background()
	ctx = WithWorkloadAccessToken(ctx, "wl-token")

	val, ok := GetWorkloadAccessToken(ctx)
	if !ok {
		t.Fatal("GetWorkloadAccessToken returned ok=false")
	}
	if val != "wl-token" {
		t.Fatalf("expected wl-token, got %s", val)
	}
}

func TestGetWorkloadAccessTokenFromEnv(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN", "env-token")
	defer os.Unsetenv("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN")

	val, ok := GetWorkloadAccessToken(context.Background())
	if !ok {
		t.Fatal("expected ok=true from env fallback")
	}
	if val != "env-token" {
		t.Fatalf("expected env-token, got %s", val)
	}
}

func TestGetWorkloadAccessTokenEnvEmpty(t *testing.T) {
	os.Unsetenv("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN")
	_, ok := GetWorkloadAccessToken(context.Background())
	if ok {
		t.Fatal("expected ok=false when no token and no env")
	}
}

func TestGetWorkloadAccessTokenContextOverridesEnv(t *testing.T) {
	os.Setenv("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN", "env-token")
	defer os.Unsetenv("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN")

	ctx := WithWorkloadAccessToken(context.Background(), "ctx-token")
	val, ok := GetWorkloadAccessToken(ctx)
	if !ok {
		t.Fatal("expected ok=true")
	}
	if val != "ctx-token" {
		t.Fatalf("expected ctx-token (context override), got %s", val)
	}
}

func TestClearContext(t *testing.T) {
	ctx := context.Background()
	ctx = WithUserId(ctx, "user-123")
	ctx = WithUserToken(ctx, "jwt-token")
	ctx = WithCustomState(ctx, "state")
	ctx = WithWorkloadAccessToken(ctx, "wl-token")

	ctx = ClearContext(ctx)

	_, ok := GetUserId(ctx)
	if ok {
		t.Fatal("userId should be cleared")
	}
	_, ok = GetUserToken(ctx)
	if ok {
		t.Fatal("userToken should be cleared")
	}
	_, ok = GetCustomState(ctx)
	if ok {
		t.Fatal("customState should be cleared")
	}
	_, ok = GetWorkloadAccessToken(ctx)
	if ok {
		t.Fatal("workloadAccessToken should be cleared")
	}
}
