import unittest2

from mlabns.db import model
from mlabns.util import reverse_proxy

from google.appengine.ext import testbed


class ReverseProxyTest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_all_stubs()

        self.fake_reverse_proxy = model.ReverseProxyProbability(
            name="default",
            probability=0.0,
            url="https://mlab-ns.appspot.com")
        reverse_proxy._reverse_proxy = None

    def tearDown(self):
        self.testbed.deactivate()

    # @mock.patch.object(model, 'ReverseProxyProbability')
    # def test_get_reverse_proxy_returns_mock_value(self, mock_reverse_proxy):
    #     mock_reverse_proxy.return_value.get_by_key_name.return_value = self.fake_reverse_proxy
    #     actual = reverse_proxy.get_reverse_proxy('default')

    #     self.assertEqual(actual.name, self.fake_reverse_proxy.name)
    #     self.assertEqual(actual.probability,
    #                      self.fake_reverse_proxy.probability)
    #     self.assertEqual(actual.url, self.fake_reverse_proxy.url)

    # @mock.patch.object(model, 'ReverseProxyProbability')
    # def test_get_reverse_proxy_returns_default_value(self, mock_reverse_proxy):
    #     mock_reverse_proxy.return_value.get_by_key_name.return_value = None
    #     actual = reverse_proxy.get_reverse_proxy('default')

    #     self.assertEqual(actual, reverse_proxy.default_reverse_proxy)
    #     self.assertEqual(actual.name, reverse_proxy.default_reverse_proxy.name)
    #     self.assertEqual(actual.probability,
    #                      reverse_proxy.default_reverse_proxy.probability)
    #     self.assertEqual(actual.url, reverse_proxy.default_reverse_proxy.url)

    # def test_during_business_hours_returns_true(self):
    #     t = datetime.datetime(2019, 1, 24, 16, 0, 0)
    #     self.assertTrue(reverse_proxy.during_business_hours(t))

    # def test_during_business_hours_with_ignore_environment_returns_true(self):
    #     t = datetime.datetime(2019, 1, 25, 16, 0, 0)
    #     os.environ['IGNORE_BUSINESS_HOURS'] = '1'
    #     self.assertTrue(reverse_proxy.during_business_hours(t))
    #     del os.environ['IGNORE_BUSINESS_HOURS']

    # def test_during_business_hours_returns_false(self):
    #     t = datetime.datetime(2019, 1, 25, 16, 0, 0)
    #     self.assertFalse(reverse_proxy.during_business_hours(t))

    # def test_try_reverse_proxy_url_when_wrong_path_returns_emptystr(self):
    #     mock_request = mock.Mock()
    #     mock_request.path = '/wrong_path'
    #     t = datetime.datetime(2019, 1, 24, 16, 0, 0)

    #     url = reverse_proxy.try_reverse_proxy_url(mock_request, t)

    #     self.assertEqual(url, "")

    # def test_try_reverse_proxy_url_when_probability_zero_returns_emptystr(self):
    #     mock_request = mock.Mock()
    #     mock_request.path = '/ndt_ssl'
    #     t = datetime.datetime(2019, 1, 24, 16, 0, 0)
    #     rp = model.ReverseProxyProbability(name="default",
    #                                        probability=0.0,
    #                                        url="https://fake.appspot.com")
    #     memcache.set('default',
    #                  rp,
    #                  time=1800,
    #                  namespace=constants.MEMCACHE_NAMESPACE_REVERSE_PROXY)

    #     url = reverse_proxy.try_reverse_proxy_url(mock_request, t)

    #     self.assertEqual(url, "")

    # def test_try_reverse_proxy_url_when_outside_business_returns_emptystr(self):
    #     mock_request = mock.Mock()
    #     mock_request.path = '/ndt_ssl'
    #     t = datetime.datetime(2019, 1, 25, 16, 0, 0)
    #     rp = model.ReverseProxyProbability(name="default",
    #                                        probability=1.0,
    #                                        url="https://fake.appspot.com")
    #     memcache.set('default',
    #                  rp,
    #                  time=1800,
    #                  namespace=constants.MEMCACHE_NAMESPACE_REVERSE_PROXY)

    #     url = reverse_proxy.try_reverse_proxy_url(mock_request, t)

    #     self.assertEqual(url, "")

    # def test_try_reverse_proxy_url_returns_url(self):
    #     mock_request = mock.Mock()
    #     mock_request.path = '/ndt_ssl'
    #     mock_request.path_qs = '/ndt_ssl?format=geo_options'
    #     t = datetime.datetime(2019, 1, 24, 16, 0, 0)
    #     rp = model.ReverseProxyProbability(name="default",
    #                                        probability=1.0,
    #                                        url="https://fake.appspot.com")
    #     memcache.set('default',
    #                  rp,
    #                  time=1800,
    #                  namespace=constants.MEMCACHE_NAMESPACE_REVERSE_PROXY)

    #     actual_url = reverse_proxy.try_reverse_proxy_url(mock_request, t)

    #     self.assertEqual(actual_url,
    #                      'https://fake.appspot.com/ndt_ssl?format=geo_options')
