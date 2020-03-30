import logging
import os
import re

from mlabns.util import parse_fqdn


def is_production_site(site_name):
    """Determines if the given site name matches the production site schema

    Args:
        site_name: Name of site to check (e.g. "lga01")

    Returns:
        True if the site name matches the schema of a production site.
    """
    site_regex = os.environ.get('SITE_REGEX')
    return re.match(site_regex, site_name, re.IGNORECASE) != None


def is_production_slice(slice_fqdn):
    """Determines if the given FQDN matches the schema for a production slice

    Args:
        slice_fqdn: Slice FQDN to check e.g.,
          "ndt.iupui.mlab3.mad01.measurement-lab.org"
          "wehe.mlab2.mad01.measurement-lab.org"
          "ndt-iupui-mlab2-mad01.mlab-oti.measurement-lab.org"

    Returns:
        True if the slice FQDN matches the schema of a production slice.
    """
    site_regex = os.environ.get('SITE_REGEX')
    machine_regex = os.environ.get('MACHINE_REGEX')

    fqdn_parts = parse_fqdn.parse(slice_fqdn)
    if not fqdn_parts:
        logging.error("Failed to parse FQDN: %s" % slice_fqdn)
        return False

    # Makes sure that the machine ("server") and site both match the current
    # patterns for production slices/sites.
    if re.match(site_regex, fqdn_parts['site'], re.IGNORECASE) and re.match(
            machine_regex, fqdn_parts['machine'], re.IGNORECASE):
        return True

    logging.info(
        "FQDN %s did not match site_regex (%s) AND/OR machine_regex (%s)" %
        (slice_fqdn, site_regex, machine_regex))
    return False
