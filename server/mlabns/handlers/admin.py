from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from mlabns.util import constants
from mlabns.db import model
from mlabns.util import util
from mlabns.util import message

import gflags
import logging

class AdminHandler(webapp.RequestHandler):
    def post(self):
        """Not implemented."""
        return util.send_not_found(self)

    def get(self):
        path = self.request.path.rstrip('/')
        if not path or path == '/admin' or path == '/admin/map':
            return self.redirect('/admin/map/ipv4/all')

        parts = self.request.path.strip('/').split('/')

        # http://mlabns.appspot.com/admin/sites
        if 'sites' in parts:
            return self.site_view()

        # http://mlabns.appspot.com/admin/sliver_tools
        if 'sliver_tools' in parts:
            return self.sliver_tool_view()

        # http://mlabns.appspot.com/admin/cache?tool=tool_id
        # TODO (claudiu) This is for debug only.
        if 'cache' in parts:
            return self.cache_view()

        # http://mlabns.appspot.com/admin/map/*
        if 'map' in parts:
            tool_id = parts[len(parts) - 1]
            view_status = 'ipv4'
            if 'ipv6' in parts:
                view_status = 'ipv6'
            return self.map_view(tool_id, view_status)

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

    def map_view(self, tool_id, view_status):
        sliver_tools = None

        if tool_id == 'all':
            sliver_tools = model.SliverTool.gql('ORDER BY tool_id DESC')
        else:
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

        data = self.get_sites_info(sliver_tools, view_status)
        json_data = simplejson.dumps(data)
        file_name = '' . join([
            'mlabns/templates/', tool_id, '_map_view_', view_status, '.html'])
        self.response.out.write(
            template.render(file_name, {'cities' : json_data}))

    def get_sites_info(self, sliver_tools, view_status):
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


