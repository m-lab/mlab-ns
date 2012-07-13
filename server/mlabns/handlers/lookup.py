from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.util import distance
from mlabns.db import model
from mlabns.util import message
from mlabns.util import resolver

import logging
import time

class LookupHandler(webapp.RequestHandler):
    """Redirects an HTTP GET request to the appropriate SliverTool's URL.
    
    Currently, a closest-node policy it's used, which means that the
    geographically closest node will be selected. Future versions might
    implement other policies.
    
    The geolocation data of the client making the request is included
    automatically in the headers by GoogleAppengine:
        -self.request.headers['X-AppEngine-City']
        -self.request.headers['X-AppEngine-Region']
        -self.request.headers['X-AppEngine-Country']
        -self.request.headers['X-AppEngine-CityLatLong']
    
    The url is of the form: 'http://mlab-ns.appspot.com/tool-name', where
    tool-name must be one of the registered tools, e.g:
        GET 'http://mlab-ns.appspot.com/npad'
        GET 'http://mlab-ns.appspot.com/ndt'
    
    By default, the server selection decision is based on the remote IP 
    address of the client, so if it's an IPv4 address only IPv4 nodes 
    will be considered for selection, while the same applies for requests
    from IPv6 addresses.
    In addition, an 'IPv6 only' policy might be enforced, by using an url
    of the form 'http://mlab-ns.appspot.com/tool-name/ipv6'.
    """ 
    def post(self):
        """Not implemented."""
        return self.not_found()
    
    def get(self):
        """Handles an HTTP GET request."""
        
        query = self.get_lookup_query()
        sliver_tool = None
        if (query.policy == message.POLICY_GEO):
            geo_resolver = resolver.GeoResolver()
            sliver_tool = geo_resolver.answer_query(query)
        
        if (query.policy == message.POLICY_METRO):
            metro_resolver = resolver.MetroResolver()
            sliver_tool = metro_resolver.answer_query(query)
        
        if sliver_tool is None:        
            logging.error('No results found for %s.', self.request.path)
            # TODO(claudiu) Use a default url if something goes wrong.
            return self.not_found()
        
        # TODO(claudiu) Remove this, is only for debugging.
        # self.redirect(sliver_tool.url)
        
        self.log_request(query, sliver_tool)
        
        records = []
        records.append(sliver_tool)
        values = {'records' : records}
        self.response.out.write(
            template.render('mlabns/templates/sliver_tool.html', values))
    
    def get_lookup_query(self):
        """Extracts the parameters from the url or query string.
           
        The first part of the url must be the tool_id and all the other
        path's components are treated as boolean flags, enabling some
        policy. Currently only two types of URLs are supported: /tool_id
        for the default policy and /tool_id/ipv6 to specify an IPv6 only
        policy.
        
        Return:
            A LookupQuery containing the lookup parameters.
        """ 
        parts = self.request.path.strip('/').split('/')
        query = resolver.LookupQuery()
        query.tool_id = parts[0]
        
        query.user_ip = self.request.remote_addr
        query.policy = self.request.get(message.POLICY)
        query.metro = self.request.get(message.METRO)
        
        if self.request.headers.has_key(message.COUNTRY):
            query.user_country = self.request.headers[message.COUNTRY]
        if self.request.headers.has_key(message.CITY):
            query.user_city = self.request.headers[message.CITY]
        if self.request.headers.has_key(message.LAT_LONG):
            query.user_lat_long = self.request.headers[message.LAT_LONG]
        
        logging.error('Policy is "%s".', query.policy)
        if not query.policy:
            if query.metro:
                logging.error('Policy metro %s.', query.metro)
                query.policy = message.POLICY_METRO
            else:
                logging.error('Policy geo %s.', query.metro)
                query.policy = message.POLICY_GEO
        
        return query
     
    def has_geolocation_info(self):
        """Verifies if the request has geolocation data.
    
        Return:
            True if the headers contain geolocation information,
            False otherwise.
        """
        if self.request.headers.has_key(message.LAT_LONG):
            return True
        return False
    
    def not_found(self):
        self.error(404)
        self.response.out.write(
            template.render('mlabns/templates/not_found.html', {}))
    
    def send_not_found(self):
        self.error(404)
        self.response.out.write(
            template.render('mlabns/templates/not_found.html', {}))
    
    def log_request(self,  query, sliver_tool):
        """Logs the request.
        
        Args:
            lookup_request: A dict containing the lookup parameters.
            sliver_tool: SliverTool entity chosen in the server 
                selection phase.
        """
        # Retrieve the node from db.
        node = model.Node.get_by_key_name(sliver_tool.node_id)
        
        if node is not None:
            # Log the request to file.
            logging.info(
                '[LOOKUP] \
                tool_id:%s \
                user_ip:%s \
                user_city:%s \
                user_country:%s \
                user_lat_long:%s \
                node_id:%s \
                node_city:%s \
                node_country:%s \
                node_lat_long:%s',
                query.tool_id,
                query.user_ip,
                query.user_city,
                query.user_country,
                query.user_lat_long,
                node.node_id,
                node.city,
                node.country,
                node.lat_long)
            
            # Log the request to db.
            # TOD(claudiu) Add a counter for IPv4 and IPv6.
            lookup_entry = model.Lookup(
                tool_id=query.tool_id,
                policy=query.policy,
                user_ip=query.user_ip,
                user_city=query.user_city,
                user_country=query.user_country,
                user_lat_long=query.user_lat_long,
                node_id=node.node_id,
                node_city=node.city,
                node_country=node.country,
                node_lat_long=node.lat_long,
                key_name=query.user_ip)
            lookup_entry.put()
