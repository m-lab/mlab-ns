def parse_sliver_tool_status(status):
    """Parses the status of a single sliver tool.
    Args:
        status: one line corresponding to the status of a single sliver tool
        from nagios.
    Returns:
        list of the form [sliver_fqdn, status, tool_extras]
        None if status can't be parsed properly
    """
    sliver_fields = status.split(' ')

    if len(sliver_fields) <= 3:
        return None

    slice_fqdn = sliver_fields[0]
    state = sliver_fields[1]
    tool_extra = " ".join(sliver_fields[3:])
    sliver_fqdn = slice_fqdn.split('/')[0]

    return [sliver_fqdn, state, tool_extra]
