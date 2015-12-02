"""Rewrites raw M-Lab FQDNs to apply post-processing or annotations."""

import logging

from mlabns.util import message


def rewrite(fqdn, address_family, tool_id):
    """Rewrites an FQDN to add necessary annotations and special-casing.

    Performs the following rewrites on an FQDN:
    * Adds a v4/v6 annotation if the client requested an explicit address family
    * Applies a workaround to fix FQDNs for NDT-SSL queries.

    Args:
        fqdn: A tool FQDN with no address family specific annotation.
        address_family: The address family for which to create the FQDN or None
            to create an address family agnostic FQDN.
        tool_id: Name of tool associated with the FQDN (e.g. 'ndt_ssl').

    Returns:
        FQDN after rewriting to apply all modifications to the raw FQDN.
    """
    rewritten_fqdn = _apply_af_awareness(fqdn, address_family)
    rewritten_fqdn = _apply_ndt_ssl_workaround(rewritten_fqdn, tool_id)
    return rewritten_fqdn


def _apply_af_awareness(fqdn, address_family):
    """Adds the v4/v6 only annotation to the fqdn.

    Example:
        fqdn:       'npad.iupui.mlab3.ath01.measurement-lab.org'
        ipv4 only:  'npad.iupui.mlab3v4.ath01.measurement-lab.org'
        ipv6 only:  'npad.iupui.mlab3v6.ath01.measurement-lab.org'

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

    fqdn_parts = _split_fqdn(fqdn)
    fqdn_parts[2] += fqdn_annotation

    return '.'.join(fqdn_parts)


def _apply_ndt_ssl_workaround(fqdn, tool_id):
    """Rewrites ndt_ssl FQDNs to use dash separators for subdomains.

    Rewrites ndt_ssl FQDNs to have proper formatting. Leaves FQDNs for all
    other tools unmodified.

    The NDT-SSL test uses dashes instead of dots as separators in the subdomain.
    For example, instead of:
        ndt.iupui.mlab1.lga06.measurement-lab.org
    NDT-SSL uses:
        ndt-iupui-mlab1-lga06.measurement-lab.org

    The long term plan is to adjust all FQDNs to match this schema, but
    currently Nagios (the source of mlab-ns' FQDN data) is not are not
    aware of the dash-separator schema. We apply a special-case workaround here
    so that we serve the correct FQDNs to clients for NDT-SSL queries until we
    fix the naming in Nagios.

    See https://github.com/m-lab/mlab-ns/issues/48 for more information.

    Args:
        fqdn: Tool's FQDN before any rewrites.
        tool_id: Name of tool associated with the FQDN (e.g. 'ndt_ssl').

    Returns:
        FQDN with rewritten dashes if a rewrite was necessary, the original FQDN
        otherwise.
    """
    # If this is not ndt_ssl, leave FQDN untouched.
    if tool_id != 'ndt_ssl':
        return fqdn
    fqdn_parts = _split_fqdn(fqdn)

    # Create subdomain like ndt-iupui-mlab1-lga06
    subdomain = '-'.join(fqdn_parts[:-2])

    return '.'.join((subdomain, fqdn_parts[-2], fqdn_parts[-1]))


def _split_fqdn(fqdn):
    return fqdn.split('.')
