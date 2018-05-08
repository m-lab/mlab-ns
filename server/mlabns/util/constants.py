# Name of the entry in the Nagios table, containing the default
# configuration.
DEFAULT_NAGIOS_ENTRY = 'default'

# Name of the entry in the Prometheus table, containing the default
# configuration.
DEFAULT_PROMETHEUS_ENTRY = 'prometheus_default'

# String that the code will insert into SliverTool.tool_extra when the status
# source in Prometheus. For Nagios, tool_extra comes from the Nagios plugin that
# runs the check. This string for Prometheus is arbitrary and mostly used to
# signal that the current status was set from Prometheus data.
PROMETHEUS_TOOL_EXTRA = 'Prometheus was here \o/.'

# Earth radius in km.
EARTH_RADIUS = 6371

# Geolocation type values.
GEOLOCATION_APP_ENGINE = 'app_engine'
GEOLOCATION_MAXMIND = 'maxmind'
GEOLOCATION_USER_DEFINED = 'user_defined'

GEOLOCATION_MAXMIND_GCS_BUCKET = 'mlab-ns.appspot.com'
GEOLOCATION_MAXMIND_BUCKET_PATH = 'maxmind/current'
GEOLOCATION_MAXMIND_CITY_FILE = 'GeoLite2-City.mmdb'

# Maximum number of entities fetched from datastore in a single query.
MAX_FETCHED_RESULTS = 500

# Memcache namespace for map: tool_id -> list of sliver_tools.
MEMCACHE_NAMESPACE_TOOLS = 'memcache_tools'

# Service state status values from Nagios:
# OK            0
# WARNING       1
# CRITICAL      2
# UNKNOWN       3
NAGIOS_SERVICE_STATUS_OK = '0'

# Service state status values from Prometheus:
# OK            1
# CRITICAL      0
PROMETHEUS_SERVICE_STATUS_OK = '1'

# Maximum number of entities fetched from datastore in a single query.
GQL_BATCH_SIZE = 1000

# Name of the encryption key used by the RegistrationClient.
REGISTRATION_KEY_ID = 'admin'

# Country code representing an unknown country location. This is automatically
# added in the X-AppEngine-Country header if AppEngine cannot determine the
# location.
UNKNOWN_COUNTRY = 'ZZ'
UNKNOWN_CITY = 'Zion'

# URL to the privacy doc. All requests to http://mlab-ns.appspot.com/privacy
# will be redirected to this URL.
PRIVACY_DOC_URL = 'https://github.com/m-lab/mlab-ns/blob/master/MLAB-NS_PRIVACY_POLICY.md'

# URL to the design doc. All requests to http://mlab-ns.appspot.com/docs will be
# redirected to this URL.
DESIGN_DOC_URL = 'https://github.com/m-lab/mlab-ns/blob/master/DESIGN_DOC.md'
