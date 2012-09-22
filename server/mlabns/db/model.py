from google.appengine.ext import db

# The classes defined in this file are described in detail in
# the design doc at http://goo.gl/48S22.

class SliverTool(db.Model):
    tool_id = db.StringProperty()
    slice_id = db.StringProperty()
    site_id = db.StringProperty()
    server_id = db.StringProperty()
    server_port = db.StringProperty()
    http_port = db.StringProperty()
    fqdn_ipv4 = db.StringProperty()
    fqdn_ipv6 = db.StringProperty()
    sliver_ipv4 = db.StringProperty()
    sliver_ipv6 = db.StringProperty()
    url = db.StringProperty()

    # These can have the following values: online, offline, error.
    status_ipv4 = db.StringProperty()
    status_ipv6 = db.StringProperty()

    update_request_timestamp = db.IntegerProperty(default=0)

    # To avoid an additional lookup in the datastore,
    # we keep also the geographical coordinates of the site.
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()

    # Date representing the last modification time.
    when = db.DateTimeProperty(auto_now=True)

class Site(db.Model):
    site_id = db.StringProperty()
    city = db.StringProperty()
    region = db.StringProperty()
    country = db.StringProperty()

    # Latitude/longitude of the airport that uniquely identifies
    # an M-Lab site.
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()

    # List of 'group' identifiers (e.g., [ath, ath01]). It allows to
    # select a server from a specific subset of sites.
    metro = db.StringListProperty(default=None)

    # Date representing the registration time (the first time a new site
    # is added to mlab-ns).
    timestamp = db.IntegerProperty(default=0)

    # Date representing the last modification time.
    when = db.DateTimeProperty(auto_now=True)

class Lookup(db.Model):
    tool_id = db.StringProperty()
    policy = db.StringProperty()
    user_ip = db.StringProperty()
    user_city = db.StringProperty()
    user_country = db.StringProperty()
    user_latitude = db.FloatProperty()
    user_longitude = db.FloatProperty()
    slice_id=db.StringProperty()
    server_id = db.StringProperty()
    site_id=db.StringProperty()
    site_city = db.StringProperty()
    site_country = db.StringProperty()
    site_latitude = db.FloatProperty()
    site_longitude = db.FloatProperty()
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

class MaxmindCityv6(db.Model):
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
    key_id = db.StringProperty()
    encryption_key = db.StringProperty()

class Slice(db.Model):
    slice_id = db.StringProperty()
    tool_id = db.StringProperty()

class Nagios(db.Model):
    key_id = db.StringProperty()
    username = db.StringProperty()
    password = db.StringProperty()
    url = db.StringProperty()

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
    """
    return '-'.join([tool_id, slice_id, server_id, site_id])
