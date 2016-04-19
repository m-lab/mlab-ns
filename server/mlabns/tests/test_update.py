import mock
import StringIO
import unittest2
import urllib2

from mlabns.db import model
from mlabns.handlers import update
from mlabns.util import message
from mlabns.util import nagios_status
from mlabns.util import util


class MockHttpError(urllib2.HTTPError):

    def __init__(self, cause):
        self.cause = cause


class SiteRegistrationHandlerTest(unittest2.TestCase):

    def setUp(self):
        # Patch out the APIs that SiteRegistrationHandler calls.
        #
        # TODO(mtlynch): Redesign SiteRegistrationHandler to be more
        # test-friendly and rely less on patching.
        urlopen_patch = mock.patch.object(urllib2, 'urlopen', autospec=True)
        self.addCleanup(urlopen_patch.stop)
        urlopen_patch.start()

        site_model_patch = mock.patch.object(model, 'Site', autospec=True)
        self.addCleanup(site_model_patch.stop)
        site_model_patch.start()

        tool_model_patch = mock.patch.object(model, 'Tool', autospec=True)
        self.addCleanup(tool_model_patch.stop)
        tool_model_patch.start()

        util_patch = mock.patch.object(util, 'send_success', autospec=True)
        self.addCleanup(util_patch.stop)
        util_patch.start()

    def testGetIgnoresTestSites(self):
        """Test sites should not be processed in the sites update."""
        urllib2.urlopen.return_value = StringIO.StringIO("""[
{
    "site": "xyz0t",
    "metro": ["xyz0t", "xyz"],
    "created": 1310048316,
    "city": "Xyzville",
    "country": "AB",
    "latitude": null,
    "longitude": null
},
{
    "site": "xyz01",
    "metro": ["xyz01", "xyz"],
    "created": 1310048316,
    "city": "Xyzville",
    "country": "AB",
    "latitude": 123.456789,
    "longitude": 34.567890
}
]""")
        model.Site.all.return_value = [mock.Mock(site_id='xyz01')]
        handler = update.SiteRegistrationHandler()
        handler.get()

        self.assertTrue(util.send_success.called)

        self.assertFalse(model.Site.called,
                         'Test site should not be added to the datastore')


