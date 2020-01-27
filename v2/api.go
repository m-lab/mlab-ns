// Package v2 defines the request API for the location service.
//
// While well provisioned, the M-Lab Platform is finite. On occassion, due to
// peak usage, local service outages, or abnormal client behavior the location
// service must decline to schedule new user requests. This is necesssary to
// safegaurd measurement quality of your measurements and those of others. The
// v2 API classifies user requests into three priorities.
//
//  API-key | Access Token | Priority
//  --------------------------------------------------------
//  YES     | YES          | API-Key, High Availability Pool
//  YES     | NO           | API-Key, Best Effort Pool
//  NO      | NO           | Global Best Effort Pool
//
// For highest priority access to the platform, register an API key and use the
// QueryResult.NextRequest.URL when provided.
package v2

import "time"

// QueryResult is returned by the location service in response to query
// requests.
type QueryResult struct {

	// Error contains information about request failures.
	Error *Error `json:"error,omitempty"`

	// NextRequest defines the earliest time that a client should make a new
	// request using the included URL.
	//
	// Under normal circumstances, NextRequest is provided *with* Results. The
	// next request time is sampled from an exponential distribution such that
	// inter-request times are memoryless. Under abnormal circumstances, such as
	// high single-client request rates or target capacity exhaustion, the next
	// request is provided *without* Results.
	//
	// Non-interactive or batch clients SHOULD schedule measurements with this
	// value. All clients SHOULD NOT make additional requests more often than
	// NextRequest. The server MAY reject requests indefinitely when clients do
	// not respect this limit.
	NextRequest *NextRequest `json:"next_request,omitempty"`

	// Results contains an array of Targets matching the client request.
	Results []Target `json:"results,omitempty"`
}

// NextRequest contains a URL for scheduling the next request. The URL embeds an
// access token that will be valid after `NotBefore`. The access token will
// remain valid until it `Expires`. If a client uses an expired URL, the request
// will be handled as if no access token were provided, i.e. using a lower
// priority class.
type NextRequest struct {
	NotBefore time.Time `json:"not_before"` // Valid after.
	Expires   time.Time `json:"expires"`    // Valid until.
	URL       string    `json:"url"`
}

// Target contains information needed to run a measurement to a measurement
// service on a single M-Lab machine. Measurement services may support multiple
// resources. A Target contains at least one measurement service resource in
// URLs.
type Target struct {

	// Machine is the FQDN of the machine hosting the measurement service.
	Machine string `json:"machine"`

	// URLs contains measurement service resource names and the complete URL for
	// running a measurement.
	//
	// A measurement service may support multiple resources (e.g. upload,
	// download, etc). Each key is a resource name and the value is a complete
	// URL with protocol, service name, port, and parameters fully specified.
	URLs map[string]string `json:"urls"`
}

// Error describes an error condition that prevents the server from completing a
// QueryResult.
type Error struct {
	// RFC7807 Fields for "Problem Details".
	Type     string `json:"type"`
	Title    string `json:"title"`
	Status   int    `json:"status"`
	Detail   string `json:"detail,omitempty"`
	Instance string `json:"instance,omitempty"`
}
