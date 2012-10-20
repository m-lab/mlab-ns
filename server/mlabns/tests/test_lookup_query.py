import unittest2

from mlabns.util import constants
from mlabns.util import lookup_query
from mlabns.util import message

class LookupQueryTestCase(unittest2.TestCase):

    def testDefaultConstructor(self):
        query = lookup_query.LookupQuery()
        self.assertIsNone(query.tool_id)
        self.assertIsNone(query.policy)
        self.assertIsNone(query.metro)
        self.assertIsNone(query.geolocation_type)
        self.assertIsNone(query.response_format)
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

        class RequestMockup:
            def get(self, unused_arg):
                return None
        
        query = lookup_query.LookupQuery()
        query.set_response_format(RequestMockup())
        self.assertEqual(query.response_format,
                         message.DEFAULT_RESPONSE_FORMAT)
       
    def testSetResponseFormatNonValidFormat(self):

        class RequestMockup:
            def get(self, unused_arg):
                return 'non_Valid_format'
        
        query = lookup_query.LookupQuery()
        query.set_response_format(RequestMockup())
        self.assertEqual(query.response_format,
                         message.DEFAULT_RESPONSE_FORMAT)
       
    def testSetResponseFormatValidFormat(self):

        class RequestMockup:
            def get(self, unused_arg):
                return message.FORMAT_HTML
        
        query = lookup_query.LookupQuery()
        query.set_response_format(RequestMockup())
        self.assertEqual(query.response_format, message.FORMAT_HTML)

    def testSetUserDefinedIpAndAfNoIpNoAf(self):

        class RequestMockup:
            def get(self, unused_arg):
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertIsNone(query.user_defined_ip)
        self.assertIsNone(query.user_defined_af)
        
    def testSetUserDefinedIpAndAfNoIpNonValidAf(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.ADDRESS_FAMILY:
                    return 'non_valid_af'
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertIsNone(query.user_defined_ip)
        self.assertIsNone(query.user_defined_af)

    def testSetUserDefinedIpAndAfNoIpValidAf4(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.ADDRESS_FAMILY:
                    return message.ADDRESS_FAMILY_IPv4
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertIsNone(query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfNoIpValidAf6(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.ADDRESS_FAMILY:
                    return message.ADDRESS_FAMILY_IPv6
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertIsNone(query.user_defined_ip)

    def testSetUserDefinedIpAndAfNonValidIpNoAf(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return 'non_valid_ip'
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertIsNone(query.user_defined_ip)
        self.assertIsNone(query.user_defined_af)

    def testSetUserDefinedIpAndAfNonValidIpNonValidAf(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return 'non_valid_ip'
                if arg == message.ADDRESS_FAMILY:
                    return 'non_valid_af'
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertIsNone(query.user_defined_ip)
        self.assertIsNone(query.user_defined_af)

    def testSetUserDefinedIpAndAfNonValidIpValidAf4(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return 'non_valid_ip'
                if arg == message.ADDRESS_FAMILY:
                    return message.ADDRESS_FAMILY_IPv4
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertIsNone(query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfNonValidIpValidAf6(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return 'non_valid_ip'
                if arg == message.ADDRESS_FAMILY:
                    return message.ADDRESS_FAMILY_IPv6
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertIsNone(query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv4NoAf(self):
        valid_ipv4 = '1.2.3.4'

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return valid_ipv4
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv4, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv6NoAf(self):
        valid_ipv6 = '1:2:3::4'

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return valid_ipv6
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv6, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6,
                         query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv4NonvalidAf(self):
        valid_ipv4 = '1.2.3.4'

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return valid_ipv4
                if arg == message.ADDRESS_FAMILY:
                    return 'non_valid_af'
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv4, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv6NonvalidAf(self):
        valid_ipv6 = '1:2:3::4'

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return valid_ipv6
                if arg == message.ADDRESS_FAMILY:
                    return 'non_valid_af'
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv6, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv4ValidAf4(self):
        valid_ipv4 = '1.2.3.4'

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return valid_ipv4
                if arg == message.ADDRESS_FAMILY:
                    return message.ADDRESS_FAMILY_IPv4
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv4, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv4ValidAf6(self):
        valid_ipv4 = '1.2.3.4'

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return valid_ipv4
                if arg == message.ADDRESS_FAMILY:
                    return message.ADDRESS_FAMILY_IPv6
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv4, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.user_defined_af)
        
    def testSetUserDefinedIpAndAfValidIpv6ValidAf4(self):
        valid_ipv6 = '1:2:3::4'

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return valid_ipv6
                if arg == message.ADDRESS_FAMILY:
                    return message.ADDRESS_FAMILY_IPv4
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv6, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.user_defined_af)

    def testSetUserDefinedIpAndAfValidIpv6ValidAf6(self):
        valid_ipv6 = '1:2:3::4'

        class RequestMockup:
            def get(self, arg):
                if arg == message.REMOTE_ADDRESS:
                    return valid_ipv6
                if arg == message.ADDRESS_FAMILY:
                    return message.ADDRESS_FAMILY_IPv6
                return None
        
        query = lookup_query.LookupQuery()
        query.set_user_defined_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv6, query.user_defined_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.user_defined_af)

    def testSetGaeIpAndAfNoIp(self):

        class RequestMockup:
            def __init__(self):
                self.remote_addr = None
        
        query = lookup_query.LookupQuery()
        query.set_gae_ip_and_af(RequestMockup())
        self.assertIsNone(query.gae_ip)
        self.assertIsNone(query.gae_af)

    def testSetGaeIpAndAfNonValidIp(self):

        class RequestMockup:
            def __init__(self):
                self.remote_addr = 'non_valid_ip'
        
        query = lookup_query.LookupQuery()
        query.set_gae_ip_and_af(RequestMockup())
        self.assertIsNone(query.gae_ip)
        self.assertIsNone(query.gae_af)

    def testSetGaeIpAndAfValidIpv4(self):
        valid_ipv4 = '1.2.3.4'

        class RequestMockup:
            def __init__(self):
                self.remote_addr = valid_ipv4
        
        query = lookup_query.LookupQuery()
        query.set_gae_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv4, query.gae_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv4, query.gae_af)

    def testSetGaeIpAndAfValidIpv6(self):
        valid_ipv6 = '1:2:3::4'

        class RequestMockup:
            def __init__(self):
                self.remote_addr = valid_ipv6
        
        query = lookup_query.LookupQuery()
        query.set_gae_ip_and_af(RequestMockup())
        self.assertEqual(valid_ipv6, query.gae_ip)
        self.assertEqual(message.ADDRESS_FAMILY_IPv6, query.gae_af)

    def testSetGeoLocationUsedDefinedValidLatLong(self):
        valid_lat = 0.0        
        valid_long = 4.3        

        class RequestMockup:
            def get(self, arg):
                if arg == message.LATITUDE:
                    return valid_lat
                if arg == message.LONGITUDE:
                    return valid_long
                return None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
        
        query = LookupQueryMockup()
        query.set_geolocation(RequestMockup())
        self.assertEqual(valid_lat, query.user_defined_latitude)
        self.assertEqual(valid_long, query.user_defined_longitude)
        self.assertEqual(constants.GEOLOCATION_USER_DEFINED,
                         query.geolocation_type)
     
    def testSetGeoLocationUsedDefinedNoValidLatLongNoMaxmind(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.LATITUDE:
                    return 'non_valid_lat'
                return None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
        
        query = LookupQueryMockup()
        query.set_geolocation(RequestMockup())
        self.assertIsNone(query.user_defined_latitude)
        self.assertIsNone(query.user_defined_longitude)
        self.assertIsNone(query.geolocation_type)

    def testSetGeoLocationUsedDefinedNoValidLatLongMaxmind(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.LATITUDE:
                    return 'non_valid_lat'
                if arg == message.LONGITUDE:
                    return 'non_valid_lat'
                if arg == message.COUNTRY:
                    return 'valid_country'
                return None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
            def set_maxmind_geolocation(
                self, unused_arg1, unused_arg2, unused_arg3): pass
        
        query = LookupQueryMockup()
        query.user_defined_ip = 'valid_ip'
        query.set_geolocation(RequestMockup())
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)

        query = LookupQueryMockup()
        query.set_geolocation(RequestMockup())
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)

    def testSetGeoLocationUsedDefinedIpOrCountryPlusMaxmind(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.COUNTRY:
                    return 'valid_country'
                return None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
            def set_maxmind_geolocation(
                self, unused_arg1, unused_arg2, unused_arg3): pass
        
        query = LookupQueryMockup()
        query.user_defined_ip = 'valid_ip'
        query.set_geolocation(RequestMockup())
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)

        query = LookupQueryMockup()
        query.set_geolocation(RequestMockup())
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)

    def testSetGeoLocationGAELatLong(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
        
        query = LookupQueryMockup()
        query.gae_latitude = 'gae_latitude' 
        query.gae_longitude = 'gae_longitude' 
        query.set_geolocation(RequestMockup())
        self.assertEqual(constants.GEOLOCATION_APP_ENGINE,
                         query.geolocation_type)
    
    def testSetGeoLocationGAEIpOrCountryPlusMaxmind(self):

        class RequestMockup:
            def get(self, arg):
                if arg == message.COUNTRY:
                    return 'valid_country'
                return None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
            def set_maxmind_geolocation(
                self, unused_arg1, unused_arg2, unused_arg3): pass
        
        query = LookupQueryMockup()
        query.gae_ip = 'valid_ip'
        query.set_geolocation(RequestMockup())
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)

        query = LookupQueryMockup()
        query.set_geolocation(RequestMockup())
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)

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

        class RequestMockup:
            def __init__(self):
                self.headers = {}
                self.headers[message.HEADER_CITY] = valid_city 
                self.headers[message.HEADER_LAT_LONG] = '0.0,3.0'
 
        query = lookup_query.LookupQuery()
        query.set_appengine_geolocation(RequestMockup())
        self.assertEqual(valid_city, query.gae_city)
        self.assertIsNone(query.gae_country)
        self.assertEqual(valid_latitude, query.gae_latitude)
        self.assertEqual(valid_longitude, query.gae_longitude)

    def testSetPolicyUserDefinedGeoPolicyGeo(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return message.POLICY_GEO

        query = lookup_query.LookupQuery()
        query.user_defined_ip = 'valid_ip'
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_GEO, query.policy)

        query = lookup_query.LookupQuery()
        query.user_defined_latitude = 'valid_lat'
        query.user_defined_longitude = 'valid_long'
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_GEO, query.policy)

    def testSetPolicyUserDefinedGeoPolicyNoGeo(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return 'no_geo_policy'

        query = lookup_query.LookupQuery()
        query.user_defined_ip = 'valid_ip'
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_GEO, query.policy)

        query = lookup_query.LookupQuery()
        query.user_defined_latitude = 'valid_lat'
        query.user_defined_longitude = 'valid_long'
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_GEO, query.policy)

    def testSetPolicyUserDefinedCountryPolicyCountry(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return message.POLICY_COUNTRY

        query = lookup_query.LookupQuery()
        query.user_defined_country = 'valid_country'
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_COUNTRY, query.policy)
       
    def testSetPolicyUserDefinedCountryPolicyGeo(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return message.POLICY_GEO

        query = lookup_query.LookupQuery()
        query.user_defined_country = 'valid_country'
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_GEO, query.policy)
       
    def testSetPolicyUserDefinedCountryPolicyNoGeoNoCountry(self):

        class RequestMockup:
            def get(self, unused_arg):
                return 'no_geo_no_country_policy'

        query = lookup_query.LookupQuery()
        query.user_defined_country = 'valid_country'
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_GEO, query.policy)

    def testSetPolicyUserDefinedMetroPolicyMetro(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return message.POLICY_METRO

        query = lookup_query.LookupQuery()
        query.metro = 'valid_metro'
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_METRO, query.policy)
       
    def testSetPolicyUserDefinedMetroPolicyNoMetro(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return 'no_metro_policy'

        query = lookup_query.LookupQuery()
        query.metro = 'valid_metro'
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_METRO, query.policy)
      
    def testSetPolicyGeoPolicyNoGeo(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return message.POLICY_GEO

        query = lookup_query.LookupQuery()
        query.user_defined_latitude = 'valid_lat'
        query.user_defined_longitude = None
        query.gae_latitude = None
        query.gae_longitude = 'valid_long'
        query.maxmind_latitude = 'valid_lat'
        query.maxmind_longitude = None
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testSetPolicyCountryPolicyNoUserDefinedCountry(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return message.POLICY_COUNTRY

        query = lookup_query.LookupQuery()
        query.user_defined_country = None
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testSetPolicyMetroPolicyNoMetro(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return message.POLICY_METRO

        query = lookup_query.LookupQuery()
        query.metro = None
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testSetPolicyPolicyRandom(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return message.POLICY_RANDOM

        query = lookup_query.LookupQuery()
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_RANDOM, query.policy)
 
    def testSetPolicyNoPolicy(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return None

        query = lookup_query.LookupQuery()
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testSetPolicyNonValidPolicy(self):
        
        class RequestMockup:
            def get(self, unused_arg):
                return 'non_valid_policy'

        query = lookup_query.LookupQuery()
        query.set_policy(RequestMockup())
        self.assertEqual(message.POLICY_RANDOM, query.policy)

    def testInitializeFromHttpRequest(self):
        valid_metro = 'valid_metro'
        valid_tool = 'valid_tool'

        class RequestMockup:
            def __init__(self):
                self.path = valid_tool + '/xyz/'
                self.remote_addr = None  
                self.headers = {}  
            def get(self, arg):
                if arg == message.METRO:
                    return valid_metro

        query = lookup_query.LookupQuery()
        query.initialize_from_http_request(RequestMockup())
        self.assertEqual(valid_tool, query.tool_id)
        self.assertEqual(valid_metro, query.metro)


if __name__ == '__main__':
    unittest2.main()
