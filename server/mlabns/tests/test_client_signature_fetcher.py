import collections
import unittest

import mock

from mlabns.db import model
from mlabns.db import sliver_tool_fetcher
from mlabns.util import constants
from mlabns.util import message

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext import testbed

class ClientSignatureFetcherTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_all_stubs()
        ndb.get_context().clear_cache()

        client_signature_fetcher_memcache_patch = mock.patch.object(
            client_signature_fetcher,
            'ClientSignatureFetcherMemcache',
            autospec=True)
        self.addCleanup(client_signature_fetcher_memcache_patch.stop)
        client_signature_fetcher_memcache_patch.start()

        self.fetcher = client_signature_fetcher.ClientSignatureFetcher()

    def tearDown(self):
        self.testbed.deactivate()

    def testFetchFromMemcache(self):
        # The mock response is just ints here for simplicity, though the real
        # function returns SliverTool objects.
        mock_memcache_response = [0.1, 0.2, 0.3]
        client_signature_fetcher.ClientSignatureFetcher().fetch.return_value = (
            mock_memcache_response)
        tool_properties = sliver_tool_fetcher.ToolProperties(
            tool_id='mock_tool_a')
        fetcher_results_actual = self.fetcher.fetch(tool_properties)
        self.assertSequenceEqual(mock_memcache_response, fetcher_results_actual)
