import unittest

from mlabns.util import production_check as pc


class CheckProductionTestCase(unittest.TestCase):

    def testIsProductionSite(self):
        self.assertTrue(pc.is_production_site('nuq01'))
        self.assertTrue(pc.is_production_site('nuq99'))
        self.assertTrue(pc.is_production_site('tun05'))
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
            pc.is_production_site('lga01t'),
            'Sites with a t suffix are not production sites.')

    def testIsProductionSlice(self):
        self.assertTrue(pc.is_production_slice(
            'ndt.iupui.mlab3.mad01.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            '1.michigan.mlab1.hnd01.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            'npad.iupui.mlab1.dfw05.measurement-lab.org'))
        self.assertTrue(pc.is_production_slice(
            'ooni.mlab.mlab1.ams02.measurement-lab.org'))

        self.assertFalse(pc.is_production_slice(
            'ndt.iupui.mlab4.prg01.measurement-lab.org'),
            'mlab4 servers are not production slices')
        self.assertFalse(pc.is_production_slice(
            'ooni.mlab.mlab1.ams02t.measurement-lab.org'),
            'sites with t suffix do not have production slices')
        self.assertFalse(pc.is_production_slice('www.measurementlab.net'))
        self.assertFalse(pc.is_production_slice('www.measurement-lab.org'))
        self.assertFalse(pc.is_production_slice(''))
        self.assertFalse(pc.is_production_slice('.'))
