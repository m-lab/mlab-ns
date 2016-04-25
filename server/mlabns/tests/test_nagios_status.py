import mock
import unittest2
import urllib2

from mlabns.db import model
from mlabns.handlers import update
from mlabns.util import message
from mlabns.util import nagios_status


class ParseSliverToolStatusTest(unittest2.TestCase):

    def test_parse_sliver_tool_status_returns_successfully_parsed_tuple(self):
        status = 'ndt.foo.measurement-lab.org/ndt 0 1 mock tool extra'
        expected_parsed_status = ('ndt.foo.measurement-lab.org', '0',
                                  'mock tool extra')
        actual_parsed_status = nagios_status.parse_sliver_tool_status(status)

        self.assertTupleEqual(expected_parsed_status, actual_parsed_status)

    def test_parse_sliver_tool_status_raises_NagiosStatusUnparseableError_because_of_illformatted_status(
            self):
        status = 'mock status'

        with self.assertRaises(nagios_status.NagiosStatusUnparseableError):
            nagios_status.parse_sliver_tool_status(status)

    def test_parse_sliver_tool_status_raises_NagiosStatusUnparseableError_because_empty_status(
            self):
        status = ''

        with self.assertRaises(nagios_status.NagiosStatusUnparseableError):
            nagios_status.parse_sliver_tool_status(status)

    def test_parse_sliver_tool_status_raises_NagiosStatusUnparseableError_because_status_only_whitespace(
            self):
        status = '       '

        with self.assertRaises(nagios_status.NagiosStatusUnparseableError):
            nagios_status.parse_sliver_tool_status(status)

    def test_parse_sliver_tool_status_sliceurl_has_no_forward_slash_returns_successfully(
            self):
        status = 'ndt.foo.measurement-lab.org 0 1 mock tool extra'

        expected_parsed_status = ('ndt.foo.measurement-lab.org', '0',
                                  'mock tool extra')
        actual_parsed_status = nagios_status.parse_sliver_tool_status(status)

        self.assertTupleEqual(expected_parsed_status, actual_parsed_status)

    def test_parse_sliver_tool_status_raises_NagiosStatusUnparseableError_because_status_only_has_2_fields(
            self):
        status = 'ndt.foo.measurement-lab.org 0'

        with self.assertRaises(nagios_status.NagiosStatusUnparseableError):
            nagios_status.parse_sliver_tool_status(status)

    def test_parse_sliver_tool_status_raises_NagiosStatusUnparseableError_because_status_only_has_3_fields(
            self):
        status = 'ndt.foo.measurement-lab.org 0 1'

        with self.assertRaises(nagios_status.NagiosStatusUnparseableError):
            nagios_status.parse_sliver_tool_status(status)

    def test_parse_sliver_tool_status_status_has_leading_whitespace_returns_successfully(
            self):
        status = '  ndt.foo.measurement-lab.org 0 1 mock tool extra'

        expected_parsed_status = ('ndt.foo.measurement-lab.org', '0',
                                  'mock tool extra')
        actual_parsed_status = nagios_status.parse_sliver_tool_status(status)

        self.assertTupleEqual(expected_parsed_status, actual_parsed_status)

    def test_parse_sliver_tool_status_status_has_extra_spaces_between_fields_returns_successfully(
            self):
        status = ' ndt.foo.measurement-lab.org 0  1  mock tool extra'

        expected_parsed_status = ('ndt.foo.measurement-lab.org', '0',
                                  'mock tool extra')
        actual_parsed_status = nagios_status.parse_sliver_tool_status(status)

        self.assertTupleEqual(expected_parsed_status, actual_parsed_status)


