import mock
import unittest2
import urllib2

from mlabns.db import model
from mlabns.handlers import lookup
from mlabns.util import constants
from mlabns.util import redirect


class LookupTest(unittest2.TestCase):

    class OutMockup:

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

        def __init__(self, url='', path=''):
            self.response = mock.Mock()
            self.error_code = None
            self.url = url
            self.scheme = url[:url.index(':')]
            self.path = path
            self.path_qs = path
            self.uri = url

        def error(self, error_code):
            self.error_code = error_code

    class Info:

        def __init__(self, headers):
            self.headers = headers

    class URLLibResponseMockup:

        def __init__(self, data, headers):
            self.content = data
            self.headers = headers

        def info(self):
            return LookupTest.Info(self.headers)

        def read(self):
            return self.content

    @mock.patch.object(urllib2, 'urlopen')
    @mock.patch.object(redirect, 'try_redirect_url')
    def test_get_with_redirect(self, mock_try_redirect_url, mock_urlopen):
        mock_try_redirect_url.return_value = 'https://new-mlab-ns.appspot.com'
        h = lookup.LookupHandler()
        h.request = LookupTest.RequestMockup(url='https://mlab-ns.appspot.com',
                                             path='/ndt_ssl')
        h.response = LookupTest.ResponseMockup()
        mock_urlopen.return_value = LookupTest.URLLibResponseMockup(
            'any-fake-data',
            {'content-type': 'application/json'})

        h.get()

        # Check response headers, and fake content.
        self.assertEqual(h.response.out.msg, 'any-fake-data')
        self.assertEqual(h.response.headers['Content-Type'], 'application/json')

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
