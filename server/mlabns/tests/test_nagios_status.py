import unittest2

from mlabns.util import nagios_status


class ParseSliverToolStatusTest(unittest2.TestCase):

    def test_parse_sliver_tool_status_returns_successfully_parsed_tuple(self):
        status = 'ndt.iupui.mlab1.acc02.measurement-lab.org/ndt 0 1 mock tool extra'

        expected_parsed_status = ['ndt.iupui.mlab1.acc02.measurement-lab.org',
                                  '0', 'mock tool extra']
        actual_parsed_status = nagios_status.parse_sliver_tool_status(status)

        self.assertEqual(expected_parsed_status, actual_parsed_status)

    def test_parse_sliver_tool_status_returns_none_because_of_illformatted_status(
            self):
        status = 'mock status'
        expected_parsed_status = None
        actual_parsed_status = nagios_status.parse_sliver_tool_status(status)

        self.assertEqual(expected_parsed_status, actual_parsed_status)


if __name__ == '__main__':
    unittest2.main()
