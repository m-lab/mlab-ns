from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from mlabns.db import model
from mlabns.util import util
from mlabns.util import message

import logging

class AdminHandler(webapp.RequestHandler):
    def post(self):
        self.response.out.write(
            "POST OK: message is " +
            self.request.get('a') + self.request.get('b') );

    def get(self):
        view = self.request.get('db')
        path = self.request.path.rstrip('/')
        if path == '/admin':
            return self.map_view()
        if path == '/admin/sites':
            return self.site_view()
        if path == '/admin/sliver_tools':
            return self.sliver_tool_view()
        if path == '/admin/lookup':
            return self.lookup_view()
        if path == '/admin/home':
            return self.redirect('/admin')
        if path == '/admin/map':
            return self.redirect('/admin')
        if path == '/admin/cache':
            return self.cache_view()


        return util.send_not_found(self)

    def sliver_tool_view(self):
        records = model.SliverTool.gql("ORDER BY tool_id DESC")
        values = {'records' : records}
        self.response.out.write(
            template.render('mlabns/templates/sliver_tool.html', values))

    def cache_view(self):
        tool_id = self.request.get(message.TOOL_ID)
        records = memcache.get(tool_id).values()
        values = {'records' : records}
        self.response.out.write(
            template.render('mlabns/templates/sliver_tool.html', values))

    def site_view(self):
        headers = [
            'Site ID',
            'City',
            'Country',
            'Latitude',
            'Longitude',
            'Metro',
            'When']

        records = model.Site.gql('ORDER BY site_id DESC')
        values = {'records' : records, 'headers': headers}
        self.response.out.write(
            template.render('mlabns/templates/site.html', values))

    def get_sites_info(self):
        sites = model.Site.gql('ORDER BY site_id DESC')
        sliver_tools = model.SliverTool.gql('ORDER BY tool_id DESC')

        site_dict = {}
        sites_per_city = {}
        for site in sites:
            site_info = {}
            site_info['site_id'] = site.site_id
            site_info['city'] = site.city
            site_info['country'] = site.country
            site_info['latitude'] = site.latitude
            site_info['longitude'] = site.longitude
            site_info['sliver_tools'] = []
            site_dict[site.site_id] = site_info
            sites_per_city[site.city] = []

        # Add sliver tools info to the sites.
        for sliver_tool in sliver_tools:
            sliver_tool_info = {}
            sliver_tool_info['slice_id'] = sliver_tool.slice_id
            sliver_tool_info['tool_id'] = sliver_tool.tool_id
            sliver_tool_info['server_id'] = sliver_tool.server_id
            sliver_tool_info['status'] = sliver_tool.status
            sliver_tool_info['timestamp'] = sliver_tool.when.strftime(
                '%Y-%m-%d %H:%M:%S')
            site_dict[sliver_tool.site_id]['sliver_tools'].append(
                sliver_tool_info)

        for item in site_dict:
            city = site_dict[item]['city']
            sites_per_city[city].append(site_dict[item])

        return sites_per_city

    def home_view(self):
        sites = model.Site.gql('ORDER BY site_id DESC')

        records = []
        for site in sites:
            record = {}
            record['site_id'] = site.site_id
            record['city'] = site.city
            record['country'] = site.country
            record['latitude'] = site.latitude
            record['longitude'] = site.longitude
            records.append(record)

        json_data = simplejson.dumps(records)
        self.response.out.write(
            template.render(
                'mlabns/templates/home.html', {'sites' : json_data}))

    def map_view(self):
        data = self.get_sites_info()
        json_data = simplejson.dumps(data)
        self.response.out.write(
            template.render(
                'mlabns/templates/map_view.html', {'cities' : json_data}))

    def lookup_view(self):
        records = model.Lookup.gql('ORDER BY when DESC')
        values = {'records' : records}
        self.response.out.write(
            template.render('mlabns/templates/lookup.html', values))

