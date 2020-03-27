import mock
import os
import unittest

from mlabns.util import production_check as pc


class CheckProductionTestCase(unittest.TestCase):

    def setUp(self):
        # Initialize the SITE_REGEX  and MACHINE_REGEX env variable.
        environ_patch = mock.patch.dict('os.environ', {
            'MACHINE_REGEX': '',
            'SITE_REGEX': '',
        })
        self.addCleanup(environ_patch.stop)
        environ_patch.start()

    def testIsProductionSite(self):
        # Production checks
        os.environ['SITE_REGEX'] = '^[a-z]{3}[0-9c]{2}$'

        self.assertTrue(pc.is_production_site('nuq01'))
        self.assertTrue(pc.is_production_site('nuq99'))
        self.assertTrue(pc.is_production_site('tun05'))
        self.assertTrue(pc.is_production_site('lax0c'))
        self.assertTrue(
            pc.is_production_site('TUN05'),
            ('production style site names are considered production even when '
             'uppercase'))

        self.assertFalse(pc.is_production_site(''))
        self.assertFalse(pc.is_production_site('foo'))
        self.assertFalse(
            pc.is_production_site('lga123'),
            'Sites with too many numbers are not production sites.')
        self.assertFalse(
            pc.is_production_site('lga0t'),
            'Sites with a t suffix are not production sites.')

        # Sandbox checks
        os.environ['SITE_REGEX'] = '^[a-z]{3}[0-9]t$'

        self.assertTrue(
            pc.is_production_site('lga0t'),
            'Sites with a t suffix _are_ production in mlab-sandbox project.')

    def testIsProductionSlice(self):
        # Production checks
        os.environ['MACHINE_REGEX'] = '^mlab[1-3]$'
        os.environ['SITE_REGEX'] = '^[a-z]{3}[0-9c]{2}$'

        self.assertTrue(pc.is_production_slice(
            'ndt.iupui.mlab3.mad01.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            'neubot.mlab.mlab1.dfw0c.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            'wehe.mlab.mlab1.dfw02.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            'ndt-iupui-mlab1-dfw03.mlab-oti.measurement-lab.org'))

        self.assertFalse(
            pc.is_production_slice('ndt.iupui.mlab4.prg01.measurement-lab.org'),
            'mlab4 servers are not production slices')
        self.assertFalse(
            pc.is_production_slice('ndt.mlab.mlab1.ams0t.measurement-lab.org'),
            'sites with t suffix do not have production slices')
        self.assertFalse(
            pc.is_production_slice(
                'ndt-iupui-mlab4-prg01.mlab-staging.measurement-lab.org'),
            'mlab4 servers are not production slices')

        # Staging checks
        os.environ['MACHINE_REGEX'] = '^mlab4$'
        os.environ['SITE_REGEX'] = '^[a-z]{3}[0-9c]{2}$'

        self.assertTrue(pc.is_production_slice(
            'ndt.iupui.mlab4.mad01.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            'neubot.mlab.mlab4.dfw0c.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            'wehe-mlab4-dfw02.mlab-staging.measurement-lab.org'))

        self.assertFalse(
            pc.is_production_slice('ndt.iupui.mlab3.prg01.measurement-lab.org'),
            'mlab3 servers are not staging slices')
        self.assertFalse(
            pc.is_production_slice('ndt.mlab.mlab4.ams0t.measurement-lab.org'),
            'sites with t suffix do not have staging slices')

        # Sandbox checks
        os.environ['MACHINE_REGEX'] = '^mlab[1-4]$'
        os.environ['SITE_REGEX'] = '^[a-z]{3}[0-9]t$'

        self.assertTrue(pc.is_production_slice(
            'ndt.iupui.mlab4.mad0t.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            'neubot.mlab.mlab1.dfw0t.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            'wehe-mlab4-dfw0t.mlab-staging.measurement-lab.org'))

        self.assertFalse(
            pc.is_production_slice('ndt.iupui.mlab3.prg01.measurement-lab.org'),
            'Sites not ending in t are not "production" sandbox sites')

        # Malformed host names. Project doesn't matter.
        self.assertFalse(
            pc.is_production_slice(
                'wehe-mlab4-prg01.mlab-otimeasurement-lab.org'),
            'Missing dot between project and domain')
        self.assertFalse(pc.is_production_slice('www.measurementlab.net'))
        self.assertFalse(pc.is_production_slice('www.measurement-lab.org'))
        self.assertFalse(pc.is_production_slice(''))
        self.assertFalse(pc.is_production_slice('.'))
