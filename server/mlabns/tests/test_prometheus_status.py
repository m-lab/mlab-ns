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
        self.prometheus_base_url = 'https://prometheus.mlab-oti.measurementlab.net/api/v1/query?query='

    def test_get_slice_info_returns_none_with_nonexistent_tool(self):
        retrieved = prometheus_status.get_slice_info(self.prometheus_base_url,
                                                     'lol', '')
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
        slice_data = {
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

        for tool_id in ['ndt', 'neubot']:
            for address_family in ['', '_ipv6']:
                retrieved = prometheus_status.get_slice_info(
                    self.prometheus_base_url, tool_id, address_family)
                expected = slice_data[tool_id]['info' + address_family]

                self.assertEqual(expected, retrieved)


class StatusUpdateHandlerTest(unittest2.TestCase):

    def setUp(self):
        self.status_update_handler = update.StatusUpdateHandler()
        self.mock_urlopen_response = mock.Mock()
        self.opener = urllib2.OpenerDirector()

        urlopen_patch = mock.patch.object(
            prometheus_status.urllib2.OpenerDirector,
            'open',
            return_value=self.mock_urlopen_response,
            autospec=True)
        self.addCleanup(urlopen_patch.stop)
        urlopen_patch.start()

        parse_sliver_tool_status_patch = mock.patch.object(
            prometheus_status,
            'parse_sliver_tool_status',
            autospec=True)
        self.addCleanup(parse_sliver_tool_status_patch.stop)
        parse_sliver_tool_status_patch.start()

    def test_get_slice_status_returns_none_with_invalid_json(self):
        self.mock_urlopen_response.read.return_value = '{lol, not valid json'
        result = prometheus_status.get_slice_status(
            'prometheus.measurementlab.mock.net', self.opener)
        self.assertIsNone(result)

    def test_get_slice_status_returns_populated_dictionary_when_it_gets_valid_statuses(
            self):
        self.mock_urlopen_response.read.return_value = """
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
        prometheus_status.parse_sliver_tool_status.side_effect = [
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
            'prometheus.measurementlab.mock.net', self.opener)
        prometheus_status.urllib2.OpenerDirector.open.assert_called_once_with(
            self.opener, 'prometheus.measurementlab.mock.net')
        self.assertDictEqual(actual_status, expected_status)

    def test_get_slice_status_returns_none_when_a_HTTPError_is_raised_by_urlopen(
            self):

        class MockHttpError(urllib2.HTTPError):

            def __init__(self, cause):
                self.cause = cause

        self.mock_urlopen_response.read.side_effect = MockHttpError(
            'mock http error')
        self.assertIsNone(prometheus_status.get_slice_status(
            'prometheus.measurementlab.mock.net', self.opener))


if __name__ == '__main__':
    unittest2.main()
