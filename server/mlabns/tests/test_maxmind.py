import os
import sys
import unittest2
import mock
import socket

from mlabns.third_party import ipaddr
from mlabns.util import constants
from mlabns.util import maxmind

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../third_party/pygeoip')))
import pygeoip


class GeoRecordTestCase(unittest2.TestCase):

    def testDefaultConstructor(self):
        geo_record = maxmind.GeoRecord()
        self.assertIsNone(geo_record.city)
        self.assertIsNone(geo_record.country)
        self.assertIsNone(geo_record.latitude)
        self.assertIsNone(geo_record.longitude)

    def testEqualToComparisonMethodIdenticalRecords(self):
        geo_record_1 = maxmind.GeoRecord(city='Greenwich, London',
                                         country='UK',
                                         latitude=51.4800,
                                         longitude=0.0000)
        geo_record_2 = maxmind.GeoRecord(city=geo_record_1.city,
                                         country=geo_record_1.country,
                                         latitude=geo_record_1.latitude,
                                         longitude=geo_record_1.longitude)
        self.assertEqual(geo_record_1, geo_record_2)

    def testEqualToComparisonMethodDifferentRecords(self):
        geo_record_1 = maxmind.GeoRecord(city='Greenwich, London',
                                         country='UK',
                                         latitude=51.4800,
                                         longitude=0.0000)
        geo_record_2 = maxmind.GeoRecord(city=geo_record_1.city,
                                         country=geo_record_1.country,
                                         latitude=geo_record_1.latitude,
                                         longitude=99.9999)
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

        def gql(self,
                unused_arg,
                ip_num='unused_value',
                city='unused_value',
                country='unused_value'):
            return self.gql_obj

        def get_by_key_name(self, unused_arg):
            return self.location

    def assertNoneGeoRecord(self, geo_record):
        self.assertIsNone(geo_record.city)
        self.assertIsNone(geo_record.country)
        self.assertIsNone(geo_record.latitude)
        self.assertIsNone(geo_record.longitude)

    def setUp(self):
        geoip_patch = mock.patch('pygeoip.GeoIP')
        self.addCleanup(geoip_patch.stop)
        geoip_patch.start()

        mock_geoip = mock.Mock()
        pygeoip.GeoIP.return_value = mock_geoip
        self.mock_record_by_addr = mock_geoip.record_by_addr

    def testGetGeolocationNotValidAddress(self):
        ip_addr = 'abc'
        self.mock_record_by_addr.side_effect = socket.error
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation(ip_addr))
        self.mock_record_by_addr.assert_called_with(ip_addr)
        pygeoip.GeoIP.assert_called_with(
            constants.GEOLOCATION_MAXMIND_CITY_FILE,
            flags=pygeoip.const.STANDARD)

    def testGetGeolocationNoneAddress(self):
        ip_addr = None
        self.mock_record_by_addr.side_effect = TypeError
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation(ip_addr))
        self.mock_record_by_addr.assert_called_with(ip_addr)
        pygeoip.GeoIP.assert_called_with(
            constants.GEOLOCATION_MAXMIND_CITY_FILE,
            flags=pygeoip.const.STANDARD)

    def testGetGeolocationNoRecordForIp(self):
        ip_addr = '1.2.3.4'
        self.mock_record_by_addr.return_value = None
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation(ip_addr))
        self.mock_record_by_addr.assert_called_with(ip_addr)
        pygeoip.GeoIP.assert_called_with(
            constants.GEOLOCATION_MAXMIND_CITY_FILE,
            flags=pygeoip.const.STANDARD)

    def testGetGeolocationValidLocation(self):
        ip_addr = '1.2.3.4'
        mock_record = {
            'city': 'Greenwich, London',
            'country_code': 'UK',
            'latitude': '51.4800',
            'longitude': '0.0000'
        }
        expected_record = maxmind.GeoRecord(city=mock_record['city'],
                                            country=mock_record['country_code'],
                                            latitude=mock_record['latitude'],
                                            longitude=mock_record['longitude'])

        self.mock_record_by_addr.return_value = mock_record
        self.assertEqual(expected_record, maxmind.get_ip_geolocation(ip_addr))
        self.mock_record_by_addr.assert_called_with(ip_addr)
        pygeoip.GeoIP.assert_called_with(
            constants.GEOLOCATION_MAXMIND_CITY_FILE,
            flags=pygeoip.const.STANDARD)

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
