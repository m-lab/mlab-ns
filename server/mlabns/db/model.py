from google.appengine.ext import db

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
    timestamp = db.IntegerProperty(default=0)
    lat_long = db.StringProperty()
    when = db.DateTimeProperty(auto_now=True)

class Site(db.Model):
    site_id = db.StringProperty()
    city = db.StringProperty()
    region = db.StringProperty()
    country = db.StringProperty()
    lat_long = db.StringProperty()
    metro = db.StringListProperty(default=None)
    timestamp = db.IntegerProperty(default=0)
    when = db.DateTimeProperty(auto_now=True)

class Lookup(db.Model):
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


