import logging
import os
import random

from mlabns.db import model

_redirect = None

# Default value if datastore contains no records.
default_redirect = model.RedirectProbability(name="default",
                                             probability=0.0,
                                             url="https://mlab-ns.appspot.com")


def get_redirection():
    """Reads and caches the first (and only) RedirectProbability record."""
    global _redirect
    if _redirect is None:
        for prob in model.RedirectProbability.all().run():
            _redirect = prob
            return _redirect

        logging.info('No redirect probability found; using default')
        _redirect = default_redirect
    return _redirect


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


def try_redirect_url(request, t):
    """Possibly generates a URL to redirect a client.

    Args:
       request: webapp.Request, request used to construct complete url.
       t: datetime.datetime, time used to evaluate business hours.

    Returns:
       str, empty string for no action, or complete URL for client redirect.
    """
    if request.path != '/ndt_ssl':
        return ""
    rdp = get_redirection()
    if random.uniform(0, 1) > rdp.probability:
        return ""
    if not during_business_hours(t):
        return ""
    return rdp.url + request.path_qs