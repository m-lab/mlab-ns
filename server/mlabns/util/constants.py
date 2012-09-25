# Maximum period in seconds between two consecutive updates.
# If there is no liveness check during this interval, the sliver
# won't be considered in the server selection.
# This value should be always a couple of minutes greater than the interval
# used to check for updates from nagios. See the configuration of the
# '/cron/check_status' job in cron.yaml.
UPDATE_INTERVAL = 15 * 60

# Earth radius in km.
EARTH_RADIUS = 6371

# Maximum number of entities fetched from datastore in a single query.
MAX_FETCHED_RESULTS = 500
