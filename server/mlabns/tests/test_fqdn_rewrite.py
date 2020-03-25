import mock
import unittest

from google.appengine.api import app_identity
from mlabns.util import fqdn_rewrite
from mlabns.util import message


class FqdnRewriteTest(unittest.TestCase):

    def setUp(self):
        get_application_id_patch = mock.patch.object(app_identity,
                                                     'get_application_id',
                                                     autospec=True)
        self.addCleanup(get_application_id_patch.stop)
        get_application_id_patch.start()

    def testAfAgnosticNdtPlaintextFqdn(self):
        """When there is no AF and tool is not NDT-SSL, don't rewrite."""
        app_identity.get_application_id.return_value = 'mlab-oti'
        fqdn = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        self.assertEqual(fqdn, fqdn_rewrite.rewrite(fqdn, None, 'ndt'))

    def testIPv4NdtPlaintextFqdn(self):
        """Add a v4 annotation for v4-specific requests."""
        app_identity.get_application_id.return_value = 'mlab-oti'
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt.iupui.mlab1v4.lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original,
                                           message.ADDRESS_FAMILY_IPv4, 'ndt')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv6NdtPlaintextFqdn(self):
        """Add a v6 annotation for v6-specific requests."""
        app_identity.get_application_id.return_value = 'mlab-oti'
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt.iupui.mlab1v6.lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original,
                                           message.ADDRESS_FAMILY_IPv6, 'ndt')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testAfAgnosticNdtSslFqdn(self):
        """Convert dots to dashes, but omit AF annotation for NDT-SSL."""
        app_identity.get_application_id.return_value = 'mlab-oti'
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original, None, 'ndt_ssl')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv4NdtSslFqdn(self):
        """Add a v4 annotation and rewrite dots to dashes for NDT-SSL."""
        app_identity.get_application_id.return_value = 'mlab-oti'
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1v4-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(
            fqdn_original, message.ADDRESS_FAMILY_IPv4, 'ndt_ssl')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv6NdtSslFqdn(self):
        """Add a v6 annotation and rewrite dots to dashes for NDT-SSL."""
        app_identity.get_application_id.return_value = 'mlab-oti'
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1v6-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(
            fqdn_original, message.ADDRESS_FAMILY_IPv6, 'ndt_ssl')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv6NdtSslFqdnFlat(self):
        """Add a v6 annotation, but don't flatten."""
        app_identity.get_application_id.return_value = 'mlab-sandbox'
        fqdn_original = 'ndt-iupui-mlab1-lga06.mlab-oti.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1v6-lga06.mlab-oti.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(
            fqdn_original, message.ADDRESS_FAMILY_IPv6, 'ndt_ssl')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testAfAgnosticNdt7Fqdn(self):
        """Convert dots to dashes, but omit AF annotation for ndt7."""
        app_identity.get_application_id.return_value = 'mlab-oti'
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original, None, 'ndt7')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv4Ndt7Fqdn(self):
        """Add a v4 annotation and rewrite dots to dashes for ndt7."""
        app_identity.get_application_id.return_value = 'mlab-oti'
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1v4-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original,
                                           message.ADDRESS_FAMILY_IPv4, 'ndt7')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv6Ndt7Fqdn(self):
        """Add a v6 annotation and rewrite dots to dashes for ndt7."""
        app_identity.get_application_id.return_value = 'mlab-oti'
        fqdn_original = 'ndt.iupui.mlab1.lga06.measurement-lab.org'
        fqdn_expected = 'ndt-iupui-mlab1v6-lga06.measurement-lab.org'
        fqdn_actual = fqdn_rewrite.rewrite(fqdn_original,
                                           message.ADDRESS_FAMILY_IPv6, 'ndt7')
        self.assertEqual(fqdn_expected, fqdn_actual)

    def testIPv4FlatName(self):
        """Do nothing since this name is already flattened."""
        app_identity.get_application_id.return_value = 'mlab-sandbox'
        fqdn = 'ndt-iupui-mlab1-lga0t.mlab-sandbox.measurement-lab.org'
        self.assertEqual(fqdn, fqdn_rewrite.rewrite(fqdn, None, 'ndt'))


if __name__ == '__main__':
    unittest.main()
