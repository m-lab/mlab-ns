import mock
import unittest2

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import reverse_proxy

from google.appengine.api import memcache
from google.appengine.ext import testbed


class ReverseProxyTest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_all_stubs()

        reverse_proxy._reverse_proxy = None

    def tearDown(self):
        self.testbed.deactivate()

    def test_get_reverse_proxy_returns_default_value(self):
        # If the entity does not exist, get_reverse_proxy should return a
        # default probability of 0.0 for the requested experiment name.
        actual = reverse_proxy.get_reverse_proxy('not_valid')

        self.assertEqual(actual.name, 'not_valid')
        self.assertEqual(actual.probability, 0.0)
        self.assertEqual(actual.url, "https://mlab-ns.appspot.com")

    def test_get_reverse_proxy_returns_probability_and_caches(self):
        # If the entity exists, get_reverse_proxy should return it.
        ndt7_probability = model.ReverseProxyProbability(
            name="ndt7",
            probability=1.0,
            url="https://fake.appspot.com")
        ndt_ssl_probability = model.ReverseProxyProbability(
            name="ndt_ssl",
            probability=1.0,
            url="https://fake.appspot.com")
        ndt7_probability.put()
        ndt_ssl_probability.put()

        actual = reverse_proxy.get_reverse_proxy('ndt_ssl')

        self.assertEqual(actual.name, ndt_ssl_probability.name)
        self.assertEqual(actual.probability, ndt_ssl_probability.probability)
        self.assertEqual(actual.url, ndt_ssl_probability.url)

    def test_get_reverse_proxy_caches_entities(self):
        # get_reverse_proxy should refresh memcache at each cache miss.
        ndt7_probability = model.ReverseProxyProbability(
            name="ndt7",
            probability=1.0,
            url="https://fake.appspot.com")
        ndt_ssl_probability = model.ReverseProxyProbability(
            name="ndt_ssl",
            probability=1.0,
            url="https://fake.appspot.com")
        ndt7_probability.put()
        ndt_ssl_probability.put()

        reverse_proxy.get_reverse_proxy("ndt_ssl")

        cached_ndt = memcache.get(
            "ndt_ssl",
            namespace=constants.MEMCACHE_NAMESPACE_REVERSE_PROXY)
        cached_ndt7 = memcache.get(
            "ndt7", namespace=constants.MEMCACHE_NAMESPACE_REVERSE_PROXY)
        self.assertEqual(cached_ndt.name, ndt_ssl_probability.name)
        self.assertEqual(cached_ndt.probability,
                         ndt_ssl_probability.probability)
        self.assertEqual(cached_ndt.url, ndt_ssl_probability.url)

        self.assertEqual(cached_ndt7.name, ndt7_probability.name)
        self.assertEqual(cached_ndt7.probability, ndt7_probability.probability)
        self.assertEqual(cached_ndt7.url, ndt7_probability.url)

    def test_try_reverse_proxy_url_when_wrong_path_returns_emptystr(self):
        mock_request = mock.Mock()
        mock_request.path = '/wrong_path'

        url = reverse_proxy.try_reverse_proxy_url(mock_request)

        self.assertEqual(url, "")

    def test_try_reverse_proxy_url_when_probability_zero_returns_emptystr(self):
        ndt_zero_probability = model.ReverseProxyProbability(
            name="ndt_ssl",
            probability=0.0,
            url="https://fake.appspot.com")
        ndt_zero_probability.put()
        mock_request = mock.Mock()
        mock_request.path = '/ndt_ssl'

        url = reverse_proxy.try_reverse_proxy_url(mock_request)

        self.assertEqual(url, "")

    def test_try_reverse_proxy_url_returns_url_with_latlon(self):
        ndt_ssl_probability = model.ReverseProxyProbability(
            name="ndt_ssl",
            probability=1.0,
            url="https://fake.appspot.com")
        ndt_ssl_probability.put()
        mock_request = mock.Mock()
        mock_request.path = '/ndt_ssl'
        mock_request.path_qs = '/ndt_ssl?format=geo_options'
        mock_request.latitude = 40.7
        mock_request.longitude = 74.0

        actual_url = reverse_proxy.try_reverse_proxy_url(mock_request)

        self.assertEqual(actual_url, (
            'https://fake.appspot.com/ndt_ssl?format=geo_options&lat=40.700000'
            '&lon=74.000000'))

    def test_try_reverse_proxy_url_returns_url_with_only_latlon(self):
        ndt_ssl_probability = model.ReverseProxyProbability(
            name="ndt_ssl",
            probability=1.0,
            url="https://fake.appspot.com")
        ndt_ssl_probability.put()
        mock_request = mock.Mock()
        mock_request.path = '/ndt_ssl'
        mock_request.path_qs = '/ndt_ssl'
        mock_request.latitude = 40.7
        mock_request.longitude = 74.0

        actual_url = reverse_proxy.try_reverse_proxy_url(mock_request)

        self.assertEqual(
            actual_url,
            'https://fake.appspot.com/ndt_ssl?lat=40.700000&lon=74.000000')
