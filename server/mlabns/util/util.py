import datetime
import json
import os
import random

import jinja2

from mlabns.util import message
from mlabns.util import redirect


def _get_jinja_environment():
    current_dir = os.path.dirname(__file__)
    templates_dir = os.path.join(current_dir, '../templates')
    return jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir),
                              extensions=['jinja2.ext.autoescape'],
                              autoescape=True)


def _get_jinja_template(template_filename):
    return _get_jinja_environment().get_template(template_filename)


def send_not_found(request, output_type=message.FORMAT_HTML):
    request.error(404)
    if output_type == message.FORMAT_JSON:
        data = {}
        data['status_code'] = '404 Not found'
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)
    else:
        request.response.out.write(_get_jinja_template('not_found.html').render(
        ))


def send_server_error(request, output_type=message.FORMAT_HTML):
    request.error(500)
    if output_type == message.FORMAT_JSON:
        data = {}
        data['status_code'] = '500 Internal Server Error'
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)
    else:
        request.response.out.write(_get_jinja_template('not_found.html').render(
        ))


def send_success(request, output_type=message.FORMAT_JSON):
    if output_type == message.FORMAT_JSON:
        data = {}
        data['status_code'] = '200 OK'
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)
    else:
        request.response.out.write('<html> Success! </html>')


def during_business_hours(t):
    """Indicates whether the current time is within EST busines hours, M-Th.

    AppEngine system time is always in UTC. This function hard-codes business
    times as 9-5 EST and only returns True Monday through Thursday.

    Args:
        t: datetime, the time to check.

    Returns:
        bool, True if during business hours, M-Th.
    """
    # EST 9am = 14 UTC, 5pm EST = 22 UTC, 0=M, 1=Tu, 2=W, 3=Th.
    return t.hour >= 14 and t.hour <= 22 and t.weekday() < 4


def try_redirect_url(request, t):
    if request.path != '/ndt_ssl':
        return ""
    rdp = redirect.get_redirection()
    if random.uniform(0, 1) > rdp.probability:
        return ""
    if not during_business_hours(t):
        return ""
    return rdp.url + request.path_qs
