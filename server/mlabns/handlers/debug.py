from django.utils import simplejson

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.db import model
from mlabns.util  import util
from mlabns.util import message
from mlabns.util import resolver
from mlabns.util.geo import maxmind

import logging
import time

class DebugHandler(webapp.RequestHandler):
    """Returns info of the server this client would be redirected to."""

    def post(self):
        """Not implemented."""
        return util.send_not_found(self)

    def get(self):
        """Handles an HTTP GET request.

        Returns the server where the user would be redirected
        if a lookup request was made from this IP address.
        """

        logging.info('Path is %s', self.request.path)
        logging.info('Path is %s', self.request.path.lstrip('/info'))
        parts = self.request.path.strip('/').split('/')

        lookup_query = resolver.LookupQuery()
        if (parts[0] == 'geo'):
            ip_address = self.request.get(message.REMOTE_ADDRESS);
            geo_record = maxmind.get_ip_geolocation(ip_address);
            lookup_query.city = geo_record.city
            lookup_query.country = geo_record.country
            lookup_query.latitude = geo_record.latitude
            lookup_query.longitude = geo_record.longitude
            lookup_query.ip_address = ip_address
        else:
            lookup_query.initialize_from_http_request(self.request)

        lookup_query.tool_id = parts[1]

        sliver_tool = None
        if lookup_query.metro:
            metro_resolver = resolver.MetroResolver()
            sliver_tool = metro_resolver.answer_query(lookup_query)
        elif lookup_query.policy_geo:
            geo_resolver = resolver.GeoResolver()
            sliver_tool = geo_resolver.answer_query(lookup_query)

        if sliver_tool is None:
            logging.error('No results found for %s.', self.request.path)
            # TODO(claudiu) Use a default url if something goes wrong.
            return util.send_not_found(self)

        # TODO(claudiu) Move this in util.py.
        self.log_request(lookup_query, sliver_tool)

        if lookup_query.latitude == 0.0:
            lookup_query.city = "Rome"
            lookup_query.country = "Italy"
            lookup_query.latitude = 41.9000
            lookup_query.longitude = 12.500

        if lookup_query.latitude != 0.0:
            return self.send_map_view(sliver_tool, lookup_query)
        return self.send_html_view(sliver_tool)

    def send_map_view(self, sliver_tool, lookup_query):

        # Destination site.
        site = model.Site.get_by_key_name(sliver_tool.site_id)
        if site is None:
            return self.send_html_view(sliver_tool)

        destination_site = {}
        destination_site['site_id'] = site.site_id
        destination_site['city'] = site.city
        destination_site['country'] = site.country
        destination_site['latitude'] = site.latitude
        destination_site['longitude'] = site.longitude
        destination_site['url'] = sliver_tool.url
        destination_site['info'] = '<div id=siteShortInfo>' + \
            '<h2>' + site.city + "," + site.country + '</h2>' + \
            '<a class="footer" href=' + sliver_tool.url + '>' + \
            sliver_tool.url + '</a></div>';

        # Get the list af all other sites.
        sites = model.Site.gql('ORDER BY site_id DESC')
        site_list = []
        for site in sites:
            if site.site_id != destination_site['site_id']:
                record = {}
                record['site_id'] = site.site_id
                record['city'] = site.city
                record['country'] = site.country
                record['latitude'] = site.latitude
                record['longitude'] = site.longitude
                site_list.append(record)

        user_info = {}
        user_info['city'] = lookup_query.city
        user_info['country'] = lookup_query.country
        user_info['latitude'] = lookup_query.latitude
        user_info['longitude'] = lookup_query.longitude

        site_list_json = simplejson.dumps(site_list)
        destination_site_json = simplejson.dumps(destination_site)
        user_info_json = simplejson.dumps(user_info)

        self.response.out.write(
            template.render(
                'mlabns/templates/lookup_map.html',
                {
                    'sites' : site_list_json,
                    'user' : user_info_json,
                    'destination' : destination_site_json
                }))

    def send_html_view(self, sliver_tool):
        records = [sliver_tool]
        self.response.out.write(
            template.render(
                'mlabns/templates/info.html', {'records' : records}))

    def log_request(self,  query, sliver_tool):
        """Logs the request.

        Args:
            query: A LookupQuery instance.
            sliver_tool: SliverTool entity chosen in the server
                selection phase.
        """
        site = model.Site.get_by_key_name(sliver_tool.site_id)

        if site is not None:
            # Log the request to file.
            # Log the request to db.
            # TOD(claudiu) Add a counter for IPv4 and IPv6.
            lookup_entry = model.Lookup(
                tool_id=query.tool_id,
                policy=query.policy,
                user_ip=query.ip_address,
                user_city=query.city,
                user_country=query.country,
                user_latitude=query.latitude,
                user_longitude=query.longitude,
                slice_id=sliver_tool.slice_id,
                server_id=sliver_tool.server_id,
                site_id=site.site_id,
                site_city=site.city,
                site_country=site.country,
                site_latitude=site.latitude,
                site_longitude=site.longitude,
                key_name=query.ip_address)
            lookup_entry.put()

class SearchHandler(webapp.RequestHandler):
    """Returns info of the server this client would be redirected to."""

    def post(self):
        """Not implemented."""
        return util.send_not_found(self)

    def get(self):
        """Handles an HTTP GET request.

        Returns the server where the user would be redirected
        if a lookup request was made from this IP address.
        """

        logging.info('Path is %s', self.request.path)
        logging.info('Path is %s', self.request.path.lstrip('/info'))
        parts = self.request.path.strip('/').split('/')

        city = self.request.get(message.CITY)

        if not city:
            return util.send_not_found(self)

        location = model.MaxmindCityLocation.gql(
            'WHERE city= :city', city=city).get()

        city_name = 'Not found'
        country_name = 'Not found'

        if location:
            city_name = location.city
            country_name = location.country
        """

        country_name = 'Not found'
        start = 1
        end = 366000
        num_lookups = 0
        logging.info('searching for city %s', city)
        count = 0
        while (start <= end):
            mid = (end + start)/2
            location = model.MaxmindCityLocation.get_by_key_name(
                str(mid))
            count += 1
            if (count == 8):
                break
            if not location:
                break
            num_lookups += 1
            if (mid < city):
                start = mid + 1
            elif (mid > city):
                end = mid - 1
            else:
                city_name = location.city
                country_name = location.country
                break
        """
        self.response.out.write(city_name +"," + country_name)
