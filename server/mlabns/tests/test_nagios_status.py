from google.appengine.ext import db

import mock
import unittest2
import urllib2

from mlabns.db import nagios_status_data
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import nagios_status


class MockHttpError(urllib2.HTTPError):

    def __init__(self, error_code):
        self.resp = mock.Mock()
        self.resp.status = error_code


class MockDbError(db.TransactionFailedError):

    def __init__(self, error):
        self.error = error


class GetSliceUrlTest(unittest2.TestCase):

    def setUp(self):
        self.nagios_url = 'http://nagios.measurementlab.net/baseList'
        self.nagios_suffixes = ['_ipv6']

    def test_get_urls_successfully(self):
        expected_urls = [(
            'http://nagios.measurementlab.net/baseList?show_state=1&service_name=mock_one_ipv6&plugin_output=1',
            'mock_one', '_ipv6'
        ), ('http://nagios.measurementlab.net/baseList?show_state=1&service_name=mock_two_ipv6&plugin_output=1',
            'mock_two', '_ipv6')]

        with mock.patch(
                'mlabns.util.nagios_status.nagios_status_data') as mock_nagios:
            mock_nagios.get_tools_by_id.return_value = [mock.Mock(
                tool_id='mock_one'), mock.Mock(tool_id='mock_two')]
            actual_urls = nagios_status.get_slice_urls(self.nagios_url,
                                                       self.nagios_suffixes)

        self.assertTrue(expected_urls == actual_urls)

    def test_tools_list_empty(self):
        with mock.patch(
                'mlabns.util.nagios_status.nagios_status_data') as mock_nagios:
            mock_nagios.get_tools_by_id.return_value = []
            actual_urls = nagios_status.get_slice_urls(self.nagios_url,
                                                       self.nagios_suffixes)
        expected_urls = []

        self.assertTrue(expected_urls == actual_urls)


class ParseSliverToolStatusTest(unittest2.TestCase):

    def test_successful_parsing(self):
        status = 'ndt.iupui.mlab1.acc02.measurement-lab.org/ndt 0 1 mock tool extra'

        expected_parsed_status = ['ndt.iupui.mlab1.acc02.measurement-lab.org',
                                  '0', 'mock tool extra']
        actual_parsed_status = nagios_status.parse_sliver_tool_status(status)

        self.assertTrue(expected_parsed_status == actual_parsed_status)

    def test_illformatted_status(self):
        status = 'mock status'
        expected_parsed_status = None
        actual_parsed_status = nagios_status.parse_sliver_tool_status(status)

        self.assertTrue(expected_parsed_status == actual_parsed_status)


class HasNoIpTest(unittest2.TestCase):

    def setUp(self):
        self.no_ip = message.NO_IP_ADDRESS
        self.four = constants.AF_IPV4
        self.six = constants.AF_IPV6

    def test_version6_offline(self):
        sliver_tool = mock.Mock(sliver_ipv6=self.no_ip)
        expected = nagios_status.has_no_ip(sliver_tool, self.six)

        self.assertTrue(expected == True)

    def test_version4_online(self):
        sliver_tool = mock.Mock(sliver_ipv4='mock_ip')
        expected = nagios_status.has_no_ip(sliver_tool, self.four)

        self.assertTrue(expected == False)


class WasOnlineTest(unittest2.TestCase):

    def setUp(self):
        self.online = message.STATUS_ONLINE
        self.offline = message.STATUS_OFFLINE
        self.four = constants.AF_IPV4
        self.six = constants.AF_IPV6

    def test_version6_offline(self):
        sliver_tool = mock.Mock(status_ipv6=self.offline)
        expected = nagios_status.was_online(sliver_tool, self.six)

        self.assertTrue(expected == False)

    def test_version6_online_but_version4(self):
        sliver_tool = mock.Mock(status_ipv6=self.online)
        expected = nagios_status.was_online(sliver_tool, self.four)

        self.assertTrue(expected == False)

    def test_version4_online(self):
        sliver_tool = mock.Mock(status_ipv4=self.online)
        expected = nagios_status.was_online(sliver_tool, self.four)

        self.assertTrue(expected == True)


