import datetime
import os
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
        # default probability.
        actual = reverse_proxy.get_reverse_proxy('default')

        self.assertEqual(actual.name, reverse_proxy.default_reverse_proxy.name)
        self.assertEqual(actual.probability,
                         reverse_proxy.default_reverse_proxy.probability)
        self.assertEqual(actual.url, reverse_proxy.default_reverse_proxy.url)

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

    def test_during_business_hours_returns_true(self):
        t = datetime.datetime(2019, 1, 24, 16, 0, 0)
        self.assertTrue(reverse_proxy.during_business_hours(t))

    def test_during_business_hours_with_ignore_environment_returns_true(self):
        t = datetime.datetime(2019, 1, 25, 16, 0, 0)
        os.environ['IGNORE_BUSINESS_HOURS'] = '1'
        self.assertTrue(reverse_proxy.during_business_hours(t))
        del os.environ['IGNORE_BUSINESS_HOURS']

    def test_during_business_hours_returns_false(self):
        t = datetime.datetime(2019, 1, 25, 16, 0, 0)
        self.assertFalse(reverse_proxy.during_business_hours(t))

    def test_try_reverse_proxy_url_when_wrong_path_returns_emptystr(self):
        mock_request = mock.Mock()
        mock_request.path = '/wrong_path'
        t = datetime.datetime(2019, 1, 24, 16, 0, 0)

        url = reverse_proxy.try_reverse_proxy_url(mock_request, t)

        self.assertEqual(url, "")

    def test_try_reverse_proxy_url_when_probability_zero_returns_emptystr(self):
        ndt_zero_probability = model.ReverseProxyProbability(
            name="ndt_ssl",
            probability=0.0,
            url="https://fake.appspot.com")
        ndt_zero_probability.put()
        mock_request = mock.Mock()
        mock_request.path = '/ndt_ssl'
        t = datetime.datetime(2019, 1, 24, 16, 0, 0)

        url = reverse_proxy.try_reverse_proxy_url(mock_request, t)

        self.assertEqual(url, "")

    def test_try_reverse_proxy_url_when_outside_business_returns_emptystr(self):
        ndt_ssl_probability = model.ReverseProxyProbability(
            name="ndt_ssl",
            probability=1.0,
            url="https://fake.appspot.com")
        ndt_ssl_probability.put()
        mock_request = mock.Mock()
        mock_request.path = '/ndt_ssl'
        t = datetime.datetime(2019, 1, 25, 16, 0, 0)

        url = reverse_proxy.try_reverse_proxy_url(mock_request, t)

        self.assertEqual(url, "")

    def test_try_reverse_proxy_url_returns_url(self):
        ndt_ssl_probability = model.ReverseProxyProbability(
            name="ndt_ssl",
            probability=1.0,
            url="https://fake.appspot.com")
        ndt_ssl_probability.put()
        mock_request = mock.Mock()
        mock_request.path = '/ndt_ssl'
        mock_request.path_qs = '/ndt_ssl?format=geo_options'
        t = datetime.datetime(2019, 1, 24, 16, 0, 0)

        actual_url = reverse_proxy.try_reverse_proxy_url(mock_request, t)

        self.assertEqual(actual_url,
                         'https://fake.appspot.com/ndt_ssl?format=geo_options')
