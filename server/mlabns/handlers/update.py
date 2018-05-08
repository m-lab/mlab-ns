import json
import logging
import time
import urllib2

from google.appengine.api import app_identity
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp

from mlabns.db import model
from mlabns.db import nagios_config_wrapper
from mlabns.db import prometheus_config_wrapper
from mlabns.db import sliver_tool_fetcher
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import nagios_status
from mlabns.util import prometheus_status
from mlabns.util import production_check
from mlabns.util import util


class SiteRegistrationHandler(webapp.RequestHandler):
    """Registers new sites from Nagios."""

    # Message fields
    SITE_FIELD = 'site'
    METRO_FIELD = 'metro'
    CITY_FIELD = 'city'
    COUNTRY_FIELD = 'country'
    LAT_FIELD = 'latitude'
    LON_FIELD = 'longitude'
    ROUNDROBIN_FIELD = 'roundrobin'

    REQUIRED_FIELDS = [SITE_FIELD, METRO_FIELD, CITY_FIELD, COUNTRY_FIELD,
                       LAT_FIELD, LON_FIELD, ROUNDROBIN_FIELD]
    SITE_LIST_URL = 'https://storage.googleapis.com/operator-mlab-oti/metadata/v0/current/mlab-site-stats.json'
    TESTING_SITE_LIST_URL = 'https://storage.googleapis.com/operator-mlab-sandbox/metadata/v0/current/mlab-site-stats.json'

    @classmethod
    def _is_valid_site(cls, site):
        """Determines whether a site represents a valid, production M-Lab site.

        Args:
            site: A dictionary representing info for a particular site as it
            appears on Nagios.

        Returns:
            True if the site is a valid, production M-Lab site.
        """
        # TODO(claudiu) Need more robust validation.
        for field in cls.REQUIRED_FIELDS:
            if field not in site:
                logging.error('%s does not have the required field %s.',
                              json.dumps(site), field)
                return False

        if not production_check.is_production_site(site[cls.SITE_FIELD]):
            logging.info('Ignoring non-production site: %s',
                         site[cls.SITE_FIELD])
            return False
        return True

    def get(self):
        """Triggers the registration handler.

        Checks if new sites were added to Nagios and registers them.
        """
        try:
            project = app_identity.get_application_id()
            if project == 'mlab-nstesting':
                json_file = self.TESTING_SITE_LIST_URL
            else:
                json_file = self.SITE_LIST_URL
        except AttributeError:
            logging.error('Cannot get project name.')
            return util.send_not_found(self)

        try:
            sites_json = json.loads(urllib2.urlopen(json_file).read())
        except urllib2.HTTPError:
            # TODO(claudiu) Notify(email) when this happens.
            logging.error('Cannot open %s.', json_file)
            return util.send_not_found(self)
        except (TypeError, ValueError) as e:
            logging.error('The json format of %s in not valid: %s', json_file,
                          e)
            return util.send_not_found(self)

        site_ids = set()

        # Validate the site data.
        valid_sites_json = []
        for site in sites_json:
            if not self._is_valid_site(site):
                continue
            valid_sites_json.append(site)
            site_ids.add(site[self.SITE_FIELD])

        mlab_site_ids = set()
        mlab_sites = model.Site.all()
        for site in mlab_sites:
            mlab_site_ids.add(site.site_id)

        unchanged_site_ids = site_ids.intersection(mlab_site_ids)
        new_site_ids = site_ids.difference(mlab_site_ids)

        # Do not remove sites here for now.

        for site in valid_sites_json:
            # Register new site AND update an existing site anyway.
            if (site[self.SITE_FIELD] in new_site_ids) or (
                    site[self.SITE_FIELD] in unchanged_site_ids):
                if site[self.SITE_FIELD] in new_site_ids:
                    logging.info('Add new site %s.', site[self.SITE_FIELD])
                # TODO(claudiu) Notify(email) when this happens.
                if not self.update_site(site):
                    logging.error('Error updating site %s.',
                                  site[self.SITE_FIELD])
                    continue
        # call check_ip job at the end of check_site job
        IPUpdateHandler().get()

        return util.send_success(self)

    def update_site(self, site):
        """Add a new site or update an existing site.

        Args:
            site: A json representing the site info.

        Returns:
            True if the registration succeeds, False otherwise.
        """
        try:
            lat_long = float(site[self.LAT_FIELD])
            lon_long = float(site[self.LON_FIELD])
        except ValueError:
            logging.error('Geo coordinates are not float (%s, %s)',
                          site[self.LAT_FIELD], site[self.LON_FIELD])
            return False
        site = model.Site(site_id=site[self.SITE_FIELD],
                          city=site[self.CITY_FIELD],
                          country=site[self.COUNTRY_FIELD],
                          latitude=lat_long,
                          longitude=lon_long,
                          metro=site[self.METRO_FIELD],
                          registration_timestamp=long(time.time()),
                          key_name=site[self.SITE_FIELD],
                          roundrobin=site[self.ROUNDROBIN_FIELD])

        try:
            site.put()
        except db.TransactionFailedError:
            # TODO(claudiu) Trigger an event/notification.
            logging.error('Failed to write site %s to datastore.', site.site_id)
            return False
        logging.info('Succeeded to write site %s to db', site.site_id)

        tools = model.Tool.all()
        for tool in tools:
            for server_id in ['mlab1', 'mlab2', 'mlab3']:
                fqdn = model.get_fqdn(tool.slice_id, server_id, site.site_id)
                if fqdn is None:
                    logging.error('Cannot compute fqdn for slice %s.',
                                  tool.slice_id)
                    continue

                sliver_tool = IPUpdateHandler().initialize_sliver_tool(
                    tool, site, server_id, fqdn)
                if not memcache.set(
                        tool.tool_id,
                        sliver_tool,
                        namespace=constants.MEMCACHE_NAMESPACE_TOOLS):
                    logging.error(
                        'Failed to update sliver IP addresses in memcache.')
                try:
                    sliver_tool.put()
                    logging.info('Succeeded to write sliver %s to datastore.',
                                 fqdn)
                except db.TransactionFailedError:
                    logging.error('Failed to write sliver %s to datastore.',
                                  fqdn)
                    continue

        return True


