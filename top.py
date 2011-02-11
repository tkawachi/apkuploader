#!/usr/bin/env python

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

import os

class TopHandler(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            self.redirect("/c/top/")
            return

        html = "top_guest.html"
        variables = {"login_url": users.create_login_url("/")}

        path = os.path.join(os.path.dirname(__file__), "template", html)
        self.response.out.write(template.render(path, variables))

        
def main():
    application = webapp.WSGIApplication([("/", TopHandler)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
