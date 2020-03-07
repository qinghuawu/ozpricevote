package disCache

import (
	"fmt"
	"hash/crc32"
	"io/ioutil"
	"log"
	"net/http"
	"strings"
)

const defaultPath = "/discache/"

type HTTPPool struct {
	serverUrl string
	basePath  string
	urls      []string
	locCache *Cache
}

func NewHTTPPool(serverUrl string, urls []string, locCache *Cache) *HTTPPool {
	return &HTTPPool{
		serverUrl: serverUrl,
		basePath:  defaultPath,
		urls:      urls,
		locCache: locCache,
	}
}

func (p *HTTPPool) GetRemotely(key string, requestID int) (ByteView, error) {
	fmt.Printf("Swiching to remote cache [%v] for key [%v]\n", requestID, key)
	url := fmt.Sprintf("%v%v%v", p.urls[requestID], p.basePath, key)
	res, err := http.Get(url)
	if err != nil {
		return ByteView{}, err
	}

	if res.StatusCode != http.StatusOK {
		return ByteView{}, fmt.Errorf("remote server returned: %v", res.Status)
	}

	bytes, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return ByteView{}, fmt.Errorf("reading response body: %v", err)
	}
	return ByteView{bytes}, nil
}

func (p *HTTPPool) Get(key string) (ByteView, error) {
	id := p.locCache.GetNodeID(key)
	slot := crc32.ChecksumIEEE([]byte(key)) % uint32(len(p.locCache.slots))
	fmt.Printf("This server is Node [%v]; Key [%v] is on Slot [%v] on Node [%v]\n", p.locCache.id, key, slot, id)
	if id == p.locCache.id {
		return p.locCache.GetLocally(key)
	}
	return p.GetRemotely(key, id)
}

func (p *HTTPPool) Log(format string, v ...interface{}) {
	log.Printf("[Server %v] %v", p.serverUrl, fmt.Sprintf(format, v...))
}

func (p *HTTPPool) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path == "/favicon.ico" {
		return
	}
	if !strings.HasPrefix(r.URL.Path, p.basePath) {
		panic("HTTPPool serving unexpected path: " + r.URL.Path)
	}
	if p.locCache.cache == nil {
		http.Error(w, "Cache Uninitialized", http.StatusBadRequest)
		return
	}
	p.Log("%s %s", r.Method, r.URL.Path)
	// expect: /<basePath>/<key>
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) != 3 {
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}
	key := parts[2]
	if v, err := p.Get(key); err != nil {
		fmt.Println("HTTPError", v, err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
	} else {
		w.Header().Set("Content-Type", "text/html")
		w.Write(v.ByteSlice())
	}
}
