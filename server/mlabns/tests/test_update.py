import json
import mock
import os
import StringIO
import sys
import urllib2
import unittest2

from mlabns.handlers import update
from mlabns.db import model
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

    # def get(self):
    #     """
    #     Access sliver status with information from Nagios. The Nagios URL
    #     containing the information is stored in the Nagios db along with
    #     the credentials necessary to access the data.
    #     """  
        
    #     nagios = model.Nagios.get_by_key_name(constants.DEFAULT_NAGIOS_ENTRY)
    #     if nagios is None:
    #         return util.send_not_found(self)
    #     nagios_status.authenticate_nagios(nagios)
        
    #     slice_urls= nagios_status.get_slice_urls(nagios.url, self.NAGIOS_AF_SUFFIXES)
    #     for url in slice_urls: 
    #         slice_status = nagios_status.get_slice_status(slice_url)
    #         nagios_status.update_sliver_tools_status(slice_status, tool.tool_id,
    #                                             family) # NO LONGER HAVE TOOL ID
    #     return util.send_success(self)

    # def send_not_found(request, output_type=message.FORMAT_HTML):
    #     request.error(404)
    #     if output_type == message.FORMAT_JSON:
    #         data = {}
    #         data['status_code'] = '404 Not found'
    #         json_data = json.dumps(data)
    #         request.response.headers['Content-Type'] = 'application/json'
    #         request.response.out.write(json_data)
    #     else:
    #         request.response.out.write(_get_jinja_template('not_found.html').render(
    #         ))

    # def send_success(request, output_type=message.FORMAT_JSON):
    #     if output_type == message.FORMAT_JSON:
    #         data = {}
    #         data['status_code'] = '200 OK'
    #         json_data = json.dumps(data)
    #         request.response.headers['Content-Type'] = 'application/json'
    #         request.response.out.write(json_data)
    #     else:
    #         request.response.out.write('<html> Success! </html>')

class StatusUpdateHandlerTest(unittest2.TestCase):

    def setUp(self): 
        self.mock_request= mock.Mock()
        self.mock_response= mock.Mock(headers={})
        self.StatusUpdateHandler= update.StatusUpdateHandler()
        self.StatusUpdateHandler.initialize(self.mock_request, self.mock_response) 

        self.nagios_status_patch = mock.patch('mlabns.handlers.update.nagios_status')
        self.addCleanup(self.nagios_status_patch.stop)
        self.nagios_status_patch.start()

        self.util_patch = mock.patch('mlabns.handlers.update.util')
        self.addCleanup(self.util_patch.stop)
        self.util_patch.start()

    def test_successful_authentication(self): 

        with mock.patch('mlabns.db.model.Nagios') as mock_nagios: 
            mock_nagios.get_by_key_name.return_value= 'mock_credentials'  
            self.StatusUpdateHandler.get()

        self.util_patch.send_success.assert_called_once_with(self.StatusUpdateHandler)

    def test_not_found_nagios_credentials(self): 

        with mock.patch('mlabns.db.model.Nagios') as mock_nagios:
            mock_nagios.get_by_key_name.return_value= None  
            self.StatusUpdateHandler.get()

        self.util_patch.send_not_found.assert_called_once_with(self.StatusUpdateHandler)

if __name__ == '__main__':
    unittest2.main()
