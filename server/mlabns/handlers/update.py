import json
import logging
import os
import time
import urllib2

from google.appengine.api import memcache
from google.appengine.api import namespace_manager
from google.appengine.ext import db
from google.appengine.ext import webapp

from mlabns.db import model
from mlabns.db import nagios_config_wrapper
from mlabns.db import prometheus_config_wrapper
from mlabns.db import sliver_tool_fetcher
from mlabns.util import constants
from mlabns.util import maxmind
from mlabns.util import message
from mlabns.util import nagios_status
from mlabns.util import prometheus_status
from mlabns.util import production_check
from mlabns.util import reverse_proxy
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

        Checks if new sites were added to siteinfo and registers them.
        """
        try:
            locations_url = os.environ.get('LOCATIONS_URL')
            sites_json = json.loads(urllib2.urlopen(locations_url).read())
        except urllib2.HTTPError:
            # TODO(claudiu) Notify(email) when this happens.
            logging.error('Cannot open %s.', locations_url)
            return util.send_not_found(self)
        except (TypeError, ValueError) as e:
            logging.error('The json format of %s in not valid: %s',
                          locations_url, e)
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
        mlab_sites = list(model.Site.all().fetch(limit=None))
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
        IPUpdateHandler().update()

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

        return True


class IPUpdateHandler():
    """Updates SliverTools' IP addresses."""

    def update(self):
        """Triggers the update handler.

        Updates sliver tool IP addresses.
        """
        try:
            hostnames_url = os.environ.get('HOSTNAMES_URL')
            raw_json = urllib2.urlopen(hostnames_url).read()
            logging.info('Fetched hostnames.json from: %s', hostnames_url)
        except urllib2.HTTPError:
            # TODO(claudiu) Notify(email) when this happens.
            logging.error('Cannot open %s.', hostnames_url)
            return util.send_not_found(self)

        try:
            rows = json.loads(raw_json)
        except (TypeError, ValueError) as e:
            logging.error('Failed to parse raw json from %s: %s', hostnames_url,
                          e)
            return util.send_not_found(self)

        # Fetch all data that we are going to need from the datastore up front.
        sites = list(model.Site.all().fetch(limit=None))
        tools = list(model.Tool.all().fetch(limit=None))
        slivertools = list(model.SliverTool.all().fetch(limit=None))

        for row in rows:
            # Expected keys: "hostname,ipv4,ipv6" (ipv6 can be an empty string).
            fqdn = row['hostname']
            ipv4 = row['ipv4']
            ipv6 = row['ipv6']

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
            site = list(filter(lambda s: s.site_id == site_id, sites))
            if len(site) == 0:
                logging.info('mlab-ns does not support site %s.', site_id)
                continue
            else:
                site = site[0]

            # If mlab-ns does not serve/support this slice, then skip it. Note:
            # a given slice_id might have multiple tools (e.g., iupui_ndt has
            # both 'ndt' and 'ndt_ssl' tools.
            slice_tools = list(filter(lambda t: t.slice_id == slice_id, tools))

            if len(slice_tools) == 0:
                continue

            for slice_tool in slice_tools:
                # See if this sliver_tool already exists in the datastore.
                sliver_tool_id = model.get_sliver_tool_id(
                    slice_tool.tool_id, slice_id, server_id, site_id)
                slivertool = list(filter(
                    lambda st: st.key().name() == sliver_tool_id, slivertools))

                # If the sliver_tool already exists in the datastore, edit it.
                # If not, add it to the datastore.
                if len(slivertool) == 1:
                    sliver_tool = slivertool[0]
                elif len(slivertool) == 0:
                    logging.info(
                        'For tool %s,  %s is not in datastore.  Adding it.',
                        slice_tool.tool_id, sliver_tool_id)
                    sliver_tool = self.initialize_sliver_tool(slice_tool, site,
                                                              server_id, fqdn)
                else:
                    logging.error(
                        'Error, or too many sliver_tools returned for {}:{}.'.format(
                            slice_tool.tool_id, sliver_tool_id))
                    continue

                updated_sliver_tool = self.set_sliver_tool(
                    sliver_tool, ipv4, ipv6, site.roundrobin, fqdn)

                # Update datastore if the SliverTool got updated.
                if updated_sliver_tool:
                    logging.info('Updating IP info for fqdn: %s', fqdn)
                    self.put_sliver_tool(updated_sliver_tool)

        return

    def set_sliver_tool(self, sliver_tool, ipv4, ipv6, rr, fqdn):
        updated = False
        if not ipv4:
            ipv4 = message.NO_IP_ADDRESS
        if not ipv6:
            ipv6 = message.NO_IP_ADDRESS

        if not sliver_tool.sliver_ipv4 == ipv4:
            sliver_tool.sliver_ipv4 = ipv4
            updated = True
        if not sliver_tool.sliver_ipv6 == ipv6:
            sliver_tool.sliver_ipv6 = ipv6
            updated = True
        if not sliver_tool.roundrobin == rr:
            sliver_tool.roundrobin = rr
            updated = True
        if not sliver_tool.fqdn == fqdn:
            sliver_tool.fqdn = fqdn
            updated = True

        if updated:
            return sliver_tool
        return updated

    def put_sliver_tool(self, sliver_tool):
        # Update datastore
        try:
            sliver_tool.put()
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
        sliver_tools = sliver_tool_fetcher.SliverToolFetcherDatastore().fetch(
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
                    # Update tool_extra to signal that _ipv6 is not known.
                    slice_status[sliver_tool.fqdn][
                        'tool_extra'] = constants.PROMETHEUS_TOOL_EXTRA + ' (Family "_ipv6" for sliver not known by monitoring).'

                else:
                    # If monitoring data doesn't exist for this tool, append
                    # the sliver_tool unmodified to the list, since in the
                    # absence of status data we are better off having stale
                    # data than marking the sliver as down.
                    updated_sliver_tools.append(sliver_tool)
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


class ReloadMaxmindDb(webapp.RequestHandler):
    """Reloads the MaxMind database file from GCS, perhaps updating it."""

    # See util/maxmind.py for details.
    def get(self):
        # Reads the database file from GCS.
        maxmind.get_database_file()

        # Generates the new Reader object.
        maxmind.get_geo_reader()


class CountRequestSignaturesHandler(webapp.RequestHandler):
    """Counts Request Signatures in memcache relative to Datastore."""

    def get(self):
        """Logs request signature counts found in memcache."""
        namespace_manager.set_namespace('endpoint_stats')
        requests = list(model.Requests.all().fetch(limit=None))
        found = 0
        missing = 0
        for request in requests:
            val = memcache.get(request.key().name(),
                               namespace=constants.MEMCACHE_NAMESPACE_REQUESTS)
            if val is not None:
                found += 1
            else:
                missing += 1

        logging.info(('Client signatures from datastore; '
                      'found_in: %d missing_from: %d memcache'), found, missing)


class WarmupHandler(webapp.RequestHandler):
    """Loads expensive queries into memory before starting service."""

    def get(self):
        """Handles warmup request."""
        logging.info('Running warmup handlers for: redirect, maxmind')
        reverse_proxy.get_reverse_proxy()
        maxmind.get_geo_reader()
