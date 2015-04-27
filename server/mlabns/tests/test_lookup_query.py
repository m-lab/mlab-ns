import collections
import mock
import unittest2

from mlabns.util import constants
from mlabns.util import lookup_query
from mlabns.util import message


class LookupQueryTestCase(unittest2.TestCase):

    def setUp(self):
        self.mock_query_params = collections.defaultdict(lambda: None)
        self.mock_request = mock.Mock()
        self.mock_request.get.side_effect = (
            lambda arg, default_value: self.mock_query_params[arg])

    def testDefaultConstructor(self):
        query = lookup_query.LookupQuery()
        self.assertIsNone(query.tool_id)
        self.assertIsNone(query.policy)
        self.assertIsNone(query.metro)
        self.assertIsNone(query.geolocation_type)
        self.assertIsNone(query.response_format)
        self.assertIsNone(query.ip_address)
        self.assertIsNone(query.address_family)
        self.assertIsNone(query.city)
        self.assertIsNone(query.country)
        self.assertIsNone(query.latitude)
        self.assertIsNone(query.longitude)
        self.assertIsNone(query.distance)
        self.assertIsNone(query.gae_ip)
        self.assertIsNone(query.gae_af)
        self.assertIsNone(query.user_defined_ip)
        self.assertIsNone(query.user_defined_af)
        self.assertIsNone(query.gae_city)
        self.assertIsNone(query.gae_country)
        self.assertIsNone(query.gae_latitude)
        self.assertIsNone(query.gae_longitude)
        self.assertIsNone(query.maxmind_city)
        self.assertIsNone(query.maxmind_country)
        self.assertIsNone(query.maxmind_latitude)
        self.assertIsNone(query.maxmind_longitude)
        self.assertIsNone(query.user_defined_city)
        self.assertIsNone(query.user_defined_country)
        self.assertIsNone(query.user_defined_latitude)
        self.assertIsNone(query.user_defined_longitude)

    def testSetResponseFormatNoneFormat(self):
        query = lookup_query.LookupQuery()
        query.set_response_format(self.mock_request)
        self.assertEqual(query.response_format,
                         message.DEFAULT_RESPONSE_FORMAT)

    def testSetResponseFormatNonValidFormat(self):
        self.mock_query_params[message.RESPONSE_FORMAT] = 'non_valid_format'
        query = lookup_query.LookupQuery()
        query.set_response_format(self.mock_request)
        self.assertEqual(query.response_format,
                         message.DEFAULT_RESPONSE_FORMAT)

    def testSetResponseFormatValidFormat(self):
        self.mock_query_params[message.RESPONSE_FORMAT] = message.FORMAT_HTML
        query = lookup_query.LookupQuery()
        query.set_response_format(self.mock_request)
        self.assertEqual(query.response_format, message.FORMAT_HTML)

    def testSetUserDefinedIpAndAfNoIpNoAf(self):
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertIsNone(query.user_defined_ip)
        self.assertIsNone(query.user_defined_af)

    def testSetUserDefinedIpAndAfNoIpNonValidAf(self):
        self.mock_query_params[message.ADDRESS_FAMILY] = 'non_valid_af'
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertIsNone(query.user_defined_ip)
        self.assertIsNone(query.user_defined_af)

    def testSetUserDefinedIpAndAfNoIpValidAf4(self):
        self.mock_query_params[message.ADDRESS_FAMILY] = (
            message.ADDRESS_FAMILY_IPv4)
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertIsNone(query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfNoIpValidAf6(self):
        self.mock_query_params[message.ADDRESS_FAMILY] = (
            message.ADDRESS_FAMILY_IPv6)
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertIsNone(query.user_defined_ip)

    def testSetUserDefinedIpAndAfNonValidIpNoAf(self):
        self.mock_query_params[message.REMOTE_ADDRESS] = 'non_valid_ip'
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertIsNone(query.user_defined_ip)
        self.assertIsNone(query.user_defined_af)

    def testSetUserDefinedIpAndAfNonValidIpNonValidAf(self):
        self.mock_query_params[message.REMOTE_ADDRESS] = 'non_valid_ip'
        self.mock_query_params[message.ADDRESS_FAMILY] = 'non_valid_af'
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertIsNone(query.user_defined_ip)
        self.assertIsNone(query.user_defined_af)

    def testSetUserDefinedIpAndAfNonValidIpValidAf4(self):
        self.mock_query_params[message.REMOTE_ADDRESS] = 'non_valid_ip'
        self.mock_query_params[message.ADDRESS_FAMILY] = (
            message.ADDRESS_FAMILY_IPv4)
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertIsNone(query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfNonValidIpValidAf6(self):
        self.mock_query_params[message.REMOTE_ADDRESS] = 'non_valid_ip'
        self.mock_query_params[message.ADDRESS_FAMILY] = (
            message.ADDRESS_FAMILY_IPv6)
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertIsNone(query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv4NoAf(self):
        valid_ipv4 = '1.2.3.4'
        self.mock_query_params[message.REMOTE_ADDRESS] = valid_ipv4
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv4, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv6NoAf(self):
        valid_ipv6 = '1:2:3::4'
        self.mock_query_params[message.REMOTE_ADDRESS] = valid_ipv6
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv6, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6,
                         query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv4NonvalidAf(self):
        valid_ipv4 = '1.2.3.4'
        self.mock_query_params[message.REMOTE_ADDRESS] = valid_ipv4
        self.mock_query_params[message.ADDRESS_FAMILY] = 'non_valid_af'
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv4, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv6NonvalidAf(self):
        valid_ipv6 = '1:2:3::4'
        self.mock_query_params[message.REMOTE_ADDRESS] = valid_ipv6
        self.mock_query_params[message.ADDRESS_FAMILY] = 'non_valid_af'
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv6, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv4ValidAf4(self):
        valid_ipv4 = '1.2.3.4'
        self.mock_query_params[message.REMOTE_ADDRESS] = valid_ipv4
        self.mock_query_params[message.ADDRESS_FAMILY] = (
            message.ADDRESS_FAMILY_IPv4)
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv4, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv4ValidAf6(self):
        valid_ipv4 = '1.2.3.4'
        self.mock_query_params[message.REMOTE_ADDRESS] = valid_ipv4
        self.mock_query_params[message.ADDRESS_FAMILY] = (
            message.ADDRESS_FAMILY_IPv6)
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv4, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv6ValidAf4(self):
        valid_ipv6 = '1:2:3::4'
        self.mock_query_params[message.REMOTE_ADDRESS] = valid_ipv6
        self.mock_query_params[message.ADDRESS_FAMILY] = (
            message.ADDRESS_FAMILY_IPv4)
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv6, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv6ValidAf6(self):
        valid_ipv6 = '1:2:3::4'
        self.mock_query_params[message.REMOTE_ADDRESS] = valid_ipv6
        self.mock_query_params[message.ADDRESS_FAMILY] = (
            message.ADDRESS_FAMILY_IPv6)
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv6, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.user_defined_af)

    def testSetGaeIpAndAfNoIp(self):
        self.mock_request.remote_addr = None
        query = lookup_query.LookupQuery()
        query.set_gae_ip_and_af(self.mock_request)
        self.assertIsNone(query.gae_ip)
        self.assertIsNone(query.gae_af)

    def testSetGaeIpAndAfNonValidIp(self):
        self.mock_request.get.remote_addr = 'non_valid_ip'
        query = lookup_query.LookupQuery()
        query.set_gae_ip_and_af(self.mock_request)
        self.assertIsNone(query.gae_ip)
        self.assertIsNone(query.gae_af)

    def testSetGaeIpAndAfValidIpv4(self):
        valid_ipv4 = '1.2.3.4'
        self.mock_request.remote_addr = valid_ipv4
        query = lookup_query.LookupQuery()
        query.set_gae_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv4, query.gae_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.gae_af)

    def testSetGaeIpAndAfValidIpv6(self):
        valid_ipv6 = '1:2:3::4'
        self.mock_request.remote_addr = valid_ipv6
        query = lookup_query.LookupQuery()
        query.set_gae_ip_and_af(self.mock_request)
        self.assertEqual(valid_ipv6, query.gae_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.gae_af)

    def testSetIpAddressAndAddressFamilyUserDefined(self):

        class LookupQueryMockup(lookup_query.LookupQuery):
            def __init__(self):
                self.user_defined_ip = 'user_defined_ip'
                self.user_defined_af = 'user_defined_af'
                self.gae_ip = 'gae_ip'
                self.gae_af = 'gae_af'
            def set_user_defined_ip_and_af(self, unused_arg): pass
            def set_gae_ip_and_af(self, unused_arg): pass

        query = LookupQueryMockup()
        query.set_ip_address_and_address_family(self.mock_request)
        self.assertEqual('user_defined_ip', query.ip_address)
        self.assertEqual('user_defined_af', query.address_family)

    def testSetIpAddressAndAddressFamilyGAE(self):

        class LookupQueryMockup(lookup_query.LookupQuery):
            def __init__(self):
                self.user_defined_ip = None
                self.user_defined_af = None
                self.gae_ip = 'gae_ip'
                self.gae_af = 'gae_af'
            def set_user_defined_ip_and_af(self, unused_arg): pass
            def set_gae_ip_and_af(self, unused_arg): pass

        query = LookupQueryMockup()
        query.set_ip_address_and_address_family(self.mock_request)
        self.assertEqual('gae_ip', query.ip_address)
        self.assertEqual('gae_af', query.address_family)

    def testSetIpAddressAndAddressFamilyMixed(self):

        class LookupQueryMockup(lookup_query.LookupQuery):
            def __init__(self):
                self.user_defined_ip = 'user_defined_ip'
                self.user_defined_af = None
                self.gae_ip = 'gae_ip'
                self.gae_af = None
                self.address_family = None
            def set_user_defined_ip_and_af(self, unused_arg): pass
            def set_gae_ip_and_af(self, unused_arg): pass

        query = LookupQueryMockup()
        query.set_ip_address_and_address_family(self.mock_request)
        self.assertEqual('user_defined_ip', query.ip_address)
        self.assertIsNone(query.address_family)

    def testSetGeoLocationUsedDefinedValidLatLong(self):
        lat = 0.0
        lon = 4.3
        city = 'valid_city'
        country = None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass

        self.mock_query_params[message.LATITUDE] = lat
        self.mock_query_params[message.LONGITUDE] = lon
        self.mock_query_params[message.CITY] = city
        self.mock_query_params[message.COUNTRY] = country

        query = LookupQueryMockup()
        query.set_geolocation(self.mock_request)

        self.assertEqual(constants.GEOLOCATION_USER_DEFINED,
                         query.geolocation_type)
        self.assertEqual(lat, query.user_defined_latitude)
        self.assertEqual(lon, query.user_defined_longitude)
        self.assertEqual(city, query.user_defined_city)
        self.assertEqual(country, query.user_defined_country)

        self.assertEqual(query.user_defined_latitude, query.latitude)
        self.assertEqual(query.user_defined_longitude, query.longitude)
        self.assertEqual(query.user_defined_city, query.city)
        self.assertEqual(query.user_defined_country, query.country)

    def testSetGeoLocationUsedDefinedNoValidLatLong(self):
        lat = 'non_valid_lat'
        lon = 'non_valid_lon'
        city = 'valid_city'
        country = None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass

        self.mock_query_params[message.LATITUDE] = lat
        self.mock_query_params[message.LONGITUDE] = lon
        self.mock_query_params[message.CITY] = city
        self.mock_query_params[message.COUNTRY] = country

        query = LookupQueryMockup()
        query.set_geolocation(self.mock_request)

        self.assertEqual(constants.GEOLOCATION_USER_DEFINED,
                         query.geolocation_type)
        self.assertIsNone(query.user_defined_latitude)
        self.assertIsNone(query.user_defined_longitude)
        self.assertEqual(city, query.user_defined_city)
        self.assertEqual(country, query.user_defined_country)

        self.assertEqual(query.user_defined_latitude, query.latitude)
        self.assertEqual(query.user_defined_longitude, query.longitude)
        self.assertEqual(query.user_defined_city, query.city)
        self.assertEqual(query.user_defined_country, query.country)

    def testSetGeoLocationUsedDefinedIpOrCountryAndMaxmind(self):
        lat = 'maxmind_latitude'
        lon = 'maxmind_logitude'
        city = None
        country = 'maxmind_country'

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
            def set_maxmind_geolocation(
                self, unused_arg1, unused_arg2, unused_arg3):
                self.maxmind_latitude = lat
                self.maxmind_longitude = lon
                self.maxmind_city = city
                self.maxmind_country = country

        query = LookupQueryMockup()
        query.user_defined_ip = 'valid_ip'
        query.set_geolocation(self.mock_request)
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)
        self.assertEqual(lat, query.maxmind_latitude)
        self.assertEqual(lon, query.maxmind_longitude)
        self.assertEqual(city, query.maxmind_city)
        self.assertEqual(country, query.maxmind_country)

        self.assertEqual(query.maxmind_latitude, query.latitude)
        self.assertEqual(query.maxmind_longitude, query.longitude)
        self.assertEqual(query.maxmind_city, query.city)
        self.assertEqual(query.maxmind_country, query.country)

        self.mock_query_params[message.COUNTRY] = 'valid_country'
        query.set_geolocation(self.mock_request)
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)
        self.assertEqual(lat, query.maxmind_latitude)
        self.assertEqual(lon, query.maxmind_longitude)
        self.assertEqual(city, query.maxmind_city)
        self.assertEqual(country, query.maxmind_country)

        self.assertEqual(query.maxmind_latitude, query.latitude)
        self.assertEqual(query.maxmind_longitude, query.longitude)
        self.assertEqual(query.maxmind_city, query.city)
        self.assertEqual(query.maxmind_country, query.country)

    def testSetGeoLocationGAELatLong(self):
        lat = 'gae_latitude'
        lon = 'gae_logitude'
        city = None
        country = 'gae_country'

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg):
                self.gae_latitude = lat
                self.gae_longitude = lon
                self.gae_city = city
                self.gae_country = country

        query = LookupQueryMockup()
        query.set_geolocation(self.mock_request)
        self.assertEqual(constants.GEOLOCATION_APP_ENGINE,
                         query.geolocation_type)
        self.assertEqual(lat, query.gae_latitude)
        self.assertEqual(lon, query.gae_longitude)
        self.assertEqual(city, query.gae_city)
        self.assertEqual(country, query.gae_country)

        self.assertEqual(query.gae_latitude, query.latitude)
        self.assertEqual(query.gae_longitude, query.longitude)
        self.assertEqual(query.gae_city, query.city)
        self.assertEqual(query.gae_country, query.country)

    def testSetGeoLocationGAEIpOrCountryAndMaxmind(self):
        lat = 'maxmind_latitude'
        lon = 'maxmind_logitude'
        city = None
        country = 'maxmind_country'

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
            def set_maxmind_geolocation(
                self, unused_arg1, unused_arg2, unused_arg3):
                self.maxmind_latitude = lat
                self.maxmind_longitude = lon
                self.maxmind_city = city
                self.maxmind_country = country

        query = LookupQueryMockup()
        query.user_defined_ip = 'valid_ip'
        query.set_geolocation(self.mock_request)
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)
        self.assertEqual(lat, query.maxmind_latitude)
        self.assertEqual(lon, query.maxmind_longitude)
        self.assertEqual(city, query.maxmind_city)
        self.assertEqual(country, query.maxmind_country)

        self.assertEqual(query.maxmind_latitude, query.latitude)
        self.assertEqual(query.maxmind_longitude, query.longitude)
        self.assertEqual(query.maxmind_city, query.city)
        self.assertEqual(query.maxmind_country, query.country)

        query = LookupQueryMockup()
        self.mock_query_params[message.COUNTRY] = 'valid_country'
        query.set_geolocation(self.mock_request)
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)
        self.assertEqual(lat, query.maxmind_latitude)
        self.assertEqual(lon, query.maxmind_longitude)
        self.assertEqual(city, query.maxmind_city)
        self.assertEqual(country, query.maxmind_country)

        self.assertEqual(query.maxmind_latitude, query.latitude)
        self.assertEqual(query.maxmind_longitude, query.longitude)
        self.assertEqual(query.maxmind_city, query.city)
        self.assertEqual(query.maxmind_country, query.country)

    def testSetMaxmindGeolocationNone(self):
        query = lookup_query.LookupQuery()
        query.set_maxmind_geolocation(None, None, None)
        self.assertIsNone(query.maxmind_city)
        self.assertIsNone(query.maxmind_country)
        self.assertIsNone(query.maxmind_latitude)
        self.assertIsNone(query.maxmind_longitude)

    def testSetAppengineGeolocationValidLatLong(self):
        valid_city = 'valid_city'
        valid_latitude = 0.0
        valid_longitude = 3.0
        self.mock_request.headers = {
            message.HEADER_CITY: valid_city,
            message.HEADER_LAT_LONG: '0.0,3.0'
            }
        query = lookup_query.LookupQuery()
        query.set_appengine_geolocation(self.mock_request)
        self.assertEqual(valid_city, query.gae_city)
        self.assertIsNone(query.gae_country)
        self.assertEqual(valid_latitude, query.gae_latitude)
        self.assertEqual(valid_longitude, query.gae_longitude)

    def testSetPolicyUserDefinedGeoPolicyGeo(self):
        self.mock_query_params[message.POLICY] = message.POLICY_GEO
        query = lookup_query.LookupQuery()
        query.user_defined_ip = 'valid_ip'
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)

        query = lookup_query.LookupQuery()
        query.user_defined_latitude = 'valid_lat'
        query.user_defined_longitude = 'valid_long'
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)

    def testSetPolicyUserDefinedGeoPolicyNoGeo(self):
        self.mock_query_params[message.POLICY] = 'no_geo_policy'
        query = lookup_query.LookupQuery()
        query.user_defined_ip = 'valid_ip'
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)

        query = lookup_query.LookupQuery()
        query.user_defined_latitude = 'valid_lat'
        query.user_defined_longitude = 'valid_long'
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)

    def testSetPolicyUserDefinedCountryPolicyCountry(self):
        self.mock_query_params[message.POLICY] = message.POLICY_COUNTRY
        query = lookup_query.LookupQuery()
        query.user_defined_country = 'valid_country'
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_COUNTRY, query.policy)

    def testSetPolicyUserDefinedCountryPolicyGeo(self):
        self.mock_query_params[message.POLICY] = message.POLICY_GEO
        query = lookup_query.LookupQuery()
        query.user_defined_country = 'valid_country'
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)

    def testSetPolicyUserDefinedCountryPolicyNoGeoNoCountry(self):
        self.mock_query_params[message.POLICY] = 'no_geo_no_country_policy'
        query = lookup_query.LookupQuery()
        query.user_defined_country = 'valid_country'
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)

    def testSetPolicyUserDefinedMetroPolicyMetro(self):
        self.mock_query_params[message.POLICY] = message.POLICY_METRO
        query = lookup_query.LookupQuery()
        query.metro = 'valid_metro'
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_METRO, query.policy)

    def testSetPolicyUserDefinedMetroPolicyNoMetro(self):
        self.mock_query_params[message.POLICY] = 'no_metro_policy'
        query = lookup_query.LookupQuery()
        query.metro = 'valid_metro'
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_METRO, query.policy)

    def testSetPolicyGeoPolicyNoGeo(self):
        self.mock_query_params[message.POLICY] = message.POLICY_GEO
        query = lookup_query.LookupQuery()
        query.latitude = 'valid_lat'
        query.longitude = None
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testSetPolicyCountryPolicyNoUserDefinedCountry(self):
        self.mock_query_params[message.POLICY] = message.POLICY_COUNTRY
        query = lookup_query.LookupQuery()
        query.user_defined_country = None
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testSetPolicyMetroPolicyNoMetro(self):
        self.mock_query_params[message.POLICY] = message.POLICY_METRO
        query = lookup_query.LookupQuery()
        query.metro = None
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testSetPolicyPolicyRandom(self):
        self.mock_query_params[message.POLICY] = message.POLICY_RANDOM
        query = lookup_query.LookupQuery()
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testSetPolicyNoPolicy(self):
        query = lookup_query.LookupQuery()
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testSetPolicyNonValidPolicy(self):
        self.mock_query_params[message.POLICY] = 'non_valid_policy'
        query = lookup_query.LookupQuery()
        query.set_policy(self.mock_request)
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testInitializeFromHttpRequest(self):
        valid_metro = 'valid_metro'
        valid_tool = 'valid_tool'
        self.mock_query_params[message.METRO] = valid_metro
        self.mock_request.path = valid_tool + '/xyz/'
        self.mock_request.remote_addr = None
        self.mock_request.headers = {}
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(valid_tool, query.tool_id)
        self.assertEqual(valid_metro, query.metro)


if __name__ == '__main__':
    unittest2.main()
