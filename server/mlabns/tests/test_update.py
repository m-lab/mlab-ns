import mock
import StringIO
import unittest2
import urllib2

from google.appengine.ext import db
from mlabns.db import model
from mlabns.db import nagios_config_wrapper
from mlabns.db import prometheus_config_wrapper
from mlabns.handlers import update
from mlabns.util import prometheus_status
from mlabns.util import util


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

        query_db_patch = mock.patch.object(db, 'Query', autospec=True)
        self.addCleanup(query_db_patch.stop)
        query_db_patch.start()

        tool_model_patch = mock.patch.object(model, 'Tool', autospec=True)
        self.addCleanup(tool_model_patch.stop)
        tool_model_patch.start()

        util_patch = mock.patch.object(util, 'send_success', autospec=True)
        self.addCleanup(util_patch.stop)
        util_patch.start()

        # Initialize the SITE_REGEX  and MACHINE_REGEX env variable.
        environ_patch = mock.patch.dict('os.environ', {
            'MACHINE_REGEX': '^mlab4$',
            'SITE_REGEX': '^[a-z]{3}[0-9c]{2}$',
        })
        self.addCleanup(environ_patch.stop)
        environ_patch.start()

    @mock.patch.object(update.IPUpdateHandler, 'update')
    def testGetIgnoresTestSites(self, mock_update):
        """Test sites should not be processed except in sandbox project."""
        urllib2.urlopen.return_value = StringIO.StringIO("""[
{
    "site": "abc0t",
    "metro": ["abc0t", "abc"],
    "created": 1310048316,
    "city": "Abcville",
    "country": "AB",
    "latitude": null,
    "longitude": null,
    "roundrobin": false
}
]""")
        db.Query.fetch.return_value = [mock.Mock(site_id='abc0t')]
        handler = update.SiteRegistrationHandler()
        handler.get()

        self.assertTrue(util.send_success.called)
        self.assertTrue(mock_update.called)

        self.assertFalse(
            model.Site.called,
            'Test site should not be added to the staging datastore.')

    @mock.patch.object(update.IPUpdateHandler, 'update')
    def testUpdateExistingSites(self, mock_update):
        """Test updating an existing site."""
        urllib2.urlopen.return_value = StringIO.StringIO("""[
{
    "site": "def01",
    "metro": ["def01", "def"],
    "created": 1310048316,
    "city": "Defville",
    "country": "DE",
    "latitude": 123.456789,
    "longitude": 34.567890,
    "roundrobin": false
}
]""")
        db.Query.fetch.return_value = [mock.Mock(site_id='def01')]
        handler = update.SiteRegistrationHandler()
        handler.get()

        self.assertTrue(util.send_success.called)
        self.assertTrue(mock_update.called)

        self.assertTrue(model.Site.called,
                        'Update an existing site to the datastore')


