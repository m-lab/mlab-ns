# Name of the entry in the Nagios table, containing the default
# configuration.
DEFAULT_NAGIOS_ENTRY = 'default'

#Nagios ip suffixes
NAGIOS_IPV4_SUFFIX = ''
NAGIOS_IPV6_SUFFIX = '_ipv6'

# Earth radius in km.
EARTH_RADIUS = 6371

# Geolocation type values.
GEOLOCATION_APP_ENGINE = 'app_engine'
GEOLOCATION_MAXMIND = 'maxmind'
GEOLOCATION_USER_DEFINED = 'user_defined'

GEOLOCATION_MAXMIND_CITY_FILE = 'mlabns/third_party/maxmind/latest'

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
PRIVACY_DOC_URL = 'https://docs.google.com/a/google.com/document/d/1yQp7CcZngY6AfndoxvIbz8MzxcO7MpjZaj_VGFWe6Mo/pub'

# URL to the design doc. All requests to http://mlab-ns.appspot.com/docs will be
# redirected to this URL.
DESIGN_DOC_URL = 'https://docs.google.com/document/d/1eJhS75EZHDLmC6exggStr_b1euiR24_MVBJc1L6eH2c/view'
