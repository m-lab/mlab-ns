import unittest

from mlabns.util import parse_fqdn


class ParseFqdnTest(unittest.TestCase):

    def testValidV1ExperimentFqdnWithOrg(self):
        """A valid v1 experiment FQDN, with org."""
        fqdn = 'ndt.iupui.mlab4.lga06.measurement-lab.org'
        expected = {
            'experiment': 'ndt',
            'org': 'iupui',
            'machine': 'mlab4',
            'site': 'lga06',
            'project': None,
            'domain': 'measurement-lab.org',
        }
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)

    def testValidV1ExperimentFqdnWithoutOrg(self):
        """A valid v1 experiment FQDN, without org."""
        fqdn = 'wehe.mlab4.lga06.measurement-lab.org'
        expected = {
            'experiment': 'wehe',
            'org': None,
            'machine': 'mlab4',
            'site': 'lga06',
            'project': None,
            'domain': 'measurement-lab.org',
        }
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)

    def testValidV2ExperimentFqdnWithOrg(self):
        """A valid v2 experiment FQDN, with org."""
        fqdn = 'ndt-iupui-mlab4-lga06.mlab-staging.measurement-lab.org'
        expected = {
            'experiment': 'ndt',
            'org': 'iupui',
            'machine': 'mlab4',
            'site': 'lga06',
            'project': 'mlab-staging',
            'domain': 'measurement-lab.org',
        }
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)

    def testValidV1MachineFqdn(self):
        """A valid v1 machine FQDN."""
        fqdn = 'mlab2.abc03.measurement-lab.org'
        expected = {
            'experiment': None,
            'org': None,
            'machine': 'mlab2',
            'site': 'abc03',
            'project': None,
            'domain': 'measurement-lab.org',
        }
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)

    def testValidV2MachineFqdn(self):
        """A valid v2 machine FQDN."""
        fqdn = 'mlab3-xyz03.measurement-lab.org'
        expected = {
            'experiment': None,
            'org': None,
            'machine': 'mlab3',
            'site': 'xyz03',
            'project': None,
            'domain': 'measurement-lab.org',
        }
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)

    def testInvalidV1ExperimentFqdnTooManyParts(self):
        """A invalid v1 experiment FQDN with too many experiment-org parts"""
        fqdn = 'ndt.iupui.extra.mlab1.den05.measurement-lab.org'
        expected = {}
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)

    def testInvalidV2ExperimentFqdnTooManyParts(self):
        """A invalid v2 experiment FQDN with too many experiment-org parts"""
        fqdn = 'ndt-iupui-extra-mlab1-den05.mlab-oti.measurement-lab.org'
        expected = {}
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)

    def testInvalidV1ExperimentFqdnBadMachineName(self):
        """A invalid v1 experiment FQDN with invalid machine name."""
        fqdn = 'wehe.machine.den05.measurement-lab.org'
        expected = {}
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)

    def testInvalidV2ExperimentFqdnBadMachineName(self):
        """A invalid v2 experiment FQDN with invalid machine name."""
        fqdn = 'wehe-machine-den05.mlab-oti.measurement-lab.org'
        expected = {}
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)

    def testEmptyInput(self):
        """Invalid empty string input."""
        fqdn = ''
        expected = {}
        actual = parse_fqdn.parse(fqdn)
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
