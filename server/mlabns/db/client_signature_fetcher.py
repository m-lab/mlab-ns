import logging
from mlabns.util import constants

from google.appengine.api import memcache


class ClientSignatureFetcher(object):

    def fetch(self, key):
        """Fetches probabilities associated with request signatures from AppEngine memcache.

        For each client signature, if there is a match in memcache, which means that this
        client was detected sending more than normal requests in the past 24 hours, then
        mlab-ns will assign this client to regular m-lab sites with probability p (usually p < 1),
        and assign this client to backup '0c' sites with probability 1-p. p is the 'probability'
        field of the matched entry.
        If there is no matched entry in the memcache, which means this client behaved normally
        and should always be assigned to a regular site, 1.0 will be returned.

        Args:
            key: A string in format like:
                 '127.0.0.1#Davlik 2.1.0 (blah blah blah)#resource'
                 resource will look like
                 '/ndt_ssl?policy=geo_options&format=json...'
        """
        # NB: records are ints encoded as strings. Ints are fixed-format floats.
        probability_str = memcache.get(
            key, namespace=constants.MEMCACHE_NAMESPACE_REQUESTS)
        # NB: allow probability to equal zero.
        if probability_str is not None:
            try:
                # Convert string to a float.
                return int(probability_str) / 10000.0
            except ValueError as e:
                logging.warning('Corrupt value in memcache: %s - %s', probability_str, e)
                # Fall through.
        return 1.0
