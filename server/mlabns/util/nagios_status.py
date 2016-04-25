import logging
import re
import urllib2

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message


class Error(Exception):
    pass


class NagiosStatusUnparseableError(Error):
    """Indicates that there was an error parsing Nagios status information."""

    def __init__(self, cause):
        super(NagiosStatusUnparseableError, self).__init__(cause)


class NagiosSliceInfo(object):
    """Represents the information necessary to query Nagios by slice.

    Attributes:
        slice_url: URL for querying Nagios.
        tool_id: Name of a specific tool.
        address_family: Formatted string for specifying ipv4 or ipv6.
    """

    def __init__(self, slice_url, tool_id, address_family):
        self._slice_url = slice_url
        self._tool_id = tool_id
        self._address_family = address_family

    def __eq__(self, other):
        return all([self.slice_url == other.slice_url, self.tool_id ==
                    other.tool_id, self.address_family == other.address_family])

    def __ne__(self, other):
        return any([self.slice_url != other.slice_url, self.tool_id !=
                    other.tool_id, self.address_family != other.address_family])

    @property
    def slice_url(self):
        return self._slice_url

    @property
    def tool_id(self):
        return self._tool_id

    @property
    def address_family(self):
        return self._address_family


def authenticate_nagios(nagios):
    """Configures urllib to do HTTP Password authentication for Nagios URLs.

    Args:
        nagios: object containing Nagios auth information
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
            'Nagios status missing or unparseable: %s' % status)

    slice_fqdn = sliver_fields[0]
    state = sliver_fields[1]
    tool_extra = sliver_fields[3]
    sliver_fqdn = slice_fqdn.split('/')[0]

    return sliver_fqdn, state, tool_extra


def get_slice_info(nagios_base_url):
    """Builds a list of NagiosSliceInfo objects to query Nagios for all slices.

    Args:
        nagios_base_url: Base URL to get Nagios slice information.

    Returns:
         List of NagiosSliceInfo objects.
    """
    slice_objects = []
    for tool_id in model.get_all_tool_ids():
        for address_family in ['', '_ipv6']:
            slice_url = (nagios_base_url + '?show_state=1&service_name=' +
                         tool_id + address_family + "&plugin_output=1")
            slice_objects.append(NagiosSliceInfo(slice_url, tool_id,
                                                 address_family))

    return slice_objects


def get_slice_status(url):
    """Read slice status from Nagios.

    Args:
        url: String representing the URL to Nagios for a single slice.

    Returns:
        A dict mapping sliver fqdn to a dictionary representing the sliver's
        status. For example:

        {'foo.mlab1.site1.measurement-lab.org': {
            'status': 'online',
            'tool_extra': 'example tool extra'
            }
        }

        None if Nagios status is blank or url is inaccessible.
    """
    status = {}
    try:
        lines = urllib2.urlopen(url).read().strip('\n').split('\n')
    except urllib2.HTTPError:
        # TODO(claudiu) Notify(email) when this happens.
        logging.error('Cannot open %s.', url)
        return None

    lines = filter(lambda x: not x.isspace(), lines)
    if not lines:
        logging.info('Nagios gave empty response for sliver status at the' \
                     'following url: %s',url)
        return None

    for line in lines:
        try:
            sliver_fqdn, state, tool_extra = parse_sliver_tool_status(line)
        except NagiosStatusUnparseableError as e:
            logging.error('Unable to parse Nagios sliver status. %s', e)
            continue

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
