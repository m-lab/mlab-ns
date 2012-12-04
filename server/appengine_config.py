import os
from google.appengine.api import namespace_manager

major_ver, minor_ver = os.environ['CURRENT_VERSION_ID'].rsplit('.', 1)
namespace_manager.set_namespace(major_ver)

def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
