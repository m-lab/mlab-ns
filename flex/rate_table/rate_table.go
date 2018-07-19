// Package main contains the top level app-engine flex code to run the rate_table app.
package main

// 1.  Datastore stuff
// 2.  Memcache stuff
// 3.  Bigquery stuff
// 4.  Other logic

// Design elements:
//  a. Only this singleton app will write to datastore or memcache.  mlab-ns will be read only.
//  b. Since we update memcache, expiration time can be indefinite.  Any item in memcache will
//     be up to date.
//  c. We must remove any items in memcache that are not present in the newest table.
//  d. We will handle the BQ query, and directly build the table in memcache and datastore as
//     we read the query result.

func main() {

}
