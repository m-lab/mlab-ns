import logging
import re


def parse(fqdn):
    """Parses an M-Lab FQDN into its constituent parts.

    Args:
        fqdn: str, an M-Lab FQDN e.g., ndt-iupui-mlab1-den05.mlab-oti.measurement-lab.org

    Returns:
        dict representing the constituent parts.
    """
    # If there is a dash instead of a dot after the machine name, then this is
    # a v2 ("flat") name, then parse the fqdn accordingly, else parse it by v1
    # conventions.
    if re.search('mlab[1-4]-', fqdn):
        regex = '([a-z-]+?)-(mlab[1-4])-([a-z]{3}[0-9ct]{2})\.(mlab-[a-z]+)\.(measurement-lab.org)'
        version = 'v2'
    else:
        regex = '([a-z.]+?)\.(mlab[1-4])\.([a-z]{3}[0-9ct]{2})\.(measurement-lab.org)'
        version = 'v1'

    matches = re.match(regex, fqdn)
    if not matches:
        logging.error('Failed to parse FQDN: %s', fqdn)
        return {}

    parts = list(matches.groups())

    fqdn_parts = {}

    # If the experiment part of the FQDN has a dot or dash, then split it apart
    # into experiment and org.
    experiment_org = re.match('([a-z]+)([.-])([a-z]+)', parts[0])
    if experiment_org:
        fqdn_parts['experiment'] = experiment_org.group(1)
        fqdn_parts['org'] = experiment_org.group(3)
    else:
        fqdn_parts['experiment'] = parts[0]
        fqdn_parts['org'] = ''

    if version == 'v2':
        fqdn_parts['project'] = parts[3]
        fqdn_parts['domain'] = parts[4]
    else:
        fqdn_parts['project'] = ''
        fqdn_parts['domain'] = parts[3]

    fqdn_parts['machine'] = parts[1]
    fqdn_parts['site'] = parts[2]

    return fqdn_parts
