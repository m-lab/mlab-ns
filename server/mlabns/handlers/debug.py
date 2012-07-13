from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.db import model

class DebugHandler(webapp.RequestHandler):
    def get(self):
        view = self.request.get('db')
        if (view == 'sliver_tool'):
            return self.sliver_tool_view()
        if (view == 'site' ):
            return self.site_view()
        if (view == 'lookup'):
            return self.lookup_view()
        return self.send_error()
 
    def sliver_tool_view(self):  
        records = model.SliverTool.gql("ORDER BY when DESC")
        values = {'records' : records} 
        self.response.out.write(
            template.render('mlabns/templates/sliver_tool.html', values))
 
    def site_view(self):  
        records = model.Site.gql('ORDER BY when DESC')
        values = {'records' : records}
        self.response.out.write(
            template.render('mlabns/templates/site.html', values))

    def lookup_view(self):  
        records = model.Lookup.gql('ORDER BY when DESC')
        values = {'records' : records}
        self.response.out.write(
            template.render('mlabns/templates/lookup.html', values))
 
    def send_error(self, error_code=404, message='Error'):
        # 404: Not found.
        self.error(error_code)
        self.response.out.write(message)



