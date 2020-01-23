package v2

import "time"

// QueryResult is returned by the location service in response to query
// requests.
type QueryResult struct {

	// Error contains information about request failures.
	Error *Error `json:"error,omitempty"`

	// NextRequestAfter is the earliest time that a client should make a new
	// request.
	//
	// Under normal circumstances, this time is provided *with* Results. The
	// time is sampled from an exponential distribution such that inter-request
	// times are memoryless. Under abnormal circumstances, such as high
	// single-client request rates or target capacity exhaustion, this time is
	// provided *without* Results.
	//
	// Non-interactive or batch clients SHOULD schedule measurements with this
	// value. All clients SHOULD NOT make additional requests until
	// NextRequestAfter. The server MAY reject requests indefinitely when
	// clients fail to respect this limit.
	NextRequestAfter *time.Time `json:"next_request_after,omitempty"`

	// Results contains an array of Targets matching the client request.
	Results []Target `json:"results,omitempty"`
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
