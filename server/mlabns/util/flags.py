import gflags

FLAGS = gflags.FLAGS

# Arguments accepted in the query string of alookup request
gflags.DEFINE_string('policy', 'policy', '')
gflags.DEFINE_string('geo', 'geo', '')
gflags.DEFINE_string('ip', 'ip', '')

gflags.DEFINE_string(
    'policy_metro','metro','The metro policy')
gflags.DEFINE_string(
    'policy_geo','geo','The "geo" policy')
gflags.DEFINE_string(
    'address_family','address_family','The address family argument')
gflags.DEFINE_string(
    'ipv4','ipv4','The IPv4 address_family')
gflags.DEFINE_string(
    'ipv6','ipv6','The IPv6 address_family')
gflags.DEFINE_string(
    'ciphertext','ciphertext','The ciphertext field in a registration message')
gflags.DEFINE_string(
    'city','city','The city field in a registration message')
gflags.DEFINE_string(
    'country','country','The country field in a registration message')
gflags.DEFINE_string(
    'entity','entity','The entity field in a registration message')
gflags.DEFINE_string(
    'site','site','The entity value in a registration message')
gflags.DEFINE_string(
    'sliver_tool','sliver_tool','Entity value in a registration message')
gflags.DEFINE_string(
    'format','format',' Query string argument')
gflags.DEFINE_string(
    'html','html','Value of the format argument')
gflags.DEFINE_string(
    'json','json','Value of the format argument')
gflags.DEFINE_string(
    'fqdn_ipv4','fqdn_ipv4','Value of the format argument')
gflags.DEFINE_string(
    'fqdn_ipv4','fqdn_ipv4','Value of the format argument')
gflags.DEFINE_string(
    'header_city','X-AppEngine-City','HTTP header.')
gflags.DEFINE_string(
    'header_country','X-AppEngine-Country','HTTP header.')
gflags.DEFINE_string(
    'header_lat_long','X-AppEngine-CityLatLong','HTTP header.')
gflags.DEFINE_string(
    'header_lat_long','X-AppEngine-CityLatLong','HTTP header.')

# Attributes of the SliverTool entity. This fields are used in the
# RegistrationMessage and UpdateMessage respectively.
gflags.DEFINE_string('http_port', 'http_port', '')
gflags.DEFINE_string('lat_long', 'lat_long', '')
gflags.DEFINE_string('metro', 'metro', '')
gflags.DEFINE_string('server_id', 'server_id', '')
gflags.DEFINE_string('server_port', 'server_port', '')
gflags.DEFINE_string('site_id', 'site_id', '')
gflags.DEFINE_string('slice_id', 'slice_id', '')
gflags.DEFINE_string('sliver_ipv4', 'sliver_ipv4', '')
gflags.DEFINE_string('sliver_ipv6', 'sliver_ipv6', '')
gflags.DEFINE_string('status_ipv4', 'status_ipv4', '')
gflags.DEFINE_string('status_ipv6', 'status_ipv6', '')
gflags.DEFINE_string('tool_id', 'tool_id', '')
gflags.DEFINE_string('timestamp', 'timestamp', '')
gflags.DEFINE_string('online', 'online', '')
gflags.DEFINE_string('offline', 'offline', '')
gflags.DEFINE_string('error', 'error', '')
gflags.DEFINE_string('signature', 'sign', '')
gflags.DEFINE_string('addr_ipv4', 'addr_ipv4', '')
gflags.DEFINE_string('addr_ipv6', 'addr_ipv6', '')





