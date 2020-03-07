package main

import (
	"fmt"
	"goProject/disCache"
	"log"
	"net/http"
	"strconv"
	"time"
)

var db = map[string]string{
	"Tom":  "630",
	"Jack": "589",
	"Sam":  "567",
	"DD": "DVA",
	"AKA": "QQQ",
}

func createCache(id int, maxBytes int64, addrs []string, slots [128]int) *disCache.Cache {
	getter := disCache.GetterFunc(func(key string) (disCache.ByteView, error) {
		fmt.Printf("search key [%v] in DB on Node [%v]\n", key, id)
		if v, ok := db[key]; ok {
			return disCache.ByteView{B: []byte(v)}, nil
		}
		return disCache.ByteView{}, fmt.Errorf("%s not exist in DB", key)
	})
	return disCache.NewCache(id, len(addrs), getter, maxBytes, slots)
}

func startServer(addr string, pool *disCache.HTTPPool, i int) {
	log.Printf("disCache is running at %v on Node [%v]", addr, i)
	log.Fatal(http.ListenAndServe(addr[7:], pool))
}

func main() {
	numCaches := 3
	var addrs []string
	var maxBytes int64 = 100
	var slots [128]int  // also for future features e.g. move a slot to another cache node

	for i:=0; i<numCaches; i++ {
		addrs = append(addrs, "http://localhost:"+strconv.Itoa(7110+i))
	}
	for i := range slots {
		var id int
		if i < 128/3 {
			id = 0
		} else if i < 128/3*2 {
			id = 1
		} else {
			id = 2
		}
		slots[i] = id
	}

	for i, addr := range addrs {
		pool := disCache.NewHTTPPool(addr, addrs, createCache(i, maxBytes, addrs, slots))
		go startServer(addr, pool, i)
	}
	time.Sleep(time.Minute * 3) // run for 3 min
}
