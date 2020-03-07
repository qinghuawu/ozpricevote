package disCache

import (
	"fmt"
	"goProject/disCache/lru"
	"hash/crc32"
)


type Getter interface {
	Get(key string) (ByteView, error)
}

type GetterFunc func(key string) (ByteView, error)

func (f GetterFunc) Get(key string) (ByteView, error) {
	return f(key)
}

func (c *Cache) GetNodeID(key string) int {
	return c.slots[(crc32.ChecksumIEEE([]byte(key)) % uint32(len(c.slots)))]
}

type Cache struct {
	id int // 0 to numOfCaches-1
	numCaches int
	cache  *lru.Cache
	getter Getter
	slots [128]int
}

func NewCache(id int, numCaches int, getter Getter, maxBytes int64, slots [128]int) *Cache {
	return &Cache{
		id: id,
		numCaches: numCaches,
		cache: lru.New(maxBytes),
		getter: getter,
		slots: slots,
	}
}

func (c *Cache) GetLocally(key string) (ByteView, error) {
	if v, ok := c.cache.Get(key); ok {
		fmt.Printf("Key [%v] hit the cache.\n", key)
		return v.(ByteView), nil
	}
	if v, err := c.getter.Get(key); err == nil {
		c.cache.Add(key, v)
		fmt.Printf("Key [%v] hit db and was added to the cache.\n", key)
		return v, nil
	}
	c.cache.Add(key, ByteView{})
	fmt.Printf("Key [%v] cannot be found in cache or db; Null was added to cache.\n", key)
	return ByteView{}, nil
}
