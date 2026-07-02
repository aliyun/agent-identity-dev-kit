// Package context provides context helpers for propagating user identity
// and workload access tokens across async calls.
package context

import (
	"context"
	"os"
)

type contextKey int

const (
	userIdKey contextKey = iota
	userTokenKey
	customStateKey
	workloadAccessTokenKey
)

// WithUserId returns a new context with the user ID set.
func WithUserId(ctx context.Context, userId string) context.Context {
	return context.WithValue(ctx, userIdKey, userId)
}

// GetUserId retrieves the user ID from the context.
func GetUserId(ctx context.Context) (string, bool) {
	val, ok := ctx.Value(userIdKey).(string)
	return val, ok
}

// WithUserToken returns a new context with the user token set.
func WithUserToken(ctx context.Context, token string) context.Context {
	return context.WithValue(ctx, userTokenKey, token)
}

// GetUserToken retrieves the user token from the context.
func GetUserToken(ctx context.Context) (string, bool) {
	val, ok := ctx.Value(userTokenKey).(string)
	return val, ok
}

// WithCustomState returns a new context with the custom state set.
func WithCustomState(ctx context.Context, state string) context.Context {
	return context.WithValue(ctx, customStateKey, state)
}

// GetCustomState retrieves the custom state from the context.
func GetCustomState(ctx context.Context) (string, bool) {
	val, ok := ctx.Value(customStateKey).(string)
	return val, ok
}

// WithWorkloadAccessToken returns a new context with the workload access token set.
func WithWorkloadAccessToken(ctx context.Context, token string) context.Context {
	return context.WithValue(ctx, workloadAccessTokenKey, token)
}

// GetWorkloadAccessToken retrieves the workload access token from context.
// Falls back to AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN environment variable if not in context.
func GetWorkloadAccessToken(ctx context.Context) (string, bool) {
	val, ok := ctx.Value(workloadAccessTokenKey).(string)
	if ok && val != "" {
		return val, true
	}
	envVal := os.Getenv("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN")
	if envVal != "" {
		return envVal, true
	}
	return "", false
}

// ClearContext returns a new context with all Agent Identity values cleared.
func ClearContext(ctx context.Context) context.Context {
	newCtx := context.WithValue(ctx, userIdKey, nil)
	newCtx = context.WithValue(newCtx, userTokenKey, nil)
	newCtx = context.WithValue(newCtx, customStateKey, nil)
	newCtx = context.WithValue(newCtx, workloadAccessTokenKey, nil)
	return newCtx
}
