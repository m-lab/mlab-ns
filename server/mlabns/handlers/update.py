from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp

import json
import logging
import time
import urllib2

from mlabns.db import model
from mlabns.db import nagios_status_data
from mlabns.util import constants
from mlabns.util import message
from mlabns.util import nagios_status
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

    REQUIRED_FIELDS = [SITE_FIELD, METRO_FIELD, CITY_FIELD, COUNTRY_FIELD,
                       LAT_FIELD, LON_FIELD]
    SITE_LIST_URL = 'http://nagios.measurementlab.net/mlab-site-stats.json'

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
            nagios_sites_json = json.loads(urllib2.urlopen(
                self.SITE_LIST_URL).read())
        except urllib2.HTTPError:
            # TODO(claudiu) Notify(email) when this happens.
            logging.error('Cannot open %s.', self.SITE_LIST_URL)
            return util.send_not_found(self)
        except (TypeError, ValueError) as e:
            logging.error('The json format of %s in not valid: %s',
                          self.SITE_LIST_URL, e)
            return util.send_not_found(self)

        nagios_site_ids = set()

        # Validate the data from Nagios.
        valid_nagios_sites_json = []
        for nagios_site in nagios_sites_json:
            if not self._is_valid_site(nagios_site):
                continue
            valid_nagios_sites_json.append(nagios_site)
            nagios_site_ids.add(nagios_site[self.SITE_FIELD])

        mlab_site_ids = set()
        mlab_sites = model.Site.all()
        for site in mlab_sites:
            mlab_site_ids.add(site.site_id)

        unchanged_site_ids = nagios_site_ids.intersection(mlab_site_ids)
        new_site_ids = nagios_site_ids.difference(mlab_site_ids)
        removed_site_ids = mlab_site_ids.difference(nagios_site_ids)

        # Do not remove sites here for now.
        # TODO(claudiu) Implement the site removal as a separate handler.
        for site_id in removed_site_ids:
            logging.warning('Site %s removed from %s.', site_id,
                            self.SITE_LIST_URL)

        for site_id in unchanged_site_ids:
            logging.info('Site %s unchanged in %s.', site_id,
                         self.SITE_LIST_URL)

        for nagios_site in valid_nagios_sites_json:
            if (nagios_site[self.SITE_FIELD] in new_site_ids):
                logging.info('Registering site %s.',
                             nagios_site[self.SITE_FIELD])
                # TODO(claudiu) Notify(email) when this happens.
                if not self.register_site(nagios_site):
                    logging.error('Error registering site %s.',
                                  nagios_site[self.SITE_FIELD])
                    continue

        return util.send_success(self)

    def register_site(self, nagios_site):
        """Registers a new site.

        Args:
            nagios_site: A json representing the site info as provided by Nagios.

        Returns:
            True if the registration succeeds, False otherwise.
        """
        try:
            lat_long = float(nagios_site[self.LAT_FIELD])
            lon_long = float(nagios_site[self.LON_FIELD])
        except ValueError:
            logging.error('Geo coordinates are not float (%s, %s)',
                          nagios_site[self.LAT_FIELD],
                          nagios_site[self.LON_FIELD])
            return False
        site = model.Site(site_id=nagios_site[self.SITE_FIELD],
                          city=nagios_site[self.CITY_FIELD],
                          country=nagios_site[self.COUNTRY_FIELD],
                          latitude=lat_long,
                          longitude=lon_long,
                          metro=nagios_site[self.METRO_FIELD],
                          registration_timestamp=long(time.time()),
                          key_name=nagios_site[self.SITE_FIELD])

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
    """ Updates SliverTools' IP addresses from Nagios."""

    IP_LIST_URL = 'http://nagios.measurementlab.net/mlab-host-ips.txt'

    def get(self):
        """Triggers the update handler.

        Updates sliver tool IP addresses from Nagios.
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

            sliver_tool_gql = model.SliverTool.gql('WHERE fqdn=:fqdn',
                                                   fqdn=fqdn)
            # FQDN is not necessarily unique across tools.
            for sliver_tool in sliver_tool_gql.run(
                    batch_size=constants.GQL_BATCH_SIZE):
                # case 1) Sliver tool has not changed. Nothing to do.
                if (sliver_tool != None and sliver_tool.sliver_ipv4 == ipv4 and
                        sliver_tool.sliver_ipv6 == ipv6):
                    pass
                # case 2) Sliver tool has changed.
                else:
                    # case 2.1) Sliver tool does not exist in datastore. Initialize
                    #     sliver if the corresponding tool exists in the Tool table
                    #     and the corresponding site exists in the Site table. This
                    #     case occurs when a new tool has been added after the last
                    #     IPUpdateHanlder ran. The sliver tool will actually be
                    #     written to datastore at the next step.
                    if sliver_tool == None:
                        logging.warning('sliver_tool %s is not in datastore.',
                                        fqdn)
                        slice_id, site_id, server_id = \
                            model.get_slice_site_server_ids(fqdn)
                        if slice_id is None or site_id is None or server_id is None:
                            logging.info('Non valid sliver fqdn %s.', fqdn)
                            continue
                        tool = model.Tool.gql('WHERE slice_id=:slice_id',
                                              slice_id=slice_id).get()
                        if tool == None:
                            logging.info('mlab-ns does not support slice %s.',
                                         slice_id)
                            continue
                        site = model.Site.gql('WHERE site_id=:site_id',
                                              site_id=site_id).get()
                        if site == None:
                            logging.info('mlab-ns does not support site %s.',
                                         site_id)
                            continue
                        sliver_tool = self.initialize_sliver_tool(
                            tool, site, server_id, fqdn)

                    # case 2.2) Sliver tool exists in datastore.
                    if ipv4 != None:
                        sliver_tool.sliver_ipv4 = ipv4
                    else:
                        sliver_tool.sliver_ipv4 = message.NO_IP_ADDRESS
                    if ipv6 != None:
                        sliver_tool.sliver_ipv6 = ipv6
                    else:
                        sliver_tool.sliver_ipv6 = message.NO_IP_ADDRESS

                    try:
                        sliver_tool.put()
                        logging.info(
                            'Succeeded to write IPs of %s (%s, %s) in datastore.',
                            fqdn, ipv4, ipv6)
                    except db.TransactionFailedError:
                        logging.error(
                            'Failed to write IPs of %s (%s, %s) in datastore.',
                            fqdn, ipv4, ipv6)
                    continue

                if sliver_tool.tool_id not in sliver_tool_list:
                    sliver_tool_list[sliver_tool.tool_id] = []
                sliver_tool_list[sliver_tool.tool_id].append(sliver_tool)
                logging.info('sliver %s to be added to memcache',
                             sliver_tool.fqdn)

        # Update memcache
        # Never set the memcache to an empty list since it's more likely that
        # this is a Nagios failure.
        if sliver_tool_list:
            for tool_id in sliver_tool_list.keys():
                if not memcache.set(
                        tool_id,
                        sliver_tool_list[tool_id],
                        namespace=constants.MEMCACHE_NAMESPACE_TOOLS):
                    logging.error(
                        'Failed to update sliver IP addresses in memcache.')

        return util.send_success(self)

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
            city=site.city,
            country=site.country,
            update_request_timestamp=long(time.time()),
            key_name=sliver_tool_id)


class StatusUpdateHandler(webapp.RequestHandler):
    """Updates SliverTools' status from nagios."""

    IPV4 = constants.AF_IPV4
    IPV6 = constants.AF_IPV6
    NAGIOS_AF_SUFFIXES = [IPV4, IPV6]

    def get(self):
        """
        Access sliver status with information from Nagios. The Nagios URL
        containing the information is stored in the Nagios db along with
        the credentials necessary to access the data.
        """
        nagios = nagios_status_data.get_nagios_credentials()
        if nagios is None:
            return util.send_not_found(self)

        nagios_status.authenticate_nagios(nagios)
        slice_urls = nagios_status.get_slice_urls(nagios.url,
                                                  self.NAGIOS_AF_SUFFIXES)

        for url_tuple in slice_urls:
            slice_url, tool_id, ipversion = url_tuple
            slice_status = nagios_status.get_slice_status(slice_url)
            nagios_status.update_sliver_tools_status(slice_status, tool_id,
                                                     ipversion)

        return util.send_success(self)