class IPUpdateHandler(webapp.RequestHandler):
    """Updates SliverTools' IP addresses."""

    # TODO: There should eventually be a TESTING_IP_LIST_URL for testing purpose.
    IP_LIST_URL = 'https://storage.googleapis.com/operator-mlab-oti/metadata/v0/current/mlab-host-ips.txt'

    def get(self):
        """Triggers the update handler.

        Updates sliver tool IP addresses.
        """
        lines = []
        try:
            lines = urllib2.urlopen(self.IP_LIST_URL).read().strip('\n').split(
                '\n')
        except urllib2.HTTPError:
            # TODO(claudiu) Notify(email) when this happens.
            logging.error('Cannot open %s.', self.IP_LIST_URL)
            return util.send_not_found(self)

        sliver_tool_list = {}
        for line in lines:
            # Expected format: "FQDN,IPv4,IPv6" (IPv6 can be an empty string).
            line_fields = line.split(',')
            if len(line_fields) != 3:
                logging.error('Line does not have 3 fields: %s.', line)
                continue
            fqdn = line_fields[0]
            ipv4 = line_fields[1]
            ipv6 = line_fields[2]

            if not production_check.is_production_slice(fqdn):
                continue

            # Gather some information about this site which will be used to
            # determine if we need to do anything with this site/sliver.
            slice_id, site_id, server_id = \
                model.get_slice_site_server_ids(fqdn)

            # Make sure this is a valid slice FQDN, and not a mistake or just a
            # node name.
            if slice_id is None or site_id is None or server_id is None:
                continue

            # If mlab-ns does not support this site, then skip it.
            site = model.Site.gql('WHERE site_id=:site_id',
                                  site_id=site_id).get()
            if site == None:
                logging.info('mlab-ns does not support site %s.', site_id)
                continue

            # If mlab-ns does not serve/support this slice, then skip it. Note:
            # a given slice_id might have multiple tools (e.g., iupui_ndt has
            # both 'ndt' and 'ndt_ssl' tools.
            tools = model.Tool.gql('WHERE slice_id=:slice_id',
                                   slice_id=slice_id)
            if tools.count() == 0:
                continue

            for tool in tools.run():
                # Query the datastore to see if this sliver_tool exists there.
                sliver_tool_gql = model.SliverTool.gql(
                    'WHERE fqdn=:fqdn AND tool_id=:tool_id',
                    fqdn=fqdn,
                    tool_id=tool.tool_id)

                # Check to see if the sliver_tool already exists in the
                # datastore. If not, add it to the datastore.
                if sliver_tool_gql.count() == 1:
                    sliver_tool = sliver_tool_gql.get(
                        batch_size=constants.GQL_BATCH_SIZE)
                elif sliver_tool_gql.count() == 0:
                    logging.info(
                        'For tool %s, fqdn %s is not in datastore.  Adding it.',
                        tool.tool_id, fqdn)
                    sliver_tool = self.initialize_sliver_tool(tool, site,
                                                              server_id, fqdn)
                else:
                    logging.error(
                        'Error, or too many sliver_tools returned for {}:{}.'.format(
                            tool.tool_id, fqdn))
                    continue

                updated_sliver_tool = self.set_sliver_tool_ips(sliver_tool,
                                                               ipv4, ipv6)
                # Update all sliver tool.
                self.put_sliver_tool(updated_sliver_tool)

                if tool.tool_id not in sliver_tool_list:
                    sliver_tool_list[tool.tool_id] = []
                sliver_tool_list[tool.tool_id].append(sliver_tool)

        # Update memcache.  Never set the memcache to an empty list since it's
        # more likely that this is a Nagios failure.
        if sliver_tool_list:
            for tool_id in sliver_tool_list.keys():
                if not memcache.set(
                        tool_id,
                        sliver_tool_list[tool_id],
                        namespace=constants.MEMCACHE_NAMESPACE_TOOLS):
                    logging.error(
                        'Failed to update sliver IP addresses in memcache.')

        return util.send_success(self)

    def set_sliver_tool_ips(self, sliver_tool, ipv4, ipv6):
        if not ipv4:
            ipv4 = message.NO_IP_ADDRESS
        if not ipv4:
            ipv6 = message.NO_IP_ADDRESS

        if not sliver_tool.sliver_ipv4 == ipv4:
            sliver_tool.sliver_ipv4 = ipv4
        if not sliver_tool.sliver_ipv6 == ipv6:
            sliver_tool.sliver_ipv6 = ipv6

        return sliver_tool

    def put_sliver_tool(self, sliver_tool):
        # Update memcache AND datastore here.
        if not memcache.set(sliver_tool.tool_id,
                            sliver_tool,
                            namespace=constants.MEMCACHE_NAMESPACE_TOOLS):
            logging.error('Failed to update sliver IP addresses in memcache.')

        try:
            sliver_tool.put()
            logging.info('Succeeded to write IPs of %s (%s, %s) in datastore.',
                         sliver_tool.fqdn, sliver_tool.sliver_ipv4,
                         sliver_tool.sliver_ipv6)
        except db.TransactionFailedError:
            logging.error('Failed to write IPs of %s (%s, %s) in datastore.',
                          sliver_tool.fqdn, sliver_tool.sliver_ipv4,
                          sliver_tool.sliver_ipv6)

    def initialize_sliver_tool(self, tool, site, server_id, fqdn):
        sliver_tool_id = model.get_sliver_tool_id(tool.tool_id, tool.slice_id,
                                                  server_id, site.site_id)

        return model.SliverTool(
            tool_id=tool.tool_id,
            slice_id=tool.slice_id,
            site_id=site.site_id,
            server_id=server_id,
            fqdn=fqdn,
            server_port=tool.server_port,
            http_port=tool.http_port,
            # IP addresses will be updated by the IPUpdateHandler.
            sliver_ipv4=message.NO_IP_ADDRESS,
            sliver_ipv6=message.NO_IP_ADDRESS,
            # Status will be updated by the StatusUpdateHandler.
            status_ipv4=message.STATUS_OFFLINE,
            status_ipv6=message.STATUS_OFFLINE,
            tool_extra="",
            latitude=site.latitude,
            longitude=site.longitude,
            roundrobin=site.roundrobin,
            city=site.city,
            country=site.country,
            update_request_timestamp=long(time.time()),
            key_name=sliver_tool_id)


