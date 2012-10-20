from mlabns.third_party import ipaddr
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import maxmind

import logging


class LookupQuery:
    def __init__(self):
        self.tool_id = None
        self.policy = None
        self.metro = None
        self.response_format = None
        self.geolocation_type = None
        self.ip_address = None
        self.address_family = None
        self.city = None
        self.country = None
        self.latitude = None
        self.longitude = None
        self.gae_ip = None
        self.user_defined_ip = None
        self.gae_af = None
        self.user_defined_af = None
        self.user_defined_city = None
        self.user_defined_country = None
        self.user_defined_latitude = None
        self.user_defined_longitude = None
        self.gae_city = None
        self.gae_country = None
        self.gae_latitude = None
        self.gae_longitude = None
        self.maxmind_city = None
        self.maxmind_country = None
        self.maxmind_latitude = None
        self.maxmind_longitude = None

    def initialize_from_http_request(self, request):
        """Initializes the lookup parameters from the HTTP request.

        Args:
            request: An instance of google.appengine.webapp.Request.
        """
        self.tool_id = request.path.strip('/').split('/')[0]
        self.set_response_format(request)
        self.set_ip_address_and_address_family(request)
        self.set_geolocation(request)
        self.metro = request.get(message.METRO)
        self.set_policy(request)

    def set_response_format(self, request):
        self.response_format = request.get(message.RESPONSE_FORMAT)
        if not self.response_format or \
            self.response_format not in message.VALID_FORMATS:
            logging.warning('Non valid response format %s.',
                            self.response_format) 
            self.response_format = message.DEFAULT_RESPONSE_FORMAT

    def set_ip_address_and_address_family(self, request):
        self.set_user_defined_ip_and_af(request)
        self.set_gae_ip_and_af(request)

        # User-defined args have precedence over args provided by GAE.
        if self.user_defined_ip:
            self.ip_address = self.user_defined_ip
        elif self.gae_ip:
            self.ip_address = self.gae_ip

        if self.user_defined_af:
            self.address_family = self.user_defined_af
        elif self.gae_af:
            self.address_family = self.gae_af

    def set_user_defined_ip_and_af(self, request):
        self.user_defined_ip = request.get(message.REMOTE_ADDRESS)
        self.user_defined_af = request.get(message.ADDRESS_FAMILY)
        if self.user_defined_ip:
            self._set_ip_and_af('user_defined_ip', 'user_defined_af')

        if not self.user_defined_ip and self.user_defined_af:
            # Non valid user-defined IP or IP not user-defined.
            # Verify user-defined address family.
            if self.user_defined_af != message.ADDRESS_FAMILY_IPv4 \
                and self.user_defined_af != message.ADDRESS_FAMILY_IPv6:
                logging.warning('Non valid address family %s',
                                self.user_defined_af)
                self.user_defined_af = None

    def set_gae_ip_and_af(self, request):
        self.gae_ip = request.remote_addr
        if self.gae_ip:
            self._set_ip_and_af('gae_ip', 'gae_af')

    def _set_ip_and_af(self, ip_field, af_field):
        try:
            ipaddr.IPv4Address(self.__dict__[ip_field])
            if self.__dict__[af_field] and \
                self.__dict__[af_field] != message.ADDRESS_FAMILY_IPv4:
                logging.warning(
                    'IP address is IPv4, but address family is %s.',
                    self.__dict__[af_field])
                # The IP address has precedence over the address family.
            self.__dict__[af_field] = message.ADDRESS_FAMILY_IPv4
            return
        except ipaddr.AddressValueError:
            pass

        try:
            ipaddr.IPv6Address(self.__dict__[ip_field])
            if self.__dict__[af_field] and \
                self.__dict__[af_field] != message.ADDRESS_FAMILY_IPv6:
                logging.warning(
                    'IP address is IPv6, but address family is %s.',
                    self.__dict__[af_field])
                # The IP address has precedence over the address family.
            self.__dict__[af_field] = message.ADDRESS_FAMILY_IPv6
            return
        except ipaddr.AddressValueError:
            pass

        # Non (valid) user-defined IP address. Don't change address family.
        self.__dict__[ip_field] = None 
 
    def set_geolocation(self, request):
        self.set_appengine_geolocation(request)
        self.user_defined_city = request.get(message.CITY)
        self.user_defined_country = request.get(message.COUNTRY)
        input_latitude = request.get(message.LATITUDE)
        input_longitude = request.get(message.LONGITUDE)

        if input_latitude is not None and input_longitude is not None:
            self.geolocation_type = constants.GEOLOCATION_USER_DEFINED
            try:
                self.user_defined_latitude = float(input_latitude)
                self.user_defined_longitude = float(input_longitude)
            except ValueError:
                logging.error('Non valid user-defined lat, long (%s, %s).',
                               input_latitude, input_longitude)
        elif self.user_defined_ip or self.user_defined_country:
            self.geolocation_type = constants.GEOLOCATION_MAXMIND
            self.set_maxmind_geolocation(self.user_defined_ip,
                                         self.user_defined_country,
                                         self.user_defined_city)
        elif self.gae_latitude and self.gae_longitude:
            self.geolocation_type = constants.GEOLOCATION_APP_ENGINE
        elif self.gae_ip or self.gae_country:
            self.set_maxmind_geolocation(self.gae_ip, self.gae_country,
                                         self.gae_city)

        if self.geolocation_type == constants.GEOLOCATION_USER_DEFINED:
            self.city = self.user_defined_city
            self.country = self.user_defined_country
            self.latitude = self.user_defined_latitude
            self.longitude = self.user_defined_longitude
        elif self.geolocation_type == constants.GEOLOCATION_MAXMIND:
            self.city = self.maxmind_city
            self.country = self.maxmind_country
            self.latitude = self.maxmind_latitude
            self.longitude = self.maxmind_longitude
        elif self.geolocation_type == constants.GEOLOCATION_APP_ENGINE:
            self.city = self.gae_city
            self.country = self.gae_country
            self.latitude = self.gae_latitude
            self.longitude = self.gae_longitude

    def set_maxmind_geolocation(self, ip_address, country, city):
        geo_record = maxmind.GeoRecord()    
        if ip_address:
            geo_record = maxmind.get_ip_geolocation(ip_address)
        elif city and country:
            geo_record = maxmind.get_city_geolocation(city, country)
        elif country:
            geo_record = maxmind.get_country_geolocation(country)
        self.maxmind_city = geo_record.city
        self.maxmind_country = geo_record.country
        self.maxmind_latitude = geo_record.latitude
        self.maxmind_longitude = geo_record.longitude

    def set_appengine_geolocation(self, request):
        """Adds geolocation info using the data provided by AppEngine.

        If the geolocation info is not included in the headers, it will
        use the data from MaxmindCityLocation/MaxmindCityBlock.

        Args:
            request: A webapp.Request instance.
        """
        if message.HEADER_CITY in request.headers:
            self.gae_city = request.headers[message.HEADER_CITY]
        if message.HEADER_COUNTRY in request.headers:
            self.gae_country = request.headers[message.HEADER_COUNTRY]
        if message.HEADER_LAT_LONG in request.headers:
            lat_long = request.headers[message.HEADER_LAT_LONG]
            try:
                self.gae_latitude, self.gae_longitude = [
                    float(x) for x in lat_long.split(',')]
            except ValueError:
                logging.error('GAE provided bad lat/long %s.', lat_long)

    def set_policy(self, request):
        self.policy = request.get(message.POLICY)
        if (self.user_defined_latitude and self.user_defined_longitude) or \
            self.user_defined_ip:
            if self.policy != message.POLICY_GEO:  
                logging.warning(
                    'Lat/longs user-defined, but policy is %s.', self.policy)
                self.policy = message.POLICY_GEO
            return
        if self.user_defined_country:
            if self.policy != message.POLICY_COUNTRY and \
                self.policy != message.POLICY_GEO:  
                logging.warning(
                    'Country user-defined, but policy is %s.', self.policy)
                self.policy = message.POLICY_GEO
            return
        if self.metro:
            if self.policy != message.POLICY_METRO:
                logging.warning(
                     'Metro defined, but policy is %s', self.policy)
                self.policy = message.POLICY_METRO
            return
        if self.policy == message.POLICY_GEO:
            if not self.latitude or not self.longitude:
                logging.warning('Policy geo, but no geo args defined.')
                self.policy = message.POLICY_RANDOM
            return
        if self.policy == message.POLICY_COUNTRY:
            if not self.user_defined_country:
                logging.warning('Policy country, but arg country not defined.')
                self.policy = self._get_default_policy()
            return
        if self.policy == message.POLICY_METRO:
            if not self.metro:
                logging.warning('Policy metro, but arg metro not defined.')
                self.policy = self._get_default_policy()
            return
        if self.policy  ==  message.POLICY_RANDOM:
            return
        logging.warning('Non valid policy %s.', self.policy) 
        self.policy = self._get_default_policy()

    def _get_default_policy(self):
        if self.latitude and self.longitude:
            return message.POLICY_GEO
        return message.POLICY_RANDOM
