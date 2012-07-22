from google.appengine.ext.webapp import template

import json

def not_found(request, output_type='html'):
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
