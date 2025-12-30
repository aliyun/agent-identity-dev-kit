"""Tests for the cache module."""
import time
import threading
from agent_identity_python_sdk.utils.cache import (
    set_max_cache_size, get_cached_credential, store_credential_in_cache,
    DEFAULT_MAX_CACHE_SIZE, _sts_credential_cache, _cache_lock
)
from agent_identity_python_sdk.model.stscredential import STSCredential


class TestCacheModule:
    """Test cases for the cache module."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Clear the cache before each test
        with _cache_lock:
            _sts_credential_cache.clear()
        # Reset to default size
        set_max_cache_size(DEFAULT_MAX_CACHE_SIZE)

    def test_store_and_get_credential_success(self):
        """Test storing and retrieving a credential successfully."""
        # Create a mock credential
        credential = STSCredential(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_token",
            expiration="2023-12-31T23:59:59Z"
        )
        
        # Store the credential
        store_credential_in_cache("test_key", credential, ttl=600)
        
        # Retrieve the credential
        retrieved = get_cached_credential("test_key")
        
        # Verify the credential was retrieved correctly
        assert retrieved is not None
        assert retrieved.access_key_id == "test_key_id"
        assert retrieved.access_key_secret == "test_key_secret"
        assert retrieved.security_token == "test_token"
        assert retrieved.expiration == "2023-12-31T23:59:59Z"

    def test_get_nonexistent_credential(self):
        """Test getting a credential that doesn't exist in cache."""
        result = get_cached_credential("nonexistent_key")
        assert result is None

    def test_credential_expiration(self):
        """Test that expired credentials are not returned."""
        credential = STSCredential(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret", 
            security_token="test_token",
            expiration="2023-12-31T23:59:59Z"
        )
        
        # Store with a very short TTL
        store_credential_in_cache("test_key", credential, ttl=0.01)  # 10ms TTL
        
        # Wait for it to expire
        time.sleep(0.02)  # 20ms, enough to exceed 10ms TTL
        
        # Try to retrieve the expired credential
        result = get_cached_credential("test_key")
        assert result is None

    def test_cache_size_limit(self):
        """Test that cache size limit is enforced."""
        # Set a small max cache size
        set_max_cache_size(2)
        
        # Add 3 items to cache
        cred1 = STSCredential(
            access_key_id="key1",
            access_key_secret="secret1",
            security_token="token1", 
            expiration="2023-12-31T23:59:59Z"
        )
        cred2 = STSCredential(
            access_key_id="key2", 
            access_key_secret="secret2",
            security_token="token2",
            expiration="2023-12-31T23:59:59Z"
        )
        cred3 = STSCredential(
            access_key_id="key3",
            access_key_secret="secret3", 
            security_token="token3",
            expiration="2023-12-31T23:59:59Z"
        )
        
        store_credential_in_cache("key1", cred1)
        store_credential_in_cache("key2", cred2)
        store_credential_in_cache("key3", cred3)  # This should trigger LRU eviction
        
        # Verify that the oldest entry was removed (key1) and the two newer ones remain
        assert get_cached_credential("key1") is None  # Should be evicted (LRU)
        assert get_cached_credential("key2") is not None  # Should remain
        assert get_cached_credential("key3") is not None  # Should remain

    def test_cache_size_reduction_removes_excess_entries(self):
        """Test that reducing cache size removes excess entries."""
        # Add more items than the default size
        for i in range(DEFAULT_MAX_CACHE_SIZE + 5):
            cred = STSCredential(
                access_key_id=f"key{i}",
                access_key_secret=f"secret{i}",
                security_token=f"token{i}",
                expiration="2023-12-31T23:59:59Z"
            )
            store_credential_in_cache(f"key{i}", cred)
        
        # Verify cache has default size entries
        assert len(_sts_credential_cache) == DEFAULT_MAX_CACHE_SIZE
        
        # Reduce cache size to smaller value
        new_size = DEFAULT_MAX_CACHE_SIZE - 3
        set_max_cache_size(new_size)
        
        # Verify cache now has the new size
        assert len(_sts_credential_cache) == new_size

    def test_recently_used_items_not_evicted(self):
        """Test that recently used items are not evicted in LRU."""
        set_max_cache_size(2)
        
        # Add 2 items
        cred1 = STSCredential(
            access_key_id="key1",
            access_key_secret="secret1",
            security_token="token1",
            expiration="2023-12-31T23:59:59Z"
        )
        cred2 = STSCredential(
            access_key_id="key2",
            access_key_secret="secret2", 
            security_token="token2",
            expiration="2023-12-31T23:59:59Z"
        )
        
        store_credential_in_cache("key1", cred1)
        store_credential_in_cache("key2", cred2)
        
        # Access key1 to make it recently used
        get_cached_credential("key1")
        
        # Add a third item - key2 should be evicted, not key1
        cred3 = STSCredential(
            access_key_id="key3",
            access_key_secret="secret3",
            security_token="token3", 
            expiration="2023-12-31T23:59:59Z"
        )
        store_credential_in_cache("key3", cred3)
        
        # Verify key1 is still in cache (recently used)
        assert get_cached_credential("key1") is not None
        # Verify key2 was evicted (least recently used)
        assert get_cached_credential("key2") is None
        # Verify key3 was added
        assert get_cached_credential("key3") is not None

    def test_different_ttl_values(self):
        """Test different TTL values work correctly."""
        credential = STSCredential(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_token",
            expiration="2023-12-31T23:59:59Z"
        )
        
        # Store with a 1 second TTL
        store_credential_in_cache("test_key", credential, ttl=1)
        
        # Should still be available immediately
        result = get_cached_credential("test_key")
        assert result is not None
        
        # Wait for it to expire
        time.sleep(1.1)
        
        # Should no longer be available
        result = get_cached_credential("test_key")
        assert result is None

    def test_cache_thread_safety(self):
        """Test that cache operations are thread-safe."""
        set_max_cache_size(10)
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(5):
                    cred = STSCredential(
                        access_key_id=f"key_{thread_id}_{i}",
                        access_key_secret=f"secret_{thread_id}_{i}",
                        security_token=f"token_{thread_id}_{i}",
                        expiration="2023-12-31T23:59:59Z"
                    )
                    cache_key = f"key_{thread_id}_{i}"
                    
                    # Store and immediately retrieve
                    store_credential_in_cache(cache_key, cred, ttl=10)
                    retrieved = get_cached_credential(cache_key)
                    
                    results.append((cache_key, retrieved is not None))
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {str(e)}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred in threads: {errors}"
        
        # Verify all operations succeeded
        successful_ops = sum(1 for _, success in results if success)
        assert successful_ops == 25  # 5 threads * 5 operations each

    def test_zero_ttl_credential_immediately_expired(self):
        """Test that credentials with 0 TTL are immediately expired."""
        credential = STSCredential(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_token",
            expiration="2023-12-31T23:59:59Z"
        )
        
        # Store with 0 TTL
        store_credential_in_cache("test_key", credential, ttl=0)
        
        # Should be immediately expired
        result = get_cached_credential("test_key")
        assert result is None

    def test_large_ttl_values(self):
        """Test that large TTL values work correctly."""
        credential = STSCredential(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_token",
            expiration="2023-12-31T23:59:59Z"
        )
        
        # Store with a large TTL
        store_credential_in_cache("test_key", credential, ttl=3600)  # 1 hour
        
        # Should still be available immediately
        result = get_cached_credential("test_key")
        assert result is not None

    def test_cache_key_case_sensitivity(self):
        """Test that cache keys are case sensitive."""
        cred1 = STSCredential(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_token1",
            expiration="2023-12-31T23:59:59Z"
        )
        cred2 = STSCredential(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_token2",
            expiration="2023-12-31T23:59:59Z"
        )
        
        store_credential_in_cache("Key", cred1)
        store_credential_in_cache("key", cred2)
        
        # Should be able to retrieve both with different keys
        result1 = get_cached_credential("Key")
        result2 = get_cached_credential("key")
        
        assert result1 is not None
        assert result2 is not None
        assert result1.security_token == "test_token1"
        assert result2.security_token == "test_token2"

    def test_max_cache_size_zero(self):
        """Test cache behavior when max size is set to zero."""
        credential = STSCredential(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_token",
            expiration="2023-12-31T23:59:59Z"
        )
        
        # Set max cache size to 0
        set_max_cache_size(0)
        
        # Store a credential
        store_credential_in_cache("test_key", credential)
        
        # Should not be stored due to size limit
        result = get_cached_credential("test_key")
        assert result is None

    def test_cache_clear_after_size_reduction(self):
        """Test that cache is properly cleared when size is reduced to 0."""
        credential = STSCredential(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_token",
            expiration="2023-12-31T23:59:59Z"
        )
        
        # Store a credential
        store_credential_in_cache("test_key", credential)
        assert get_cached_credential("test_key") is not None
        
        # Reduce size to 0
        set_max_cache_size(0)
        
        # Should no longer be in cache
        result = get_cached_credential("test_key")
        assert result is None