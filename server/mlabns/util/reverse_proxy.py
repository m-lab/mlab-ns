import logging
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


def try_reverse_proxy_url(query):
    """Possibly generates a URL to perform a reverse proxy for client request.

    Args:
       query: lookup_query.LookupQuery, query used to construct complete url.

    Returns:
       str, empty string for no action, or complete URL to reverse proxy.
    """
    if query.path != '/ndt_ssl' and query.path != '/ndt7':
        return ""

    experiment = query.path.strip('/')
    rdp = get_reverse_proxy(experiment)

    if random.uniform(0, 1) > rdp.probability:
        return ""

    latlon = 'lat=%f&lon=%f' % (query.latitude, query.longitude)
    query_str = query.path_qs + ('&' if '?' in query.path_qs else '?') + latlon
    return rdp.url + query_str
