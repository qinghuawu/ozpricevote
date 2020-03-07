package lru

import (
	"container/list"
	"sync"
)

type Cache struct {
	maxBytes int64
	nbytes   int64
	ll       *list.List
	hash     map[string]*list.Element
	mu       sync.Mutex
}

type Value interface {
	Len() int
}

type entry struct {
	key   string
	value Value
}

func New(maxBytes int64) *Cache {
	return &Cache{
		maxBytes: maxBytes,
		ll:       list.New(),
		hash:     make(map[string]*list.Element),
	}
}

func (c *Cache) Get(key string) (value Value, ok bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if ele, ok := c.hash[key]; ok {
		c.ll.MoveToFront(ele)
		kv := ele.Value.(*entry)
		return kv.value, true
	}
	return
}

func (c *Cache) removeOldest() {
	if ele := c.ll.Back(); ele != nil {
		c.ll.Remove(ele)
		kv := ele.Value.(*entry)
		delete(c.hash, kv.key)
		c.nbytes -= int64(len(kv.key)) + int64(kv.value.Len())
	}
}

func (c *Cache) Add(key string, value Value) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if ele, ok := c.hash[key]; ok {
		c.ll.MoveToFront(ele)
		kv := ele.Value.(*entry)
		c.nbytes += int64(value.Len()) - int64(kv.value.Len())
		kv.value = value
		return
	}
	ele := c.ll.PushFront(&entry{
		key:   key,
		value: value,
	})
	c.hash[key] = ele
	c.nbytes += int64(len(key)) + int64(value.Len())
	for c.nbytes > c.maxBytes {
		c.removeOldest()
	}
}
