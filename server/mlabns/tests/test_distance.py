import unittest2

from mlabns.util import distance


class DistanceTestCase(unittest2.TestCase):

    def testValidSmallDistance(self):
        dist = distance.distance(0, 0, 10, 10)
        self.assertEqual(1568.5205567985761, dist)

    def testValidLargeDistance(self):
        dist = distance.distance(20, 20, 100, 100)
        self.assertEqual(8009.5721050828461, dist)

    def testInvalidInputs(self):
        import math
        from numbers import Number
        dist = 0
        try:
            dist = distance.distance(-700, 1000, 999, -5454)
        except Exception:
            self.fail("distance threw an exception on invalid entry")
        self.assertTrue(isinstance(dist, Number))
        self.assertFalse(math.isnan(dist))


if __name__ == '__main__':
    unittest2.main()
