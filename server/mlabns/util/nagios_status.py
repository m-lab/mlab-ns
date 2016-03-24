class NagiosStatusUpdateError(Exception):
    pass


class NagiosStatusUnparseableError(NagiosStatusUpdateError):
    """Indicates that there was an error parsing Nagios status information."""

    def __init__(self, cause):
        super(NagiosStatusUnparseableError, self).__init__(cause)


def parse_sliver_tool_status(status):
    """Parses the status of a single sliver tool.

    Expected form is [fqdn][state][state type][extra notes]

    Ex:
        ndt.foo.measurement-lab.org/ndt 0 1 TCP OK - 0.242 second response time

    Args:
        status: one line corresponding to the status of a sliver tool.

    Returns:
        Tuple of the form (sliver fqdn, current state, extra information)
        None if status can't be parsed properly
    """
    sliver_fields = status.split(' ', 3)

    if len(sliver_fields) <= 3 or status.isspace():
        raise NagiosStatusUnparseableError(
            'Nagios status missing or unparseable.')

    slice_fqdn = sliver_fields[0]
    state = sliver_fields[1]
    tool_extra = sliver_fields[3]
    sliver_fqdn = slice_fqdn.split('/')[0]

    return sliver_fqdn, state, tool_extra
