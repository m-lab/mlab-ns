import unittest2

from mlabns.util import maxmind

class MaxmindTestCase(unittest2.TestCase):

    def testValidIPv4ToLong(self):
        ip_num = maxmind.ipv4_to_long('193.39.24.56')
        self.assertEqual(3240564792, ip_num)

    def testValidIPv6ToLong(self):
        ip_num = maxmind.ipv6_to_long('2620:0:10c9:1001:a800:ff:fe12:46a9')
        self.assertEqual(2747195772977614849, ip_num >> 64)

if __name__ == '__main__':
    unittest2.main()
