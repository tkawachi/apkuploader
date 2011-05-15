#!/usr/bin/env python

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
    PREFIX = '/c/top/'
    def get(self):
        query = models.ApkEntry.all()
        query.filter("owner =", users.get_current_user())
        query.order("uploaded_date")
        param = {"remote_addr": self.request.remote_addr,
                 "host_url": self.request.host_url,
                 "my_entries": query,
                 "logout_url": users.create_logout_url("/"),
                 "username": users.get_current_user().email(),
                 "action_url": self.PREFIX,
                 "errmsg": self.request.get("errmsg"),
                 "accounts": self.request.get("accounts"),
                 "ipaddrs": self.request.get("ipaddrs")}
        self.render_template("top.html", param)

    def post(self):
        data = self.request.get("fname")
        if not data:
            url = self.PREFIX
            url += "?errmsg=" + "<h2 style=\"color: red\">File is not selected.</h2>"
            url += "&accounts=" + self.request.get("accounts")
            url += "&ipaddrs=" + self.request.get("ipaddrs")
            self.redirect(url)
            return
        blob = models.ChunkedBlob.put_binary(data)
        apk_entry = models.ApkEntry.insert_new_entry()
        apk_entry.chunked_blob = blob
        apk_entry.fname = self.request.POST[u'fname'].filename
        apk_entry.owner = users.get_current_user()
        apk_entry.ipaddrs = self.request.get("ipaddrs")
        # Input check for accounts. Valid format is xxx@yyy
        accounts = self.request.get("accounts")
        accounts = accounts.replace(" ", "")
        accounts = accounts.rstrip(",")
        if accounts != "":
            acclist = accounts.split(",")
            for acc in acclist:
                if "@" not in acc:
                    url = self.PREFIX
                    url += "?errmsg=" + "<h2 style=\"color: red\">Account is invalid.</h2>"
                    url += "&accounts=" + self.request.get("accounts")
                    url += "&ipaddrs=" + self.request.get("ipaddrs")
                    self.redirect(url)
                    return
        apk_entry.accounts = accounts

        apk_entry.basic_id = self.request.get("basic_id")
        apk_entry.basic_pw = self.request.get("basic_pw")
        
        apk_entry.put()
        self.redirect(self.PREFIX)


class DeleteHandler(AbstractHandler):
    PREFIX = '/c/delete/'
    def get(self):
        key_name = self.request.path[len(self.PREFIX):]
        entry = models.ApkEntry.get_by_key_name(key_name)
        if not entry or entry.owner != users.get_current_user():
            self.response.set_status(404)
            return

        if entry.chunked_blob:
            entry.chunked_blob.delete_binary()
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
        old_blob = None
        if data:
            # update blob only when fname is passed
            old_blob = entry.chunked_blob
            blob = models.ChunkedBlob.put_binary(data)
            entry.chunked_blob = blob
            entry.data = None # delete if old data is in .data
            entry.fname = self.request.POST[u'fname'].filename
        entry.ipaddrs = self.request.get("ipaddrs")
        entry.accounts = self.request.get("accounts")
        entry.put()
        if old_blob:
            old_blob.delete_binary()
        self.redirect("/")

def main():
    application = webapp.WSGIApplication([(TopHandler.PREFIX + '.*', TopHandler),
                                          (DeleteHandler.PREFIX + '.*', DeleteHandler),
                                          (UpdateHandler.PREFIX + '.*', UpdateHandler)
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
