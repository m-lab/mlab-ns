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
        self.assertIsNone(query.ip_address)
        self.assertIsNone(query.address_family)
        self.assertIsNone(query.city)
        self.assertIsNone(query.country)
        self.assertIsNone(query.latitude)
        self.assertIsNone(query.longitude)
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

    def testSetIpAddressAndAddressFamilyUserDefined(self):

        class RequestMockup: pass

        class LookupQueryMockup(lookup_query.LookupQuery):
            def __init__(self):
                self.user_defined_ip = 'user_defined_ip'
                self.user_defined_af = 'user_defined_af'
                self.gae_ip = 'gae_ip'
                self.gae_af = 'gae_af'
            def set_user_defined_ip_and_af(self, unused_arg): pass
            def set_gae_ip_and_af(self, unused_arg): pass
        
        query = LookupQueryMockup()
        query.set_ip_address_and_address_family(RequestMockup())
        self.assertEqual('user_defined_ip', query.ip_address)
        self.assertEqual('user_defined_af', query.address_family)

    def testSetIpAddressAndAddressFamilyGAE(self):

        class RequestMockup: pass

        class LookupQueryMockup(lookup_query.LookupQuery):
            def __init__(self):
                self.user_defined_ip = None
                self.user_defined_af = None
                self.gae_ip = 'gae_ip'
                self.gae_af = 'gae_af'
            def set_user_defined_ip_and_af(self, unused_arg): pass
            def set_gae_ip_and_af(self, unused_arg): pass
        
        query = LookupQueryMockup()
        query.set_ip_address_and_address_family(RequestMockup())
        self.assertEqual('gae_ip', query.ip_address)
        self.assertEqual('gae_af', query.address_family)

    def testSetIpAddressAndAddressFamilyMixed(self):

        class RequestMockup: pass

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
        query.set_ip_address_and_address_family(RequestMockup())
        self.assertEqual('user_defined_ip', query.ip_address)
        self.assertIsNone(query.address_family)

    def testSetGeoLocationUsedDefinedValidLatLong(self):
        lat = 0.0        
        lon = 4.3
        city = 'valid_city'        
        country = None 

        class RequestMockup:
            def get(self, arg):
                if arg == message.LATITUDE:
                    return lat
                if arg == message.LONGITUDE:
                    return lon
                if arg == message.CITY:
                    return city
                if arg == message.COUNTRY:
                    return country
                return None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
        
        query = LookupQueryMockup()
        query.set_geolocation(RequestMockup())
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

        class RequestMockup:
            def get(self, arg):
                if arg == message.LATITUDE:
                    return lat
                if arg == message.LONGITUDE:
                    return lon
                if arg == message.CITY:
                    return city
                if arg == message.COUNTRY:
                    return country
                return None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg): pass
        
        query = LookupQueryMockup()
        query.set_geolocation(RequestMockup())
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

        class RequestMockup:
            def __init__(self):
                self.country = None
            def get(self, arg):
                if arg == message.COUNTRY:
                    return self.country
                return None

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
        query.set_geolocation(RequestMockup())
        self.assertEqual(constants.GEOLOCATION_MAXMIND, query.geolocation_type)
        self.assertEqual(lat, query.maxmind_latitude)
        self.assertEqual(lon, query.maxmind_longitude)
        self.assertEqual(city, query.maxmind_city)
        self.assertEqual(country, query.maxmind_country)

        self.assertEqual(query.maxmind_latitude, query.latitude)
        self.assertEqual(query.maxmind_longitude, query.longitude)
        self.assertEqual(query.maxmind_city, query.city)
        self.assertEqual(query.maxmind_country, query.country)

        request = RequestMockup()
        request.country = 'valid_country'  
        query.set_geolocation(request)
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
        
        class RequestMockup:
            def get(self, unused_arg):
                return None

        class LookupQueryMockup(lookup_query.LookupQuery):
            def set_appengine_geolocation(self, unused_arg):
                self.gae_latitude = lat
                self.gae_longitude = lon
                self.gae_city = city
                self.gae_country = country
                
        query = LookupQueryMockup()
        query.set_geolocation(RequestMockup())
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

        class RequestMockup:
            def __init__(self):
                self.country = None
            def get(self, arg):
                if arg == message.COUNTRY:
                    return self.country
                return None

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
        query.set_geolocation(RequestMockup())
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
        request = RequestMockup()
        request.country = 'valid_country'  
        query.set_geolocation(request)
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
        query.latitude = 'valid_lat'
        query.longitude = None
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
