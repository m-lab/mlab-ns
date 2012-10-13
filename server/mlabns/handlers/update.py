from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import logging
import time
import urllib2

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import util

AF_IPV4 = 'ipv4'
AF_IPV6 = 'ipv6'

class NagiosUpdateHandler(webapp.RequestHandler):
    """Handles SliverTools updates."""

    def get(self):
        """Triggers the update handler.

        Updates sliver status with information from nagios. The nagios url
        containing the information is stored in the Nagios db along with
        the credentials necessary to access the data.
        """
        nagios = model.Nagios.get_by_key_name(
            constants.DEFAULT_NAGIOS_ENTRY)

        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(
            None, nagios.url, nagios.username, nagios.password)

        authhandler = urllib2.HTTPDigestAuthHandler(password_manager)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

        slices_gql = model.Slice.gql('ORDER by slice_id DESC')
        for item in slices_gql.run(batch_size=constants.GQL_BATCH_SIZE):
            logging.info('Slice is %s', item.tool_id)
            url = nagios.url + '?show_state=1&slice_name=' + item.tool_id
            slice_status = self.get_slice_status(url)
            for sliver_fqdn in slice_status:
                # TODO(claudiu) Ask Stephen to add IPv6 status.
                self.update_sliver_tools_status(
                    item.tool_id, sliver_fqdn,
                    slice_status[sliver_fqdn], AF_IPV4)

    def update_sliver_tools_status(
        self, tool_id, fqdn, status, address_family=AF_IPV4):
        """Updates the sliver tools identified by 'fqdn'.

        Args:
            tool_id: A string representing a tool id.
            fqdn: A string representing the fqdn that resolves
                to an IP address.
            address_family: Addres family, 'ipv4' or 'ipv6'.
            status: A string describing the status: 'online' or 'offline'.
        """
        # Set to 'fqdn_ipv4', 'status_ipv4' if address_family is 'ipv4'
        # or to 'fqdn_ipv6', 'status_ipv6' if address_family if 'ipv6'.
        fqdn_field = 'fqdn_' + address_family
        status_field = 'status_' + address_family

        logging.info('Updating %s to %s', fqdn, status)
        sliver_tools_gql = model.SliverTool.gql(
            'WHERE ' + fqdn_field +' = :fqdn', fqdn=fqdn)

        # We need to loop through the results, since the fqdn alone does
        # not necessarily identifies only one sliver tool (e.g., multiple
        # tools might run on the same sliver).
        sliver_tool_list = []
        for sliver_tool in sliver_tools_gql.run(
                batch_size=constants.GQL_BATCH_SIZE):
            sliver_tool.__dict__[status_field] = status
            sliver_tool.update_request_timestamp = long(time.time())
             # Write changes to db.
            try:
                sliver_tool.put()
                sliver_tool_list.append(sliver_tool)
            except TransactionFailedError:
                # TODO(claudiu) Trigger an event/notification.
                logging.error('Failed to write changes to db.')

        self.update_memcache(sliver_tool_list, tool_id)

    def update_memcache(self, sliver_tool_list, tool_id):
        """Adds these sliver tools to the memcache.

        For each tool, there is a memcache entry containing a list with
        all the sliver tools.

        Args:
            sliver_tool_list: A list of SliverTool instances to be added to the
                memcache.
            tool_id: A string representing a tool id.
        """
        if not memcache.set(tool_id, sliver_tool_list):
            logging.error('Memcache set failed')

    def get_slice_status(self, url):
        """Read slice status from Nagios.

        Args:
            url: String representing the URL to Nagios.

        Returns:
            A dict that contains the status of the slivers in this
            slice.
        """
        status = {}
        try:
            lines = urllib2.urlopen(url).read().strip('\n').split('\n')
            for line in lines:
                # See the design doc for a description of the file format.
                fqdn,state,state_type = line.split(' ')
                status[fqdn] = message.STATUS_ONLINE
                if state == '1':
                    status[fqdn] = message.STATUS_OFFLINE
        except urllib2.HTTPError:
            # TODO(claudiu) Notify(email) when this happens.
            logging.error('Cannot connect to nagios monitoring system.')

        return status
