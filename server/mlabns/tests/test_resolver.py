import gflags
import unittest2

from mlabns.util import constants
from mlabns.util import message
from mlabns.util import resolver

class ResolverTestCase(unittest2.TestCase):

  def testDefaultConstructor(self):
    query = resolver.LookupQuery();
    self.assertEqual(None, query.tool_id)
    self.assertEqual(None, query.policy)
    self.assertEqual(None, query.metro)
    self.assertEqual(None, query.ip_address)
    self.assertEqual(None, query.address_family)
    self.assertEqual(None, query.city)
    self.assertEqual(None, query.country)
    self.assertEqual(None, query.latitude)
    self.assertEqual(None, query.longitude)
    self.assertEqual(constants.GEOLOCATION_APP_ENGINE, query.geolocation_type)
    self.assertEqual(None, query.response_format)

  def testInitializeFromDictionary(self):
    # TODO
    pass


if __name__ == '__main__':
  unittest2.main()
