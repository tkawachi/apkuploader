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
import fnmatch

import models

class DownloadHandler(webapp.RequestHandler):
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
        if entry.ipaddrs:
            ip_allowed = False
            for allowed_ipaddr_pat in entry.ipaddrs.split(","):
                if fnmatch.fnmatchcase(self.request.remote_addr, allowed_ipaddr_pat):
                    ip_allowed = True
                    break
            if not ip_allowed:
                self.response.set_status(404)
                return
        self.response.headers["Content-Type"] = "application/vnd.android.package-archive"
        self.response.headers["Content-Disposition"] = "attachment; filename=\"%s\"" % entry.fname
        self.response.out.write(entry.data)

def main():
    application = webapp.WSGIApplication([('.*', DownloadHandler)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
