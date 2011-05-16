#!/usr/bin/env python

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from base64 import b64decode

import fnmatch
import hashlib
import os
import random

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

    def is_basicAuthorized(self, entry):
        auth_header = self.request.headers.get('Authorization')
        if auth_header:
            auth = auth_header.split(' ')
            if len(auth) != 2 or auth[0] != 'Basic':
                return False
            info = b64decode(auth[1]).split(':')
            if len(info) != 2:
                return False
            # Check ID and password
            if info[0] == entry.basic_id and hashlib.sha256(info[1]).hexdigest() == entry.basic_pw:
                return True

    def gen_key(self, len):
        alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        num = "0123456789"
        return "".join(random.sample(alpha + num, len))

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

        # Remove string after "_" if redirected from basic-authed link
        path_parts = path.split("_")
        path = path_parts[0]
        if len(path_parts) >= 2:
            key_auth = path_parts[1]
        else:
            key_auth = None

        if not path or len(path) < 1 or path[0] != "/":
            self.response.set_status(404)
            return
        key_name = path[1:]
        entry = models.ApkEntry.get_by_key_name(key_name)
        if not entry:
            self.response.set_status(404)
            return
                      
        # if the path was postfixed w/ "_" + key_auth random string
        if key_auth != None:
            user_ip = memcache.get(key_auth)
            if user_ip == self.request.remote_addr:
                memcache.delete(key_auth)
                self.respond_apk(entry)
                return
            else:
                self.response.set_status(404)
                return

        if not entry.ipaddrs and not entry.accounts and not entry.basic_id:
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

        if entry.basic_id:
            if self.is_basicAuthorized(entry):
                # A file cannot be downloaded from Android device if
                # it is protected by Basic authentication directly.
                # So, after authenticated, redirect to a different address
                # that allows only the IP address cached here.
                # self.respond_apk(entry) is what is not working here.
                auth_key = self.gen_key(32)
                user_ip = self.request.remote_addr
                # Set expiration time a little long to 60 sec, because
                # user must start downloadeing before it expires.
                memcache.set(auth_key, user_ip, 60)
                self.redirect(self.request.url + "_" + auth_key)
                return
            else:
                self.response.set_status(401)
                self.response.headers['WWW-Authenticate'] = 'Basic realm="BasicTest"'
                return

        self.response.set_status(404)

def main():
    application = webapp.WSGIApplication([('.*', DownloadHandler)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
