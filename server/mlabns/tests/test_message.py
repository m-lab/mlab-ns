import unittest2

from mlabns.util import message

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

    def testComputeSignatureNoneKey(self):
        msg = message.Message()
        self.assertRaises(ValueError, msg.compute_signature, None)

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
