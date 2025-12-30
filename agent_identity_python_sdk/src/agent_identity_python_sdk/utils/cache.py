import threading
import time
from typing import Dict, Tuple, Optional
from collections import OrderedDict

from ..model.stscredential import STSCredential

# Default maximum number of cache entries
DEFAULT_MAX_CACHE_SIZE = 100

_sts_credential_cache: OrderedDict[str, Tuple[STSCredential, float]] = OrderedDict()
_cache_lock = threading.RLock()
_max_cache_size: int = DEFAULT_MAX_CACHE_SIZE

def set_max_cache_size(max_size: int):
    """
    Set the maximum size of the cache
    
    Args:
        max_size: Maximum number of cache entries
    """
    global _max_cache_size
    with _cache_lock:
        _max_cache_size = max_size
        # If current cache exceeds the newly set maximum, remove excess entries
        while len(_sts_credential_cache) > _max_cache_size:
            _sts_credential_cache.popitem(last=False)

def get_cached_credential(cache_key: str) -> Optional[STSCredential]:
    """
    Get credential from cache
    
    Args:
        cache_key: Cache key
        
    Returns:
        STSCredential object or None (if not found or expired)
    """
    with _cache_lock:
        if cache_key in _sts_credential_cache:
            cached_credential, expire_time = _sts_credential_cache[cache_key]
            if time.time() < expire_time:
                # Move to end (mark as recently used)
                _sts_credential_cache.move_to_end(cache_key)
                return cached_credential
            else:
                # Remove expired entry
                del _sts_credential_cache[cache_key]
        return None

def store_credential_in_cache(cache_key: str, credential: STSCredential, ttl: float = 600):
    """
    Store credential in cache
    
    Args:
        cache_key: Cache key
        credential: Credential to cache
        ttl: Time to live (in seconds), default is 600 seconds
    """
    with _cache_lock:
        expire_time = time.time() + ttl
        _sts_credential_cache[cache_key] = (credential, expire_time)
        _sts_credential_cache.move_to_end(cache_key)  # Mark as recently used
        
        # If cache exceeds maximum size, remove least recently used entry
        if len(_sts_credential_cache) > _max_cache_size:
            _sts_credential_cache.popitem(last=False)