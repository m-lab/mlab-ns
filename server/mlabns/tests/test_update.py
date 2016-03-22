from google.appengine.api import memcache

import json
import mock
import os
import StringIO
import sys
import unittest2
import urllib2


from mlabns.handlers import update
from mlabns.db import model
from mlabns.db import nagios_status_data
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
        self.StatusUpdateHandler= update.StatusUpdateHandler()

        self.nagios_status_patch = mock.patch('mlabns.handlers.update.nagios_status')
        self.addCleanup(self.nagios_status_patch.stop)
        self.nagios_status_patch.start()

        self.util_patch_success = mock.patch.object(util, 'send_success', autospec=True)
        self.addCleanup(self.util_patch_success.stop)
        self.util_patch_success.start()

        self.util_patch_not_found = mock.patch.object(util, 'send_not_found', autospec=True)
        self.addCleanup(self.util_patch_not_found.stop)
        self.util_patch_not_found.start()

    def test_successful_authentication(self): 

        with mock.patch('mlabns.handlers.update.nagios_status_data') as mock_nagios:
            mock_credentials= mock.Mock(name='mock_credentials', url='mock_url')
            mock_nagios.get_nagios_credentials.return_value= mock_credentials  
            self.StatusUpdateHandler.get()

        self.assertTrue(util.send_success.called)

    def test_not_found_nagios_credentials(self): 

        with mock.patch('mlabns.handlers.update.nagios_status_data') as mock_nagios:
            mock_nagios.get_nagios_credentials.return_value= None  
            self.StatusUpdateHandler.get()

        self.assertTrue(util.send_not_found.called)

if __name__ == '__main__':
    unittest2.main()