class StatusUpdateHandlerTest(unittest2.TestCase):

    def setUp(self):
        tool_all_patch = mock.patch.object(model,
                                           'get_all_tool_ids',
                                           autospec=True)
        self.addCleanup(tool_all_patch.stop)
        tool_all_patch.start()

        tool_id_patch = mock.patch.object(model,
                                          'get_tool_from_tool_id',
                                          autospec=True)
        self.addCleanup(tool_id_patch.stop)
        tool_id_patch.start()

        tool_deps_patch = mock.patch.object(model,
                                            'get_status_source_deps',
                                            autospec=True)
        self.addCleanup(tool_deps_patch.stop)
        tool_deps_patch.start()

        prom_config_wrapper_patch = mock.patch.object(prometheus_config_wrapper,
                                                      'get_prometheus_config',
                                                      autospec=True)
        self.addCleanup(prom_config_wrapper_patch.stop)
        prom_config_wrapper_patch.start()

        prom_authenticate_patch = mock.patch.object(prometheus_status,
                                                    'authenticate_prometheus',
                                                    autospec=True)
        self.addCleanup(prom_authenticate_patch.stop)
        prom_authenticate_patch.start()

        nagios_config_wrapper_patch = mock.patch.object(nagios_config_wrapper,
                                                        'get_nagios_config',
                                                        autospec=True)
        self.addCleanup(nagios_config_wrapper_patch.stop)
        nagios_config_wrapper_patch.start()

        util_send_success_patch = mock.patch.object(util,
                                                    'send_success',
                                                    autospec=True)
        self.addCleanup(util_send_success_patch.stop)
        util_send_success_patch.start()

        self.mock_slice_status_okay = {
            'ndt.mlab1-abc01.mlab-sandbox.measurement-lab.org': {
                'status': 'online',
            },
            'ndt.mlab2-abc01.mlab-sandbox.measurement-lab.org': {
                'status': 'online',
            },
            'ndt.mlab3-abc01.mlab-sandbox.measurement-lab.org': {
                'status': 'online',
            },
            'ndt.mlab4-abc01.mlab-sandbox.measurement-lab.org': {
                'status': 'online',
            },
        }

        self.mock_slice_status_bad = {
            'ndt.mlab1-abc01.mlab-sandbox.measurement-lab.org': {
                'status': 'online',
            },
            'ndt.mlab2-abc01.mlab-sandbox.measurement-lab.org': {
                'status': 'offline',
            },
            'ndt.mlab3-abc01.mlab-sandbox.measurement-lab.org': {
                'status': 'offline',
            },
            'ndt.mlab4-abc01.mlab-sandbox.measurement-lab.org': {
                'status': 'offline',
            },
        }

    @mock.patch.object(prometheus_status, 'get_slice_status')
    @mock.patch.object(update.StatusUpdateHandler, 'update_sliver_tools_status')
    def test_get(self, mock_update, mock_get_status):

        model.get_all_tool_ids.return_value = ['ndt']

        model.get_tool_from_tool_id.return_value = (mock.Mock(
            slice_id='iupui_ndt',
            status_source='prometheus',
            tool_id='ndt'))
        model.get_status_source_deps.return_value = [
            mock.Mock(slice_id='iupui_ndt',
                      status_source='prometheus',
                      tool_id='ndt')
        ]
        prometheus_config_wrapper.get_prometheus_config.return_value = (
            mock.Mock(url='fake://url'))
        prometheus_status.authenticate_prometheus.return_value = "testing"
        nagios_config_wrapper.get_nagios_config.return_value = None

        handler = update.StatusUpdateHandler()

        # get_slice_status() is called twice for each tool, once for IPv4 and
        # once for IPv6. In this test we use a single tool (ndt), and call
        # get() twice for a total of four calls to get_slice_status()
        mock_get_status.side_effect = [
            self.mock_slice_status_okay,
            self.mock_slice_status_okay,
            self.mock_slice_status_bad,
            self.mock_slice_status_bad,
        ]

        handler.get()
        self.assertTrue(mock_update.called)
        self.assertEqual(mock_update.call_count, 2)

        # Asserts that the call_count for mock_update did not increment for our
        # two "bad" cases.
        handler.get()
        self.assertEqual(mock_update.call_count, 2)


