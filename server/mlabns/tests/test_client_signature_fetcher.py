import unittest

import mock

from mlabns.db import client_signature_fetcher

from google.appengine.ext import ndb
from google.appengine.ext import testbed


class ClientSignatureFetcherTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_all_stubs()
        ndb.get_context().clear_cache()

    def tearDown(self):
        self.testbed.deactivate()

    def testFetchFromMemcache(self):
        with mock.patch.object(
                client_signature_fetcher,
                'ClientSignatureFetcher') as _:
            mock_memcache_response = 0.1
            client_signature_fetcher.ClientSignatureFetcher().fetch.return_value = (
            mock_memcache_response)
            fetcher_results_actual = client_signature_fetcher.ClientSignatureFetcher(
            ).fetch('Faked_key')
            self.assertEqual(mock_memcache_response, fetcher_results_actual)
