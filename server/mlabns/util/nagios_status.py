from google.appengine.ext import db

import logging
import time
import urllib2

from mlabns.db import nagios_status_data
from mlabns.util import constants
from mlabns.util import message


def authenticate_nagios(nagios):
    """Handle authenticating with nagios.

	Args:
		nagios: object containing nagios auth information
    """
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password(None, nagios.url, nagios.username,
                                  nagios.password)

    authhandler = urllib2.HTTPDigestAuthHandler(password_manager)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)


def get_slice_urls(nagios_url, nagios_suffixes):
    """Builds an array of (url, tool_id, ipversion) to access slice info.

    Args:
        nagios_url: base url to get nagios slice information

    Returns:
         list of tuples of the form (url, tool_id, ipversion)
    """
    urls = []
    tools_gql = nagios_status_data.get_tools_by_id()
    for tool in tools_gql:
        for ipversion in nagios_suffixes:
            slice_url = (nagios_url + '?show_state=1&service_name=' +
                tool.tool_id + ipversion + "&plugin_output=1")
            urls.append((slice_url, tool.tool_id, ipversion))

    return urls


def parse_sliver_tool_status(status):
    """Function to parse the status of a single sliver tool.

    Args:
        status: one line corresponding to the status of a single
        single sliver tool from nagios.

    Returns:
        None if status can't be parsed properly
        list of the form [sliver_fqdn, status, tool_extras]
    """
    sliver_fields = status.split(' ')

    if len(sliver_fields) <= 3:
        return None

    slice_fqdn = sliver_fields[0]
    state = sliver_fields[1]
    tool_extra = " ".join(sliver_fields[3:])
    sliver_fqdn = slice_fqdn.split('/')[0]

    return [sliver_fqdn, state, tool_extra]


def has_no_ip(sliver_tool, ipversion):
    """Boolean logic for checking if either ipversion has no ip stored.

    Args:
        sliver_tool: model object
        ipversion: string representation of ipversion

    Returns:
        True if ipversion has no ip stored in sliver_tool
        False otherwise

    """
    four = sliver_tool.sliver_ipv4 == message.NO_IP_ADDRESS and ipversion == constants.AF_IPV4
    six = sliver_tool.sliver_ipv6 == message.NO_IP_ADDRESS and ipversion == constants.AF_IPV6
    return four or six


def was_online(sliver_tool, ipversion):
    """Boolean logic for checking if either ipversion was online.

    Args:
        sliver_tool: model object
        ipversion: string representation of ipversion

    Returns:
        True if ipversion is online in sliver_tool
        False otherwise
    """
    four = sliver_tool.status_ipv4 == message.STATUS_ONLINE and ipversion == constants.AF_IPV4
    six = sliver_tool.status_ipv6 == message.STATUS_ONLINE and ipversion == constants.AF_IPV6
    return four or six


def evaluate_status_update(sliver_tool, ipversion, slice_status):
    """Performs the necessary updates to sliver_tool.

    Modifies SliverTool model instance.

    Args:
        sliver_tool: SliverTool model instance
        ipversion: string representation of ipversion
        slice_status: dictionary of dictionary representing slice status
    """
    if has_no_ip(sliver_tool, ipversion):
        if was_online(sliver_tool, ipversion):
            logging.warning(
                'Setting status of %s to offline due to missing IP.',
                sliver_tool.fqdn)
            if ipversion == constants.AF_IPV4:
                sliver_tool.status_ipv4 = message.STATUS_OFFLINE
            else:
                sliver_tool.status_ipv6 = message.STATUS_OFFLINE
    else:
        sliver_tool.tool_extra = slice_status[sliver_tool.fqdn]['tool_extra']
        if ipversion == constants.AF_IPV4:
            sliver_tool.status_ipv4 = slice_status[sliver_tool.fqdn]['status']
        else:
            sliver_tool.status_ipv6 = slice_status[sliver_tool.fqdn]['status']


def get_slice_status(url):
    """Reads slice status from Nagios, and creates dictionary representation.

    Args:
        url: URL to Nagios for a single slice.

    Returns:
        A dict that contains the status of the slivers in this
        slice {key=fqdn, status: dictionary of formatted status info}

        None if the url does not open.
    """
    status = {}
    try:
        slice_status = urllib2.urlopen(url).read().strip('\n').split('\n')
    except urllib2.HTTPError:
        logging.error('Cannot open %s to retrieve slice status.', url)
        return None
    for sliver in slice_status:

        parsed = parse_sliver_tool_status(sliver)
        if not parsed:
            logging.error('Unable to parse nagios sliver status info: %s.',
                          sliver)
            continue
        sliver_fqdn, state, tool_extra = parsed
        if state != constants.NAGIOS_SERVICE_STATUS_OK:
            status[sliver_fqdn] = {
                'status': message.STATUS_OFFLINE,
                'tool_extra': tool_extra
            }
        else:
            status[sliver_fqdn] = {
                'status': message.STATUS_ONLINE,
                'tool_extra': tool_extra
            }

    return status


def update_sliver_tools_status(slice_status, tool_id, ipversion):
    """Updates slice status info in datastore.

    Args:
        slice_status: dictionary representation of slice status
        tool_id: string representing the fqdn that resolves to an IP address.
        ipversion: string representation of ipversion
    """
    sliver_tools_gql = nagios_status_data.get_SliverTool_by_tool_id(tool_id)
    for sliver_tool in sliver_tools_gql:
        evaluate_status_update(sliver_tool, ipversion, slice_status)
        sliver_tool.update_request_timestamp = long(time.time())
        try:
            sliver_tool.put()
        except db.TransactionFailedError:
            logging.error('Failed to update status of %s to %s in datastore.',
                          sliver_tool.fqdn, slice_status[sliver_tool.fqdn])
            continue
