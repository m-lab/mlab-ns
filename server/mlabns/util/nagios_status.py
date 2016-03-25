import re


class Error(Exception):
    pass


class NagiosStatusUnparseableError(Error):
    """Indicates that there was an error parsing Nagios status information."""

    def __init__(self, cause):
        super(NagiosStatusUnparseableError, self).__init__(cause)


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
