package agentidentity

import (
	"context"

	ictx "github.com/aliyun/agent-identity-dev-kit/agent-identity-sdk-go/internal/context"
)

// WithUserId returns a new context with the user ID set.
func WithUserId(ctx context.Context, userId string) context.Context {
	return ictx.WithUserId(ctx, userId)
}

// GetUserId retrieves the user ID from the context.
func GetUserId(ctx context.Context) (string, bool) {
	return ictx.GetUserId(ctx)
}

// WithUserToken returns a new context with the user token set.
func WithUserToken(ctx context.Context, token string) context.Context {
	return ictx.WithUserToken(ctx, token)
}

// GetUserToken retrieves the user token from the context.
func GetUserToken(ctx context.Context) (string, bool) {
	return ictx.GetUserToken(ctx)
}

// WithCustomState returns a new context with the custom state set.
func WithCustomState(ctx context.Context, state string) context.Context {
	return ictx.WithCustomState(ctx, state)
}

// GetCustomState retrieves the custom state from the context.
func GetCustomState(ctx context.Context) (string, bool) {
	return ictx.GetCustomState(ctx)
}

// WithWorkloadAccessToken returns a new context with the workload access token set.
func WithWorkloadAccessToken(ctx context.Context, token string) context.Context {
	return ictx.WithWorkloadAccessToken(ctx, token)
}

// GetWorkloadAccessToken retrieves the workload access token from context.
// Falls back to AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN environment variable if not in context.
func GetWorkloadAccessToken(ctx context.Context) (string, bool) {
	return ictx.GetWorkloadAccessToken(ctx)
}

// ClearContext returns a new context with all Agent Identity values cleared.
func ClearContext(ctx context.Context) context.Context {
	return ictx.ClearContext(ctx)
}
