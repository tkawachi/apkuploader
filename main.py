#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

import os

import models

class TopHandler(webapp.RequestHandler):
    def get(self):
        query = models.ApkEntry.all()
        query.filter("owner =", users.get_current_user())
        query.order("uploaded_date")
        param = {"remote_addr": self.request.remote_addr,
                 "my_entries": query}
        self.render_template("top.html", param)

    def post(self):
        apk_entry = models.ApkEntry.insert_new_entry()
        data = self.request.get("fname")
        apk_entry.data = db.Blob(data)
        apk_entry.fname = self.request.POST[u'fname'].filename
        apk_entry.owner = users.get_current_user()
        apk_entry.ipaddrs = self.request.get("ipaddrs")
        apk_entry.put()
        self.redirect("/")

    def render_template(self, html, variables):
        path = os.path.join(os.path.dirname(__file__), "template", html)
        self.response.out.write(template.render(path, variables))


def main():
    application = webapp.WSGIApplication([('/', TopHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
