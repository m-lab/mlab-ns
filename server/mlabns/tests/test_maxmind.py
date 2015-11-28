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

    def testGetGeolocationNotValidAddress(self):
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('non_valid_ip'))

    def testGetGeolocationNonExistentAddress(self):
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('0.0.0.0'))

    def testGetGeolocationNotValidAddress(self):
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation(None))
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('abc'))
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation(''))
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('1.2.3.256'))
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('1::1::1'))

    @mock.patch('mlabns.util.maxmind.get_ip_geolocation')
    def testGetGeolocationCalledWithArguments(self, mock_get_ip_geolocation):
        mock_call = {'ip': '1.2.3.4', 'path': '/tmp/path'}
        mock_get_ip_geolocation(mock_call['ip'], city_file = mock_call['path'])
        mock_get_ip_geolocation.assert_called_with(mock_call['ip'],
                city_file = mock_call['path'])

    @mock.patch('pygeoip.GeoIP.record_by_addr')
    def testGetGeolocationNoRecordForIp(self, mock_geoip_record_by_addr):
        mock_geoip_record_by_addr.return_value = None
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('1.2.3.4'))

    @mock.patch('pygeoip.GeoIP.record_by_addr')
    def testGetGeolocationNoneRecordForTypeError(self,
            mock_geoip_record_by_addr):
        mock_geoip_record_by_addr.side_effect = TypeError
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation('1.2.3.4'))

    @mock.patch('pygeoip.GeoIP.record_by_addr')
    def testGetGeolocationValidLocation(self, mock_geoip_record_by_addr):
        mock_geolocation = {
            'city': 'city',
            'country_code': 'country',
            'latitude': 'latitude',
            'longitude': 'longitude'
        }
        expected_geo_record = maxmind.GeoRecord()
        expected_geo_record.city = mock_geolocation['city']
        expected_geo_record.country = mock_geolocation['country_code']
        expected_geo_record.latitude = mock_geolocation['latitude']
        expected_geo_record.longitude = mock_geolocation['longitude']

        mock_geoip_record_by_addr.return_value = mock_geolocation
        self.assertGeoRecordEqual(expected_geo_record,
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
