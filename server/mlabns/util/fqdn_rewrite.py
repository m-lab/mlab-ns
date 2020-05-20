"""Rewrites raw M-Lab FQDNs to apply post-processing or annotations."""

import logging

from mlabns.util import message
from mlabns.util import parse_fqdn


def rewrite(fqdn, address_family, tool_id):
    """Rewrites an FQDN to add necessary annotations and special-casing.

    Performs the following rewrites on an FQDN:
    * Adds a v4/v6 annotation if the client requested an explicit address family
    * Applies a workaround to fix FQDNs for NDT-SSL and ndt7 queries.

    Args:
        fqdn: A tool FQDN with no address family specific annotation.
        address_family: The address family for which to create the FQDN or None
            to create an address family agnostic FQDN.
        tool_id: Name of tool associated with the FQDN (e.g. 'ndt_ssl').

    Returns:
        FQDN after rewriting to apply all modifications to the raw FQDN.
    """
    rewritten_fqdn = _apply_af_awareness(fqdn, address_family)
    return rewritten_fqdn


def _apply_af_awareness(fqdn, address_family):
    """Adds the v4/v6 only annotation to the fqdn.

    Example:
        fqdn:       'ndt.iupui.mlab3.ath01.measurement-lab.org'
        ipv4 only:  'ndt.iupui.mlab3v4.ath01.measurement-lab.org'
        ipv6 only:  'ndt.iupui.mlab3v6.ath01.measurement-lab.org'

    Args:
        fqdn: A tool FQDN with no address family specific annotation.
        address_family: The address family for which to create the FQDN or None
            to create an address family agnostic FQDN.

    Returns:
        A FQDN specific to a particular address family, or the original FQDN
        if an address family is not specified.
    """
    if not address_family:
        fqdn_annotation = ''
    elif address_family == message.ADDRESS_FAMILY_IPv4:
        fqdn_annotation = 'v4'
    elif address_family == message.ADDRESS_FAMILY_IPv6:
        fqdn_annotation = 'v6'
    else:
        logging.error('Unrecognized address family: %s', address_family)
        return fqdn

    fqdn_parts = parse_fqdn.parse(fqdn)
    if not fqdn_parts:
        logging.error('Cannot parse FQDN: %s', fqdn)
        return fqdn
    decorated_machine = fqdn_parts['machine'] + fqdn_annotation

    return fqdn.replace(fqdn_parts['machine'], decorated_machine)
