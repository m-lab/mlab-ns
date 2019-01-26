import re
import os


def is_production_site(site_name):
    """Determines if the given site name matches the production site schema

    Args:
        site_name: Name of site to check (e.g. "lga01")

    Returns:
        True if the site name matches the schema of a production site.
    """
    # Regular platform site names match the pattern [a-z]{3}\d{2}, but we now
    # have some cloud VMs that we use for special purposes on the platform, and
    # these sites end with the letter "c" (for "cloud"), not unlike testing
    # sites end in the letter "t". The following regex should match both regular
    # platform nodes as well as cloud VMs.
    return re.match('^[a-z]{3}(\d{2}|\dc)$', site_name, re.IGNORECASE) != None


def is_production_slice(slice_fqdn):
    """Determines if the given FQDN matches the schema for a production slice

    Args:
        slice_fqdn: Slice FQDN to check (e.g.
          "ndt.iupui.mlab3.mad01.measurement-lab.org")

    Returns:
        True if the slice FQDN matches the schema of a production slice.
    """
    fqdn_parts = slice_fqdn.split('.')
    # Look for a production site name in the FQDN
    for i in range(1, len(fqdn_parts)):
        # If a production site name exists, the previous part of the FQDN will
        # be the server ID. For example, in "mlab1.nuq02", nuq02 is the site
        # name and mlab1 is the server ID.
        if is_production_site(fqdn_parts[i]):
            server_id = fqdn_parts[i - 1]
            return re.match(os.environ.get('SERVER_REGEX', '^mlab[123]$'), server_id, re.IGNORECASE) != None
    return False
