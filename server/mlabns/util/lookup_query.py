from mlabns.third_party import ipaddr
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import maxmind

import logging

def _is_valid_ip(ip):
    """Indicates whether this is a valid IP string.

    Args:
      ip: A string containing an IP address in IPv4 or IPv6 format.

    Returns:
      True if the IP address is a well-formed and legal IP address.
    """
    return _is_valid_ipv4(ip) or _is_valid_ipv6(ip)

def _is_valid_ipv4(ip):
    try:
        ipaddr.IPv4Address(ip)
        return True
    except ipaddr.AddressValueError:
        return False

def _is_valid_ipv6(ip):
    try:
        ipaddr.IPv6Address(ip)
        return True
    except ipaddr.AddressValueError:
        return False

class LookupQuery:
    def __init__(self):
        self.tool_id = None
        self.policy = None
        self.metro = None
        self.response_format = None
        self._geolocation_type = None
        self.ip_address = None
        self.tool_address_family = None
        self.city = None
        self.country = None
        self.latitude = None
        self.longitude = None
        self.distance = None
        self._ip_is_explicit = False
        self._user_defined_city = None
        #TODO(mtlynch): We are using two country fields to store the same type
        # of information, but using user_defined_country in some cases and
        # country in others. We should consolidate them into a single field.
        self.user_defined_country = None
        self._user_defined_latitude = None
        self._user_defined_longitude = None
        self._gae_city = None
        self._gae_country = None
        self._gae_latitude = None
        self._gae_longitude = None
        self._maxmind_city = None
        self._maxmind_country = None
        self._maxmind_latitude = None
        self._maxmind_longitude = None

    def initialize_from_http_request(self, request):
        """Initializes the lookup parameters from the HTTP request.

        Args:
            request: An instance of google.appengine.webapp.Request.
        """
        self.tool_id = request.path.strip('/').split('/')[0]
        self._set_response_format(request)
        self._set_ip_address(request)
        self._set_tool_address_family(request)
        self._set_geolocation(request)
        self.metro = request.get(message.METRO, default_value=None)
        self._set_policy(request)

    def _set_response_format(self, request):
        self.response_format = request.get(
            message.RESPONSE_FORMAT,
            default_value=message.DEFAULT_RESPONSE_FORMAT)
        if self.response_format not in message.VALID_FORMATS:
            logging.warning('Non valid response format %s.',
                            self.response_format)
            self.response_format = message.DEFAULT_RESPONSE_FORMAT

    def _set_ip_address(self, request):
        user_defined_ip = request.get(message.REMOTE_ADDRESS)

        # User-defined IP overrides the request source IP
        if (_is_valid_ip(user_defined_ip) and
                user_defined_ip != request.remote_addr):
            self.ip_address = user_defined_ip
            self._ip_is_explicit = True
        else:
            self.ip_address = request.remote_addr
            self._ip_is_explicit = False

    def _set_tool_address_family(self, request):
        tool_address_family = request.get(message.ADDRESS_FAMILY)
        valid_address_families = (message.ADDRESS_FAMILY_IPv4,
                                  message.ADDRESS_FAMILY_IPv6)
        if tool_address_family in valid_address_families:
          self.tool_address_family = tool_address_family

    def _set_geolocation(self, request):
        self._set_appengine_geolocation(request)
        self._user_defined_city = request.get(message.CITY)
        self.user_defined_country = request.get(message.COUNTRY)
        input_latitude, input_longitude = self._get_user_defined_lat_lon(
            request)

        if (input_latitude is not None) and (input_longitude is not None):
            self._geolocation_type = constants.GEOLOCATION_USER_DEFINED
            self._user_defined_latitude = input_latitude
            self._user_defined_longitude = input_longitude
        elif self._ip_is_explicit or self.user_defined_country:
            if self._ip_is_explicit:
              ip_address_to_geolocate = self.ip_address
            else:
              ip_address_to_geolocate = None
            self._geolocation_type = constants.GEOLOCATION_MAXMIND
            self._set_maxmind_geolocation(ip_address_to_geolocate,
                                          self.user_defined_country,
                                          self._user_defined_city)
        elif self._gae_latitude and self._gae_longitude:
            self._geolocation_type = constants.GEOLOCATION_APP_ENGINE
        else:
            self._geolocation_type = constants.GEOLOCATION_MAXMIND
            self._set_maxmind_geolocation(self.ip_address, self._gae_country,
                                          self._gae_city)

        if self._geolocation_type == constants.GEOLOCATION_USER_DEFINED:
            self.city = self._user_defined_city
            self.country = self.user_defined_country
            self.latitude = self._user_defined_latitude
            self.longitude = self._user_defined_longitude
        elif self._geolocation_type == constants.GEOLOCATION_MAXMIND:
            self.city = self._maxmind_city
            self.country = self._maxmind_country
            self.latitude = self._maxmind_latitude
            self.longitude = self._maxmind_longitude
        elif self._geolocation_type == constants.GEOLOCATION_APP_ENGINE:
            self.city = self._gae_city
            self.country = self._gae_country
            self.latitude = self._gae_latitude
            self.longitude = self._gae_longitude

    def _get_user_defined_lat_lon(self, request):
        """Retrieves and validates the user-defined lat/lon from the request.

        Retrieves the lat/lon fields from the query string of the request and
        validates that the values are in the correct format and in the legal
        range.

        Args:
            request: A webapp.Request instance.

        Returns:
            (lat, lon) as a 2-tuple of floats if the user provided valid values
            for both latitude and longitude.
            (None, None) if the values were not present or not valid.
        """
        MAX_LATITUDE_ABSOLUTE = 90.0
        MAX_LONGITUDE_ABSOLUTE = 180.0
        input_latitude = request.get(message.LATITUDE)
        input_longitude = request.get(message.LONGITUDE)

        if not input_latitude or not input_longitude:
            return None, None

        try:
            latitude = float(input_latitude)
            longitude = float(input_longitude)
        except ValueError:
            logging.error('Invalid user-defined lat, long (%s, %s).',
                           input_latitude, input_longitude)
            return None, None

        if ((abs(latitude) > MAX_LATITUDE_ABSOLUTE) or
                (abs(longitude) > MAX_LONGITUDE_ABSOLUTE)):
            logging.error('Lat/long out of range (%f, %f).',
                           latitude, longitude)
            return None, None

        return latitude, longitude

    def _set_maxmind_geolocation(self, ip_address, country, city):
        geo_record = maxmind.GeoRecord()
        if ip_address is not None:
            geo_record = maxmind.get_ip_geolocation(ip_address)
        elif city is not None and country is not None:
            geo_record = maxmind.get_city_geolocation(city, country)
        elif country is not None:
            geo_record = maxmind.get_country_geolocation(country)
        self._maxmind_city = geo_record.city
        self._maxmind_country = geo_record.country
        self._maxmind_latitude = geo_record.latitude
        self._maxmind_longitude = geo_record.longitude

    def _set_appengine_geolocation(self, request):
        """Adds geolocation info using the data provided by AppEngine.

        If the geolocation info is not included in the headers, it will
        use the data from MaxmindCityLocation/MaxmindCityBlock.

        Args:
            request: A webapp.Request instance.
        """
        if message.HEADER_CITY in request.headers:
            self._gae_city = request.headers[message.HEADER_CITY]
        if message.HEADER_COUNTRY in request.headers:
            self._gae_country = request.headers[message.HEADER_COUNTRY]
        if message.HEADER_LAT_LONG in request.headers:
            lat_long = request.headers[message.HEADER_LAT_LONG]
            try:
                self._gae_latitude, self._gae_longitude = [
                    float(x) for x in lat_long.split(',')]
            except ValueError:
                logging.error('GAE provided bad lat/long %s.', lat_long)

    def _set_policy(self, request):
        self.policy = request.get(message.POLICY, default_value=None)
        if ((self._user_defined_latitude and
             self._user_defined_longitude) or
                self._ip_is_explicit):
            if self.policy != message.POLICY_GEO and \
               self.policy != message.POLICY_GEO_OPTIONS:
                if self.policy:
                     logging.warning(
                         'Lat/longs user-defined, but policy is %s.',
                         self.policy)
                self.policy = message.POLICY_GEO
            return
        if self.user_defined_country is not None:
            if self.policy != message.POLICY_COUNTRY and \
                self.policy != message.POLICY_GEO:
                if self.policy:
                    logging.warning(
                        'Country user-defined, but policy is %s.',
                        self.policy)
                self.policy = message.POLICY_GEO
            return
        if self.metro is not None:
            if self.policy != message.POLICY_METRO:
                if self.policy:
                    logging.warning(
                         'Metro defined, but policy is %s', self.policy)
                self.policy = message.POLICY_METRO
            return
        if self.policy == message.POLICY_GEO:
            if self.latitude is None or self.longitude is None:
                logging.warning('Policy geo, but no geo args defined.')
                self.policy = message.POLICY_RANDOM
            return
        if self.policy == message.POLICY_COUNTRY:
            if self.user_defined_country is None:
                logging.warning('Policy country, but arg country not defined.')
                self.policy = self._get_default_policy()
            return
        if self.policy == message.POLICY_METRO:
            if self.metro is None:
                logging.warning('Policy metro, but arg metro not defined.')
                self.policy = self._get_default_policy()
            return
        if self.policy  ==  message.POLICY_RANDOM:
            return
        if self.policy == message.POLICY_GEO_OPTIONS:
            return
        if self.policy == message.POLICY_ALL:
            return
        if self.policy:
            logging.warning('Non valid policy %s.', self.policy)
        self.policy = self._get_default_policy()

    def _get_default_policy(self):
        if self.latitude is not None and self.longitude is not None:
            return message.POLICY_GEO
        return message.POLICY_RANDOM
