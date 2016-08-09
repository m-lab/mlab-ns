import unittest2

from mlabns.util import message
from mlabns.util import util


class UtilTestCase(unittest2.TestCase):

    class OutMockup:

        def write(self, msg):
            self.msg = msg

    class ResponseMockup:

        def __init__(self):
            self.out = UtilTestCase.OutMockup()
            self.headers = {}

    class RequestMockup:

        def __init__(self):
            self.response = UtilTestCase.ResponseMockup()
            self.error_code = None

        def error(self, error_code):
            self.error_code = error_code

    def testSendNotFoundJson(self):
        request = UtilTestCase.RequestMockup()
        util.send_not_found(request, output_type=message.FORMAT_JSON)
        self.assertEqual(request.error_code, 404)
        self.assertEqual(request.response.headers['Content-Type'],
                         'application/json')
        self.assertEqual(request.response.out.msg,
                         '{"status_code": "404 Not found"}')

    def testSendNotFoundNoJson(self):
        request = UtilTestCase.RequestMockup()
        util.send_not_found(request, output_type=message.FORMAT_HTML)
        self.assertEqual(request.error_code, 404)
        util.send_not_found(request, output_type='not_suppored_format')
        self.assertEqual(request.error_code, 404)

    def testSendServerErrorJson(self):
        request = UtilTestCase.RequestMockup()
        util.send_server_error(request, output_type=message.FORMAT_JSON)
        self.assertEqual(request.error_code, 500)
        self.assertEqual(request.response.headers['Content-Type'],
                         'application/json')
        self.assertEqual(request.response.out.msg,
                         '{"status_code": "500 Internal Server Error"}')

    def testSendServerErrorNoJson(self):
        request = UtilTestCase.RequestMockup()
        util.send_server_error(request, output_type=message.FORMAT_HTML)
        self.assertEqual(request.error_code, 500)
        util.send_server_error(request, output_type='not_suppored_format')
        self.assertEqual(request.error_code, 500)

    def testSendSuccessJson(self):
        request = UtilTestCase.RequestMockup()
        util.send_success(request, output_type=message.FORMAT_JSON)
        self.assertEqual(request.error_code, None)
        self.assertEqual(request.response.headers['Content-Type'],
                         'application/json')
        self.assertEqual(request.response.out.msg, '{"status_code": "200 OK"}')

    def testSendSuccessNoJson(self):
        request = UtilTestCase.RequestMockup()
        util.send_success(request, output_type=message.FORMAT_HTML)
        self.assertEqual(request.error_code, None)
        self.assertEqual(request.response.out.msg, '<html> Success! </html>')
        util.send_success(request, output_type='not_suppored_format')
        self.assertEqual(request.error_code, None)
        self.assertEqual(request.response.out.msg, '<html> Success! </html>')


if __name__ == '__main__':
    unittest2.main()
