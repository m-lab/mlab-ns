import unittest

from mlabns.util import fqdn_rewrite
from mlabns.util import message


class FqdnRewriteTest(unittest.TestCase):

    def testAfAgnosticNdtPlaintextFqdn(self):
        """When there is no AF and tool is not NDT-SSL, don't rewrite."""
        fqdn = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        self.assertEqual(fqdn, fqdn_rewrite.rewrite(fqdn, None, 'ndt'))

    def testIPv4NdtPlaintextFqdn(self):
        """Add a v4 annotation for v4-specific requests."""
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt.iupui.mlab1v4.lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original,
                                           message.ADDRESS_FAMILY_IPv4, 'ndt')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv6NdtPlaintextFqdn(self):
        """Add a v6 annotation for v6-specific requests."""
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt.iupui.mlab1v6.lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original,
                                           message.ADDRESS_FAMILY_IPv6, 'ndt')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testAfAgnosticNdtSslFqdn(self):
        """Convert dots to dashes, but omit AF annotation for NDT-SSL."""
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original, None, 'ndt_ssl')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv4NdtSslFqdn(self):
        """Add a v4 annotation and rewrite dots to dashes for NDT-SSL."""
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1v4-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(
            fqdn_original, message.ADDRESS_FAMILY_IPv4, 'ndt_ssl')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv6NdtSslFqdn(self):
        """Add a v6 annotation and rewrite dots to dashes for NDT-SSL."""
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1v6-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(
            fqdn_original, message.ADDRESS_FAMILY_IPv6, 'ndt_ssl')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testAfAgnosticNdt7Fqdn(self):
        """Convert dots to dashes, but omit AF annotation for ndt7."""
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original, None, 'ndt7')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv4Ndt7Fqdn(self):
        """Add a v4 annotation and rewrite dots to dashes for ndt7."""
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1v4-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original,
                                           message.ADDRESS_FAMILY_IPv4, 'ndt7')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv6Ndt7Fqdn(self):
        """Add a v6 annotation and rewrite dots to dashes for ndt7."""
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1v6-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original,
                                           message.ADDRESS_FAMILY_IPv6, 'ndt7')
        self.assertEqual(fqdn_expected, fqdn_actual)


if __name__ == '__main__':
    unittest.main()
