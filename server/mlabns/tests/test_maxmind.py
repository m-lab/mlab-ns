import unittest2

from mlabns.third_party import ipaddr
from mlabns.util import constants
from mlabns.util import maxmind

class GeoRecordTestCase(unittest2.TestCase):
    def testDefaultConstructor(self):
        geo_record = maxmind.GeoRecord()
        self.assertIsNone(geo_record.city)
        self.assertIsNone(geo_record.country)
        self.assertIsNone(geo_record.latitude)
        self.assertIsNone(geo_record.longitude)

class MaxmindTestClass(unittest2.TestCase):
    class GqlMockup:
        def __init__(self, result=None):
            self.result = result
        def get(self):
            return self.result

    class ModelMockup:
        def __init__(self, gql_obj=None, location=None):
            self.gql_obj = gql_obj
            if not gql_obj:
                self.gql_obj = MaxmindTestClass.GqlMockup()
            self.location = location
        def gql(self, unused_arg, ip_num='unused_value', city='unused_value',
                country='unused_value'):
            return self.gql_obj
        def get_by_key_name(self, unused_arg):
            return self.location

    def assertNoneGeoRecord(self, geo_record):
        self.assertIsNone(geo_record.city)
        self.assertIsNone(geo_record.country)
        self.assertIsNone(geo_record.latitude)
        self.assertIsNone(geo_record.longitude)

    def assertGeoRecordEqual(self, geo_record1, geo_record2):
        self.assertEqual(geo_record1.city, geo_record2.city)
        self.assertEqual(geo_record1.country, geo_record2.country)
        self.assertEqual(geo_record1.latitude, geo_record2.latitude)
        self.assertEqual(geo_record1.longitude, geo_record2.longitude)

    def testGetGeolocationDatastoreNotValidAddress(self):
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('non_valid_ip',
            db_type=constants.GEOLOCATION_MAXMIND_USE_DATASTORE))

    def testGetGeolocationDatafileNotValidAddress(self):
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('non_valid_ip',
            db_type=constants.GEOLOCATION_MAXMIND_USE_FILE))

    def testGetGeolocationDatafileNonExistentAddress(self):
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('0.0.0.0',
            db_type=constants.GEOLOCATION_MAXMIND_USE_FILE))

    def testGetIpv4GeolocationDatastoreNotValidAddress(self):
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv4_geolocation_datastore,
                None)
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv4_geolocation_datastore,
                'abc')
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv4_geolocation_datastore,
                '')
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv4_geolocation_datastore,
                '12.3.4')
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv4_geolocation_datastore,
                '1.2.3.256')

    def testGetIpv6GeolocationDatastoreNotValidAddress(self):
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv6_geolocation_datastore,
                None)
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv6_geolocation_datastore,
                'abc')
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv6_geolocation_datastore,
                '')
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv6_geolocation_datastore,
                '1.2.3.4')
        self.assertRaises(
            ipaddr.AddressValueError, maxmind.get_ipv6_geolocation_datastore,
                '1::1::1')

    def testGetIpv4GeolocationDatastoreNoIp(self):
        self.assertNoneGeoRecord(
            maxmind.get_ipv4_geolocation_datastore(
                '1.2.3.4', ipv4_table=MaxmindTestClass.ModelMockup()))

    def testGetIpv6GeolocationDatastoreNoIp(self):
        self.assertNoneGeoRecord(
            maxmind.get_ipv6_geolocation_datastore(
                '::1', ipv6_table=MaxmindTestClass.ModelMockup()))

    def testGetIpv4GeolocationDatastoreTooSmallEndIp(self):
        class GqlResultMockup:
            def __init__(self):
                self.end_ip_num = 16909059  # 1.2.3.3
        self.assertNoneGeoRecord(
            maxmind.get_ipv4_geolocation_datastore(
                '1.2.3.4', ipv4_table=MaxmindTestClass.ModelMockup(
                    gql_obj=MaxmindTestClass.GqlMockup(
                        result=GqlResultMockup()))))

    def testGetIpv6GeolocationDatastoreTooSmallEndIp(self):
        class GqlResultMockup:
            def __init__(self):
                self.end_ip_num = 281483566841859  # 1:2:3:3::5 >> 64
        self.assertNoneGeoRecord(
            maxmind.get_ipv6_geolocation_datastore(
                '1:2:3:4::5', ipv6_table=MaxmindTestClass.ModelMockup(
                    gql_obj=MaxmindTestClass.GqlMockup(
                        result=GqlResultMockup()))))

    def testGetIpv4GeolocationDatastoreNoLocation(self):
        class GqlResultMockup:
            def __init__(self):
                self.end_ip_num = 16909061  # 1.2.3.5
                self.location_id = 'unused'
        self.assertNoneGeoRecord(
            maxmind.get_ipv4_geolocation_datastore(
                '1.2.3.4',
                 ipv4_table=MaxmindTestClass.ModelMockup(
                     gql_obj=MaxmindTestClass.GqlMockup(
                          result=GqlResultMockup())),
                 city_table=MaxmindTestClass.ModelMockup()))

    def testGetIpv4GeolocationValidLocation(self):
        class GqlResultMockup:
            def __init__(self):
                self.end_ip_num = 16909061  # 1.2.3.5
                self.location_id = 'unused'
        class Location:
            def __init__(self):
                self.city = 'city'
                self.country = 'country'
                self.latitude = 'latitude'
                self.longitude = 'longitude'
        location = Location()
        expected_geo_record = maxmind.GeoRecord()
        expected_geo_record.city = location.city
        expected_geo_record.country = location.country
        expected_geo_record.latitude = location.latitude
        expected_geo_record.longitude = location.longitude

        self.assertGeoRecordEqual(
            expected_geo_record,
            maxmind.get_ipv4_geolocation_datastore(
                '1.2.3.4',
                 ipv4_table=MaxmindTestClass.ModelMockup(
                     gql_obj=MaxmindTestClass.GqlMockup(
                          result=GqlResultMockup())),
                 city_table=MaxmindTestClass.ModelMockup(
                     location=location)))

    def testGetIpv6GeolocationValidLocation(self):
        class GqlResultMockup:
            def __init__(self):
                self.end_ip_num = 281483566841861  # 1:2:3:5::5 >> 64
                self.country = location.country
                self.latitude = location.latitude
                self.longitude = location.longitude

        class Location:
            def __init__(self):
                self.country = 'country'
                self.latitude = 'latitude'
                self.longitude = 'longitude'
        location = Location()
        expected_geo_record = maxmind.GeoRecord()
        expected_geo_record.city = constants.UNKNOWN_CITY
        expected_geo_record.country = location.country
        expected_geo_record.latitude = location.latitude
        expected_geo_record.longitude = location.longitude

        self.assertGeoRecordEqual(
            expected_geo_record,
            maxmind.get_ipv6_geolocation_datastore(
                '1:2:3:4::5',
                 ipv6_table=MaxmindTestClass.ModelMockup(
                     gql_obj=MaxmindTestClass.GqlMockup(
                         result=GqlResultMockup()))))

    def testGetCountryGeolocationNoCountry(self):
        self.assertNoneGeoRecord(
            maxmind.get_country_geolocation(
                'unused_country',
                 country_table=MaxmindTestClass.ModelMockup()))

    def testGetCountryGeolocationYesCountry(self):
        class Location:
            def __init__(self):
                self.alpha2_code = 'country'
                self.latitude = 'latitude'
                self.longitude = 'longitude'
        location = Location()
        expected_geo_record = maxmind.GeoRecord()
        expected_geo_record.city = constants.UNKNOWN_CITY
        expected_geo_record.country = location.alpha2_code
        expected_geo_record.latitude = location.latitude
        expected_geo_record.longitude = location.longitude

        self.assertGeoRecordEqual(
            expected_geo_record,
            maxmind.get_country_geolocation(
                'unused_country',
                 country_table=MaxmindTestClass.ModelMockup(location=location)))

    def testGetCityGeolocationNoCity(self):
        self.assertNoneGeoRecord(
            maxmind.get_city_geolocation(
                'unused_city',
                'unused_country',
                 city_table=MaxmindTestClass.ModelMockup(
                     gql_obj=MaxmindTestClass.GqlMockup())))

    def testGetCityGeolocationYesCity(self):
        class Location:
            def __init__(self):
                self.city = 'city'
                self.country = 'country'
                self.latitude = 'latitude'
                self.longitude = 'longitude'
        location = Location()
        expected_geo_record = maxmind.GeoRecord()
        expected_geo_record.city = location.city
        expected_geo_record.country = location.country
        expected_geo_record.latitude = location.latitude
        expected_geo_record.longitude = location.longitude
        self.assertGeoRecordEqual(
            expected_geo_record,
            maxmind.get_city_geolocation(
                'unused_city',
                'unused_country',
                 city_table=MaxmindTestClass.ModelMockup(
                     gql_obj=MaxmindTestClass.GqlMockup(result=location))))


if __name__ == '__main__':
    unittest2.main()
