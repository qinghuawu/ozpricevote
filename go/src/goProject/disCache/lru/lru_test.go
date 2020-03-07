package lru

import (
	"testing"
)

type String string

func (s String) Len() int{
	return len(s)
}

func TestCache_Get(t *testing.T) {
	lru := New(int64(1))
	lru.Add("Key1", String("1234"))
	if v, ok := lru.Get("Key1"); ok {
		t.Fatal("cache miss Key1=1234 failed", v.(String), String("1234"))
	}
	lru.maxBytes = int64(12)
	lru.Add("Key1", String("1234"))
	if v, ok := lru.Get("Key1"); !ok || v.(String) != String("1234") {
		t.Fatal("cache hit Key1=1234 failed", v.(String), String("1234"))
	}
	if _, ok := lru.Get("Key2"); ok {
		t.Fatalf("cache miss key2 failed")
	}
	lru.Add("Key2", String("12345"))
	if v, ok := lru.Get("Key2"); !ok || v.(String) != String("12345") {
		t.Fatal("cache hit Key2=12345 failed", v.(String), String("12345"))
	}
	if v, ok := lru.Get("Key1"); ok {
		t.Fatal("cache delete Key1=1234 failed", v.(String), String("1234"))
	}
}