class GetSliceInfoTest(unittest2.TestCase):

    def setUp(self):
        self.nagios_base_url = 'http://nagios.mock-mlab.net/baseList'

    def test_get_slice_info_returns_valid_objects_when_tools_stored(self):
        slice_a_url = 'http://nagios.mock-mlab.net/baseList?show_state=1&service_name=mock_tool_a&plugin_output=1'
        slice_a_info = nagios_status.NagiosSliceInfo(slice_a_url, 'mock_tool_a',
                                                     '')
        slice_a_v6_url = 'http://nagios.mock-mlab.net/baseList?show_state=1&service_name=mock_tool_a_ipv6&plugin_output=1'
        slice_a_v6_info = nagios_status.NagiosSliceInfo(slice_a_v6_url,
                                                        'mock_tool_a', '_ipv6')
        slice_b_url = 'http://nagios.mock-mlab.net/baseList?show_state=1&service_name=mock_tool_b&plugin_output=1'
        slice_b_info = nagios_status.NagiosSliceInfo(slice_b_url, 'mock_tool_b',
                                                     '')
        slice_b_v6_url = 'http://nagios.mock-mlab.net/baseList?show_state=1&service_name=mock_tool_b_ipv6&plugin_output=1'
        slice_b_v6_info = nagios_status.NagiosSliceInfo(slice_b_v6_url,
                                                        'mock_tool_b', '_ipv6')
        expected = [slice_a_info, slice_a_v6_info, slice_b_info,
                    slice_b_v6_info]

        with mock.patch.object(model, 'get_all_tool_ids') as get_all_tool_ids:
            get_all_tool_ids.return_value = ['mock_tool_a', 'mock_tool_b']
            retrieved = nagios_status.get_slice_info(self.nagios_base_url)

        self.assertListEqual(expected, retrieved)

    def test_get_slice_info_returns_empty_list_when_no_tools_stored(self):
        with mock.patch.object(model, 'get_all_tool_ids') as get_all_tool_ids:
            get_all_tool_ids.return_value = []
            retrieved = nagios_status.get_slice_info(self.nagios_base_url)
        expected = []
        self.assertListEqual(expected, retrieved)


