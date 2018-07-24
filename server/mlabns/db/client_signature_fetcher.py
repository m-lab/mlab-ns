from mlabns.util import constants

from google.appengine.api import memcache


class ClientSignatureFetcher(object):
    """Fetch probability of matched client signature from AppEngine memcache."""

    def fetch(self, key):
        """Fetch probability of matched client signature.

        Args:
            key: A string in format like:
                 'name=127.0.0.1#userAgent#/ndt_ssl?policy=geo_options'

        Returns:
            The probability of matched client signature or 0 if there is no
            matched entry.
        """
        matched_requests = memcache.get(
            key,
            namespace=constants.MEMCACHE_NAMESPACE_REQUESTS)
        if matched_requests and len(matched_requests) == 1:
            return matched_requests[0].probability
        return 0
