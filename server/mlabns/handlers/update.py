from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import urllib2

import logging
import time

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import update_message
from mlabns.util import util

class NagiosHandler(webapp.RequestHandler):
    """Handles SliverTools updates."""

    def get(self):
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
                self.update_sliver_tools_status(
                    fqdn, slice_status[server_fqdn])

    def update_sliver_tools_status(self, fqdn, status):
        logging.info('Updating %s to %s', fqdn, status)
        sliver_tools = model.SliverTool.gql(
            'WHERE fqdn = :fqdn',
            fqdn=fqdn).fetch(constants.MAX_FETCHED_RESULTS)

        logging.info('Returned %s records', len(sliver_tools))

        for sliver_tool in sliver_tools:
            logging.info('%s status is %s', fqdn, status)
            sliver_tool.status = status
             # Write changes to db.
            try:
                sliver_tool.put()
            except TransactionFailedError:
                # TODO(claudiu) Trigger an event/notification.
                logging.error('Failed to write changes to db.')
            self.update_memcache(sliver_tool)

    def update_memcache(self, sliver_tool):
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

    def get_slice_status(self, url, username, password, tool_id):
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)

        authhandler = urllib2.HTTPDigestAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

        status = {}
        try:
            lines = urllib2.urlopen(url).read().strip('\n').split('\n')
            for line in lines:
                fqdn,state,hard_state = line.split(' ')
                status[fqdn] = 'online' if state == '0' else 'offline'
        except urllib2.HTTPError:
            logging.error('Cannot connect to nagios monitoring system')

        return status

class UpdateHandler(webapp.RequestHandler):
    """Handles SliverTools updates."""

    def get(self):
        # Not implemented.
        return util.send_not_found(self)

    def post(self):
        dictionary = {}
        for argument in self.request.arguments():
            dictionary[argument] = self.request.get(argument)

        update = update_message.UpdateMessage()
        try:
            update.initialize_from_dictionary(dictionary)
        except message.FormatError, e:
            logging.error('Format error: %s', e)
            return util.send_not_found(self)

        sliver_tool_id = model.get_sliver_tool_id(
            update.tool_id,
            update.slice_id,
            update.server_id,
            update.site_id)
        sliver_tool = model.SliverTool.get_by_key_name(sliver_tool_id)

        if sliver_tool is None:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Unknown sliver_tool_id %s.', sliver_tool_id)
            return util.send_not_found(self)

        signature = update.compute_signature(
            sliver_tool.sliver_tool_key)
        logging.info('key is %s', sliver_tool.sliver_tool_key)
        if (signature != self.request.get(message.SIGNATURE)):
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Bad signature from %s.', sliver_tool_id)
            return util.send_not_found(self)

        # Prevent reply attacks.
        if (update.timestamp <= sliver_tool.update_request_timestamp):
            logging.error(
                'Timestamp in update %s is older than value in db (%s).',
                sliver_tool_id, sliver_tool.update_request_timestamp)
            return util.send_not_found(self)

        # TODO(claudiu) Monitor and log changes in the parameters.
        # TODO(claudiu) Trigger an event or notification.
        sliver_tool.status = update.status
        if update.sliver_ipv4:
            logging.info(
                "Changing IPv4 address from %s to %s.",
                sliver_tool.sliver_ipv4, update.sliver_ipv4)
            sliver_tool.sliver_ipv4 = update.sliver_ipv4
        if update.sliver_ipv6:
            logging.info(
                "Changing IPv6 address from %s to %s.",
                sliver_tool.sliver_ipv6, update.sliver_ipv6)
            sliver_tool.sliver_ipv6 = update.sliver_ipv6
        sliver_tool.url = update.url
        sliver_tool.update_request_timestamp = long(time.time())

        # Write changes to db.
        try:
            sliver_tool.put()
        except TransactionFailedError:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Failed to write changes to db.')

        # Update the memcache.
        sliver_tools = memcache.get(sliver_tool.tool_id)
        if sliver_tools is None:
            sliver_tools = {}

        sliver_tools[sliver_tool_id] = sliver_tool
        if not memcache.set(sliver_tool.tool_id, sliver_tools):
            logging.error('Memcache set failed')

        return util.send_success(self)