class EvaluateStatusUpdateTest(unittest2.TestCase):

    def setUp(self):
        self.no_ip = message.NO_IP_ADDRESS
        self.online = message.STATUS_ONLINE
        self.offline = message.STATUS_OFFLINE
        self.four = constants.AF_IPV4
        self.six = constants.AF_IPV6
        self.slice_status= lambda x: {'mock_fqdn':{'tool_extra':'mock_tool_extra', 'status': x }}

    def test_version4_has_no_ip_and_was_online(self):
        with mock.patch.object(nagios_status, 'was_online', return_value=True):
            with mock.patch.object(nagios_status,
                                   'has_no_ip',
                                   return_value=True):
                mock_sliver_tool = mock.Mock(fqdn='mock_fqdn')
                nagios_status.evaluate_status_update(
                    mock_sliver_tool, self.four, self.slice_status(self.online))

        self.assertTrue(mock_sliver_tool.status_ipv4 == self.offline)

    def test_version6_has_ip_and_no_change(self):
        with mock.patch.object(nagios_status, 'has_no_ip', return_value=False):
            mock_sliver_tool = mock.Mock(fqdn='mock_fqdn')
            nagios_status.evaluate_status_update(mock_sliver_tool, self.six,
                                                 self.slice_status(self.online))

        self.assertTrue(mock_sliver_tool.tool_extra == 'mock_tool_extra')
        self.assertTrue(mock_sliver_tool.status_ipv6 == self.online)


class GetSliceStatusTest(unittest2.TestCase):

    def test_http_error(self):
        with mock.patch.object(urllib2,
                               'urlopen',
                               side_effect=MockHttpError('mock_code')):
            status_actual = nagios_status.get_slice_status('mock_url')
        self.assertTrue(status_actual == None)

    def test_one_none_status(self):
        with mock.patch.object(urllib2, 'urlopen'):
            with mock.patch.object(nagios_status,
                                   'parse_sliver_tool_status',
                                   return_value=None):
                actual_status = nagios_status.get_slice_status('mock_url')
                self.assertTrue(actual_status == {})


class UpdateSliverToolsStatusTest(unittest2.TestCase):

    def setUp(self):
        evaluate_patch = mock.patch.object(nagios_status,
                                           'evaluate_status_update',
                                           autospec=True)
        self.addCleanup(evaluate_patch.stop)
        evaluate_patch.start()

    def test_db_error_continues(self):
        error_sliver = mock.Mock(fqdn='mock_fqdn')
        error_sliver.put.side_effect = MockDbError('mock_error')
        after_error_sliver = mock.Mock(fqdn='mock_fqdn')
        slivers = [error_sliver, after_error_sliver]

        with mock.patch.object(nagios_status_data,
                               'get_SliverTool_by_tool_id',
                               return_value=slivers):
            nagios_status.update_sliver_tools_status(
                {'mock_fqdn': 'mock_status'}, 'mock_tool_id', 'mock_ip')
            self.assertTrue(after_error_sliver.put.called)

    def test_everything_successful(self):
        first_sliver = mock.Mock(fqdn='mock_fqdn')
        second_sliver = mock.Mock(fqdn='mock_fqdn')
        slivers = [first_sliver, second_sliver]

        with mock.patch.object(nagios_status_data,
                               'get_SliverTool_by_tool_id',
                               return_value=slivers):
            nagios_status.update_sliver_tools_status('mock_status',
                                                     'mock_tool_id', 'mock_ip')
            self.assertTrue(first_sliver.update_request_timestamp)
            self.assertTrue(second_sliver.update_request_timestamp)
            self.assertTrue(first_sliver.put.called)
            self.assertTrue(second_sliver.put.called)


if __name__ == '__main__':
    unittest2.main()
