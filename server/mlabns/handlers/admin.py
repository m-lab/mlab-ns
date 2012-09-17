from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from mlabns.db import model
from mlabns.util import util
from mlabns.util import message

import gflags
import logging

def get_sites_info(sliver_tools, view_status):
    sites = model.Site.gql('ORDER BY site_id DESC')

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
        if view_status == 'ipv4':
            sliver_tool_info['status'] = sliver_tool.status_ipv4
        else:
            sliver_tool_info['status'] = sliver_tool.status_ipv6

        sliver_tool_info['timestamp'] = sliver_tool.when.strftime(
            '%Y-%m-%d %H:%M:%S')
        site_dict[sliver_tool.site_id]['sliver_tools'].append(
            sliver_tool_info)

    for item in site_dict:
        city = site_dict[item]['city']
        sites_per_city[city].append(site_dict[item])

    return sites_per_city


class AdminHandler(webapp.RequestHandler):
    def post(self):
        self.response.out.write(
            "POST OK: message is " +
            self.request.get('a') + self.request.get('b') );

    def get(self):
        view = self.request.get('db')
        path = self.request.path.rstrip('/')
        if not path:
            return self.redirect('/admin/map/ipv4')
        if path == '/admin':
            return self.redirect('/admin/map/ipv4')
        if path == '/admin/map':
            return self.redirect('/admin/map/ipv4')
        if path == '/admin/sites':
            return self.site_view()
        if path == '/admin/sliver_tools':
            return self.sliver_tool_view()
        if path == '/admin/lookup':
            return self.lookup_view()
        if path == '/admin/home':
            return self.redirect('/admin/map/ipv4')
        if path == '/admin/map/ipv4':
            return self.map_view_ipv4()
        if path == '/admin/map/ipv6':
            return self.map_view_ipv6()
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

    def get_sites_info_ipv4(self):
        sliver_tools = model.SliverTool.gql('ORDER BY tool_id DESC')
        return get_sites_info(sliver_tools, view_status='ipv4')

    def get_sites_info_ipv6(self):
        sliver_tools = model.SliverTool.gql('ORDER BY tool_id DESC')
        return get_sites_info(sliver_tools, view_status='ipv6')

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

    def map_view_ipv4(self):
        data = self.get_sites_info_ipv4()
        json_data = simplejson.dumps(data)
        self.response.out.write(
            template.render(
                'mlabns/templates/map_view_ipv4.html', {'cities' : json_data}))

    def map_view_ipv6(self):
        data = self.get_sites_info_ipv6()
        json_data = simplejson.dumps(data)
        self.response.out.write(
            template.render(
                'mlabns/templates/map_view_ipv6.html', {'cities' : json_data}))

    def lookup_view(self):
        records = model.Lookup.gql('ORDER BY when DESC')
        values = {'records' : records}
        self.response.out.write(
            template.render('mlabns/templates/lookup.html', values))


class MapViewHandler(webapp.RequestHandler):
    def post(self):
        return util.send_not_found(self)

    def get(self):
        parts = self.request.path.strip('/').split('/')
        tool_id = parts[len(parts) -1]

        sliver_tools = None
        cached_sliver_tools = memcache.get(tool_id)
        if cached_sliver_tools:
            sliver_tools = cached_sliver_tools.values()
        else:
            sliver_tools = model.SliverTool.gql(
                'WHERE tool_id=:tool_id '
                'ORDER BY tool_id DESC',
                tool_id=tool_id)

        if not sliver_tools:
            return util.send_not_found(self)

        view_status = 'ipv4'
        if 'ipv6' in parts:
            view_status = 'ipv6'

        data = get_sites_info(sliver_tools, view_status)

        json_data = simplejson.dumps(data)
        file_name = '' . join([
            'mlabns/templates/', tool_id, '_map_view_', view_status, '.html'])
        self.response.out.write(
            template.render(file_name, {'cities' : json_data}))
