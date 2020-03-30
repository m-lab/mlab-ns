import logging
import re


def parse(fqdn):
    """Parses an M-Lab FQDN into its constituent parts.

    Args:
        fqdn: str, an M-Lab FQDN e.g., ndt-iupui-mlab1-den05.mlab-oti.measurement-lab.org

    Returns:
        dict representing the constituent parts.
    """
    # This regex *should* match all valid M-Lab domain names, for both nodes
    # and experiments, for both v1 and v2 names. It makes use of non-capturging
    # groups denoted by '(?:)'. What is interesting is that you can specify
    # capturing groups inside of non-capturing groups.
    regex = '(?:([a-z]+)(?:[.-]([a-z]+))?[.-])?(mlab[1-4])[.-]([a-z]{3}[0-9ct]{2})(?:\.(mlab-[a-z]+))?\.(.*)$'

    matches = re.match(regex, fqdn)
    if not matches or len(matches.groups()) != 6:
        logging.error('Failed to parse FQDN: %s', fqdn)
        return {}

    parts = list(matches.groups())

    fqdn_parts = {
        'experiment': parts[0],
        'org': parts[1],
        'machine': parts[2],
        'site': parts[3],
        'project': parts[4],
        'domain': parts[5],
    }

    return fqdn_parts
