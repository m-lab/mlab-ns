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

    def test_get_all_tool_ids_returns_successfully_from_datastore(self):
        tool_a = model.Tool(tool_id='tool_a')
        tool_b = model.Tool(tool_id='tool_b')
        tool_c = model.Tool(tool_id='tool_c')
        expected_ids = ['tool_a', 'tool_b', 'tool_c']

        tool_a.put()
        tool_b.put()
        tool_c.put()

        actual_ids = model.get_all_tool_ids()
        self.assertItemsEqual(actual_ids, expected_ids)
        self.assertTrue(model.is_valid_tool('tool_c'))
        self.assertFalse(model.is_valid_tool('this_is_an_invalid_tool_id'))

    def test_get_all_tool_ids_no_stored_tools_returns_empty(self):
        self.assertItemsEqual(model.get_all_tool_ids(), [])
        self.assertFalse(model.is_valid_tool('any_tool_id'))


if __name__ == '__main__':
    unittest2.main()
