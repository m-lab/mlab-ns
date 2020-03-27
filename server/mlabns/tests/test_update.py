import mock
import StringIO
import unittest2
import urllib2

from google.appengine.ext import db
from mlabns.db import model
from mlabns.handlers import update
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
    @mock.patch.object(update.IPUpdateHandler, 'put_sliver_tool')
    def test_update(self, mock_put_sliver_tool, mock_urlopen):
        mock_urlopen.return_value = StringIO.StringIO("""[
{
    "hostname": "ndt.iupui.mlab4.xyz01.measurement-lab.org",
    "ipv4": "192.168.0.1",
    "ipv6": "2002:AB:1234::1"
}
]""")
        model.Site.all.return_value.fetch.return_value = [
            mock.Mock(site_id='xyz01')
        ]
        model.Tool.all.return_value.fetch.return_value = [
            mock.Mock(slice_id='iupui_ndt', tool_id='ndt')
        ]
        model.SliverTool.all.return_value.fetch.return_value = [
            mock.Mock(slice_id='iupui_ndt',
                      tool_id='ndt',
                      fqdn='ndt.iupui.mlab4.xyz01.measurement-lab.org')
        ]

        handler = update.IPUpdateHandler()
        handler.update()

        self.assertTrue(mock_put_sliver_tool.called)


if __name__ == '__main__':
    unittest2.main()
