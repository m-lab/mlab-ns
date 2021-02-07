package main_test

import (
	"context"
	"encoding/json"
	"log"
	"testing"

	"cloud.google.com/go/datastore"
	"google.golang.org/appengine"
	"google.golang.org/appengine/aetest"
	"google.golang.org/appengine/memcache"
)

type EndpointStats struct {
	AF             string  `datastore:"af"`
	Format         string  `datastore:"format"`
	Latitude       string  `datastore:"latitude"`
	Longitude      string  `datastore:"longitude"`
	Metro          string  `datastore:"metro"`
	Policy         string  `datastore:"policy"`
	Path           string  `datastore:"path"`
	Probability    float32 `datastore:"probability"`
	RequesterIP    string  `datastore:"requester_ip"`
	RequestsPerDay int32   `datastore:"requests_per_day"`
	TargetIP       string  `datastore:"target_ip"`
}

func xTestDSEntity(t *testing.T) {
	ctx := context.Background()

	// Set your Google Cloud Platform project ID.
	projectID := "mlab-nstesting"

	// Creates a client.
	client, err := datastore.NewClient(ctx, projectID)
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}
	// Sets the kind for the new entity.
	kind := "requests"
	// Sets the name/ID for the new entity.
	//       127.0.0.1#Davlik 2.1.0 (blah blah blah)#ndt_ssl#format#geo_options#af#ip#metro#lat#lon"
	name := "127.0.0.1#Davlik 2.1.0 (blah blah blah)#ndt_ssl##geo_options#####"
	// Creates a Key instance.
	key := datastore.NameKey(kind, name, nil)
	key.Namespace = "endpoint_stats"

	// Creates a Task instance.
	ep := EndpointStats{
		Path:     "ndt_ssl",
		Policy:   "geo_options",
		TargetIP: "127.0.0.1",
	}

	// Saves the new entity.
	if _, err := client.Put(ctx, key, &ep); err != nil {
		log.Fatalf("Failed to save task: %v", err)
	}
}

var (
	gctx context.Context
	gkey string
)

func Inner(b *testing.B) {
	for i := 0; i < b.N; i++ {
		if _, err := memcache.Get(gctx, gkey); err != nil {
			b.Fatal(err)
		}
	}
}

// This shows that memcache read, with aetest environment, takes about 400 usec.
func BenchmarkMemcacheGet(b *testing.B) {
	ctx, done, err := aetest.NewContext()
	if err != nil {
		b.Fatal(err)
	}
	defer done()
	ctx, err = appengine.Namespace(ctx, "memcache_requests")
	if err != nil {
		b.Fatal(err)
	}

	ep := EndpointStats{
		Path:     "ndt_ssl",
		Policy:   "geo_options",
		TargetIP: "127.0.0.1",
	}
	epJson, err := json.Marshal(ep)
	if err != nil {
		b.Fatal(err)
	}
	key := "foobar"
	// Set the item, unconditionally
	if err := memcache.Set(ctx, &memcache.Item{Key: key, Value: epJson}); err != nil {
		b.Fatalf("error setting item: %v", err)
	}

	// Get the item from the memcache
	if item, err := memcache.Get(ctx, key); err == memcache.ErrCacheMiss {
		b.Fatal("item not in the cache")
	} else if err != nil {
		b.Fatalf("error getting item: %v", err)
	} else {
		log.Printf("the lyric is %q", item.Value)
	}

	gkey = key
	gctx = ctx
	b.Run("MemcacheRead", Inner)
}
