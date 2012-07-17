from . import message

class SiteRegistrationMessage(message.Message):
    def __init__(self):
        message.Message.__init__(self)
        self.entity = ''
        self.site_id = ''
        self.city = ''
        self.country = ''
        self.lat_long = ''
        self.metro = ''

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
                raise FormatError('Missing field %s.' % (field))

        self.entity = dictionary[message.ENTITY]
        self.site_id = dictionary[message.SITE_ID]
        self.city = dictionary[message.CITY]
        self.country = dictionary[message.COUNTRY]
        self.lat_long = dictionary[message.LAT_LONG]
        self.metro = dictionary[message.METRO]

        if message.TIMESTAMP in dictionary:
            self.timestamp = dictionary[message.TIMESTAMP]

        if message.SIGNATURE in dictionary:
            self.signature = dictionary[message.SIGNATURE]


    def compute_signature(self, key):
        dictionary = self.to_dictionary()
        dictionary[message.SIGNATURE] = ''

        return message.Message.compute_signature(self, key, dictionary)


    def sign(self, key):
        """Adds a signature to the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.
        """
        self.signature = self.compute_signature(key);


    def verify_signature(self, key):
        """Verifies the signature of the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.

        Return:
            True if the signature is correct, False otherwise.
        """

        signature = self.compute_signature(key)
        return (signature == self.signature)

    def to_dictionary(self):

        dictionary = {}
        dictionary[message.CITY] = self.city
        dictionary[message.COUNTRY] = self.country
        dictionary[message.ENTITY] = self.entity
        dictionary[message.LAT_LONG] = self.lat_long
        dictionary[message.METRO] = self.metro
        dictionary[message.SIGNATURE] = self.signature
        dictionary[message.SITE_ID] = self.site_id
        dictionary[message.TIMESTAMP] = self.timestamp

        return dictionary

class SliverToolRegistrationMessage(message.Message):

    def __init__(self):
        message.Message.__init__(self)
        self.entity = ''
        self.tool_id = ''
        self.slice_id = ''
        self.server_id = ''
        self.sliver_ipv4 = ''
        self.sliver_ipv6 = ''
        self.sliver_tool_key = ''
        self.status = ''
        self.url = ''

        self.required_fields = set([
            message.ENTITY,
            message.SERVER_ID,
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
                raise FormatError('Missing field %s.' % (field))

        self.entity = dictionary[message.ENTITY]
        self.tool_id = dictionary[message.TOOL_ID]
        self.slice_id = dictionary[message.SLICE_ID]
        self.server_id = dictionary[message.SERVER_ID]
        self.site_id = dictionary[message.SITE_ID]
        self.sliver_ipv4 = dictionary[message.SLIVER_IPv4]
        self.sliver_ipv6 = dictionary[message.SLIVER_IPv6]
        self.sliver_tool_key = dictionary[message.SLIVER_TOOL_KEY]
        self.status = dictionary[message.STATUS]
        self.url = dictionary[message.URL]

        if message.TIMESTAMP in dictionary:
            self.timestamp = dictionary[message.TIMESTAMP]

        if message.SIGNATURE in dictionary:
            self.signature = dictionary[message.SIGNATURE]


    def compute_signature(self, key):
        dictionary = self.to_dictionary()
        dictionary[message.SIGNATURE] = ''
        return message.Message.compute_signature(self, key, dictionary)

    def sign(self, key):
        """Adds a signature to the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.
        """
        self.signature = self.compute_signature(key);

    def verify_signature(self, key):
        """Verifies the signature of the message.

        Args:
            key: A string representing the key that is used to compute
                the signature.

        Return:
            True if the signature is correct, False otherwise.
        """

        signature = self.compute_signature(key)
        return (signature == self.signature)


    def to_dictionary(self):

        dictionary = {}
        dictionary[message.ENTITY] = self.entity
        dictionary[message.SERVER_ID] = self.server_id
        dictionary[message.SIGNATURE] = self.signature
        dictionary[message.SITE_ID] = self.site_id
        dictionary[message.SLICE_ID] = self.slice_id
        dictionary[message.SLIVER_IPv4] = self.sliver_ipv4
        dictionary[message.SLIVER_IPv6] = self.sliver_ipv6
        dictionary[message.SLIVER_TOOL_KEY] = self.sliver_tool_key
        dictionary[message.STATUS] = self.status
        dictionary[message.TIMESTAMP] = self.timestamp
        dictionary[message.TOOL_ID] = self.tool_id
        dictionary[message.URL] = self.url

        return dictionary
