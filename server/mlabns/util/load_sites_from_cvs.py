from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from mlabns.db import model

"""
class GeoLiteCityLocation(db.Model):
    location_id = db.StringProperty()
    country = db.StringProperty()
    region = db.StringProperty()
    city = db.StringProperty()
    postal_code = db.StringProperty()
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    postal_code = db.StringProperty()
    metro_code = db.StringProperty()
    area_code = db.StringProperty()
"""
#filename = 'mlabns/util/GeoLiteCityLocation.csv'
keys = [
    'location_id',
    'country',
    'region',
    'city',
    'postal_code',
    'latitude',
    'longitude',
    'metro_code',
    'area_code'
]

filename = 'GeoLiteCityLocation.100'

for line in open(filename, 'r'):
    values = line.split(',')
    location = dict(zip(keys, values))
    location['latitude'] = float(location['latitude'])
    location['longitude'] = float(location['longitude'])

    model.GeoLiteCityLocation(
        location_id=location['location_id'],
        country=location['country'],
        region=location['region'],
        city=location['city'],
        latitude=location['latitude'],
        longitude=location['longitude']).put()

