import gflags

FLAGS = gflags.FLAGS

# Arguments accepted in the query string of a lookup request
# policy, address_family, format, ip, city, country. For more
# information see the design doc at http://goo.gl/48S22.

# http://mlabns.appspot.com/npad?policy=[geo|metro]
gflags.DEFINE_string('policy', 'policy', '')
gflags.DEFINE_string('policy_metro', 'metro', '')
gflags.DEFINE_string('policy_geo', 'geo', '')

# For debugging only:
# http://mlabns.appspot.com/npad?ip=ip_address
gflags.DEFINE_string('ip', 'ip', '')

# http://mlabns.appspot.com/npad?address_family=[ipv4|ipv6]
gflags.DEFINE_string('address_family', 'address_family', '')
gflags.DEFINE_string('address_family_ipv4', 'ipv4','')
gflags.DEFINE_string('address_family_ipv6', 'ipv6','')

# e.g., http://mlabns.appspot.com/npad?format=[json|html]
gflags.DEFINE_string('format','format', '')
gflags.DEFINE_string('format_html', 'html', '')
gflags.DEFINE_string('format_json', 'json', '')

# e.g., http://mlabns.appspot.com/npad?city=Rome
gflags.DEFINE_string('city', 'city', '')

# e.g., http://mlabns.appspot.com/npad?country=US
gflags.DEFINE_string('country', 'country', '')



##############
# message.py #
##############
gflags.DEFINE_string('entity', 'entity', '')
gflags.DEFINE_string('entity_site', 'site', '')
gflags.DEFINE_string('entity_sliver_tool', 'sliver_tool', '')

gflags.DEFINE_string('ciphertext', 'ciphertext', '')

gflags.DEFINE_string('header_city', 'X-AppEngine-City', '')
gflags.DEFINE_string('header_country', 'X-AppEngine-Country', '')
gflags.DEFINE_string('header_lat_long', 'X-AppEngine-CityLatLong', '')


# Attributes of the SliverTool and Site entities. This fields are used in the
# RegistrationMessage and UpdateMessage respectively.

gflags.DEFINE_string('site_id', 'site_id', '')

gflags.DEFINE_string('slice_id', 'slice_id', '')

gflags.DEFINE_string('tool_id', 'tool_id', '')

gflags.DEFINE_string('http_port', 'http_port', '')

gflags.DEFINE_string('lat_long', 'lat_long', '')

gflags.DEFINE_string('metro', 'metro', '')

gflags.DEFINE_string('server_id', 'server_id', '')

gflags.DEFINE_string('server_port', 'server_port', '')

gflags.DEFINE_string('sliver_ipv4', 'sliver_ipv4', '')

gflags.DEFINE_string('sliver_ipv6', 'sliver_ipv6', '')

gflags.DEFINE_string('status_ipv4', 'status_ipv4', '')

gflags.DEFINE_string('status_ipv6', 'status_ipv6', '')

gflags.DEFINE_string('timestamp', 'timestamp', '')

gflags.DEFINE_string('signature', 'sign', '')

gflags.DEFINE_string('status_online', 'online', '')
gflags.DEFINE_string('status_offline', 'offline', '')
gflags.DEFINE_string('status_error', 'error', '')

gflags.DEFINE_string('addr_ipv4', 'addr_ipv4', '')
gflags.DEFINE_string('addr_ipv6', 'addr_ipv6', '')

# Earth radius used to compute the distance between two geo-points.
gflags.DEFINE_int('radius', 6371, '')
