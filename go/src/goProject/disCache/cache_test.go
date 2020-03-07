package disCache

import (
	"fmt"
	"reflect"
	"testing"
)

var db = map[string]string {
	"Key1": "Test1",
	"Key2": "Test2",
	"Key3": "Test3",
}

var getFromDB GetterFunc = func(key string) (ByteView, error) {
	if v, ok := db[key]; ok {
		return ByteView{[]byte(v)}, nil
	}
	return ByteView{}, fmt.Errorf("%v not exist in DB", key)
}

func Test_GetFromDB(t *testing.T) {
	if v, err := getFromDB("Key1"); err != nil || !reflect.DeepEqual(v, ByteView{[]byte("Test1")}) {
		t.Fatalf("Key1 error")
	}
	if v, err := getFromDB("key1"); err == nil {
		t.Fatalf("key1 error: %v", v)
	}
}

func Test_cache(t *testing.T) {
	myCache := NewCache(1, getFromDB, 100, [128]int{})
	if v, err := myCache.Get("key1"); err == nil {
		t.Fatalf("key1 error in cache: %v", v)
	}
	if v, err := myCache.Get("Key2"); err != nil || !reflect.DeepEqual(v, ByteView{[]byte("Test2")}){
		t.Fatalf("Key1 error in cache: %v", v)
	}
}