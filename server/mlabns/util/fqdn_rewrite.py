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
    # If this is ndt_ssl, apply the special case workaround.
    if tool_id == 'ndt_ssl':
        rewritten_fqdn = _apply_ndt_ssl_workaround(rewritten_fqdn)
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


def _apply_ndt_ssl_workaround(fqdn):
    """Rewrites ndt_ssl FQDNs to use dash separators for subdomains.

    The NDT-SSL test uses dashes instead of dots as separators in the subdomain,
    but Nagios currently reports the FQDNs as using dots.

    For example, instead of:

        ndt.iupui.mlab1.lga06.measurement-lab.org

    NDT-SSL uses:

        ndt-iupui-mlab1-lga06.measurement-lab.org

    We rewrite the dotted FQDNs to use dashes so that NDT-SSL works properly.
    This is intended to be a temporary workaround until we can find a solution
    that does not require NDT-SSL to be a special case from mlab-ns's
    perspective.

    See https://github.com/m-lab/mlab-ns/issues/48 for more information.

    Args:
        fqdn: An NDT-SSL FQDN in dotted notation.

    Returns:
        FQDN with rewritten dashes if a rewrite was necessary, the original FQDN
        otherwise.
    """
    fqdn_parts = _split_fqdn(fqdn)

    # Create subdomain like ndt-iupui-mlab1-lga06
    subdomain = '-'.join(fqdn_parts[:-2])

    return '.'.join((subdomain, fqdn_parts[-2], fqdn_parts[-1]))


def _split_fqdn(fqdn):
    return fqdn.split('.')
