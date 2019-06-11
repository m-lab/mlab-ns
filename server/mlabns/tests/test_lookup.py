import mock
import unittest2
import urllib2

from mlabns.db import model
from mlabns.handlers import lookup
from mlabns.util import constants
from mlabns.util import reverse_proxy

from google.appengine.ext import testbed


class LookupTest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    class OutMockup:

        def __init__(self):
            self.msg = ''

        def write(self, msg):
            self.msg = msg

    class ResponseMockup:

        def __init__(self):
            self.out = LookupTest.OutMockup()
            self.headers = {}

        def set_status(self, code):
            self.code = code

        def clear(self):
            pass

    class RequestMockup:

        def __init__(self, url='', path='', qs=''):
            self.response = mock.Mock()
            self.error_code = None
            self.url = url
            self.scheme = url[:url.index(':')]
            self.path = path
            self.path_qs = path + ('?' + qs if qs else '')
            self.uri = url
            self.remote_addr = '127.0.0.1'
            self.headers = {'X-AppEngine-CityLatLong': '30,120',}

        def get(self, key, default_value=''):
            return getattr(self, key, default_value)

        def error(self, error_code):
            self.error_code = error_code

    class Info:

        def __init__(self, headers):
            self.headers = headers

        def getheader(self, header):
            return self.headers[header.lower()]

    class URLLibResponseMockup:

        def __init__(self, data, headers):
            self.content = data
            self.headers = headers

        def info(self):
            return LookupTest.Info(self.headers)

        def read(self):
            return self.content

    @mock.patch.object(urllib2, 'urlopen')
    @mock.patch.object(reverse_proxy, 'try_reverse_proxy_url')
    def test_get_with_reverse_proxy(self, mock_try_reverse_proxy_url,
                                    mock_urlopen):
        mock_try_reverse_proxy_url.return_value = (
            'https://new-mlab-ns.appspot.com')
        h = lookup.LookupHandler()
        h.request = LookupTest.RequestMockup(url='https://mlab-ns.appspot.com',
                                             path='/ndt_ssl?policy=geo_options')
        h.response = LookupTest.ResponseMockup()
        mock_urlopen.return_value = LookupTest.URLLibResponseMockup(
            'any-fake-data', {'content-type': 'application/json'})

        h.get()

        # Check response headers, and fake content.
        self.assertEqual(h.response.out.msg, 'any-fake-data')
        self.assertEqual(h.response.headers['Content-Type'], 'application/json')

    @mock.patch.object(reverse_proxy, 'try_reverse_proxy_url')
    def test_get_with_no_content(self, mock_try_reverse_proxy_url):
        tool_a = model.Tool(tool_id='tool_a')
        tool_b = model.Tool(tool_id='tool_b')
        tool_a.put()
        tool_b.put()
        # Skip reverse proxy.
        mock_try_reverse_proxy_url.return_value = ''

        sliver_a = model.SliverTool(
            tool_id='tool_a',
            status='online',
            site_id='foo01',
            slice_id='tool_a',
            fqdn='a.tool.mlab1.foo01.measurement-lab.org',
            sliver_ipv4='192.168.1.2')
        sliver_a.put()

        h = lookup.LookupHandler()
        h.request = LookupTest.RequestMockup(url='https://mlab-ns.appspot.com',
                                             path='/tool_a',
                                             qs='policy=geo_options')
        h.response = LookupTest.ResponseMockup()

        h.get()

        self.assertEqual(h.response.out.msg, '')

    @mock.patch.object(reverse_proxy, 'try_reverse_proxy_url')
    def test_get_with_not_found(self, mock_try_reverse_proxy_url):
        # Skip reverse proxy.
        mock_try_reverse_proxy_url.return_value = ''

        h = lookup.LookupHandler()
        h.request = LookupTest.RequestMockup(url='https://mlab-ns.appspot.com',
                                             path='/FAKE_TOOL_ID',
                                             qs='policy=geo_options')
        h.response = LookupTest.ResponseMockup()

        h.get()

        self.assertEqual(h.response.out.msg, '{"status_code": "404 Not found"}')

    def test_log_location(self):
        h = lookup.LookupHandler()
        h.request = LookupTest.RequestMockup(url='https://mlab-ns.appspot.com',
                                             path='/ndt_ssl')
        h.response = LookupTest.ResponseMockup()
        query = mock.Mock()
        query.tool_id = 'ndt_ssl'
        # Place lat/lon at known distances apart and from server.
        query._gae_latitude, query._gae_longitude = (0.0, 1.0)
        query._maxmind_latitude, query._maxmind_longitude = (0.0, 2.0)
        query._geolocation_type = constants.GEOLOCATION_APP_ENGINE
        sliver_tools = [model.SliverTool(tool_id='ndt_ssl',
                                         site_id='foo01',
                                         country='US',
                                         city='New_York',
                                         latitude=0.0,
                                         longitude=0.0)]

        h.log_location(query, sliver_tools)


if __name__ == '__main__':
    unittest2.main()
