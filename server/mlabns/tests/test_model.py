import unittest2

from google.appengine.api import memcache
from google.appengine.ext import testbed

from mlabns.db import model


def assertObjectSetsEqualByAttribute(test_case, set_a, set_b, attribute_lambda):
    """Equality of sets is based on length and attribute value of objects

    attribute_lambda of the form: 'lambda x: x.attribute'
    """
    list_a = list(set_a)
    list_b = list(set_b)

    ids_a = [attribute_lambda(x) for x in list_a]
    ids_b = [attribute_lambda(x) for x in list_b]
    test_case.assertEqual(len(list_a), len(list_b))
    test_case.assertListEqual(sorted(ids_a), sorted(ids_b))


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
        tools = [tool_a, tool_b, tool_c]

        tool_a.put()
        tool_b.put()
        tool_c.put()

        retrieved = model.get_all_tool_ids()
        tool_id_lambda = lambda x: x.tool_id
        assertObjectSetsEqualByAttribute(self, retrieved, tools, tool_id_lambda)

    def test_get_all_tool_ids_no_stored_tools_returns_empty(self):
        assertObjectSetsEqualByAttribute(self, model.get_all_tool_ids(), [],
                                         None)


class GetSliverToolByToolIdTest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.tool_id_lambda = lambda x: x.tool_id
        self.tool_extra_lambda = lambda x: x.tool_extra

    def tearDown(self):
        self.testbed.deactivate()

    def test_get_SliverTool_by_tool_id_returns_successfully_from_memcache(self):
        sliver_tool_a = model.SliverTool(tool_id='mock_tool_id',
                                         tool_extra='sliver_tool_a')
        sliver_tool_b = model.SliverTool(tool_id='mock_tool_id',
                                         tool_extra='sliver_tool_b')
        sliver_tool_c = model.SliverTool(tool_id='mock_tool_id',
                                         tool_extra='sliver_tool_c')
        expected = [sliver_tool_a, sliver_tool_b, sliver_tool_c]

        memcache.set('sliver_tool_tool_id_mock_tool_id', expected)
        retrieved = model.get_SliverTool_by_tool_id('mock_tool_id')

        assertObjectSetsEqualByAttribute(self, retrieved, expected,
                                         self.tool_id_lambda)
        assertObjectSetsEqualByAttribute(self, retrieved, expected,
                                         self.tool_extra_lambda)

    def test_get_SliverTool_by_tool_id_returns_successfully_from_datastore(
            self):
        sliver_tool_a = model.SliverTool(tool_id='mock_tool_id',
                                         tool_extra='sliver_tool_a')
        sliver_tool_b = model.SliverTool(tool_id='mock_tool_id',
                                         tool_extra='sliver_tool_b')
        sliver_tool_c = model.SliverTool(tool_id='mock_tool_id',
                                         tool_extra='sliver_tool_c')
        expected = [sliver_tool_a, sliver_tool_b, sliver_tool_c]

        sliver_tool_a.put()
        sliver_tool_b.put()
        sliver_tool_c.put()

        retrieved = model.get_SliverTool_by_tool_id('mock_tool_id')
        assertObjectSetsEqualByAttribute(self, retrieved, expected,
                                         self.tool_id_lambda)
        assertObjectSetsEqualByAttribute(self, retrieved, expected,
                                         self.tool_extra_lambda)

    def test_get_SliverTool_by_tool_id_datastore_and_memcache_empty_return_none(
            self):
        self.assertEqual(
            model.get_SliverTool_by_tool_id('mock_tool_id'), [], None)

    def test_get_SliverTool_by_tool_id_returns_from_memcache_over_datastore(
            self):
        memcache_a = model.SliverTool(tool_id='mock_tool_id',
                                      tool_extra='memcache')
        memcache_b = model.SliverTool(tool_id='mock_tool_id',
                                      tool_extra='memcache')
        memcache_c = model.SliverTool(tool_id='mock_tool_id',
                                      tool_extra='memcache')
        memcache_expected = [memcache_a, memcache_b, memcache_c]

        model.SliverTool(tool_id='mock_tool_id', tool_extra='datastore').put()
        model.SliverTool(tool_id='mock_tool_id', tool_extra='datastore').put()
        model.SliverTool(tool_id='mock_tool_id', tool_extra='datastore').put()

        memcache.set('sliver_tool_tool_id_mock_tool_id', memcache_expected)

        retrieved = model.get_SliverTool_by_tool_id('mock_tool_id')
        assertObjectSetsEqualByAttribute(self, retrieved, memcache_expected,
                                         self.tool_id_lambda)
        assertObjectSetsEqualByAttribute(self, retrieved, memcache_expected,
                                         self.tool_extra_lambda)


if __name__ == '__main__':
    unittest2.main()
