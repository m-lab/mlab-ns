from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import distance

import logging
import random
import time

class LookupQuery:
    def __init__(self):
        self.tool_id = ""
        self.policy = ""
        self.metro = ""
        self.user_ip = ""
        self.user_city = ""
        self.user_country = ""
        self.user_lat_long = ""

class GeoResolver:
    """Implements the closest-node policy."""
    
    def get_sliver_tool_candidates(self, lookup_query):
        """Find candidates for server selection.
        
        Select all the sliver tools that match the requirements
        for the policy specified in the request.Currently only
        the 'geo' policy is implemented, so all the sliver tools
        available that match the 'tool_id' will be selected.
        Looks only for SliverTool entities that are online, and who
        recently updated their status.
        
        Return:
            A list of SliverTool entities.
        """        
        
        oldest_timestamp = long(time.time()) - constants.UPDATE_INTERVAL
        candidates = model.SliverTool.gql(
            "WHERE tool_id = :tool_id "
            "AND status = 'online' "
            "AND timestamp > :timestamp ",
            tool_id=lookup_query.tool_id,
            timestamp=oldest_timestamp)
            # TODO (claudiu) Check ipv6/ipv4.
        return candidates.fetch(constants.MAX_FETCHED_RESULTS) 
    
    def answer_query(self, query):
        """Select the geographically closest sliver tool.
        
        Args:
            sliver_tools: A list of SliverTool entities that match the
                requirements of the request.
        
        Return:
            A SliverTool entity that best matches the request.
        """
        sliver_tools = self.get_sliver_tool_candidates(query)
        
        logging.info('Found %s results.', len(sliver_tools))
        if not sliver_tools:
            logging.error('No results found for %s.', query.tool_id)
            return None
        
        if not query.user_lat_long:
            logging.error('No results found for %s.', query.tool_id)
            return sliver_tools[0]
        
        min_distance = float('+inf')
        nodes = []
        distances = {}
        
        # Compute for each sliver_tool the distance and update the
        # best match if the distance is less that the current minimum.
        # To avoid computing the distances twice, cache the results in
        # a dict.
        for sliver_tool in sliver_tools:
            # Check if we already computed this distance.
            if (distances.has_key(sliver_tool.lat_long)):
                current_distance = distances[sliver_tool.lat_long]
            else:
                # Compute the distance.
                current_distance = distance.distance(
                    query.user_lat_long,
                    sliver_tool.lat_long)
                
                # Add the distance to the dict.
                distances[sliver_tool.lat_long] = current_distance
            
            if (current_distance <= min_distance):
                min_distance = current_distance
                nodes.insert(0, sliver_tool)
        
        closest_nodes = []
        for node in nodes:
            if distances[node.lat_long] <= min_distance * constants.EPSILON:
                closest_nodes.append(node)
            else:
                break
        
        return random.choice(closest_nodes)

class MetroResolver:
    """Implements the metro policy."""
    
    def answer_query(self, query):
        """Select the sliver tool that best matches the requirements.
        
        Select all the sliver tools that match the 'metro' requirements
        specified in the request, order the results by timestamp and
        return the first result.
        
        Return:
            A SliverTool entity if available, or None.
        """        
        
        nodes = model.Node.all().filter("metro =", query.metro).fetch(
            constants.MAX_FETCHED_RESULTS)
        
        logging.info('No result found for metro %s.', len(nodes))
        if len(nodes) == 0:
            logging.info('No result found for metro %s.', query.metro)
            return None
        
        node_id_list = []
        for node in nodes:
            node_id_list.append(node.node_id)
        
        oldest_timestamp = long(time.time()) - constants.UPDATE_INTERVAL
        candidates = model.SliverTool.gql(
            "WHERE tool_id = :tool_id "
            "AND status = 'online' "
            "AND timestamp > :timestamp "
            "AND node_id in :node_id_list ",
            tool_id=query.tool_id,
            timestamp=oldest_timestamp,
            node_id_list=node_id_list).fetch(constants.MAX_FETCHED_RESULTS)
            # TODO (claudiu) Check ipv6/ipv4.
        
        if not candidates:
            return None
        
        return random.choice(candidates)
