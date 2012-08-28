import logging

from . import message

class UpdateMessage(message.Message):

    def __init__(self):
        message.Message.__init__(self)
        self.tool_id = None
        self.fqdn_ipv4 = None
        self.fqdn_ipv6 = None
        self.slice_id = None
        self.server_id = None
        self.server_port = None
        self.http_port = None
        self.sliver_ipv4 = None
        self.sliver_ipv6 = None
        self.status_ipv4 = None
        self.status_ipv6 = None

        self.required_fields = set([
            message.SERVER_ID,
            message.FQDN_IPv4,
            message.FQDN_IPv6,
            message.SERVER_PORT,
            message.HTTP_PORT,
            message.SITE_ID,
            message.SLICE_ID,
            message.STATUS_IPv4,
            message.STATUS_IPv6,
            message.TOOL_ID])

    def initialize_from_dictionary(self, dictionary):
        for field in self.required_fields:
            if field not in dictionary:
                raise message.FormatError('Missing field %s.' % (field))

        self.tool_id = dictionary[message.TOOL_ID]
        self.slice_id = dictionary[message.SLICE_ID]
        self.server_id = dictionary[message.SERVER_ID]
        self.server_port = dictionary[message.SERVER_PORT]
        self.http_port = dictionary[message.HTTP_PORT]
        self.fqdn_ipv4 = dictionary[message.FQDN_IPv4]
        self.fqdn_ipv6 = dictionary[message.FQDN_IPv6]
        self.site_id = dictionary[message.SITE_ID]
        self.status = dictionary[message.STATUS_IPv4]
        self.status = dictionary[message.STATUS_IPv6]
        self.sliver_ipv4 = ''
        self.sliver_ipv6 = ''

        if message.TIMESTAMP in dictionary:
            self.timestamp = dictionary[message.TIMESTAMP]
        if message.SLIVER_IPv4 in dictionary:
            self.sliver_ipv4 = dictionary[message.SLIVER_IPv4]
        if message.SLIVER_IPv6 in dictionary:
            self.sliver_ipv6 = dictionary[message.SLIVER_IPv6]

    def to_dictionary(self):
        dictionary = {}
        dictionary[message.SITE_ID] = self.site_id
        dictionary[message.SERVER_ID] = self.server_id
        dictionary[message.SERVER_PORT] = self.server_port
        dictionary[message.HTTP_PORT] = self.http_port
        dictionary[message.FQDN_IPv4] = self.fqdn_ipv4
        dictionary[message.FQDN_IPv6] = self.fqdn_ipv6
        dictionary[message.SLICE_ID] = self.slice_id
        dictionary[message.SLIVER_IPv4] = self.sliver_ipv4
        dictionary[message.SLIVER_IPv6] = self.sliver_ipv6
        dictionary[message.STATUS_IPv4] = self.status_ipv4
        dictionary[message.STATUS_IPv6] = self.status_ipv6
        dictionary[message.TIMESTAMP] = self.timestamp
        dictionary[message.TOOL_ID] = self.tool_id

        return dictionary
