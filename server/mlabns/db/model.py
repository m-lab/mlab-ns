from google.appengine.ext import db

# The classes defined in this file are described in detail in
# the design doc at http://goo.gl/48S22.

class SliverTool(db.Model):
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
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    when = db.DateTimeProperty(auto_now=True)

class Site(db.Model):
    site_id = db.StringProperty()
    city = db.StringProperty()
    region = db.StringProperty()
    country = db.StringProperty()
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    metro = db.StringListProperty(default=None)
    timestamp = db.IntegerProperty(default=0)
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


class GeoLiteCityLocation(db.Model):
    location_id = db.StringProperty()
    country = db.StringProperty()
    region = db.StringProperty()
    city = db.StringProperty()
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    postal_code = db.StringProperty()
    metro_code = db.StringProperty()
    area_code = db.StringProperty()

class GeoLiteCityBlock:
    start_ip_num = db.IntegerProperty()
    end_ip_num = db.IntegerProperty()
    location_id = db.StringProperty()

class GeoLiteCityv6:
    start_ip_num = db.IntegerProperty()
    end_ip_num = db.IntegerProperty()
    country = db.StringProperty()
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()

def get_sliver_tool_id(update_request):
    """Creates the SliverTool id from an UpdateMessage.

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

