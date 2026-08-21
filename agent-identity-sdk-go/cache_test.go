package agentidentity

import (
	"fmt"
	"sync"
	"testing"
	"time"
)

// ============================================================================
// cache.go tests
// ============================================================================

func TestStoreAndGetCachedCredential(t *testing.T) {
	cred := &STSCredential{
		AccessKeyId:     "ak-123",
		AccessKeySecret: "sk-456",
		SecurityToken:   "st-789",
		Expiration:      "2099-01-01T00:00:00Z",
	}

	key := "test-cache-key-" + generateUUID()
	StoreCredentialInCache(key, cred, 600*time.Second)

	got := GetCachedCredential(key)
	if got == nil {
		t.Fatal("expected cached credential, got nil")
	}
	if got.AccessKeyId != "ak-123" {
		t.Fatalf("expected ak-123, got %s", got.AccessKeyId)
	}
	if got.AccessKeySecret != "sk-456" {
		t.Fatalf("expected sk-456, got %s", got.AccessKeySecret)
	}
	if got.SecurityToken != "st-789" {
		t.Fatalf("expected st-789, got %s", got.SecurityToken)
	}
}

func TestGetCachedCredential_NotFound(t *testing.T) {
	got := GetCachedCredential("nonexistent-key")
	if got != nil {
		t.Fatal("expected nil for nonexistent key")
	}
}

func TestCachedCredential_Expires(t *testing.T) {
	key := "test-expire-key-" + generateUUID()
	cred := &STSCredential{
		AccessKeyId: "ak-expiring-" + key,
	}

	StoreCredentialInCache(key, cred, 1*time.Second)

	got := GetCachedCredential(key)
	if got == nil {
		t.Fatal("expected credential before expiry")
	}

	time.Sleep(1100 * time.Millisecond)

	got = GetCachedCredential(key)
	if got != nil {
		t.Fatal("expected nil for expired credential")
	}
}

func TestSetMaxCacheSize(t *testing.T) {
	key := "test-maxsize-key-" + generateUUID()

	SetMaxCacheSize(1)

	cred1 := &STSCredential{AccessKeyId: "ak-1"}
	cred2 := &STSCredential{AccessKeyId: "ak-2"}

	StoreCredentialInCache(key+"-1", cred1, 600*time.Second)
	StoreCredentialInCache(key+"-2", cred2, 600*time.Second)

	got1 := GetCachedCredential(key + "-1")
	got2 := GetCachedCredential(key + "-2")

	if got1 != nil {
		t.Fatal("expected first entry to be evicted")
	}
	if got2 == nil {
		t.Fatal("expected second entry to exist")
	}
	if got2.AccessKeyId != "ak-2" {
		t.Fatalf("expected ak-2, got %s", got2.AccessKeyId)
	}

	SetMaxCacheSize(100)
}

func TestStoreCredentialInCache_UpdateExisting(t *testing.T) {
	cred1 := &STSCredential{AccessKeyId: "ak-old"}
	cred2 := &STSCredential{AccessKeyId: "ak-new"}

	key := "test-update-key-" + generateUUID()
	StoreCredentialInCache(key, cred1, 600*time.Second)
	StoreCredentialInCache(key, cred2, 600*time.Second)

	got := GetCachedCredential(key)
	if got == nil {
		t.Fatal("expected cached credential")
	}
	if got.AccessKeyId != "ak-new" {
		t.Fatalf("expected ak-new, got %s", got.AccessKeyId)
	}
}

func TestStoreCredentialInCache_CustomTTL(t *testing.T) {
	cred := &STSCredential{AccessKeyId: "ak-ttl"}

	key := "test-ttl-key-" + generateUUID()
	StoreCredentialInCache(key, cred, 120*time.Second)

	got := GetCachedCredential(key)
	if got == nil {
		t.Fatal("expected cached credential")
	}
	if got.AccessKeyId != "ak-ttl" {
		t.Fatalf("expected ak-ttl, got %s", got.AccessKeyId)
	}
}

func TestStoreCredentialInCache_DefaultTTL(t *testing.T) {
	cred := &STSCredential{AccessKeyId: "ak-default"}

	key := "test-default-ttl-key-" + generateUUID()
	StoreCredentialInCache(key, cred)

	got := GetCachedCredential(key)
	if got == nil {
		t.Fatal("expected cached credential")
	}
	if got.AccessKeyId != "ak-default" {
		t.Fatalf("expected ak-default, got %s", got.AccessKeyId)
	}
}

func TestCacheConcurrency(t *testing.T) {
	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			key := fmt.Sprintf("concurrent-key-%d", i)
			cred := &STSCredential{AccessKeyId: fmt.Sprintf("ak-%d", i)}
			StoreCredentialInCache(key, cred, 600*time.Second)
			got := GetCachedCredential(key)
			if got == nil || got.AccessKeyId != fmt.Sprintf("ak-%d", i) {
				t.Errorf("concurrent access failed for key %d", i)
			}
		}(i)
	}
	wg.Wait()
}

func TestLRUOrder(t *testing.T) {
	SetMaxCacheSize(2)

	cred1 := &STSCredential{AccessKeyId: "ak-1"}
	cred2 := &STSCredential{AccessKeyId: "ak-2"}
	cred3 := &STSCredential{AccessKeyId: "ak-3"}

	StoreCredentialInCache("lru-key-1", cred1, 600*time.Second)
	StoreCredentialInCache("lru-key-2", cred2, 600*time.Second)

	GetCachedCredential("lru-key-1")

	StoreCredentialInCache("lru-key-3", cred3, 600*time.Second)

	got1 := GetCachedCredential("lru-key-1")
	got2 := GetCachedCredential("lru-key-2")
	got3 := GetCachedCredential("lru-key-3")

	if got1 == nil {
		t.Fatal("expected key-1 to still exist (was accessed)")
	}
	if got2 != nil {
		t.Fatal("expected key-2 to be evicted (was LRU)")
	}
	if got3 == nil {
		t.Fatal("expected key-3 to exist")
	}

	SetMaxCacheSize(100)
}
