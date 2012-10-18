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
            url = nagios.url + '?show_state=1&service_name=' + item.tool_id

            slice_status = self.get_slice_status(url)
            # TODO(claudiu) Ask Stephen to add IPv6 status.
            self.update_sliver_tools_status(
                slice_status, item.tool_id, AF_IPV4)

    def update_sliver_tools_status(
        self, slice_status, tool_id, address_family):
        """Updates sliver tools status.

        Args:
            slice_status: A dict that contains the status of the
                slivers in the slice {key=fqdn, status:online|offline}
            tool_id: A string representing the fqdn that resolves
                to an IP address.
            address_family: Addres family, 'ipv4' or 'ipv6'.
        """
        # Set to 'status_ipv4' if address_family is 'ipv4'
        # or to 'status_ipv6' if address_family if 'ipv6'.
        status_field = 'status_' + address_family

        sliver_tools_gql = model.SliverTool.gql(
            'WHERE tool_id=:tool_id', tool_id=tool_id)

        sliver_tool_list = []
        for sliver_tool in sliver_tools_gql.run(
            batch_size=constants.GQL_BATCH_SIZE):
            for sliver_fqdn in slice_status:
                is_match = False

                if sliver_tool.fqdn_ipv4 == sliver_fqdn:
                    sliver_tool.status_ipv4 = slice_status[sliver_fqdn]
                    is_match = True
                elif sliver_tool.fqdn_ipv6 == sliver_fqdn:
                    sliver_tool.status_ipv6 = slice_status[sliver_fqdn]
                    is_match = True

                if is_match:
                    sliver_tool.update_request_timestamp = long(time.time())
                    # Write changes to db.
                    try:
                        sliver_tool.put()
                        sliver_tool_list.append(sliver_tool)
                        logging.info(
                            'Updating %s: status is %s.',
                            sliver_fqdn, slice_status[sliver_fqdn])
                    except TransactionFailedError:
                        # TODO(claudiu) Trigger an event/notification.
                        logging.error('Failed to write changes to db.')

        # Never set the memcache to an empty list since it's more likely that
        # this is a Nagios failure.
        if sliver_tool_list:
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
            slice {key=fqdn, status:online|offline}
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
