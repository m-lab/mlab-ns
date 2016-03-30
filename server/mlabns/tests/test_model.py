import unittest2

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

    def tearDown(self):
        self.testbed.deactivate()

    def assertUnorderedToolSetsEqual(self, set_a, set_b):
        list_a = list(set_a)
        list_b = list(set_b)

        ids_a = [x.tool_id for x in list_a]
        ids_b = [x.tool_id for x in list_b]
        self.assertEqual(len(list_a), len(list_b))
        self.assertListEqual(sorted(ids_a), sorted(ids_b))

    def test_get_all_tool_ids_returns_successfully_from_datastore(self):
        tool_a = model.Tool(tool_id='tool_a')
        tool_b = model.Tool(tool_id='tool_b')
        tool_c = model.Tool(tool_id='tool_c')
        tools = [tool_a, tool_b, tool_c]

        tool_a.put()
        tool_b.put()
        tool_c.put()

        retrieved = model.get_all_tool_ids()
        self.assertUnorderedToolSetsEqual(retrieved, tools)

    def test_get_all_tool_ids_no_stored_tools_returns_empty(self):
        self.assertUnorderedToolSetsEqual(model.get_all_tool_ids(), [])


if __name__ == '__main__':
    unittest2.main()
