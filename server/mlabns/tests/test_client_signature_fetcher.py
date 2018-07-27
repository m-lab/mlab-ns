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

        client_signature_fetcher_patch = mock.patch.object(
        client_signature_fetcher,
            'ClientSignatureFetcher',
            autospec=True)
        self.addCleanup(client_signature_fetcher_patch.stop)
        client_signature_fetcher_patch.start()

        self.fetcher = client_signature_fetcher.ClientSignatureFetcher()

    def tearDown(self):
        self.testbed.deactivate()

    def testFetchFromMemcache(self):
        # The mock response is just ints here for simplicity, though the real
        # function returns SliverTool objects.
        mock_memcache_response = 0.1
        client_signature_fetcher.ClientSignatureFetcher().fetch.return_value = (
            mock_memcache_response)
        fetcher_results_actual = self.fetcher.fetch('Faked_key')
        self.assertEqual(mock_memcache_response, fetcher_results_actual)
