from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import logging
import time
import urllib2

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import util

class NagiosUpdateHandler(webapp.RequestHandler):
    """Handles SliverTools updates."""

    def get(self):
        """Triggers the update handler.

        Updates sliver status with information from nagios. The nagios url
        containing the information is stored in the Nagios db along with
        the credentials necessary to access the data.

        """
        nagios = model.Nagios.get_by_key_name('default')
        mlab_slices = model.Slice.gql(
            'ORDER by slice_id DESC').fetch(constants.MAX_FETCHED_RESULTS)

        for mlab_slice in mlab_slices:
            slice_parts =  mlab_slice.slice_id.split('_')
            url = nagios.url + '?show_state=1&slice=' + mlab_slice.slice_id
            slice_status = self.get_slice_status(
                url, nagios.username, nagios.password, mlab_slice.tool_id)
            for server_fqdn in slice_status:
                fqdn = '.'.join([
                    slice_parts[1],
                    slice_parts[0],
                    server_fqdn])
                self.update_sliver_tools_status_ipv4(
                    fqdn, slice_status[server_fqdn])

    def update_sliver_tools_status_ipv4(self, fqdn_ipv4, status):
        """Updates the sliver tools identified by fqdn_ipv4.

        Note that the fqdn alone does not necessarily identifies only
        one sliver tool, since multiple tools might run on the same
        sliver.

        Args:
            fqdn_ipv4: A string representing the fqdn that resolves
                to an IPv4 address.
            status: A string describing the status: 'online' or 'offline'.

        """
        logging.info('Updating %s to %s', fqdn_ipv4, status)
        sliver_tools = model.SliverTool.gql(
            'WHERE fqdn_ipv4 = :fqdn_ipv4',
            fqdn_ipv4=fqdn_ipv4).fetch(constants.MAX_FETCHED_RESULTS)

        logging.info('Returned %s records', len(sliver_tools))

        for sliver_tool in sliver_tools:
            logging.info('%s status is %s', fqdn_ipv4, status)
            sliver_tool.status_ipv4 = status
            sliver_tool.update_request_timestamp = long(time.time())
             # Write changes to db.
            try:
                sliver_tool.put()
            except TransactionFailedError:
                # TODO(claudiu) Trigger an event/notification.
                logging.error('Failed to write changes to db.')
            self.update_memcache(sliver_tool)


    def update_sliver_tools_status_ipv6(self, fqdn_ipv6, status):
        """Updates the sliver tools identified by fqdn_ipv6.

        Note that the fqdn alone does not necessarily identifies only
        one sliver tool, since multiple tools might run on the same
        sliver.

        Args:
            fqdn_ipv6: A string representing the fqdn that resolves
                to an IPv6 address.
            status: A string describing the status: 'online' or 'offline'.

        """
        logging.info('Updating %s to %s', fqdn_ipv6, status)
        sliver_tools = model.SliverTool.gql(
            'WHERE fqdn_ipv6 = :fqdn_ipv6',
            fqdn_ipv6=fqdn_ipv6).fetch(constants.MAX_FETCHED_RESULTS)

        logging.info('Returned %s records', len(sliver_tools))

        for sliver_tool in sliver_tools:
            logging.info('%s status is %s', fqdn_ipv6, status)
            sliver_tool.status_ipv6 = status
            sliver_tool.update_request_timestamp = long(time.time())
             # Write changes to db.
            try:
                sliver_tool.put()
            except TransactionFailedError:
                # TODO(claudiu) Trigger an event/notification.
                logging.error('Failed to write changes to db.')
            self.update_memcache(sliver_tool)

    def update_memcache(self, sliver_tool):
        """Adds this sliver tool to the memcache.

        For each tool, there is a memcache entry containing a dict with
        all the sliver tools. Each entry in the dict is a pair of the type
        (key = sliver_tool_id, value = SliverTool instance).

        Args:
            sliver_tool: A SliverTool instance to be added to the memcache.
        """
        sliver_tool_id = model.get_sliver_tool_id(
            sliver_tool.tool_id,
            sliver_tool.slice_id,
            sliver_tool.server_id,
            sliver_tool.site_id)

        # Retrieve the sliver tools from memcache.
        sliver_tools = memcache.get(sliver_tool.tool_id)
        if sliver_tools is None:
            sliver_tools = {}

        sliver_tools[sliver_tool_id] = sliver_tool
        if not memcache.set(sliver_tool.tool_id, sliver_tools):
            logging.error('Memcache set failed')

    def get_slice_status(self, url, username, password, slice_id):
        """Read slice status from Nagios.

        Args:
            url: String representing the URL to Nagios.
            username: Nagios username.
            password: Nagios password.
            slice_id: String representing the name of slice.

        Returns:
            A dict that contains the status of the slivers in this
            slice.
        """
        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, url, username, password)

        authhandler = urllib2.HTTPDigestAuthHandler(password_manager)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

        status = {}
        try:
            lines = urllib2.urlopen(url).read().strip('\n').split('\n')
            for line in lines:
                fqdn,state,hard_state = line.split(' ')
                status[fqdn] = 'online' if state == '0' else 'offline'
        except urllib2.HTTPError:
            # TODO(claudiu) Notify(email) when this happens.
            logging.error('Cannot connect to nagios monitoring system.')

        return status
