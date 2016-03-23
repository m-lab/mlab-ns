import unittest2

from google.appengine.api import memcache
from google.appengine.ext import testbed

from mlabns.db import nagios_status_data
from mlabns.db import model
from mlabns.util import constants


class GetNagiosCredentialsTest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_get_nagios_credentials_returns_successfully_from_memcache(self):
        nagios_model = model.Nagios(url='foo')
        memcache.set(constants.DEFAULT_NAGIOS_ENTRY, nagios_model)
        retrieved = nagios_status_data.get_nagios_credentials()
        self.assertEqual(retrieved.url, 'foo')

    def test_get_nagios_credentials_returns_successfully_from_datastore(self):
        nagios_model = model.Nagios(key_name=constants.DEFAULT_NAGIOS_ENTRY,
                                    url='foo')
        nagios_model.put()
        retrieved = nagios_status_data.get_nagios_credentials()
        self.assertEqual(retrieved.url, 'foo')

    def test_get_nagios_credentials_no_credentials_stored_logs_error(self):
        retrieved = nagios_status_data.get_nagios_credentials()
        self.assertIsNone(retrieved)


if __name__ == '__main__':
    unittest2.main()
