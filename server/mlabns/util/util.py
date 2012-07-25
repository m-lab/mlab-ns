from google.appengine.ext.webapp import template

import json

def send_not_found(request, output_type='html'):
    request.error(404)
    if output_type == 'html':
        request.response.out.write(
            template.render('mlabns/templates/not_found.html', {}))
    if output_type == 'json':
        data = {}
        data['error'] = 'Not found'
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)

def send_server_error(request, output_type='html'):
    request.error(500)
    if output_type == 'html':
        request.response.out.write(
            template.render('mlabns/templates/not_found.html', {}))
    if output_type == 'json':
        data = {}
        data['status_code'] = '500 Internal Server Error'
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)

def send_success(request, output_type='json'):
    if output_type == 'html':
        request.response.out.write('<html> Success! </html>')
    if output_type == 'json':
        data = {}
        data['status_code'] = '200 OK'
        json_data = json.dumps(data)
        request.response.headers['Content-Type'] = 'application/json'
        request.response.out.write(json_data)
