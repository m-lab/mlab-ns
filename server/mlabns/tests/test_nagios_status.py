import mock
import unittest2

from mlabns.db import model
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


if __name__ == '__main__':
    unittest2.main()
