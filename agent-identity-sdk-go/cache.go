package agentidentity

import (
	"time"

	"github.com/aliyun/agent-identity-dev-kit/agent-identity-sdk-go/internal/cache"
)

// Global cache instance
var globalCache = cache.New(100)

// StoreCredentialInCache stores a credential in the LRU cache.
// Default TTL is 600 seconds.
func StoreCredentialInCache(cacheKey string, credential *STSCredential, ttl ...time.Duration) {
	if cacheKey == "" || credential == nil {
		return
	}
	globalCache.Store(cacheKey, credential, ttl...)
}

// GetCachedCredential retrieves a credential from the cache.
// Returns nil if not found or expired.
func GetCachedCredential(cacheKey string) *STSCredential {
	v := globalCache.Get(cacheKey)
	if v == nil {
		return nil
	}
	return v.(*STSCredential)
}

// SetMaxCacheSize updates the maximum cache size.
// If the current cache exceeds the new size, oldest entries are evicted.
func SetMaxCacheSize(maxSize int) {
	globalCache.SetMaxSize(maxSize)
}
