from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from mlabns.handlers import admin
from mlabns.handlers import docs
from mlabns.handlers import lookup
from mlabns.handlers import privacy
from mlabns.handlers import update
# from mlabns.handlers import log2bq

app = webapp.WSGIApplication(
    [(r'/', admin.AdminHandler),
    (r'/admin.*', admin.AdminHandler),
    (r'/cron/check_status', update.StatusUpdateHandler),
    (r'/cron/check_site', update.SiteRegistrationHandler),
    (r'/privacy', privacy.PrivacyHandler),
    (r'/docs', docs.DocsHandler),
    # (r'/cron/process_logs', log2bq.Log2BigQueryHandler),
    (r'/.*', lookup.LookupHandler)],
    debug=True )

def main():
    run_wsgi_app(app)

if __name__ == "__main__":
    main()
