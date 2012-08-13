from . import message

class SiteRegistrationMessage(message.Message):
    def __init__(self):
        message.Message.__init__(self)
        self.entity = message.ENTITY_SITE
        self.site_id = None
        self.city = None
        self.country = None
        self.lat_long = None
        self.metro = None

        self.required_fields = set([
            message.ENTITY,
            message.SITE_ID,
            message.CITY,
            message.COUNTRY,
            message.LAT_LONG,
            message.METRO])

    def initialize_from_dictionary(self, dictionary):
        for field in self.required_fields:
            if field not in dictionary:
                raise message.FormatError('Missing field %s.' % (field))

        self.entity = dictionary[message.ENTITY]
        self.site_id = dictionary[message.SITE_ID]
        self.city = dictionary[message.CITY]
        self.country = dictionary[message.COUNTRY]
        self.lat_long = dictionary[message.LAT_LONG]
        self.metro = dictionary[message.METRO]

        if message.TIMESTAMP in dictionary:
            self.timestamp = dictionary[message.TIMESTAMP]

    def to_dictionary(self):
        dictionary = {}
        dictionary[message.ENTITY] = self.entity
        dictionary[message.SITE_ID] = self.site_id
        dictionary[message.CITY] = self.city
        dictionary[message.COUNTRY] = self.country
        dictionary[message.LAT_LONG] = self.lat_long
        dictionary[message.METRO] = self.metro
        dictionary[message.TIMESTAMP] = self.timestamp

        return dictionary

class SliverToolRegistrationMessage(message.Message):

    def __init__(self):
        message.Message.__init__(self)
        self.entity = message.ENTITY_SLIVER_TOOL
        self.tool_id = None
        self.slice_id = None
        self.server_id = None
        self.server_port = None
        self.http_port = None
        self.fqdn = None
        self.sliver_ipv4 = None
        self.sliver_ipv6 = None
        self.sliver_tool_key = None
        self.status = None
        self.url = None

        self.required_fields = set([
            message.ENTITY,
            message.SERVER_ID,
            message.SERVER_PORT,
            message.HTTP_PORT,
            message.FQDN,
            message.SITE_ID,
            message.SLICE_ID,
            message.SLIVER_IPv4,
            message.SLIVER_IPv6,
            message.SLIVER_TOOL_KEY,
            message.STATUS,
            message.TOOL_ID,
            message.URL])

    def initialize_from_dictionary(self, dictionary):
        for field in self.required_fields:
            if field not in dictionary:
                raise message.FormatError('Missing field %s.' % (field))

        self.entity = dictionary[message.ENTITY]
        self.tool_id = dictionary[message.TOOL_ID]
        self.slice_id = dictionary[message.SLICE_ID]
        self.server_id = dictionary[message.SERVER_ID]
        self.server_port = dictionary[message.SERVER_PORT]
        self.http_port = dictionary[message.HTTP_PORT]
        self.fqdn = dictionary[message.FQDN]
        self.site_id = dictionary[message.SITE_ID]
        self.sliver_ipv4 = dictionary[message.SLIVER_IPv4]
        self.sliver_ipv6 = dictionary[message.SLIVER_IPv6]
        self.sliver_tool_key = dictionary[message.SLIVER_TOOL_KEY]
        self.status = dictionary[message.STATUS]
        self.url = dictionary[message.URL]

        if message.TIMESTAMP in dictionary:
            self.timestamp = dictionary[message.TIMESTAMP]

    def to_dictionary(self):
        dictionary = {}
        dictionary[message.ENTITY] = self.entity
        dictionary[message.SITE_ID] = self.site_id
        dictionary[message.SERVER_ID] = self.server_id
        dictionary[message.SERVER_PORT] = self.server_port
        dictionary[message.HTTP_PORT] = self.http_port
        dictionary[message.FQDN] = self.fqdn
        dictionary[message.SLICE_ID] = self.slice_id
        dictionary[message.SLIVER_IPv4] = self.sliver_ipv4
        dictionary[message.SLIVER_IPv6] = self.sliver_ipv6
        dictionary[message.SLIVER_TOOL_KEY] = self.sliver_tool_key
        dictionary[message.STATUS] = self.status
        dictionary[message.TIMESTAMP] = self.timestamp
        dictionary[message.TOOL_ID] = self.tool_id
        dictionary[message.URL] = self.url

        return dictionary
