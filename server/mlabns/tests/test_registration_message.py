import unittest2

from mlabns.util import message
from mlabns.util import registration_message

class SiteRegistrationMessageTestCase(unittest2.TestCase):
    def testDefaultConstructor(self):
        site_registration_message = \
            registration_message.SiteRegistrationMessage()
        for var in site_registration_message.required_fields:
            if var is message.ENTITY:
                self.assertEqual(message.ENTITY_SITE, 
                                 site_registration_message.__dict__[var])
            else:
                self.assertIsNone(site_registration_message.__dict__[var])

    def testInitializeFromDictionaryValid(self):
        site_registration_message = \
            registration_message.SiteRegistrationMessage()
        
        # Without timestamp.
        input_dictionary = {}
        for message_field in site_registration_message.required_fields:
            input_dictionary[message_field] = message_field
        site_registration_message.initialize_from_dictionary(input_dictionary)
        for message_field in site_registration_message.required_fields:
	    self.assertEqual(input_dictionary[message_field],
                             site_registration_message.__dict__[message_field]) 
        self.assertIsNone(site_registration_message.timestamp)

        # With timestamp.
        input_dictionary[message.TIMESTAMP] = message.TIMESTAMP
        site_registration_message.initialize_from_dictionary(input_dictionary)  
        self.assertEqual(input_dictionary[message.TIMESTAMP],
                         site_registration_message.__dict__[message.TIMESTAMP]) 
      
    def testInitializeFromDictionaryMissingFields(self):
        input_dictionary = {}
        input_dictionary[message.ENTITY] = 'fake_entity'
        site_registration_message = \
            registration_message.SiteRegistrationMessage()
        self.assertRaises(
            message.FormatError,
            site_registration_message.initialize_from_dictionary,
            input_dictionary)

    def testToDictionaryValid(self):
        site_registration_message = \
            registration_message.SiteRegistrationMessage()
        expected_dictionary = {}
        for message_field in site_registration_message.required_fields:
            site_registration_message.__dict__[message_field] =  message_field
            expected_dictionary[message_field] = message_field
        expected_dictionary[message.TIMESTAMP] = None
        self.assertDictEqual(
            expected_dictionary, site_registration_message.to_dictionary()) 
        
class SliverToolRegistrationMessageTestCase(unittest2.TestCase):
    def testDefaultConstructor(self):
        sliver_tool_registration_message = \
            registration_message.SliverToolRegistrationMessage()
        for var in sliver_tool_registration_message.required_fields:
            if var is message.ENTITY:
                self.assertEqual(message.ENTITY_SLIVER_TOOL, 
                                 sliver_tool_registration_message.__dict__[var])
            else:
                self.assertIsNone(
                    sliver_tool_registration_message.__dict__[var])

    def testInitializeFromDictionaryValid(self):
        sliver_tool_registration_message = \
            registration_message.SliverToolRegistrationMessage()
        
        # Without timestamp.
        input_dictionary = {}
        for message_field in sliver_tool_registration_message.required_fields:
            input_dictionary[message_field] = message_field
        sliver_tool_registration_message.initialize_from_dictionary(
            input_dictionary)
        for message_field in sliver_tool_registration_message.required_fields:
	    self.assertEqual(
                input_dictionary[message_field],
	        sliver_tool_registration_message.__dict__[message_field]) 
        self.assertIsNone(sliver_tool_registration_message.timestamp)

        # With timestamp.
        input_dictionary[message.TIMESTAMP] = message.TIMESTAMP
        sliver_tool_registration_message.initialize_from_dictionary(
            input_dictionary)  
        self.assertEqual(input_dictionary[message.TIMESTAMP],
                         sliver_tool_registration_message.timestamp) 
      
    def testInitializeFromDictionaryMissingFields(self):
        input_dictionary = {}
        input_dictionary[message.ENTITY] = 'fake_entity'
        sliver_tool_registration_message = \
            registration_message.SliverToolRegistrationMessage()
        self.assertRaises(
            message.FormatError,
            sliver_tool_registration_message.initialize_from_dictionary,
            input_dictionary)

    def testToDictionaryValid(self):
        sliver_tool_registration_message = \
            registration_message.SliverToolRegistrationMessage()
        expected_dictionary = {}
        for message_field in sliver_tool_registration_message.required_fields:
            sliver_tool_registration_message.__dict__[message_field] = \
                 message_field
            expected_dictionary[message_field] = message_field
        expected_dictionary[message.TIMESTAMP] = None
        self.assertDictEqual(
            expected_dictionary,
            sliver_tool_registration_message.to_dictionary()) 


if __name__ == '__main__':
  unittest2.main()
