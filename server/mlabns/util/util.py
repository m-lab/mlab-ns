import json

from google.appengine.ext.webapp import template
from mlabns.util import message

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
            template.render('mlabns/templates/not_found.html', {}))

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
            template.render('mlabns/templates/not_found.html', {}))

def send_success(request, output_type=message.FORMAT_JSON):
    if output_type == message.FORMAT_JSON:
        data = {}
        data['status_code'] = '200 OK'
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)
    else:
        request.response.out.write('<html> Success! </html>')

def send_teapot(request, output_type=message.FORMAT_HTML):
    request.error(404)
    if output_type == message.FORMAT_JSON:
        data={}
        data['status_code'] = "418 I'm a teapot"
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)
    else:
        request.response.out.write(
            template.render('mlabns/templates/teapot.html', {}))
