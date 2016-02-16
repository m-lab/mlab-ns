import json
import os

import jinja2

from mlabns.util import message


def _get_jinja_environment():
    current_dir = os.path.dirname(__file__)
    templates_dir = os.path.join(current_dir, '../templates')
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
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
        request.response.out.write(
            _get_jinja_template('not_found.html').render())


def send_server_error(request, output_type=message.FORMAT_HTML):
    request.error(500)
    if output_type == message.FORMAT_JSON:
        data = {}
        data['status_code'] = '500 Internal Server Error'
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)
    else:
        request.response.out.write(
            _get_jinja_template('not_found.html').render())


def send_success(request, output_type=message.FORMAT_JSON):
    if output_type == message.FORMAT_JSON:
        data = {}
        data['status_code'] = '200 OK'
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)
    else:
        request.response.out.write('<html> Success! </html>')