class StatusUpdateHandlerTest(unittest2.TestCase):

    def setUp(self):
        self.status_update_handler = update.StatusUpdateHandler()
        self.mock_urlopen_response = mock.Mock()

        urlopen_patch = mock.patch.object(
            nagios_status.urllib2,
            'urlopen',
            return_value=self.mock_urlopen_response,
            autospec=True)
        self.addCleanup(urlopen_patch.stop)
        urlopen_patch.start()

        parse_sliver_tool_status_patch = mock.patch.object(
            nagios_status,
            'parse_sliver_tool_status',
            autospec=True)
        self.addCleanup(parse_sliver_tool_status_patch.stop)
        parse_sliver_tool_status_patch.start()

    def test_get_slice_status_returns_populated_dictionary_when_it_gets_valid_statuses(
            self):
        mock_slice_status = """
mock.mlab1.xyz01.measurement-lab.org/ndt 0 1 mock tool extra
mock.mlab2.xyz01.measurement-lab.org/ndt 0 1 mock tool extra
mock.mlab3.xyz01.measurement-lab.org/ndt 2 1 mock tool extra
""".lstrip()

        self.mock_urlopen_response.read.return_value = mock_slice_status
        nagios_status.parse_sliver_tool_status.side_effect = iter([
            ('mock.mlab1.xyz01.measurement-lab.org', '0', 'mock tool extra'), (
                'mock.mlab2.xyz01.measurement-lab.org', '0', 'mock tool extra'
            ), ('mock.mlab3.xyz01.measurement-lab.org', '2', 'mock tool extra')
        ])

        expected_status = {
            'mock.mlab1.xyz01.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab2.xyz01.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab3.xyz01.measurement-lab.org': {
                'status': message.STATUS_OFFLINE,
                'tool_extra': 'mock tool extra'
            }
        }

        actual_status = nagios_status.get_slice_status(
            'nagios.measurementlab.mock.net')
        nagios_status.urllib2.urlopen.assert_called_once_with(
            'nagios.measurementlab.mock.net')
        self.assertDictEqual(actual_status, expected_status)

    def test_get_slice_status_returns_populated_dictionary_when_it_gets_valid_statuses_and_one_whitespace_sliver_status(
            self):
        mock_slice_status = """
mock.mlab1.xyz01.measurement-lab.org/ndt 0 1 mock tool extra
\t\t
mock.mlab3.xyz01.measurement-lab.org/ndt 2 1 mock tool extra
""".lstrip()

        self.mock_urlopen_response.read.return_value = mock_slice_status
        nagios_status.parse_sliver_tool_status.side_effect = iter([
            ('mock.mlab1.xyz01.measurement-lab.org', '0', 'mock tool extra'), (
                'mock.mlab3.xyz01.measurement-lab.org', '2', 'mock tool extra')
        ])

        expected_status = {
            'mock.mlab1.xyz01.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab3.xyz01.measurement-lab.org': {
                'status': message.STATUS_OFFLINE,
                'tool_extra': 'mock tool extra'
            }
        }

        actual_status = nagios_status.get_slice_status(
            'nagios.measurementlab.mock.net')
        nagios_status.urllib2.urlopen.assert_called_once_with(
            'nagios.measurementlab.mock.net')
        self.assertDictEqual(actual_status, expected_status)

    def test_get_slice_status_returns_none_when_Nagios_response_is_whitespace_and_no_newline(
            self):
        self.mock_urlopen_response.read.return_value = '  '
        actual_status = nagios_status.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertIsNone(actual_status)

    def test_get_slice_status_returns_none_when_Nagios_response_is_tab_whitespace(
            self):
        mock_empty_tab_slice_status = '\t\t\t\n'
        self.mock_urlopen_response.read.return_value = mock_empty_tab_slice_status
        actual_status = nagios_status.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertIsNone(actual_status)

    def test_get_slice_status_handles_NagiosStatusUnparseableError_from_one_status_in_parse_sliver_tool_status(
            self):
        mock_slice_status = """
mock.mlab1.xyz01.measurement-lab.org/ndt 0 1 mock tool extra
unparseable status
mock.mlab3.xyz01.measurement-lab.org/ndt 2 1 mock tool extra
""".lstrip()

        self.mock_urlopen_response.read.return_value = mock_slice_status

        nagios_status.parse_sliver_tool_status.side_effect = iter([
            ('mock.mlab1.xyz01.measurement-lab.org', '0', 'mock tool extra'
            ), nagios_status.NagiosStatusUnparseableError('mock error'), (
                'mock.mlab3.xyz01.measurement-lab.org', '2', 'mock tool extra')
        ])

        expected_status = {
            'mock.mlab1.xyz01.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab3.xyz01.measurement-lab.org': {
                'status': message.STATUS_OFFLINE,
                'tool_extra': 'mock tool extra'
            }
        }

        actual_status = nagios_status.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertDictEqual(actual_status, expected_status)

    def test_get_slice_status_handles_NagiosStatusUnparseableError_from_two_statuses_in_parse_sliver_tool_status(
            self):
        mock_slice_status = """
mock.mlab1.xyz01.measurement-lab.org/ndt 0 1 mock tool extra
unparseable status 1
unparseable status 2
""".lstrip()

        self.mock_urlopen_response.read.return_value = mock_slice_status
        nagios_status.parse_sliver_tool_status.side_effect = iter([
            ('mock.mlab1.xyz01.measurement-lab.org', '0', 'mock tool extra'
            ), nagios_status.NagiosStatusUnparseableError('mock error'),
            nagios_status.NagiosStatusUnparseableError('mock error')
        ])

        expected_status = {
            'mock.mlab1.xyz01.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            }
        }

        actual_status = nagios_status.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertDictEqual(actual_status, expected_status)

    def test_get_slice_status_returns_none_when_a_HTTPError_is_raised_by_urlopen(
            self):

        class MockHttpError(urllib2.HTTPError):

            def __init__(self, cause):
                self.cause = cause

        self.mock_urlopen_response.read.side_effect = MockHttpError(
            'mock http error')
        self.assertIsNone(nagios_status.get_slice_status(
            'nagios.measurementlab.mock.net'))


if __name__ == '__main__':
    unittest2.main()
