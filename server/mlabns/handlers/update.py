from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import logging
import time

from mlabns.db import model
from mlabns.util import message
from mlabns.util import sign

class UpdateHandler(webapp.RequestHandler):
    """Handles SliverTools updates.
    
    Updates are keep-alive messages that the clients must send regularly
    send to the GAE server. This is needed to ensure that only the servers
    who are up and running will be considered in a lookup request as 
    candidates for server selection.
    
    The handler accepts requests at http://mlab-ns.appspot.com/update, 
    with the following arguments:
    
    node_id=[mlab node id, e.g. mlab1.atl01.measurement-lab.org]
    tool_id=[tool id or tool name, e.g. npad]
    tool_sliver_id=[a unique id for this instance of the tool]
    sliver_ipv4=[IPv4 address of the sliver|none]
    sliver_ipv6=[IPv6 address of the sliver|none]
    url=[Full URL to the tool running on the sliver]
    status=[online|offline|other errors]
    timestamp=[UTC timestamp in seconds]
    sign=[signature of this request, using the shared key]
    
    When an update request arrives, the server first checks that the IP
    address of the sender is one of the MLab nodes and then verifies the
    signature of the request. The request will be processed only if both
    checks succeed.
    """
    
    def check_signature(self, sliver_tool):
        """Checks the integrity of the data in the update message.
        
        Args:
            sliver_tool: The SliverTool entity sending the update. A dict
                containing all the data that describes an instance of a
                tool running on the sliver.
        
        Return:
            True if the signature is correct and False otherwise.
        """
        data = {}
        for argument in self.request.arguments():
            data[argument] = self.request.get(argument)
        
        if not data.has_key(message.SIGNATURE):
            logging.error('Updates is not signed.')
            return False
        
        signature = data[message.SIGNATURE]
        data[message.SIGNATURE] = ''
        expected_signature = sign.sign_message(
            data,
            sliver_tool.sliver_tool_key)
        logging.info(
            'Checking (key = %s) signature = %s,expected = %s',
            sliver_tool.sliver_tool_key,
            signature,
            expected_signature)
        return (signature == expected_signature)
    
    def process_request(self, sliver_tool):
        """Updates the status of the SliverTool.
        
        The following attributes may change between consecutive updates:
            - status: e.g. changed from online to offline.
            - sliver_ipv4: e.g. the ipv4 interface is down.
            - sliver_ipv6: e.g. the ipv6 interface is down.
            - url: e.g. the port might have changed.
        
        Args:
            sliver_tool: The SliverTool entity sending the update. A dict
                containing all the data that describes an instance of
                a tool running on the sliver.
        """
        
        # TODO(claudiu) Monitor and log changes in the parameters.
        # TODO(claudiu) Trigger an event/notification.
        sliver_tool.status = self.request.get(
            message.STATUS)
        sliver_tool.sliver_ipv4 = self.request.get(
            message.SLIVER_IPv4)
        sliver_tool.sliver_ipv6 = self.request.get(
            message.SLIVER_IPv6) 
        sliver_tool.url = self.request.get(
            message.URL)
        sliver_tool.timestamp = long(time.time())
        
        # Write changes to db.
        sliver_tool.put()
    
    def get(self):
        # Not implemented.
        self.send_not_found()
    
    def post(self):
        
        sliver_tool_id = "". join(
            [self.request.get(message.TOOL_ID), 
            self.request.get(message.SLICE_ID),
            self.request.get(message.SERVER_ID),
            self.request.get(message.SITE_ID)])
        sliver_tool = model.SliverTool.get_by_key_name(sliver_tool_id)
        
        if sliver_tool is None:
            # TODO(claudiu) Trigger an event/notification.
            logging.error(
                'Bad sliver_tool_id %s.',
                sliver_tool_id)
            return self.send_error(401)
        if not self.check_signature(sliver_tool):
            # TODO(claudiu) Trigger an event/notification.
            logging.error(
                'Bad signature from %s.', 
                sliver_tool_id)
            return self.send_error(401)
        
        self.process_request(sliver_tool)
        self.send_success()
    
    def send_error(self, error_code=404):
        # 404: Not found.
        self.error(error_code)
        self.response.out.write(message.ERROR)
    
    def send_not_found(self):
        self.error(404)
        self.response.out.write(
            template.render('mlabns/templates/not_found.html', {}))
    
    def send_success(self):
        self.response.out.write(message.SUCCESS)
