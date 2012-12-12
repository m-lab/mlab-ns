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
            for family in ['', '_ipv6']:
              url = nagios.url + '?show_state=1&service_name=' + \
                    item.tool_id + family

              slice_status = self.get_slice_status(url)
              self.update_sliver_tools_status(slice_status, item.tool_id,
                                              family)

    def update_sliver_tools_status(self, slice_status, tool_id, family):
        """Updates sliver tools status.

        Args:
            slice_status: A dict that contains the status of the
                slivers in the slice {key=fqdn, status:online|offline}
            tool_id: A string representing the fqdn that resolves
                to an IP address.
        """

        sliver_tools_gql = model.SliverTool.gql('WHERE tool_id=:tool_id',
                                                tool_id=tool_id)

        sliver_tool_list = []
        for sliver_tool in sliver_tools_gql.run(
            batch_size=constants.GQL_BATCH_SIZE):
            for sliver_fqdn in slice_status:
                is_match = False

                if sliver_tool.fqdn == sliver_fqdn:
                    is_match = True
                    if family == '':
                        # Set offline if we don't have a valid IP address for
                        # the slice.
                        if sliver_tool.sliver_ipv4 == 'off':
                            logging.warning('Setting IPv4 status for %s ' \
                                'offline due to missing IP address.',
                                sliver_fqdn)
                            slice_status[sliver_fqdn] = message.STATUS_OFFLINE
                        sliver_tool.status_ipv4 = slice_status[sliver_fqdn]
                    elif family == '_ipv6':
                        # Set offline if we don't have a valid IP address for
                        # the slice.
                        if sliver_tool.sliver_ipv6 == 'off':
                            logging.warning('Setting IPv6 status for %s ' \
                                'offline due to missing IP address.',
                                sliver_fqdn)
                            slice_status[sliver_fqdn] = message.STATUS_OFFLINE
                        sliver_tool.status_ipv6 = slice_status[sliver_fqdn]
                    else:
                        logging.error('Unexpected family: %s', family)

                if is_match:
                    sliver_tool.update_request_timestamp = long(time.time())
                    # Write changes to db.
                    try:
                        sliver_tool.put()
                        sliver_tool_list.append(sliver_tool)
                        logging.info('Updating %s: status is %s.',
                                     sliver_fqdn, slice_status[sliver_fqdn])
                    except TransactionFailedError:
                        # TODO(claudiu) Trigger an event/notification.
                        logging.error('Failed to write changes to db.')

        # Never set the memcache to an empty list since it's more likely that
        # this is a Nagios failure.
        if sliver_tool_list:
            if not memcache.set(tool_id, sliver_tool_list,
                                namespace=constants.MEMCACHE_NAMESPACE_TOOLS):
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
                if len(line) == 0:
                    continue
                # See the design doc for a description of the file format.
                slice_fqdn,state,state_type = line.split(' ')
                sliver_fqdn, tool_id = slice_fqdn.split('/')
                status[sliver_fqdn] = message.STATUS_ONLINE
                if state != constants.NAGIOS_SERVICE_STATUS_OK:
                    status[sliver_fqdn] = message.STATUS_OFFLINE
        except urllib2.HTTPError:
            # TODO(claudiu) Notify(email) when this happens.
            logging.error('Cannot connect to nagios monitoring system.')

        return status
