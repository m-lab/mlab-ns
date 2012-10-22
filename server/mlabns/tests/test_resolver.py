import unittest2

from mlabns.util import message
from mlabns.util import resolver

class ResolverBaseTestCase(unittest2.TestCase):
    def testGetCandidates(self):
        
        class QueryMockup:
            pass
            
        class ResolverBaseMockup(resolver.ResolverBase):
            def _get_candidates(self, unused_arg, address_family):
                if address_family == message.ADDRESS_FAMILY_IPv6:
                    return ['valid_candidate']
                return []

        base_resolver = ResolverBaseMockup()
        
        # Case 1) List is not empty for the input address family.
        query = QueryMockup()
        query.address_family = message.ADDRESS_FAMILY_IPv6
        self.assertGreater(len(base_resolver.get_candidates(query)), 0)
        
        # Case 2) List is empty for input address_family and there is no
        #         user-defined address family.
        query = QueryMockup()
        query.address_family = message.ADDRESS_FAMILY_IPv4
        query.user_defined_af = None        
        self.assertGreater(len(base_resolver.get_candidates(query)), 0)
        
        # Case 3) List is empty for input address_family and user-defined
        #         address family == input address family.
        query = QueryMockup()
        query.address_family = message.ADDRESS_FAMILY_IPv4
        query.user_defined_af = message.ADDRESS_FAMILY_IPv4
        self.assertEqual(len(base_resolver.get_candidates(query)), 0)
        
        # Case 4) List is empty for input address_family and user-defined
        #         address family != input address family.
        query = QueryMockup()
        query.address_family = message.ADDRESS_FAMILY_IPv4
        query.user_defined_af = message.ADDRESS_FAMILY_IPv6
        self.assertGreater(len(base_resolver.get_candidates(query)), 0)
        
    def testAnswerQueryEmptyResult(self):
        class QueryMockup:
            def __init__(self):
                self.tool_id = 'tool_id'
            
        class ResolverBaseMockup(resolver.ResolverBase):
            def get_candidates(self, unused_arg):
                return []
        
        base_resolver = ResolverBaseMockup()
        query = QueryMockup()
        self.assertIsNone(base_resolver.answer_query(query))
        
    def testAnswerQueryNonEmptyResult(self):
        class QueryMockup:
            def __init__(self):
                self.tool_id = 'tool_id'
            
        class ResolverBaseMockup(resolver.ResolverBase):
            def get_candidates(self, unused_arg):
                return ['candidate']
        
        base_resolver = ResolverBaseMockup()
        query = QueryMockup()
        self.assertGreater(len(base_resolver.answer_query(query)), 0)


class ResolverTestCase(unittest2.TestCase):
    def testNewResolver(self):
        self.assertIsInstance(resolver.new_resolver(message.POLICY_GEO),
                              resolver.GeoResolver)
        self.assertIsInstance(resolver.new_resolver(message.POLICY_METRO),
                              resolver.MetroResolver)
        self.assertIsInstance(resolver.new_resolver(message.POLICY_RANDOM),
                              resolver.RandomResolver)
        self.assertIsInstance(resolver.new_resolver(message.POLICY_COUNTRY),
                              resolver.CountryResolver)
        self.assertIsInstance(resolver.new_resolver('another_policy'),
                              resolver.RandomResolver)


if __name__ == '__main__':
    unittest2.main()
