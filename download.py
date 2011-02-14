#!/usr/bin/env python

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

import os
import fnmatch

import models

class DownloadHandler(webapp.RequestHandler):

    def is_ip_allowed(self, entry):
        for allowed_ipaddr in entry.ipaddrs.split(","):
            if fnmatch.fnmatchcase(self.request.remote_addr, allowed_ipaddr):
                return True
        return False

    def is_user_allowed(self, entry, cur_user):
        for allowed_account in entry.accounts.split(","):
            if fnmatch.fnmatchcase(cur_user.email(), allowed_account):
                return True
        return False

    def respond_apk(self, entry):
        self.response.headers["Content-Type"] = \
            "application/vnd.android.package-archive"
        self.response.headers["Content-Disposition"] = \
            "attachment; filename=\"%s\"" % entry.fname
        if entry.data:
            data = entry.data
        else:
            data = entry.chunked_blob.get_binary()
        self.response.out.write(data)

    def get(self):
        path = self.request.path
        if not path or len(path) < 1 or path[0] != "/":
            self.response.set_status(404)
            return
        key_name = path[1:]
        entry = models.ApkEntry.get_by_key_name(key_name)
        if not entry:
            self.response.set_status(404)
            return

        if not entry.ipaddrs and not entry.accounts:
            # public available if both empty
            self.respond_apk(entry)
            return

        if entry.ipaddrs:
            if self.is_ip_allowed(entry):
                self.respond_apk(entry)
                return

        if entry.accounts:
            cur_user = users.get_current_user()
            if cur_user:
                if self.is_user_allowed(entry, cur_user):
                    self.respond_apk(entry)
                    return
            self.redirect(users.create_login_url(self.request.path))
            return

        self.response.set_status(404)

def main():
    application = webapp.WSGIApplication([('.*', DownloadHandler)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
