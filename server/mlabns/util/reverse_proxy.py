import logging
import os
import random

from google.appengine.api import memcache

from mlabns.db import model
from mlabns.util import constants

# Default value if datastore contains no record for a given experiment.
# This object should not be returned directly, but you can make a copy
# with a custom name by calling default_reverse_proxy.with_name("name").
default_reverse_proxy = model.ReverseProxyProbability(
    name="default",
    probability=0.0,
    url="https://mlab-ns.appspot.com")


def get_reverse_proxy(experiment):
    """Reads the ReverseProxyProbability record for an experiment.

    If the entity is not cached, it also refreshes the cache.
    """
    reverse_proxy = memcache.get(
        experiment,
        namespace=constants.MEMCACHE_NAMESPACE_REVERSE_PROXY)

    if reverse_proxy is None:
        # Update ReverseProxyProbability for all the experiments.
        for prob in model.ReverseProxyProbability.all().run():
            if experiment == prob.name:
                reverse_proxy = prob

            if not memcache.set(
                    prob.name,
                    prob,
                    time=1800,
                    namespace=constants.MEMCACHE_NAMESPACE_REVERSE_PROXY):
                logging.error(
                    'Failed to update ReverseProxyProbability in memcache ' +
                    'for experiment %s', prob.name)

        if reverse_proxy is None:
            logging.info('No reverse proxy probability found; using default')
            reverse_proxy = default_reverse_proxy.with_name(experiment)

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


def try_reverse_proxy_url(query, t):
    """Possibly generates a URL to perform a reverse proxy for client request.

    Args:
       query: lookup_query.LookupQuery, query used to construct complete url.
       t: datetime.datetime, time used to evaluate business hours.

    Returns:
       str, empty string for no action, or complete URL to reverse proxy.
    """
    if query.path != '/ndt_ssl' and query.path != '/ndt7':
        return ""

    experiment = query.path.strip('/')
    rdp = get_reverse_proxy(experiment)
    if random.uniform(0, 1) > rdp.probability:
        return ""
    if query.path == '/ndt_ssl' and not during_business_hours(t):
        return ""

    latlon = 'lat=%f&lon=%f' % (query.latitude, query.longitude)
    query_str = query.path_qs + ('&' if '?' in query.path_qs else '?') + latlon
    return rdp.url + query_str
