import mock
import unittest2

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


class GetSliceUrlsTest(unittest2.TestCase):

    def setUp(self):
        self.nagios_url = 'http://nagios.measurementlab.net/baseList'
        self.nagios_suffixes = ['_ipv6']

    def assertToolListEqual(self, list_a, list_b):
        """Equality of tool lists is based on tool_ids of Tools"""

        ids_a = [x.tool_id for x in list_a]
        ids_b = [x.tool_id for x in list_b]
        self.assertListEqual(ids_a, ids_b)

    def test_get_slice_info_returns_valid_objects_when_tools_stored(self):
        slice_a_url = 'http://nagios.measurementlab.net/baseList?show_state=1&service_name=mock_tool_a_ipv6&plugin_output=1'
        slice_a_info = nagios_status.NagiosSliceInfo(slice_a_url, 'mock_tool_a',
                                                     '_ipv6')

        slice_b_url = 'http://nagios.measurementlab.net/baseList?show_state=1&service_name=mock_tool_b_ipv6&plugin_output=1'
        slice_b_info = nagios_status.NagiosSliceInfo(slice_b_url, 'mock_tool_b',
                                                     '_ipv6')
        expected = [slice_a_info, slice_b_info]

        with mock.patch('mlabns.util.nagios_status.model') as mock_model:
            mock_model.get_all_tool_ids.return_value = [mock.Mock(
                tool_id='mock_tool_a'), mock.Mock(tool_id='mock_tool_b')]
            retrieved = nagios_status.get_slice_info(self.nagios_url,
                                                     self.nagios_suffixes)

        self.assertToolListEqual(expected, retrieved)

    def test_get_slice_info_returns_empty_list_when_no_tools_stored(self):
        with mock.patch('mlabns.util.nagios_status.model') as mock_model:
            mock_model.get_all_tool_ids.return_value = []
            retrieved = nagios_status.get_slice_info(self.nagios_url,
                                                     self.nagios_suffixes)
        expected = []
        self.assertEqual(expected, retrieved)


if __name__ == '__main__':
    unittest2.main()