class StatusUpdateHandlerTest(unittest2.TestCase):

    def setUp(self):
        self.status_update_handler = update.StatusUpdateHandler()
        self.mock_nagios_content = mock.Mock()

        urlopen_patch = mock.patch.object(update.urllib2,
                                          'urlopen',
                                          return_value=self.mock_nagios_content,
                                          autospec=True)
        self.addCleanup(urlopen_patch.stop)
        urlopen_patch.start()

        parse_sliver_tool_status_patch = mock.patch.object(
            update.nagios_status,
            'parse_sliver_tool_status',
            autospec=True)
        self.addCleanup(parse_sliver_tool_status_patch.stop)
        parse_sliver_tool_status_patch.start()

        logging_patch = mock.patch.object(update.logging,
                                          'error',
                                          autospec=True)
        self.addCleanup(logging_patch.stop)
        logging_patch.start()

        # Expected slice status format
        self.mock_slice_status = 'mock.mlab1.site1.measurement-lab.org/ndt 0 1 mock tool extra\n'
        self.mock_slice_status += 'mock.mlab2.site1.measurement-lab.org/ndt 0 1 mock tool extra\n'
        self.mock_slice_status += 'mock.mlab3.site1.measurement-lab.org/ndt 0 1 mock tool extra\n'
        self.mock_slice_status += 'mock.mlab1.site2.measurement-lab.org/ndt 0 1 mock tool extra\n'

        # Expected parsing of slice status shown above
        self.parsed_statuses = {
            'mock.mlab1.site1.measurement-lab.org/ndt 0 1 mock tool extra': (
                'mock.mlab1.site1.measurement-lab.org', '0', 'mock tool extra'),
            'mock.mlab2.site1.measurement-lab.org/ndt 0 1 mock tool extra': (
                'mock.mlab2.site1.measurement-lab.org', '0', 'mock tool extra'),
            'mock.mlab3.site1.measurement-lab.org/ndt 0 1 mock tool extra': (
                'mock.mlab3.site1.measurement-lab.org', '0', 'mock tool extra'),
            'mock.mlab1.site2.measurement-lab.org/ndt 0 1 mock tool extra': (
                'mock.mlab1.site2.measurement-lab.org', '0', 'mock tool extra')
        }

    def test_get_slice_status_gets_valid_statuses_returns_populated_dictionary(
            self):

        self.mock_nagios_content.read.return_value = self.mock_slice_status

        mock_parse_sliver_tool_status = lambda status: self.parsed_statuses[status]
        update.nagios_status.parse_sliver_tool_status.side_effect = mock_parse_sliver_tool_status

        expected_status = {
            'mock.mlab1.site1.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab2.site1.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab3.site1.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab1.site2.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            }
        }

        actual_status = self.status_update_handler.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertEqual(actual_status, expected_status)

    def test_get_slice_status_reads_in_blank_statuses_returns_none(self):
        mock_empty_slice_status = '  '
        self.mock_nagios_content.read.return_value = mock_empty_slice_status
        actual_status = self.status_update_handler.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertIsNone(actual_status)

    def test_get_slice_status_reads_in_tab_whitespace_statuses_returns_none(
            self):
        mock_empty_tab_slice_status = '\t\t\t\n'
        self.mock_nagios_content.read.return_value = mock_empty_tab_slice_status
        actual_status = self.status_update_handler.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertIsNone(actual_status)

    def test_get_slice_status_handles_nagiosstatusunparseable_error_from_one_status_in_parse_sliver_tool_status(
            self):
        self.mock_nagios_content.read.return_value = self.mock_slice_status

        def parsed_statuses_with_exceptions(status):
            if status == 'mock.mlab2.site1.measurement-lab.org/ndt 0 1 mock tool extra':
                raise nagios_status.NagiosStatusUnparseableError('mock error')
            return self.parsed_statuses[status]

        update.nagios_status.parse_sliver_tool_status.side_effect = parsed_statuses_with_exceptions

        expected_status = {
            'mock.mlab1.site1.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab3.site1.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab1.site2.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            }
        }

        self.assertRaises(
            nagios_status.NagiosStatusUnparseableError,
            update.nagios_status.parse_sliver_tool_status,
            'mock.mlab2.site1.measurement-lab.org/ndt 0 1 mock tool extra')
        actual_status = self.status_update_handler.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertDictEqual(actual_status, expected_status)

    def test_get_slice_status_handles_nagiosstatusunparseable_error_from_two_statuses_in_parse_sliver_tool_status(
            self):

        self.mock_nagios_content.read.return_value = self.mock_slice_status

        def parsed_statuses_with_exceptions(status):
            if status ==  'mock.mlab2.site1.measurement-lab.org/ndt 0 1 mock tool extra' \
                or status ==  'mock.mlab3.site1.measurement-lab.org/ndt 0 1 mock tool extra':
                raise nagios_status.NagiosStatusUnparseableError('mock error')
            return self.parsed_statuses[status]

        update.nagios_status.parse_sliver_tool_status.side_effect = parsed_statuses_with_exceptions

        expected_status = {
            'mock.mlab1.site1.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            },
            'mock.mlab1.site2.measurement-lab.org': {
                'status': message.STATUS_ONLINE,
                'tool_extra': 'mock tool extra'
            }
        }

        self.assertRaises(
            nagios_status.NagiosStatusUnparseableError,
            update.nagios_status.parse_sliver_tool_status,
            'mock.mlab2.site1.measurement-lab.org/ndt 0 1 mock tool extra')
        self.assertRaises(
            nagios_status.NagiosStatusUnparseableError,
            update.nagios_status.parse_sliver_tool_status,
            'mock.mlab3.site1.measurement-lab.org/ndt 0 1 mock tool extra')
        actual_status = self.status_update_handler.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertDictEqual(actual_status, expected_status)

    def test_get_slice_status_handles_httperror_from_urlopen_returns_none(self):
        self.mock_nagios_content.read.side_effect = MockHttpError(
            'mock http error')
        self.assertIsNone(self.status_update_handler.get_slice_status(
            'nagios.measurementlab.mock.net'))

    def test_get_slice_status_sliver_status_offline_returns_successfully(self):
        mock_offline_slice_status = 'mock.mlab1.site1.measurement-lab.org/ndt 2 1 mock tool extra\n'
        self.mock_nagios_content.read.return_value = mock_offline_slice_status

        parsed_offline_status = {
            'mock.mlab1.site1.measurement-lab.org/ndt 2 1 mock tool extra': (
                'mock.mlab1.site1.measurement-lab.org', '2', 'mock tool extra')
        }

        mock_parse_sliver_tool_status = lambda status: parsed_offline_status[status]
        update.nagios_status.parse_sliver_tool_status.side_effect = mock_parse_sliver_tool_status

        expected_status = {
            'mock.mlab1.site1.measurement-lab.org': {
                'status': message.STATUS_OFFLINE,
                'tool_extra': 'mock tool extra'
            }
        }

        actual_status = self.status_update_handler.get_slice_status(
            'nagios.measurementlab.mock.net')
        self.assertDictEqual(actual_status, expected_status)


if __name__ == '__main__':
    unittest2.main()
