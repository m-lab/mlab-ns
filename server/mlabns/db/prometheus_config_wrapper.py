import logging

from google.appengine.api import memcache

from mlabns.db import model
from mlabns.util import constants


def get_prometheus_config():
    """Retrieves Prometheus config info. First checks memcache, then datastore.

    Returns:
        Prometheus model instance
    """
    prometheus = memcache.get(constants.DEFAULT_PROMETHEUS_ENTRY)
    if not prometheus:
        prometheus = model.Prometheus.get_by_key_name(
            constants.DEFAULT_PROMETHEUS_ENTRY)
        if prometheus:
            memcache.set(constants.DEFAULT_PROMETHEUS_ENTRY, prometheus)
        else:
            logging.error('Datastore does not have the Prometheus credentials.')

    return prometheus
