# These constants are all possible fields in a message.
ADDRESS_FAMILY = 'address_family'
ADDRESS_FAMILY_IPv4 = 'ipv4'
ADDRESS_FAMILY_IPv6 = 'ipv6'

CITY = 'city'
COUNTRY = 'country'

RESPONSE_FORMAT = 'format'
FORMAT_HTML = 'html'
FORMAT_JSON = 'json'
FORMAT_MAP = 'map'
FORMAT_REDIRECT = 'redirect'
FORMAT_BT = 'bt'
VALID_FORMATS = [FORMAT_HTML, FORMAT_JSON, FORMAT_MAP, FORMAT_REDIRECT,
                 FORMAT_BT]
DEFAULT_RESPONSE_FORMAT = FORMAT_JSON

HEADER_CITY = 'X-AppEngine-City'
HEADER_COUNTRY = 'X-AppEngine-Country'
HEADER_LAT_LONG = 'X-AppEngine-CityLatLong'
LATITUDE = 'lat'
LONGITUDE = 'lon'
METRO = 'metro'

POLICY = 'policy'
POLICY_GEO = 'geo'
POLICY_GEO_OPTIONS = 'geo_options'
POLICY_METRO = 'metro'
POLICY_RANDOM = 'random'
POLICY_COUNTRY = 'country'
POLICY_ALL = 'all'

REMOTE_ADDRESS = 'ip'
NO_IP_ADDRESS = 'off'
STATUS = 'status'
STATUS_IPv4 = 'status_ipv4'
STATUS_IPv6 = 'status_ipv6'
STATUS_OFFLINE = 'offline'
STATUS_ONLINE = 'online'
URL = 'url'
