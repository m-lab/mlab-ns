EPSILON = 1.005

# Maximum period in seconds between two consecutive updates.
# If there is no liveness check during this interval, the sliver
# won't be considered in the server selection.
# TODO(claudiu) This is only for debug. The true value should
# probably be no more than one hour.
MAX_FETCHED_RESULTS = 500

METRO           = 'metro'
POLICY_METRO    = 'metro'
STATUS_ERROR    = 'error'
STATUS_OFFLINE  = 'offline'
STATUS_ONLINE   = 'online'
STATUS_REGISTERED = 'init'
SUCCESS         = 'SUCCESS'
TIMESTAMP       = 'timestamp'
TOOL_ID         = 'tool_id'
#UPDATE_INTERVAL = 3600 * 24 * 60

# 10 minutes.
UPDATE_INTERVAL = 10 * 60
URL             = 'url'
USER_CITY       = 'user_city'
USER_COUNTRY    = 'user_country'
USER_IP         = 'user_ip'
USER_LAT_LONG   = 'user_lat_long'
