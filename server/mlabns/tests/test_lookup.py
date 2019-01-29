import mock
import unittest2

from mlabns.handlers import lookup
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
            self.path = path
            self.path_qs = path
            self.uri = url

        def error(self, error_code):
            self.error_code = error_code

    @mock.patch.object(redirect, 'try_redirect_url')
    def test_get_with_redirect(self, mock_try_redirect_url):
        mock_try_redirect_url.return_value = 'https://new-mlab-ns.appspot.com'
        h = lookup.LookupHandler()
        h.request = LookupTest.RequestMockup(url='https://mlab-ns.appspot.com',
                                             path='/ndt_ssl')
        h.response = LookupTest.ResponseMockup()

        h.get()

        self.assertEqual(h.response.code, 302)


if __name__ == '__main__':
    unittest2.main()
