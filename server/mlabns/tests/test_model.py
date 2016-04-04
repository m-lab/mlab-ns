import unittest2

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


if __name__ == '__main__':
    unittest2.main()