class StatusUpdateHandler(webapp.RequestHandler):
    """Updates SliverTools' status."""

    def get(self):
        """Triggers the update handler.

        Updates sliver status with information from either Nagios or Prometheus.
        The base URLs for accessing status information are stored in the
        datastore along with the credentials necessary to access the data.
        """
        # Determine if there are any dependencies on Prometheus.
        prometheus_deps = model.get_status_source_deps('prometheus')
        # Get Prometheus configs, and authenticate.
        prometheus_config = prometheus_config_wrapper.get_prometheus_config()
        if prometheus_config is None:
            logging.error('Datastore does not have the Prometheus configs.')
        else:
            prometheus_opener = prometheus_status.authenticate_prometheus(
                prometheus_config)

        # Determine if there are any dependencies on Nagios.
        nagios_deps = model.get_status_source_deps('nagios')
        # Get Nagios configs, and authenticate.
        nagios_config = nagios_config_wrapper.get_nagios_config()
        if nagios_config is None:
            logging.error('Datastore does not have the Nagios configs.')
        else:
            nagios_opener = nagios_status.authenticate_nagios(nagios_config)

        # If we have dependencies on both Prometheus and Nagios, and neither one
        # of the configs is available, then abort, because we can't fetch status
        # from either. However, if we have one or the other, then continue,
        # because it may be preferable to update _some_ statuses than none.
        if (prometheus_deps and not prometheus_config) and (nagios_deps and
                                                            not nagios_config):
            logging.error(
                'Neither Nagios nor Prometheus configs are available.')
            return util.send_not_found(self)

        for tool_id in model.get_all_tool_ids():
            tool = model.get_tool_from_tool_id(tool_id)
            for address_family in ['', '_ipv6']:
                if tool.status_source == 'prometheus':
                    logging.info('Status source for %s%s is: prometheus',
                                 tool_id, address_family)
                    # Only proceed if prometheus_config exists, and hence
                    # prometheus_opener should also exist.
                    if prometheus_config:
                        slice_info = prometheus_status.get_slice_info(
                            prometheus_config.url, tool_id, address_family)
                        if not slice_info:
                            continue
                        slice_status = prometheus_status.get_slice_status(
                            slice_info.slice_url, prometheus_opener)
                    else:
                        logging.error(
                            'Prometheus config unavailable. Skipping %s%s',
                            tool_id, address_family)
                        continue
                elif tool.status_source == 'nagios':
                    logging.info('Status source for %s%s is: nagios', tool_id,
                                 address_family)
                    # Only proceed if nagios_config exists, and hence
                    # nagios_opener should also exist.
                    if nagios_config:
                        slice_info = nagios_status.get_slice_info(
                            nagios_config.url, tool_id, address_family)
                        slice_status = nagios_status.get_slice_status(
                            slice_info.slice_url, nagios_opener)
                    else:
                        logging.error(
                            'Nagios config unavailable. Skipping %s%s', tool_id,
                            address_family)
                        continue
                else:
                    logging.error('Unknown tool status_source: %s.',
                                  tool.status_source)
                    continue

                if slice_status:
                    self.update_sliver_tools_status(slice_status,
                                                    slice_info.tool_id,
                                                    slice_info.address_family)

        return util.send_success(self)

    def update_sliver_tools_status(self, slice_status, tool_id, family):
        """Updates status of sliver tools in input slice.

        Args:
            slice_status: A dict that contains the status of the
                slivers in the slice {key=fqdn, status:online|offline}
            tool_id: A string representing the fqdn that resolves
                to an IP address.
            family: Address family to update.
        """
        sliver_tools = sliver_tool_fetcher.SliverToolFetcher().fetch(
            sliver_tool_fetcher.ToolProperties(tool_id=tool_id,
                                               all_slivers=True))
        updated_sliver_tools = []
        for sliver_tool in sliver_tools:

            if sliver_tool.fqdn not in slice_status:
                logging.info('Monitoring does not know sliver %s.',
                             sliver_tool.fqdn)
                if family == '_ipv6':
                    # We don't want to entirely remove a sliver from memcache
                    # just because IPv6 information is missing from monitoring.
                    # If IPv6 monitoring information is missing, then just flag
                    # IPv6 as offline, and continue as usual.
                    slice_status[sliver_tool.fqdn] = {}
                    slice_status[sliver_tool.fqdn][
                        'status'] = message.STATUS_OFFLINE
                    # Don't wipe out the IPv4 'tool_extra', just append to it.
                    slice_status[sliver_tool.fqdn][
                        'tool_extra'] = sliver_tool.tool_extra + '(Family "_ipv6" for sliver not known by monitoring).'
                else:
                    continue

            if family == '':
                if sliver_tool.sliver_ipv4 == message.NO_IP_ADDRESS:
                    if sliver_tool.status_ipv4 == message.STATUS_ONLINE:
                        logging.warning('Setting IPv4 status of %s to offline '\
                                        'due to missing IP.', sliver_tool.fqdn)
                        sliver_tool.status_ipv4 = message.STATUS_OFFLINE
                else:
                    if (sliver_tool.status_ipv4 !=
                            slice_status[sliver_tool.fqdn]['status'] or
                            sliver_tool.tool_extra !=
                            slice_status[sliver_tool.fqdn]['tool_extra']):
                        sliver_tool.status_ipv4 = \
                          slice_status[sliver_tool.fqdn]['status']
                        sliver_tool.tool_extra = \
                          slice_status[sliver_tool.fqdn]['tool_extra']
            elif family == '_ipv6':
                if sliver_tool.sliver_ipv6 == message.NO_IP_ADDRESS:
                    if sliver_tool.status_ipv6 == message.STATUS_ONLINE:
                        logging.warning('Setting IPv6 status for %s to offline'\
                                        ' due to missing IP.', sliver_tool.fqdn)
                        sliver_tool.status_ipv6 = message.STATUS_OFFLINE
                else:
                    if (sliver_tool.status_ipv6 !=
                            slice_status[sliver_tool.fqdn]['status'] or
                            sliver_tool.tool_extra !=
                            slice_status[sliver_tool.fqdn]['tool_extra']):
                        sliver_tool.status_ipv6 = \
                          slice_status[sliver_tool.fqdn]['status']
                        sliver_tool.tool_extra = \
                          slice_status[sliver_tool.fqdn]['tool_extra']
            else:
                logging.error('Unexpected address family: %s.', family)
                continue

            sliver_tool.update_request_timestamp = long(time.time())
            updated_sliver_tools.append(sliver_tool)

        if updated_sliver_tools:
            try:
                db.put(updated_sliver_tools)
            except db.TransactionFailedError as e:
                logging.error(
                    'Error updating sliver statuses in datastore. Some' \
                    'statuses might be outdated. %s', e)

            if not memcache.set(tool_id,
                                updated_sliver_tools,
                                namespace=constants.MEMCACHE_NAMESPACE_TOOLS):
                logging.error('Failed to update sliver status in memcache.')
