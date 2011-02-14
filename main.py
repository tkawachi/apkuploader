#!/usr/bin/env python

from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

import os

import models

class TopHandler(webapp.RequestHandler):
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
                 "action_url": blobstore.create_upload_url('/c/upload')}
        self.response.out.write(template.render(
                os.path.join(os.path.dirname(__file__), "template", "top.html"),
                param))

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    PREFIX = '/c/upload'
    REDIRECT_URL = '/c/top/'

    def post(self):
        upload_files = self.get_uploads("fname")
        if not upload_files or not upload_files[0] \
                or not upload_files[0].filename:
            self.redirect(self.REDIRECT_URL)
            return
        apk_entry = models.ApkEntry.insert_new_entry()
        apk_entry.fname = upload_files[0].filename
        apk_entry.blob = upload_files[0]
        apk_entry.owner = users.get_current_user()
        apk_entry.ipaddrs = self.request.get("ipaddrs")
        apk_entry.accounts = self.request.get("accounts")
        apk_entry.put()
        self.redirect(self.REDIRECT_URL)

class DeleteHandler(webapp.RequestHandler):
    PREFIX = '/c/delete/'
    def get(self):
        key_name = self.request.path[len(self.PREFIX):]
        entry = models.ApkEntry.get_by_key_name(key_name)
        if not entry or entry.owner != users.get_current_user():
            self.response.set_status(404)
            return

        if entry.blob:
            blob = blobstore.BlobInfo.get(entry.blob)
            if blob:
                blob.delete()
        entry.delete()
        self.redirect("/")

class UpdateHandler(blobstore_handlers.BlobstoreUploadHandler):
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
                 "post_url": blobstore.create_upload_url(self.request.path) }
        self.response.out.write(template.render(
                os.path.join(os.path.dirname(__file__), "template", "update_form.html"),
                param))

    def post(self):
        key_name = self.request.path[len(self.PREFIX):]
        entry = models.ApkEntry.get_by_key_name(key_name)
        if not entry or entry.owner != users.get_current_user():
            self.response.set_status(404)
            return


        upload_files = self.get_uploads("fname")
        old_blob = None
        if upload_files and upload_files[0] \
                and upload_files[0].filename:
            # update blob only when fname is passed
            old_blob = entry.blob
            blob = upload_files[0].key()
            entry.data = None # delete if old data is in .data
            entry.fname = upload_files[0].filename

        entry.ipaddrs = self.request.get("ipaddrs")
        entry.accounts = self.request.get("accounts")
        entry.put()
        if old_blob:
            old_blob.delete()
        self.redirect("/")

def main():
    application = webapp.WSGIApplication([(TopHandler.PREFIX + '.*', TopHandler),
                                          (UploadHandler.PREFIX + '.*', UploadHandler),
                                          (DeleteHandler.PREFIX + '.*', DeleteHandler),
                                          (UpdateHandler.PREFIX + '.*', UpdateHandler)
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
