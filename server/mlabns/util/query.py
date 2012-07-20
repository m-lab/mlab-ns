import logging
import socket

from mlabns.util import message

class LookupQuery:
    def __init__(self):
        self.tool_id = None
        self.policy = None
        self.metro = None
        self.user_ipv4 = None
        self.user_ipv6 = None
        self.user_city = None
        self.user_country = None
        self.user_latitude = 0.0
        self.user_longitude = 0.0
        self.response_format = None

    def initialize_from_http_request(self, request):
        """Inizializes the lookup parameters from the HTTP request."""
        # TODO(claudiu) Add support for URLs of the type:
        # http://mlab-ns.appspot.com/tool-name/ipv6.
        parts = request.path.strip('/').split('/')
        self.tool_id = parts[0]

        try:
            socket.inet_pton(socket.AF_INET6, request.remote_addr)
            self.user_ipv6 = request.remote_addr
        except socket.error:
            self.user_ipv4 = request.remote_addr

        self.policy = request.get(message.POLICY)
        self.metro = request.get(message.METRO)
        self.response_format = request.get(message.RESPONSE_FORMAT)

        # Default to geo policy.
        if not self.policy:
            self.policy = message.POLICY_GEO

        if message.HEADER_CITY in request.headers:
            self.user_city = request.headers[message.HEADER_CITY]
        if message.HEADER_COUNTRY in request.headers:
            self.user_country = request.headers[message.HEADER_COUNTRY]
        if message.HEADER_LAT_LONG in request.headers:
            lat_long = request.headers[message.HEADER_LAT_LONG]
            try:
                self.user_latitude, self.user_longitude = [
                    float(x) for x in lat_long.split(',')]
            except ValueError:
                # TODO(claudiu) Use geolocation data from Maxmind.
                # Log all these cases without geolocation info.
                logging.error('Bad geo coordinates %s', lat_long)

