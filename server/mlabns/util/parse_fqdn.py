import logging
import re


def parse(fqdn):
    # If there is a dash instead of a dot after the machine name, then this is
    # a v2 ("flat") name, then parse the fqdn accordingly, else parse it by v1
    # conventions.
    if re.search('mlab[1-4]-', fqdn):
        regex = '([a-z-]+?)-(mlab[1-4])-([a-z]{3}[0-9ct]{2})\.(mlab-[a-z]+)\.(measurement-lab.org)'
        version = 'v2'
    else:
        regex = '([a-z.]+?)\.(mlab[1-4])\.([a-z]{3}[0-9ct]{2})\.(measurement-lab.org)'
        version = 'v1'

    m = re.match(regex, fqdn)
    if not m:
        logging.error('Failed to parse FQDN: %s', fqdn)
        return False

    p = list(m.groups())

    fqdn_parts = {}

    # If the experiment part of the FQDN has a dot or dash, then split it apart
    # into experiment and org.
    s = re.match('([a-z]+)([.-])([a-z]+)', p[0])
    if s:
        fqdn_parts['experiment'] = s.group(1)
        fqdn_parts['org'] = s.group(3)
    else:
        fqdn_parts['experiment'] = p[0]
        fqdn_parts['org'] = ''

    if version == 'v2':
        fqdn_parts['project'] = p[3]
        fqdn_parts['domain'] = p[4]
    else:
        fqdn_parts['project'] = ''
        fqdn_parts['domain'] = p[3]

    fqdn_parts['machine'] = p[1]
    fqdn_parts['site'] = p[2]

    return fqdn_parts
