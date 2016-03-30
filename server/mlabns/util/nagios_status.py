import re
import urllib2

from mlabns.db import model


class Error(Exception):
    pass


class NagiosStatusUnparseableError(Error):
    """Indicates that there was an error parsing Nagios status information."""

    def __init__(self, cause):
        super(NagiosStatusUnparseableError, self).__init__(cause)

class NagiosSliceInfo(object):
    """Represents the information necessary to query nagios by slice.

    Attributes:
        slice_url: Base url for querying nagios.
        tool_id: Name of a specific tool.
        ip_version: Formatted string for specifying ipv4 or ipv6.

    """
    def __init__(self, slice_url, tool_id, ip_version):
        self.slice_url = slice_url
        self.tool_id = tool_id
        self.ip_version= ip_version


def authenticate_nagios(nagios):
    """Configures urllib to do HTTP Password authentication for Nagios URLs.

    Args:
        nagios: object containing nagios auth information
    """
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password(None, nagios.url, nagios.username,
                                  nagios.password)

    authhandler = urllib2.HTTPDigestAuthHandler(password_manager)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)


def parse_sliver_tool_status(status):
    """Parses the status of a single sliver tool.

    This status is returned from Nagios, the M-Lab monitoring system.
    Expected form is [fqdn][state][state type][extra notes]

    Ex:
        ndt.foo.measurement-lab.org/ndt 0 1 TCP OK - 0.242 second response time

    Args:
        status: One line corresponding to the status of a sliver tool.

    Returns:
        Tuple of the form (sliver fqdn, current state, extra information)

    Raises:
        NagiosStatusUnparseableError: Error can be triggered by empty statuses
            or statuses that can't be separated into exactly four fields.
    """
    sliver_fields = re.split(r'\s+', status.strip(), maxsplit=3)

    if len(sliver_fields) != 4:
        raise NagiosStatusUnparseableError(
            'Nagios status missing or unparseable.')

    slice_fqdn = sliver_fields[0]
    state = sliver_fields[1]
    tool_extra = sliver_fields[3]
    sliver_fqdn = slice_fqdn.split('/')[0]

    return sliver_fqdn, state, tool_extra

def get_slice_urls(nagios_url, nagios_suffixes):
    """Builds a list of NagiosSliceInfo objects to query Nagios for all slices.

    Args:
        nagios_url: Base url to get nagios slice information.
        nagios_suffixes: List of suffixes that specifiy ip version in nagios.

    Returns:
         List of NagiosSliceInfo objects
    """
    urls = []
    tools_gql = nagios_status_data.get_tools_by_id()
    for tool in tools_gql:
        for ipversion in nagios_suffixes:
            slice_url = (nagios_url + '?show_state=1&service_name=' +
                         tool.tool_id + ipversion + "&plugin_output=1")
            urls.append((slice_url, tool.tool_id, ipversion))

    return urls

