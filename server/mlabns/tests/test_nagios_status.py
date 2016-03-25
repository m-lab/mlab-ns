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


if __name__ == '__main__':
    unittest2.main()
