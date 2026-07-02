// Package cache provides a thread-safe LRU cache.
package cache

import (
	"container/list"
	"sync"
	"time"
)

type entry struct {
	key        string
	value      any
	expireTime int64 // unix timestamp in seconds
}

// Cache is a thread-safe LRU cache.
type Cache struct {
	mu      sync.RWMutex
	items   map[string]*list.Element
	order   *list.List
	maxSize int
}

// New creates a new Cache with the given max size.
func New(maxSize int) *Cache {
	return &Cache{
		items:   make(map[string]*list.Element),
		order:   list.New(),
		maxSize: maxSize,
	}
}

// Store stores a value in the LRU cache.
// Default TTL is 600 seconds.
func (c *Cache) Store(cacheKey string, value any, ttl ...time.Duration) {
	cacheTTL := 600 * time.Second
	if len(ttl) > 0 && ttl[0] > 0 {
		cacheTTL = ttl[0]
	}

	c.mu.Lock()
	defer c.mu.Unlock()

	expireTime := time.Now().Add(cacheTTL).Unix()

	if elem, ok := c.items[cacheKey]; ok {
		c.order.Remove(elem)
		delete(c.items, cacheKey)
	}

	e := &entry{
		key:        cacheKey,
		value:      value,
		expireTime: expireTime,
	}
	elem := c.order.PushFront(e)
	c.items[cacheKey] = elem

	for c.order.Len() > c.maxSize {
		oldest := c.order.Back()
		if oldest != nil {
			oldEntry := oldest.Value.(*entry)
			c.order.Remove(oldest)
			delete(c.items, oldEntry.key)
		}
	}
}

// Get retrieves a value from the cache.
// Returns nil if not found or expired.
func (c *Cache) Get(cacheKey string) any {
	c.mu.Lock()
	defer c.mu.Unlock()

	elem, ok := c.items[cacheKey]
	if !ok {
		return nil
	}

	e := elem.Value.(*entry)

	if time.Now().Unix() >= e.expireTime {
		c.order.Remove(elem)
		delete(c.items, cacheKey)
		return nil
	}

	c.order.MoveToFront(elem)
	return e.value
}

// SetMaxSize updates the maximum cache size.
func (c *Cache) SetMaxSize(maxSize int) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.maxSize = maxSize
	for c.order.Len() > c.maxSize {
		oldest := c.order.Back()
		if oldest != nil {
			oldEntry := oldest.Value.(*entry)
			c.order.Remove(oldest)
			delete(c.items, oldEntry.key)
		}
	}
}
