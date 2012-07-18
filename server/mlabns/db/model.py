from google.appengine.ext import db

# The design documentation can be found at http://goo.gl/48S22.

class SliverTool(db.Model):
    """SliverTool entity.

    Note that 'lat_long' information is redundant since is already
    included in the 'Site' db. However, this information is replicated
    here to avoid an additional lookup.
    """
    tool_id = db.StringProperty()
    slice_id = db.StringProperty()
    site_id = db.StringProperty()
    server_id = db.StringProperty()
    sliver_tool_key = db.StringProperty()
    sliver_ipv4 = db.StringProperty()
    sliver_ipv6 = db.StringProperty()
    url = db.StringProperty()
    status = db.StringProperty()
    update_request_timestamp = db.IntegerProperty(default=0)
    lat_long = db.StringProperty()
    when = db.DateTimeProperty(auto_now=True)

def get_sliver_tool_id(update_request):
    """Creates the SliverTool's key from an UpdateMessage.

    Args:
        update_request: An UpdateMessage instance.

    Returns:
        A string representing the key that uniquely identifies a
        SliverTool.
    """
    return '-'. join([
            update_request.tool_id,
            update_request.slice_id,
            update_request.server_id,
            update_request.site_id])

class Site(db.Model):
    """ Site entity."""
    site_id = db.StringProperty()
    city = db.StringProperty()
    region = db.StringProperty()
    country = db.StringProperty()
    lat_long = db.StringProperty()
    metro = db.StringListProperty(default=None)
    timestamp = db.IntegerProperty(default=0)
    when = db.DateTimeProperty(auto_now=True)

class Lookup(db.Model):
    """ Lookup entity."""
    tool_id = db.StringProperty()
    policy = db.StringProperty()
    user_ip = db.StringProperty()
    user_city = db.StringProperty()
    user_country = db.StringProperty()
    user_lat_long = db.StringProperty()
    slice_id=db.StringProperty()
    server_id = db.StringProperty()
    site_id=db.StringProperty()
    site_city = db.StringProperty()
    site_country = db.StringProperty()
    site_lat_long = db.StringProperty()
    when = db.DateTimeProperty(auto_now=True)

