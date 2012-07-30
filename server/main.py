from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from mlabns.handlers import admin
from mlabns.handlers import update
from mlabns.handlers import lookup
from mlabns.handlers import registration
from mlabns.handlers import debug

app = webapp.WSGIApplication(
    [(r'/admin.*', admin.AdminHandler),
    (r'/tools/.*', debug.InfoHandler),
    (r'/geo/.*', debug.InfoHandler),
    (r'/register', registration.RegistrationHandler),
    (r'/update', update.UpdateHandler),
    (r'/.*', lookup.LookupHandler)],
    debug=True )

def main():
    run_wsgi_app(app)

if __name__ == "__main__":
    main()
