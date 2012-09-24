import gflags
import unittest2

from mlabns.util import message
from mlabns.util import resolver

class ResolverTestCase(unittest2.TestCase):

  def testDefaultConstructor(self):
    query = resolver.LookupQuery();
    self.assertEqual(message.POLICY_GEO, query.policy);
    self.assertEqual(gflags.FLAGS.ipv4, query.address_family);

  def testInitializeFromDictionary(self):
    # TODO
    pass


if __name__ == '__main__':
  unittest2.main()
