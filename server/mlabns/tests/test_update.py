import mock
import StringIO
import unittest2
import urllib2

from google.appengine.api import app_identity
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

        get_application_id_patch = mock.patch.object(app_identity,
                                                     'get_application_id',
                                                     autospec=True)
        self.addCleanup(get_application_id_patch.stop)
        get_application_id_patch.start()

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
    "longitude": null,
    "roundrobin": false
}
]""")
        app_identity.get_application_id.return_value = 'mlab-nstesting'
        db.Query.fetch.return_value = [mock.Mock(site_id='xyz01')]
        handler = update.SiteRegistrationHandler()
        handler.get()

        self.assertTrue(util.send_success.called)

        self.assertFalse(model.Site.called,
                         'Test site should not be added to the datastore')

    def testUpdateExistingSites(self):
        """Test updating an existing site."""
        urllib2.urlopen.return_value = StringIO.StringIO("""[
{
    "site": "xyz01",
    "metro": ["xyz01", "xyz"],
    "created": 1310048316,
    "city": "Xyzville",
    "country": "AB",
    "latitude": 123.456789,
    "longitude": 34.567890,
    "roundrobin": false
}
]""")
        app_identity.get_application_id.return_value = 'mlab-nstesting'
        db.Query.fetch.return_value = [mock.Mock(site_id='xyz01')]
        handler = update.SiteRegistrationHandler()
        handler.get()

        self.assertTrue(util.send_success.called)

        self.assertTrue(model.Site.called,
                        'Update an existing site to the datastore')


if __name__ == '__main__':
    unittest2.main()
