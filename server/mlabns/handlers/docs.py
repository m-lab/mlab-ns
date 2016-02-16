from google.appengine.ext import webapp

from mlabns.util import constants
from mlabns.util import util


class DocsHandler(webapp.RequestHandler):

    def post(self):
        """Not implemented."""
        return util.send_not_found(self)

    def get(self):
        self.redirect(constants.DESIGN_DOC_URL)
