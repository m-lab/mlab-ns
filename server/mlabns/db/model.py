from google.appengine.ext import db

# The classes defined in this file are described in detail in
# the design doc at http://goo.gl/48S22.

class SliverTool(db.Model):
    tool_id = db.StringProperty()
    slice_id = db.StringProperty()
    site_id = db.StringProperty()
    server_id = db.StringProperty()
    server_port = db.StringProperty()

    # For web-based tools, this is used to build the URL the client is
    # redirected to: http://fqdn[ipv4|ipv6]:http_port
    http_port = db.StringProperty()

    fqdn_ipv4 = db.StringProperty()
    fqdn_ipv6 = db.StringProperty()
    sliver_ipv4 = db.StringProperty()
    sliver_ipv6 = db.StringProperty()

    # These can have the following values: online and offline.
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

    # Date representing the last modification time of this entity.
    when = db.DateTimeProperty(auto_now=True)

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
    # For instance, a request for http://mlabns.appspot.com/npad?metro=ath
    # will only consider sliver tools from the 'ath' sites
    # (currently ath01 and ath02).
    metro = db.StringListProperty(default=None)

    # Date representing the registration time (the first time a new site
    # is added to mlab-ns).
    registration_timestamp = db.IntegerProperty(default=0)

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

class MaxmindCityBlock(db.Model):
    start_ip_num = db.IntegerProperty()
    end_ip_num = db.IntegerProperty()
    location_id = db.StringProperty()
    when = db.DateTimeProperty(auto_now=True)

class MaxmindCityBlockv6(db.Model):
    start_ip_num = db.IntegerProperty()
    end_ip_num = db.IntegerProperty()
    country = db.StringProperty()
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
    tool_id = db.StringProperty()

class Nagios(db.Model):
    key_id = db.StringProperty()
    username = db.StringProperty()
    password = db.StringProperty()
    url = db.StringProperty()

# A single query. TODO(dominic) Add the result location?
class Ping(db.Model):
    latitude = db.FloatProperty(required=True, indexed=False)
    longitude = db.FloatProperty(required=True, indexed=False)
    tool_id = db.StringProperty(required=True)
    address_family = db.StringProperty(required=True)
    time = db.FloatProperty(required=True)

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
