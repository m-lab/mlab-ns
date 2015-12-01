import unittest2
import mock

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

    def testEqualToComparisonMethodIdenticalRecords(self):
        geo_record_1 = maxmind.GeoRecord()
        geo_record_1.city = "Greenwich, London"
        geo_record_1.country = "UK"
        geo_record_1.latitude = 51.4800
        geo_record_1.longitude = 0.0000

        geo_record_2 = maxmind.GeoRecord()
        geo_record_2.city = geo_record_1.city
        geo_record_2.country = geo_record_1.country
        geo_record_2.latitude = geo_record_1.latitude
        geo_record_2.longitude = geo_record_1.longitude

        with self.assertRaises(AssertionError):
            self.assertNotEqual(geo_record_1, geo_record_2)
        self.assertEqual(geo_record_1, geo_record_2)

    def testEqualToComparisonMethodDifferentRecords(self):
        geo_record_1 = maxmind.GeoRecord()
        geo_record_1.city = "Greenwich, London"
        geo_record_1.country = "UK"
        geo_record_1.latitude = 51.4800
        geo_record_1.longitude = 0.0000

        geo_record_2 = maxmind.GeoRecord()
        geo_record_2.city = geo_record_1.city
        geo_record_2.country = geo_record_1.country
        geo_record_2.latitude = geo_record_1.latitude
        geo_record_2.longitude = 99.9999

        with self.assertRaises(AssertionError):
            self.assertEqual(geo_record_1, geo_record_2)
        self.assertNotEqual(geo_record_1, geo_record_2)

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

    def testGetGeolocationNotValidAddress(self):
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('non_valid_ip'))

    def testGetGeolocationNonExistentAddress(self):
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('0.0.0.0'))

    def testGetGeolocationNotValidAddress(self):
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation(None))
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('abc'))

    @mock.patch('pygeoip.GeoIP.record_by_addr')
    def testGetGeolocationNoRecordForIp(self, mock_geoip_record_by_addr):
        mock_geoip_record_by_addr.return_value = None
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('1.2.3.4'))

    @mock.patch('pygeoip.GeoIP.record_by_addr')
    def testGetGeolocationValidLocation(self, mock_geoip_record_by_addr):
        mock_geolocation = {
            'city': 'Greenwich, London',
            'country_code': 'UK',
            'latitude': '51.4800',
            'longitude': '0.0000'
        }

        expected_geo_record = maxmind.GeoRecord()
        expected_geo_record.city = mock_geolocation['city']
        expected_geo_record.country = mock_geolocation['country_code']
        expected_geo_record.latitude = mock_geolocation['latitude']
        expected_geo_record.longitude = mock_geolocation['longitude']

        mock_geoip_record_by_addr.return_value = mock_geolocation
        self.assertEqual(expected_geo_record,
                maxmind.get_ip_geolocation('1.2.3.4'))

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

        self.assertEqual(
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
        self.assertEqual(
            expected_geo_record,
            maxmind.get_city_geolocation(
                'unused_city',
                'unused_country',
                 city_table=MaxmindTestClass.ModelMockup(
                     gql_obj=MaxmindTestClass.GqlMockup(result=location))))


if __name__ == '__main__':
    unittest2.main()
