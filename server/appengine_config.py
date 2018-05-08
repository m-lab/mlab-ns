def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app

# Add any libraries in the "mlabns/third_party" directory.
from google.appengine.ext import vendor
#vendor.add('mlabns/third_party/geoip2')
#vendor.add('mlabns/third_party/google_cloudstorage')
