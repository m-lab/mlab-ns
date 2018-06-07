import mock
import unittest2
import urllib2

from mlabns.util import constants
from mlabns.util import maxmind

from google.appengine.ext import testbed


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

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_all_stubs()

    def tearDown(self):
        self.testbed.deactivate()

    # The GAE app uses the GoogleAppEngineCloudStorageClient python module to
    # fetch the MaxMind database file from GCS. However, that module doesn't,
    # apparently, work in a non-GAE environment, like Travis-CI. So this
    # functions is used to mock fetching the database file, but using the
    # public GCS link instead.
    def get_database_file(self):
        base_url = 'https://storage.googleapis.com'
        bucket = base_url + '/' + constants.GEOLOCATION_MAXMIND_GCS_BUCKET
        path = bucket + '/' + constants.GEOLOCATION_MAXMIND_BUCKET_PATH
        database_url = path + '/' + constants.GEOLOCATION_MAXMIND_CITY_FILE
        db_file = urllib2.urlopen(database_url)
        db_file.name = constants.GEOLOCATION_MAXMIND_CITY_FILE
        return db_file

    class GqlMockup:

        def __init__(self, result=None):
            self.result = result

        def get(self):
            return self.result

    # NOTE: Below, we are intentionally not testing for a valid entry in the
    # MaxMind database. The database is (currently) around 55MB, takes too long
    # to download, changes frequently, and a local copy cannot be added to this
    # codebase because it exceeds the maximum size for a static file in GAE.
    # TODO: MaxMind maintains a Github repo which, among other things, contains 
    # sample databases that they use for unit testing. We should pull in one of
    # those databases for testing:
    # https://github.com/maxmind/MaxMind-DB/tree/master/test-data
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

    @mock.patch.object(maxmind, 'get_database_file')
    def testGetGeolocationNotValidAddress(self, mock_database_file):
        mock_database_file.side_effect = self.get_database_file
        ip_addr = 'abc'
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation(ip_addr))

    @mock.patch.object(maxmind, 'get_database_file')
    def testGetGeolocationNoneAddress(self, mock_database_file):
        mock_database_file.side_effect = self.get_database_file
        ip_addr = None
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation(ip_addr))

    @mock.patch.object(maxmind, 'get_database_file')
    def testGetGeolocationNoRecordForIp(self, mock_database_file):
        mock_database_file.side_effect = self.get_database_file
        # ip_addr can be any invalid IP that looks like an IP.
        ip_addr = '0.1.2.3'
        self.assertNoneGeoRecord(maxmind.get_ip_geolocation(ip_addr))

    def testGetCountryGeolocationNoCountry(self):
        self.assertNoneGeoRecord(maxmind.get_country_geolocation(
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
        self.assertNoneGeoRecord(maxmind.get_city_geolocation(
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
