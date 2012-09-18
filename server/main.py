from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from mlabns.handlers import admin
from mlabns.handlers import update
from mlabns.handlers import lookup
from mlabns.handlers import registration
from mlabns.handlers import debug
from mlabns.handlers import log2bq

app = webapp.WSGIApplication(
    [(r'/', admin.AdminHandler),
    (r'/admin.*', admin.AdminHandler),
    (r'/geo/.*', debug.DebugHandler),
    (r'/register', registration.RegistrationHandler),
    (r'/update', update.UpdateHandler),
    (r'/cron/check_status', update.NagiosUpdateHandler),
    (r'/cron/process_logs', log2bq.Log2BigQueryHandler),
    (r'/history', log2bq.UserLookupHandler),
    (r'/.*', lookup.LookupHandler)],
    debug=True )

def main():
    run_wsgi_app(app)

if __name__ == "__main__":
    main()