class IPUpdateHandlerTest(unittest2.TestCase):

    def setUp(self):
        # Patch out the APIs that IPUpdateHandler calls.
        site_model_patch = mock.patch.object(model, 'Site', autospec=True)
        self.addCleanup(site_model_patch.stop)
        site_model_patch.start()

        tool_model_patch = mock.patch.object(model, 'Tool', autospec=True)
        self.addCleanup(tool_model_patch.stop)
        tool_model_patch.start()

        sliver_model_patch = mock.patch.object(model,
                                               'SliverTool',
                                               autospec=True)
        self.addCleanup(sliver_model_patch.stop)
        sliver_model_patch.start()

        # Initialize the SITE_REGEX  and MACHINE_REGEX env variable.
        environ_patch = mock.patch.dict('os.environ', {
            'MACHINE_REGEX': '^mlab4$',
            'SITE_REGEX': '^[a-z]{3}[0-9c]{2}$',
        })
        self.addCleanup(environ_patch.stop)
        environ_patch.start()

    @mock.patch.object(urllib2, 'urlopen')
    @mock.patch.object(update.IPUpdateHandler, 'initialize_sliver_tool')
    @mock.patch.object(update.IPUpdateHandler, 'put_sliver_tool')
    def test_update(self, mock_put, mock_initialize, mock_urlopen):
        mock_urlopen.return_value = StringIO.StringIO("""[
{
    "hostname": "ndt-iupui-mlab4-xyz01.mlab-staging.measurement-lab.org",
    "ipv4": "192.168.0.99",
    "ipv6": "2002:AB:1234::99"
}
]""")
        model.Site.all.return_value.fetch.return_value = [
            mock.Mock(site_id='xyz01', roundrobin=True)
        ]
        model.Tool.all.return_value.fetch.return_value = [
            mock.Mock(slice_id='iupui_ndt', tool_id='ndt')
        ]

        mock_slivertools = mock.Mock(
            slice_id='iupui_ndt',
            tool_id='ndt',
            fqdn='ndt.iupui.mlab4.xyz01.measurement-lab.org',
            sliver_ipv4='192.168.0.1',
            sliver_ipv6='2002:AB:1234::1',
            roundrobin=True)
        sliver_tool_id = model.get_sliver_tool_id('ndt', 'iupui_ndt', 'mlab4',
                                                  'xyz01')
        mock_slivertools.key.return_value.name.return_value = sliver_tool_id
        model.SliverTool.all.return_value.fetch.return_value = [
            mock_slivertools
        ]

        handler = update.IPUpdateHandler()
        handler.update()

        self.assertFalse(mock_initialize.called)
        self.assertTrue(mock_put.called)

    @mock.patch.object(urllib2, 'urlopen')
    @mock.patch.object(update.IPUpdateHandler, 'initialize_sliver_tool')
    @mock.patch.object(update.IPUpdateHandler, 'put_sliver_tool')
    def test_initialize(self, mock_put, mock_initialize, mock_urlopen):
        mock_urlopen.return_value = StringIO.StringIO("""[
{
    "hostname": "ndt-iupui-mlab4-abc02.mlab-staging.measurement-lab.org",
    "ipv4": "192.168.0.1",
    "ipv6": "2002:AB:1234::1"
}
]""")
        model.Site.all.return_value.fetch.return_value = [
            mock.Mock(site_id='abc02', roundrobin=True)
        ]
        model.Tool.all.return_value.fetch.return_value = [
            mock.Mock(slice_id='iupui_ndt', tool_id='ndt')
        ]
        model.SliverTool.all.return_value.fetch.return_value = []

        handler = update.IPUpdateHandler()
        handler.update()

        self.assertTrue(mock_initialize.called)
        self.assertTrue(mock_put.called)

    @mock.patch.object(urllib2, 'urlopen')
    @mock.patch.object(update.IPUpdateHandler, 'initialize_sliver_tool')
    @mock.patch.object(update.IPUpdateHandler, 'put_sliver_tool')
    def test_no_update(self, mock_put, mock_initialize, mock_urlopen):

        mock_urlopen.return_value = StringIO.StringIO("""[
{
    "hostname": "ndt-iupui-mlab4-abc02.mlab-staging.measurement-lab.org",
    "ipv4": "192.168.0.1",
    "ipv6": "2002:AB:1234::1"
}
]""")
        model.Site.all.return_value.fetch.return_value = [
            mock.Mock(site_id='abc02', roundrobin=True)
        ]
        model.Tool.all.return_value.fetch.return_value = [
            mock.Mock(slice_id='iupui_ndt', tool_id='ndt')
        ]

        mock_slivertools = mock.Mock(
            slice_id='iupui_ndt',
            tool_id='ndt',
            fqdn='ndt-iupui-mlab4-abc02.mlab-staging.measurement-lab.org',
            sliver_ipv4='192.168.0.1',
            sliver_ipv6='2002:AB:1234::1',
            roundrobin=True)
        sliver_tool_id = model.get_sliver_tool_id('ndt', 'iupui_ndt', 'mlab4',
                                                  'abc02')
        mock_slivertools.key.return_value.name.return_value = sliver_tool_id
        model.SliverTool.all.return_value.fetch.return_value = [
            mock_slivertools
        ]

        handler = update.IPUpdateHandler()
        handler.update()

        self.assertFalse(mock_initialize.called)
        self.assertFalse(mock_put.called)


if __name__ == '__main__':
    unittest2.main()
