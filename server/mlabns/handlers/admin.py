from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import oauth
from google.appengine.api import users
import logging
import os

class AdminHandler(webapp.RequestHandler):
    def post(self):
        self.response.out.write('Not found')

    def get(self):
        try:
            self.get2()
        except:
            logging.error("get: got an exception", exc_info=True)

    def get2(self):
        logging.debug("get: running")
        self.response.headers['Content-type'] = 'text/html'
        out = self.response.out
        out.write('<p>Oauth test</p>')
        try:
            user = oauth.get_current_user()
            admin = oauth.is_current_user_admin()
            out.write("<p>oauth: user %s admin %s</p>\n" % (user, admin))
        except oauth.Error, e:
            logging.error("oauth failed (%s)", e, exc_info=e)
            out.write("<p>oauth failed (%s)</p>\n" % (e))

        path_info = os.environ['PATH_INFO']
        try:
            user2 = users.get_current_user();
            admin2 = users.is_current_user_admin()
            login = users.create_login_url(dest_url=path_info)
            logout = users.create_logout_url(path_info)

            out.write("<p>user: user2 %s admin2 %s <a href='%s'>login</a> <a href='%s'>logout</a></p>\n" % (user2, admin2, login, logout))
        except user.Error, e:
            logging.error("user failed (%s)", e, exc_info=e)
            out.write("<p>user failed (%s)</p>\n" % (e))

        out.write('Ok')
