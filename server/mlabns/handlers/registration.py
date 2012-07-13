from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.util import sign
from mlabns.util import message
from mlabns.db import model

class RegistrationHandler(webapp.RequestHandler):
    """Handles SliverTools registrations.
    
    All the registrations come as HTTP POST requests and must be signed.
    """
    
    def get(self):
        """Not implemented."""
        return self.send_not_found()
    
    def check_signature(self):
        data = {}
        for argument in self.request.arguments():
            data[argument] = self.request.get(argument)
        
        if not data.has_key(message.SIGNATURE):
            return False 
        expected_signature = data[message.SIGNATURE]
        data[message.SIGNATURE] = ''
        key = 'mlab-ns@admin'
        signature = sign.sign_message(data, key)
        return (signature == expected_signature)
    
    def post(self):
        """Handles registrations through HTTP POST requests.
        
        Verify the request and if valid, add a new record to the
        corresponding dbi.
        """
        # TODO(claudiu): Require admin login.
        if not self.check_signature():
            self.send_not_found()
        entity = self.request.get(message.ENTITY)
        if (entity == message.ENTITY_SLIVER_TOOL):
            sliver_tool_id = "" . join(
                [self.request.get(message.TOOL_ID),
                self.request.get(message.SLICE_ID),
                self.request.get(message.SERVER_ID),
                self.request.get(message.SITE_ID)])
            
            sliver_tool = model.SliverTool(
                tool_id=self.request.get(message.TOOL_ID),
                slice_id=self.request.get(message.SLICE_ID),
                site_id=self.request.get(message.SITE_ID),
                server_id=self.request.get(message.SERVER_ID),
                sliver_tool_key=self.request.get(message.SLIVER_TOOL_KEY),
                sliver_ipv4=self.request.get(message.SLIVER_IPv4),
                sliver_ipv6=self.request.get(message.SLIVER_IPv6),
                url=self.request.get(message.URL),
                status=self.request.get(message.STATUS),
                lat_long=self.request.get(message.SITE_LAT_LONG),
                key_name=sliver_tool_id) 
            sliver_tool.put()
            self.send_success()
        elif (entity == message.ENTITY_SITE):
            site = model.Site(
                site_id=self.request.get(message.SITE_ID),
                city=self.request.get(message.SITE_CITY),
                region=self.request.get(message.SITE_REGION),
                country=self.request.get(message.SITE_COUNTRY),
                lat_long=self.request.get(message.SITE_LAT_LONG),
                metro=self.request.get(message.METRO).split(','),
                key_name=self.request.get(message.SITE_ID))
            site.put()
            self.send_success()
        else:
            self.send_not_found()
    
    def send_success(self, message='SUCCESS'):
        self.response.out.write(message)
    
    def send_error(self, error_code=404, message='Error'):
        # 404: Not found.
        self.error(error_code)
        self.response.out.write(message)
    
    def send_not_found(self):
        self.error(404)
        self.response.out.write(
        template.render('mlabns/templates/not_found.html', {}))
