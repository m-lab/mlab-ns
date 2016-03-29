import unittest2

from google.appengine.api import memcache
from google.appengine.ext import testbed

from mlabns.db import model


class ModelTestCase(unittest2.TestCase):

    def testGetSliverToolIdNone(self):
        tool_id = None
        slice_id = 'slice_id'
        server_id = 'server_id'
        site_id = 'site_id'
        self.assertIsNone(model.get_sliver_tool_id(tool_id, slice_id, server_id,
                                                   site_id))

    def testGetSliverToolIdValid(self):
        tool_id = 'tool_id'
        slice_id = 'slice_id'
        server_id = 'server_id'
        site_id = 'site_id'
        self.assertEqual(
            model.get_sliver_tool_id(tool_id, slice_id, server_id, site_id),
            'tool_id-slice_id-server_id-site_id')


class GetAllToolIdsTest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_get_all_tool_ids_returns_successfully_from_memcache(self):
        tool_a = model.Tool(tool_id='tool_a')
        tool_b = model.Tool(tool_id='tool_b')
        tool_c = model.Tool(tool_id='tool_c')

        tools = [tool_c, tool_b, tool_a]
        memcache.set('all_ordered_tool_ids', tools)
        retrieved = model.get_all_tool_ids()

        self.assertEqual(len(retrieved), 3)
        self.assertEqual(retrieved[0].tool_id, 'tool_c')
        self.assertEqual(retrieved[1].tool_id, 'tool_b')
        self.assertEqual(retrieved[2].tool_id, 'tool_a')

    def test_get_all_tool_ids_returns_successfully_from_datastore(self):
        tool_a = model.Tool(tool_id='tool_a')
        tool_b = model.Tool(tool_id='tool_b')
        tool_c = model.Tool(tool_id='tool_c')

        tool_a.put()
        tool_b.put()
        tool_c.put()

        retrieved = model.get_all_tool_ids()
        self.assertEqual(len(retrieved), 3)
        self.assertEqual(retrieved[0].tool_id, 'tool_c')
        self.assertEqual(retrieved[1].tool_id, 'tool_b')
        self.assertEqual(retrieved[2].tool_id, 'tool_a')

    def test_get_all_tool_ids_no_stored_tools_returns_empty(self):
        self.assertEqual(model.get_all_tool_ids(), [])

    def test_get_all_tool_ids_returns_from_memcache_over_datastore(self):
        memcache_tool = model.Tool(tool_id='memcache_tool')

        tools = [memcache_tool]
        memcache.set('all_ordered_tool_ids', tools)

        datastore_tool = model.Tool(tool_id='datastore_tool')
        datastore_tool.put()

        retrieved = model.get_all_tool_ids()
        self.assertEqual(retrieved[0].tool_id, 'memcache_tool')


if __name__ == '__main__':
    unittest2.main()
