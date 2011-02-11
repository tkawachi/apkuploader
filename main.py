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

class AbstractHandler(webapp.RequestHandler):
    def render_template(self, html, variables):
        path = os.path.join(os.path.dirname(__file__), "template", html)
        self.response.out.write(template.render(path, variables))

class TopHandler(AbstractHandler):
    def get(self):
        query = models.ApkEntry.all()
        query.filter("owner =", users.get_current_user())
        query.order("uploaded_date")
        param = {"remote_addr": self.request.remote_addr,
                 "host_url": self.request.host_url,
                 "my_entries": query,
                 "logout_url": users.create_logout_url("/")}
        self.render_template("top.html", param)

    def post(self):
        data = self.request.get("fname")
        if not data:
            self.redirect("/")
            return
        apk_entry = models.ApkEntry.insert_new_entry()
        apk_entry.data = db.Blob(data)
        apk_entry.fname = self.request.POST[u'fname'].filename
        apk_entry.owner = users.get_current_user()
        apk_entry.ipaddrs = self.request.get("ipaddrs")
        apk_entry.accounts = self.request.get("accounts")
        apk_entry.put()
        self.redirect("/")


class DeleteHandler(AbstractHandler):
    PREFIX = '/c/delete/'
    def get(self):
        key_name = self.request.path[len(self.PREFIX):]
        entry = models.ApkEntry.get_by_key_name(key_name)
        if not entry or entry.owner != users.get_current_user():
            self.response.set_status(404)
            return

        entry.delete()
        self.redirect("/")

class UpdateHandler(AbstractHandler):
    """Update handler for an entry.
    """
    PREFIX = '/c/update/'

    def get(self):
        key_name = self.request.path[len(self.PREFIX):]
        entry = models.ApkEntry.get_by_key_name(key_name)
        if not entry or entry.owner != users.get_current_user():
            self.redirect("/")
            return

        param = {"remote_addr": self.request.remote_addr,
                 "host_url": self.request.host_url,
                 "entry": entry,
                 "post_url": self.request.path }
        self.render_template("update_form.html", param)

    def post(self):
        key_name = self.request.path[len(self.PREFIX):]
        entry = models.ApkEntry.get_by_key_name(key_name)
        if not entry or entry.owner != users.get_current_user():
            self.response.set_status(404)
            return

        data = self.request.get("fname")
        if data:
            # update blob only when fname is passed
            entry.data = db.Blob(data)
            entry.fname = self.request.POST[u'fname'].filename
        entry.ipaddrs = self.request.get("ipaddrs")
        entry.accounts = self.request.get("accounts")
        entry.put()
        self.redirect("/")

def main():
    application = webapp.WSGIApplication([('/', TopHandler),
                                          (DeleteHandler.PREFIX + '.*', DeleteHandler),
                                          (UpdateHandler.PREFIX + '.*', UpdateHandler)
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
