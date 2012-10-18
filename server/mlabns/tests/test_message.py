import time
import unittest2

from mlabns.util import message
from mlabns.util import registration_message

class MessageTestCase(unittest2.TestCase):
    def testAddTimestampValid(self):
        fake_timestamp = 12345
        # Mockup Message class, because add_timestamp calls time().
        # An alternative is to mockup time().
        class MessageMockup(message.Message):
            def add_timestamp(self):
                self.timestamp = fake_timestamp
                
        msg = MessageMockup()
        self.assertIsNone(msg.timestamp)
        msg.add_timestamp()
        self.assertEqual(fake_timestamp, msg.timestamp)

    def testComputeSignatureValid(self):
        # Cannot use directly a message, because Message does not implement
        # to_dictionary() and initialize_from_dictionary()
        msg = registration_message.SiteRegistrationMessage()
        msg_dictionary = {}
        for message_field in msg.required_fields:
            msg_dictionary[message_field] = message_field
        msg.initialize_from_dictionary(msg_dictionary)
        fake_key = 'xyz'
        self.assertEqual('98aVlVuCPxm5Jlg1Jlwla1hdTck=',
                         msg.compute_signature(fake_key))

    def testComputeSignatureNoneKey(self):
        msg = message.Message()
        self.assertRaises(ValueError, msg.compute_signature, None)

    def testEncryptMessageWrongLengthKey(self):
        # Cannot use directly a message, because Message does not implement
        # to_dictionary() and initialize_from_dictionary()
        msg = registration_message.SiteRegistrationMessage()
        msg_dictionary = {}
        for message_field in msg.required_fields:
            msg_dictionary[message_field] = message_field
        msg.initialize_from_dictionary(msg_dictionary)
        fake_key = '12345678'
        self.assertRaises(ValueError, msg.encrypt_message, fake_key)

    def testEncryptMessageValid(self):
        # Cannot use directly a message, because Message does not implement
        # to_dictionary() and initialize_from_dictionary() length
        msg = registration_message.SiteRegistrationMessage()
        msg_dictionary = {}
        for message_field in msg.required_fields:
            msg_dictionary[message_field] = message_field
        msg.initialize_from_dictionary(msg_dictionary)
        fake_key = '1234567812345678'
        
        msg.encrypt_message(fake_key)
        expected_ciphertext = ('Nn3TLN5+83L8pD7TcXAmdjAnddNrzoRspdAaYGsf3b4d3F'
                               '0AgQBYDP4FbZW7uLgmAz0Vq4lVBf01gQwpO0VNCBsi+Ty6U'
                               '2sI6ti5pcv0TMDl+Gh4vTdUGOcmMqrtsbd9jJp5zbzsFOKO'
                               '+i78E3mYjm6Nj/loGUM7dUYvwKC+D01qgNLpBOrP8vzCyPy'
                               'ROjUYSuPl1SlI6qaJwUKDwoW71g==')
        self.assertEqual(expected_ciphertext, msg.ciphertext)
        self.assertEqual('249FD/c17Eb1kocrWutyw+jdRdY=', msg.signature)

    def testEncryptMessageNoneKey(self):
        msg = message.Message()
        self.assertRaises(ValueError, msg.compute_signature, None)

    def testDecryptMessageNoneKey(self):
        msg = message.Message()
        self.assertRaises(ValueError, msg.decrypt_message, {}, None)

    def testDecryptMessageNoSignature(self):
        msg = message.Message()
        self.assertRaises(message.DecryptionError, msg.decrypt_message, {},
                          'unused_key')

    def testDecryptMessageNoCiphertext(self):
        msg = message.Message()
        data = {}
        data[message.SIGNATURE] = 'unused_signature'
        self.assertRaises(message.DecryptionError, msg.decrypt_message,
                          data, 'unused_key')


if __name__ == '__main__':
    unittest2.main()
