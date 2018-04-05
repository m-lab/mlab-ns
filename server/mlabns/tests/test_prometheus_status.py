import mock
import unittest2
import urllib
import urllib2

from mlabns.handlers import update
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import prometheus_status


class ParseSliverToolStatusTest(unittest2.TestCase):

    def test_parse_sliver_tool_status_returns_successfully_parsed_tuple(self):
        status = {
            "metric": {
                "experiment": "ndt.iupui",
                "machine": "mlab1.abc01.measurement-lab.org"
            },
            "value": [1522782427.81, "1"]
        }
        expected_parsed_status = ('ndt.iupui.mlab1.abc01.measurement-lab.org',
                                  '1', constants.PROMETHEUS_TOOL_EXTRA)
        actual_parsed_status = prometheus_status.parse_sliver_tool_status(
            status)

        self.assertTupleEqual(expected_parsed_status, actual_parsed_status)

    def test_parse_sliver_tool_status_raises_PrometheusStatusUnparseableError_because_of_illformatted_status(
            self):
        status = 'mock status'

        with self.assertRaises(
                prometheus_status.PrometheusStatusUnparseableError):
            prometheus_status.parse_sliver_tool_status(status)


class GetSliceInfoTest(unittest2.TestCase):

    def setUp(self):
        self.prometheus_base_url = 'https://prom.mock.mlab.net/api/?query='

    def test_get_slice_info_returns_none_with_nonexistent_tool(self):
        retrieved = prometheus_status.get_slice_info(self.prometheus_base_url,
                                                     'nonexistent_tool', '')
        self.assertIsNone(retrieved)

    def test_get_slice_info_returns_valid_objects_when_tools_stored(self):
        ndt_url_ipv4 = self.prometheus_base_url + urllib.quote_plus(
            prometheus_status.QUERIES['ndt'])
        ndt_url_ipv6 = self.prometheus_base_url + urllib.quote_plus(
            prometheus_status.QUERIES['ndt_ipv6'])
        neubot_url_ipv4 = self.prometheus_base_url + urllib.quote_plus(
            prometheus_status.QUERIES['neubot'])
        neubot_url_ipv6 = self.prometheus_base_url + urllib.quote_plus(
            prometheus_status.QUERIES['neubot_ipv6'])
        expected_slice_data = {
            'ndt': {
                'info':
                prometheus_status.PrometheusSliceInfo(ndt_url_ipv4, 'ndt', ''),
                'info_ipv6': prometheus_status.PrometheusSliceInfo(
                    ndt_url_ipv6, 'ndt', '_ipv6'),
            },
            'neubot': {
                'info': prometheus_status.PrometheusSliceInfo(neubot_url_ipv4,
                                                              'neubot', ''),
                'info_ipv6': prometheus_status.PrometheusSliceInfo(
                    neubot_url_ipv6, 'neubot', '_ipv6'),
            }
        }

        retrieved = prometheus_status.get_slice_info(self.prometheus_base_url,
                                                     'ndt', '')
        self.assertEqual(expected_slice_data['ndt']['info'], retrieved)

        retrieved = prometheus_status.get_slice_info(self.prometheus_base_url,
                                                     'ndt', '_ipv6')
        self.assertEqual(expected_slice_data['ndt']['info_ipv6'], retrieved)

        retrieved = prometheus_status.get_slice_info(self.prometheus_base_url,
                                                     'neubot', '')
        self.assertEqual(expected_slice_data['neubot']['info'], retrieved)

        retrieved = prometheus_status.get_slice_info(self.prometheus_base_url,
                                                     'neubot', '_ipv6')
        self.assertEqual(expected_slice_data['neubot']['info_ipv6'], retrieved)


class StatusUpdateHandlerTest(unittest2.TestCase):

    def setUp(self):
        self.mock_response = mock.Mock()
        self.mock_response.msg = 'mock message'
        self.mock_response.code = '200'

    @mock.patch.object(urllib2.OpenerDirector, 'open', autospec=True)
    def test_get_slice_status_returns_none_with_invalid_json(self, mock_open):
        self.mock_response.read.return_value = '{lol, not valid json'
        mock_open.return_value = self.mock_response
        result = prometheus_status.get_slice_status(
            'https://prometheus.measurementlab.mock.net',
            urllib2.OpenerDirector())
        self.assertIsNone(result)

    @mock.patch.object(urllib2.OpenerDirector, 'open', autospec=True)
    @mock.patch.object(prometheus_status, 'parse_sliver_tool_status')
    def test_get_slice_status_returns_populated_dictionary_when_it_gets_valid_statuses(
            self, mock_parse_sliver_tool_status, mock_open):
        self.mock_response.read.return_value = """
        {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    { "metric": {
                          "experiment": "mock",
                          "machine": "mlab1.xyz01.measurement-lab.org" },
                      "value": [1522782427.81, "1"]
                    },
                    { "metric": {
                          "experiment": "mock",
                          "machine": "mlab2.xyz01.measurement-lab.org" },
                      "value": [1522773427.51, "0"]
                    }
                ]
            }
        }"""
        mock_open.return_value = self.mock_response

        mock_parse_sliver_tool_status.side_effect = [
            ('mock.mlab1.xyz01.measurement-lab.org', '1',
             constants.PROMETHEUS_TOOL_EXTRA),
            ('mock.mlab2.xyz01.measurement-lab.org', '0',
             constants.PROMETHEUS_TOOL_EXTRA)
        ]

        expected_status = {
            'mock.mlab1.xyz01.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': constants.PROMETHEUS_TOOL_EXTRA
            },
            'mock.mlab2.xyz01.measurement-lab.org': {
                'status': message.STATUS_OFFLINE,
                'tool_extra': constants.PROMETHEUS_TOOL_EXTRA
            }
        }

        actual_status = prometheus_status.get_slice_status(
            'https://prometheus.measurementlab.mock.net',
            urllib2.OpenerDirector())
        self.assertDictEqual(actual_status, expected_status)

    @mock.patch.object(urllib2.OpenerDirector, 'open', autospec=True)
    def test_get_slice_status_returns_none_when_a_HTTPError_is_raised_by_urlopen(
            self, mock_open):

        class MockHttpError(urllib2.HTTPError):

            def __init__(self, cause):
                self.cause = cause

        self.mock_response.read.side_effect = MockHttpError('mock http error')
        mock_open.return_value = self.mock_response
        self.assertIsNone(prometheus_status.get_slice_status(
            'https://prometheus.measurementlab.mock.net',
            urllib2.OpenerDirector()))


if __name__ == '__main__':
    unittest2.main()
