import copy
import logging

from google.appengine.ext import db
from mlabns.util import constants
from mlabns.util import parse_fqdn

# The classes defined in this file are described in detail in
# the design doc at http://goo.gl/48S22.


# Data format of this class is defined in
# https://github.com/m-lab/mlab-ns-rate-limit/blob/master/endpoint/endpoint.go
class Requests(db.Model):
    probability = db.FloatProperty()
    requests_per_day = db.IntegerProperty()


class SliverTool(db.Model):
    tool_id = db.StringProperty()
    slice_id = db.StringProperty()
    site_id = db.StringProperty()
    server_id = db.StringProperty()
    server_port = db.StringProperty()
    http_port = db.StringProperty()
    tool_extra = db.StringProperty()

    # Unannotated fqdn. v4 and v6 versions can be built if necessary.
    fqdn = db.StringProperty()

    # IP addresses. Can be message.NO_IP_ADDRESS
    sliver_ipv4 = db.StringProperty()
    sliver_ipv6 = db.StringProperty()

    # These can have the following values: message.STATUS_OFFLINE or
    # message.STATUS_ONLINE.
    status_ipv4 = db.StringProperty()
    status_ipv6 = db.StringProperty()

    update_request_timestamp = db.IntegerProperty(default=0)

    # To avoid an additional lookup in the datastore
    # when replying to a user lookup request,
    # we keep also the geographical coordinates of the site.
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    city = db.StringProperty()
    country = db.StringProperty()
    roundrobin = db.BooleanProperty(required=False, default=False)

    # Date representing the last modification time of this entity.
    when = db.DateTimeProperty(auto_now=True)

    def __repr__(self):
        return ('<tool_id={tool_id},site_id={site_id},slice_id={slice_id},'
                'lat/lon=({latitude},{longitude}),geo={city},{country}>'.format(
                    tool_id=self.tool_id,
                    site_id=self.site_id,
                    slice_id=self.slice_id,
                    latitude=self.latitude,
                    longitude=self.longitude,
                    city=self.city,
                    country=self.country))


class Site(db.Model):
    site_id = db.StringProperty()
    city = db.StringProperty()
    country = db.StringProperty()

    # Latitude/longitude of the airport that uniquely identifies
    # an M-Lab site.
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()

    # List of sites and metros, e.g., [ath, ath01].
    # It allows to select a server from a specific subset of sites.
    # For instance, a request for http://mlabns.appspot.com/ndt?metro=ath
    # will only consider sliver tools from the 'ath' sites
    # (currently ath01 and ath02).
    metro = db.StringListProperty(default=None)

    # Date representing the registration time (the first time a new site
    # is added to mlab-ns).
    registration_timestamp = db.IntegerProperty(default=0)

    # Whether do round robin for this site. Default value is false.
    roundrobin = db.BooleanProperty(required=False, default=False)

    # Date representing the last modification time of this entity.
    when = db.DateTimeProperty(auto_now=True)


class MaxmindCityLocation(db.Model):
    location_id = db.StringProperty()
    country = db.StringProperty()
    region = db.StringProperty()
    city = db.StringProperty()
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    when = db.DateTimeProperty(auto_now=True)


class CountryCode(db.Model):
    name = db.StringProperty()
    alpha2_code = db.StringProperty()
    alpha3_code = db.StringProperty()
    numeric_code = db.IntegerProperty()
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    when = db.DateTimeProperty(auto_now=True)


class EncryptionKey(db.Model):
    """Key used to encrypt the communication with the RegistrationClient."""
    # Name of the key (by default is 'admin').
    key_id = db.StringProperty()

    # 16 bytes encryption key (AES).
    encryption_key = db.StringProperty()


class Slice(db.Model):
    slice_id = db.StringProperty()


class Tool(db.Model):
    slice_id = db.StringProperty()
    tool_id = db.StringProperty()
    server_port = db.StringProperty()
    # For web-based tools, this is used to build the URL the client is
    # redirected to: http://fqdn[ipv4|ipv6]:http_port
    http_port = db.StringProperty()
    show_tool_extra = db.BooleanProperty()
    status_source = db.StringProperty()


class Nagios(db.Model):
    key_id = db.StringProperty()
    username = db.StringProperty()
    password = db.StringProperty()
    url = db.StringProperty()


class Prometheus(db.Model):
    key_id = db.StringProperty()
    username = db.StringProperty()
    password = db.StringProperty()
    url = db.StringProperty()


class ReverseProxyProbability(db.Model):
    name = db.StringProperty()
    probability = db.FloatProperty()
    url = db.StringProperty()

    def with_name(self, name):
        prob = copy.copy(self)
        prob.name = name
        return prob


def get_sliver_tool_id(tool_id, slice_id, server_id, site_id):
    """Creates the SliverTool id from an UpdateMessage.

    Args:
        tool_id: String representing the tool id.
        slice_id: String representing the slice id.
        server_id: String representing the server id.
        site_id: String representing the site id.

    Returns:
        A string representing the key that uniquely identifies a
        SliverTool.
        It returns None is any of the input values are None.
    """
    try:
        return '-'.join([tool_id, slice_id, server_id, site_id])
    except TypeError:
        return None


def get_fqdn(slice_id, server_id, site_id):
    """Returns an FQDN or None if the given slice_id is not valid."""

    slice_parts = slice_id.split('_')
    if len(slice_parts) != 2:
        return None
    return '.'.join([slice_parts[1], slice_parts[0], server_id, site_id,
                     'measurement-lab.org'])


def get_slice_site_server_ids(fqdn):
    p = parse_fqdn.parse(fqdn)
    if not p:
        return None, None, None

    if p['org']:
        experiment = '%s_%s' % (p['org'], p['experiment'])
    else:
        experiment = p['experiment']

    return experiment, p['site'], p['machine']


def get_tool_from_tool_id(tool_id):
    tools_gql = Tool.gql("WHERE tool_id = :tool_id", tool_id=tool_id)
    for tool in tools_gql.run():
        return tool
    logging.info('Tool %s not found in data store.', tool_id)
    return None


def get_all_tool_ids():
    """Gets all Tool model objects.

    Returns:
        List of tool_ids.
    """
    tool_ids = []
    for tool in Tool.all().run(batch_size=constants.GQL_BATCH_SIZE):
        tool_ids.append(tool.tool_id)
    return tool_ids


def get_status_source_deps(source):
    """Gets all Tools that rely on the given status source.

    Args:
        source: str, status source, either 'nagios or 'prometheus'.

    Returns:
        list, Tools that depend on `source`.
    """
    tools = []
    tools_gql = Tool.gql("WHERE status_source = :source", source=source)
    for tool in tools_gql.run():
        tools.append(tool)
    if not tools:
        logging.info('No tools get their status from %s.', source)
    return tools


def is_valid_tool(tool_id):
    """Indicates whether the given tool_id is valid and known in datastore."""
    return tool_id in get_all_tool_ids()
