import collections

import mock
import unittest2

from mlabns.util import constants
from mlabns.util import lookup_query
from mlabns.util import maxmind
from mlabns.util import message


class LookupQueryTestCase(unittest2.TestCase):

    def mock_get(self, arg, default_value=None):
        """Mock method to replace the GAE get() API for web requests."""
        if arg in self.mock_query_params:
            return self.mock_query_params[arg]
        else:
            return default_value

    def setUp(self):
        # Mock out calls to Maxmind
        maxmind_get_ip_geolocation_patch = mock.patch.object(
            maxmind, 'get_ip_geolocation', autospec=True)
        self.addCleanup(maxmind_get_ip_geolocation_patch.stop)
        maxmind_get_ip_geolocation_patch.start()

        maxmind_get_city_geolocation_patch = mock.patch.object(
            maxmind, 'get_city_geolocation', autospec=True)
        self.addCleanup(maxmind_get_city_geolocation_patch.stop)
        maxmind_get_city_geolocation_patch.start()

        maxmind_get_country_geolocation_patch = mock.patch.object(
            maxmind, 'get_country_geolocation', autospec=True)
        self.addCleanup(maxmind_get_country_geolocation_patch.stop)
        maxmind_get_country_geolocation_patch.start()

        # Create a defaul mock request with no explicit parameters except
        # the tool ID.
        self.mock_tool_id = 'ndt'
        self.mock_request_ip = '1.2.3.4'
        self.mock_request_af = message.ADDRESS_FAMILY_IPv4
        self.mock_query_params = {}
        self.mock_request = mock.Mock()
        self.mock_request.path = '/' + self.mock_tool_id
        self.mock_request.remote_addr = self.mock_request_ip
        self.mock_request.get.side_effect = self.mock_get

        # Set mock GAE geolocation headers
        self.mock_gae_latitude = 123.4
        self.mock_gae_longitude = 32.1
        self.mock_gae_city = 'gae_city'
        self.mock_gae_country = 'gae_country'
        self.mock_request.headers = {
            message.HEADER_LAT_LONG: '%.1f,%.1f' % (
                self.mock_gae_latitude, self.mock_gae_longitude),
            message.HEADER_CITY: self.mock_gae_city,
            message.HEADER_COUNTRY: self.mock_gae_country,
            }

    def testDefaultConstructor(self):
        query = lookup_query.LookupQuery()
        self.assertIsNone(query.tool_id)
        self.assertIsNone(query.policy)
        self.assertIsNone(query.metro)
        self.assertIsNone(query.response_format)
        self.assertIsNone(query.ip_address)
        self.assertIsNone(query.tool_address_family)
        self.assertIsNone(query.city)
        self.assertIsNone(query.country)
        self.assertIsNone(query.latitude)
        self.assertIsNone(query.longitude)
        self.assertIsNone(query.distance)

    def testInitializeWhenNoUserDefinedOptionsAreSpecified(self):
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(query.response_format,
                         message.DEFAULT_RESPONSE_FORMAT)
        self.assertEqual(self.mock_tool_id, query.tool_id)
        self.assertEqual(message.POLICY_GEO, query.policy)
        self.assertIsNone(query.metro)
        self.assertEqual(message.DEFAULT_RESPONSE_FORMAT, query.response_format)
        self.assertEqual(self.mock_request_ip, query.ip_address)
        self.assertIsNone(query.tool_address_family)
        self.assertEqual(self.mock_gae_city, query.city)
        self.assertEqual(self.mock_gae_country, query.country)
        self.assertEqual(self.mock_gae_latitude, query.latitude)
        self.assertEqual(self.mock_gae_longitude, query.longitude)
        self.assertIsNone(query.distance)

    def testInitializeParsesToolName(self):
        self.mock_request.path = '/valid_tool_name'

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual('valid_tool_name', query.tool_id)

    def testInitializeSetsDefaultResponseFormatWhenUserDefinedValueIsInvalid(
            self):
        self.mock_query_params[message.RESPONSE_FORMAT] = 'invalid_format'
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(query.response_format,
                         message.DEFAULT_RESPONSE_FORMAT)

    def testInitializeAcceptsValidUserDefinedFormat(self):
        self.mock_query_params[message.RESPONSE_FORMAT] = message.FORMAT_HTML
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(query.response_format, message.FORMAT_HTML)

    def testInitializeIgnoresInvalidUserDefinedAf(self):
        """An invalid user-defined AF should be ignored."""
        self.mock_query_params[message.ADDRESS_FAMILY] = 'invalid_af'
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(self.mock_request_ip, query.ip_address)
        self.assertIsNone(query.tool_address_family)

    def testInitializeAcceptsValidToolAfv4(self):
        user_defined_af = message.ADDRESS_FAMILY_IPv4
        self.mock_query_params[message.ADDRESS_FAMILY] = user_defined_af
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(user_defined_af, query.tool_address_family)

    def testInitializeAcceptsValidToolAfv6(self):
        user_defined_af = message.ADDRESS_FAMILY_IPv6
        self.mock_query_params[message.ADDRESS_FAMILY] = user_defined_af
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(user_defined_af, query.tool_address_family)

    def testInitializeIgnoresInvalidUserDefinedIp(self):
        """Ignore an invalid user-defined IP address."""
        self.mock_query_params[message.REMOTE_ADDRESS] = 'invalid_ip'
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(self.mock_request_ip, query.ip_address)

    def testInitializeAcceptsUserDefinedAfEvenWhenItDoesNotMatchUserDefinedIpv4(
            self):
        # The address family query parameter refers to the address family of the
        # tool, while the IP refers to the client's IP. It is legal to specify
        # an IPv4 client that wants an IPv6 tool.
        user_defined_ipv4 = '9.8.7.6'
        user_defined_af = message.ADDRESS_FAMILY_IPv6
        self.mock_query_params[message.REMOTE_ADDRESS] = user_defined_ipv4
        self.mock_query_params[message.ADDRESS_FAMILY] = user_defined_af
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(user_defined_ipv4, query.ip_address)
        self.assertEqual(user_defined_af, query.tool_address_family)

    def testInitializeAcceptsUserDefinedAfEvenWhenItDoesNotMatchUserDefinedIpv6(
            self):
        # The address family query parameter refers to the address family of the
        # tool, while the IP refers to the client's IP. It is legal to specify
        # an IPv6 client that wants an IPv4 tool.
        user_defined_ipv6 = '1:2:3::4'
        user_defined_af = message.ADDRESS_FAMILY_IPv4
        self.mock_query_params[message.REMOTE_ADDRESS] = user_defined_ipv6
        self.mock_query_params[message.ADDRESS_FAMILY] = user_defined_af
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(user_defined_ipv6, query.ip_address)
        self.assertEqual(user_defined_af, query.tool_address_family)

    def testInitializeAcceptsValidUserDefinedCityAndLatLon(self):
        user_defined_city = 'user_defined_city'
        user_defined_latitude = '0.0'
        user_defined_longitude = '4.3'

        self.mock_query_params[message.CITY] = user_defined_city
        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        #TODO(mtlynch): We should revisit this because the combination of
        # parameters here is confusing. What takes precedence if the city
        # and the lat/lon are contradictory?
        self.assertEqual(message.POLICY_GEO, query.policy)
        self.assertEqual(user_defined_city, query.city)
        self.assertIsNone(query.country)
        self.assertEqual(float(user_defined_latitude), query.latitude)
        self.assertEqual(float(user_defined_longitude), query.longitude)

    def testInitializeIgnoresInvalidUserDefinedLatWithValidLon(self):
        """If lat is invalid, but lon is valid, ignore both."""
        user_defined_latitude = 'invalid_latitude'
        user_defined_longitude = '36.0'

        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(self.mock_gae_latitude, query.latitude)
        self.assertEqual(self.mock_gae_longitude, query.longitude)
        self.assertEqual(self.mock_gae_city, query.city)
        self.assertEqual(self.mock_gae_country, query.country)

    def testInitializeIgnoresTooNegativeLatitude(self):
        """Ignore a latitude that's below the -90 -> +90 valid range."""
        user_defined_latitude = '-90.1'
        user_defined_longitude = '100.2'

        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(self.mock_gae_latitude, query.latitude)
        self.assertEqual(self.mock_gae_longitude, query.longitude)
        self.assertEqual(self.mock_gae_city, query.city)
        self.assertEqual(self.mock_gae_country, query.country)

    def testInitializeIgnoresTooPositiveLatitude(self):
        """Ignore a latitude that's above the -90 -> +90 valid range."""
        user_defined_latitude = '90.1'
        user_defined_longitude = '36.0'

        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(self.mock_gae_latitude, query.latitude)
        self.assertEqual(self.mock_gae_longitude, query.longitude)
        self.assertEqual(self.mock_gae_city, query.city)
        self.assertEqual(self.mock_gae_country, query.country)

    def testInitializeIgnoresTooNegativeLongitude(self):
        """Ignore a longitude that's below the -180 -> +180 valid range."""
        user_defined_latitude = '15.5'
        user_defined_longitude = '-180.01'

        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(self.mock_gae_latitude, query.latitude)
        self.assertEqual(self.mock_gae_longitude, query.longitude)
        self.assertEqual(self.mock_gae_city, query.city)
        self.assertEqual(self.mock_gae_country, query.country)

    def testInitializeIgnoresTooPositiveLongitude(self):
        """Ignore a longitude that's above the -180 -> +180 valid range."""
        user_defined_latitude = '15.5'
        user_defined_longitude = '180.1'

        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(self.mock_gae_latitude, query.latitude)
        self.assertEqual(self.mock_gae_longitude, query.longitude)
        self.assertEqual(self.mock_gae_city, query.city)
        self.assertEqual(self.mock_gae_country, query.country)

    def testInitializeIgnoresValidUserDefinedLatWithInvalidLon(self):
        """If lat is valid, but lon is invalid, ignore both."""
        user_defined_latitude = '36.0'
        user_defined_longitude = 'invalid_longitude'

        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(self.mock_gae_latitude, query.latitude)
        self.assertEqual(self.mock_gae_longitude, query.longitude)
        self.assertEqual(self.mock_gae_city, query.city)
        self.assertEqual(self.mock_gae_country, query.country)

    def testInitializeIgnoresInvalidUserDefinedLatLonEvenIfCityIsValid(self):
        user_defined_latitude = 'invalid_latitude'
        user_defined_longitude = 'invalid_longitude'
        user_defined_city = 'valid_city'

        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude
        self.mock_query_params[message.CITY] = user_defined_city

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        # Lat/lon is invalid, user-defined city is ignored if there's no
        # country to go with it. Treat this as if the request specified nothing.
        self.assertEqual(message.POLICY_GEO, query.policy)
        self.assertEqual(self.mock_gae_city, query.city)
        self.assertEqual(self.mock_gae_country, query.country)
        self.assertEqual(self.mock_gae_latitude, query.latitude)
        self.assertEqual(self.mock_gae_longitude, query.longitude)

    def testInitializeIgnoresInvalidUserDefinedLatLonEvenIfCountryIsValid(self):
        user_defined_latitude = 'invalid_latitude'
        user_defined_longitude = 'invalid_longitude'
        user_defined_country = 'user_defined_country'

        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude
        self.mock_query_params[message.COUNTRY] = user_defined_country

        maxmind_latitude = 55.5
        maxmind_longitude = 77.7
        maxmind.get_country_geolocation.return_value = maxmind.GeoRecord(
            latitude=maxmind_latitude, longitude=maxmind_longitude,
            country=user_defined_country)

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        #TODO(mtlynch): This is confusing behavior. If the only valid user-
        # defined field is the country name, the policy should implicitly be
        # message.COUNTRY.
        self.assertEqual(message.POLICY_GEO, query.policy)
        self.assertEqual(maxmind_latitude, query.latitude)
        self.assertEqual(maxmind_longitude, query.longitude)
        self.assertIsNone(query.city)
        self.assertEqual(user_defined_country, query.country)

    def testInitializeWithUserDefinedCountryGetsGeolocationForThatCountry(self):
        user_defined_country = 'user_defined_country'
        self.mock_query_params[message.COUNTRY] = user_defined_country

        maxmind_city = None
        maxmind_country = user_defined_country
        maxmind_latitude = 55.5
        maxmind_longitude = 77.7

        maxmind.get_country_geolocation.return_value = maxmind.GeoRecord(
            city=maxmind_city, country=maxmind_country,
            latitude=maxmind_latitude, longitude=maxmind_longitude)

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(maxmind_latitude, query.latitude)
        self.assertEqual(maxmind_longitude, query.longitude)
        self.assertIsNone(query.city)
        self.assertEqual(maxmind_country, query.country)
        self.assertEqual(user_defined_country, query.user_defined_country)

    def testInitializeAcceptsUserDefinedLatLonAndCountry(self):
        user_defined_latitude = '89.0'
        user_defined_longitude = '100.0'
        user_defined_country = 'user_defined_country'

        self.mock_query_params[message.LATITUDE] = user_defined_latitude
        self.mock_query_params[message.LONGITUDE] = user_defined_longitude
        self.mock_query_params[message.COUNTRY] = user_defined_country

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(float(user_defined_latitude), query.latitude)
        self.assertEqual(float(user_defined_longitude), query.longitude)
        self.assertIsNone(query.city)
        self.assertEqual(user_defined_country, query.country)
        self.assertEqual(user_defined_country, query.user_defined_country)

    def testInitializeAcceptsGeoPolicy(self):
        self.mock_query_params[message.POLICY] = message.POLICY_GEO
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)

    def testInitializeAcceptsCountryPolicy(self):
        user_defined_country = 'user_defined_country'
        self.mock_query_params[message.POLICY] = message.COUNTRY
        self.mock_query_params[message.COUNTRY] = user_defined_country
        maxmind.get_country_geolocation.return_value = maxmind.GeoRecord(
            country=user_defined_country)

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(message.POLICY_COUNTRY, query.policy)
        self.assertEqual(user_defined_country, query.country)
        self.assertEqual(user_defined_country, query.user_defined_country)

    def testInitializeUsesMaxmindWhenUserDefinedIpv4Exists(self):
        user_defined_ip = '5.6.7.8'
        self.mock_query_params[message.REMOTE_ADDRESS] = user_defined_ip

        maxmind_city = 'maxmind_city'
        maxmind_country = 'maxmind_country'
        maxmind_latitude = 55.5
        maxmind_longitude = 77.7

        maxmind.get_ip_geolocation.return_value = maxmind.GeoRecord(
            city=maxmind_city, country=maxmind_country,
            latitude=maxmind_latitude, longitude=maxmind_longitude)

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        # Make sure we looked up the user-defined IP, not the request IP.
        maxmind.get_ip_geolocation.assert_called_with(user_defined_ip)
        self.assertEqual(message.POLICY_GEO, query.policy)
        self.assertEqual(maxmind_city, query.city)
        self.assertEqual(maxmind_country, query.country)
        self.assertEqual(maxmind_latitude, query.latitude)
        self.assertEqual(maxmind_longitude, query.longitude)

    def testInitializeUsesAppEngineGeoDataWhenUserDefinedIpv4MatchesRequestIp(
            self):
        # Simulate when the client supplies an explicit IPv4 address in the URL
        # and it matches the source IP of the web request (i.e. the user
        # explicitly declared their own IP address).
        user_defined_ip = self.mock_request_ip
        self.mock_query_params[message.REMOTE_ADDRESS] = user_defined_ip

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)
        self.assertEqual(self.mock_gae_city, query.city)
        self.assertEqual(self.mock_gae_country, query.country)
        self.assertEqual(self.mock_gae_latitude, query.latitude)
        self.assertEqual(self.mock_gae_longitude, query.longitude)

        # Verify we didn't retrieve any geoip information from Maxmind.
        self.assertFalse(maxmind.get_ip_geolocation.called)

    def testInitializeUsesMaxmindWhenUserDefinedIpv6Exists(self):
        user_defined_ip = '1:2:3::4'
        self.mock_query_params[message.REMOTE_ADDRESS] = user_defined_ip

        maxmind_city = 'maxmind_city'
        maxmind_country = 'maxmind_country'
        maxmind_latitude = 55.5
        maxmind_longitude = 77.7

        maxmind.get_ip_geolocation.return_value = maxmind.GeoRecord(
            city=maxmind_city, country=maxmind_country,
            latitude=maxmind_latitude, longitude=maxmind_longitude)

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        # Make sure we looked up the user-defined IP, not the request IP.
        maxmind.get_ip_geolocation.assert_called_with(user_defined_ip)
        self.assertEqual(message.POLICY_GEO, query.policy)
        self.assertEqual(maxmind_city, query.city)
        self.assertEqual(maxmind_country, query.country)
        self.assertEqual(maxmind_latitude, query.latitude)
        self.assertEqual(maxmind_longitude, query.longitude)

    def testInitializeUsesMaxmindWhenAppEngineGeoDataIsMissing(self):
        # Remove all mock AppEngine headers
        self.mock_request.headers = {}

        maxmind_city = 'maxmind_city'
        maxmind_country = 'maxmind_country'
        maxmind_latitude = 55.5
        maxmind_longitude = 77.7

        maxmind.get_ip_geolocation.return_value = maxmind.GeoRecord(
            city=maxmind_city, country=maxmind_country,
            latitude=maxmind_latitude, longitude=maxmind_longitude)

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)
        self.assertEqual(maxmind_city, query.city)
        self.assertEqual(maxmind_country, query.country)
        self.assertEqual(maxmind_latitude, query.latitude)
        self.assertEqual(maxmind_longitude, query.longitude)

    def testInitializeUsesRandomPolicyWhenAllGeoDataIsMissing(self):
        """When no geo information is available, choose a random site."""
        # Remove all mock AppEngine headers
        self.mock_request.headers = {}

        # Simulate Maxmind missing geo data for the request IP
        maxmind.get_ip_geolocation.return_value = maxmind.GeoRecord()

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testInitializeDefaultsToGeoPolicyWhenUserDefinedPolicyIsInvalidAndGeoDataIsAvailable(
            self):
        self.mock_query_params[message.POLICY] = 'invalid_policy'
        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)
        self.assertEqual(message.POLICY_GEO, query.policy)

    def testInitializeAcceptsMetroOption(self):
        self.mock_query_params[message.METRO] = 'lax'

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(self.mock_request)

        self.assertEqual(message.POLICY_METRO, query.policy)
        self.assertEqual('lax', query.metro)


if __name__ == '__main__':
    unittest2.main()

