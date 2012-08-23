from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from mlabns.handlers import admin
from mlabns.handlers import update
from mlabns.handlers import lookup
from mlabns.handlers import registration
from mlabns.handlers import debug
from mlabns.handlers import log2bq
#from solution import level4

app = webapp.WSGIApplication(
    [(r'/admin.*', admin.AdminHandler),
    (r'/geo/.*', debug.DebugHandler),
    (r'/query/.*', debug.QueryHandler),
    (r'/status.*', debug.StatusHandler),
    (r'/map/.*', admin.MapViewHandler),
    (r'/register', registration.RegistrationHandler),
    (r'/tools/.*', debug.DebugHandler),
    (r'/update', update.UpdateHandler),
    (r'/cron/check_status', update.NagiosHandler),
  #  (r'/solution/level4', level4.Level4Handler),
    (r'/cron/process_logs', log2bq.Log2BigQueryHandler),
    (r'/history', log2bq.UserLookupHandler),
    (r'/.*', lookup.LookupHandler)],
    debug=True )

def main():
    run_wsgi_app(app)

if __name__ == "__main__":
    main()
