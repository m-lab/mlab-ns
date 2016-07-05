import logging

from google.appengine.api import memcache

from mlabns.db import model
from mlabns.util import constants


def get_nagios_config():
    """Retrieves nagios config info. First checks memcache, then datastore.

    Returns:
        Nagios model instance
    """
    nagios = memcache.get(constants.DEFAULT_NAGIOS_ENTRY)
    if not nagios:
        nagios = model.Nagios.get_by_key_name(constants.DEFAULT_NAGIOS_ENTRY)
        if nagios:
            memcache.set(constants.DEFAULT_NAGIOS_ENTRY, nagios)
        else:
            logging.error('Datastore does not have the Nagios credentials.')

    return nagios
