import logging
import os
import random

from google.appengine.api import memcache

from mlabns.db import model
from mlabns.util import constants

# Default value if datastore contains no records.
default_reverse_proxy = model.ReverseProxyProbability(
    name="default",
    probability=0.0,
    url="https://mlab-ns.appspot.com")


def get_reverse_proxy():
    """Reads and caches the first (and only) ReverseProxyProbability record."""
    reverse_proxy = memcache.get(
        'default',
        namespace=constants.MEMCACHE_NAMESPACE_REVERSE_PROXY)
    if reverse_proxy is None:
        for prob in model.ReverseProxyProbability.all().run():
            if not memcache.set(
                    'default',
                    prob,
                    time=1800,
                    namespace=constants.MEMCACHE_NAMESPACE_REVERSE_PROXY):
                logging.error(
                    'Failed to update ReverseProxyProbability in memcache')
            return prob
        logging.info('No reverse proxy probability found; using default')
        reverse_proxy = default_reverse_proxy
    return reverse_proxy


def during_business_hours(t):
    """Indicates whether the current time is within EST busines hours, M-Th.

    AppEngine system time is always in UTC. This function hard-codes business
    times as 9-5 EST and only returns True Monday through Thursday.

    Args:
        t: datetime, the time to check.

    Returns:
        bool, True if during business hours, M-Th.
    """
    if os.environ.get('IGNORE_BUSINESS_HOURS', None) is not None:
        return True
    # EST 9am = 14 UTC, 5pm EST = 22 UTC, 0=M, 1=Tu, 2=W, 3=Th.
    return t.hour >= 14 and t.hour <= 22 and t.weekday() < 4


def try_reverse_proxy_url(request, t):
    """Possibly generates a URL to perform a reverse proxy for client request.

    Args:
       request: webapp.Request, request used to construct complete url.
       t: datetime.datetime, time used to evaluate business hours.

    Returns:
       str, empty string for no action, or complete URL to reverse proxy.
    """
    if request.path != '/ndt_ssl':
        return ""
    rdp = get_reverse_proxy()
    if random.uniform(0, 1) > rdp.probability:
        return ""
    if not during_business_hours(t):
        return ""
    return rdp.url + request.path_qs
