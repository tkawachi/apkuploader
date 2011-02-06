from google.appengine.ext import db

import random
import time

class ApkEntry(db.Model):
    owner = db.UserProperty()
    fname = db.StringProperty()
    data = db.BlobProperty()
    ipaddrs = db.StringProperty()
    uploaded_date = db.DateTimeProperty(auto_now=True)
    salt = db.StringProperty(required=True)

    # http://satoshi.blogs.com/life/2009/11/unique.html
    @classmethod
    def insert_new_entry(cls):
        l = 5
        fail_cnt = 0
        while True:
            key_name = cls.gen_key_name(l)
            salt = str(time.time()) + str(random.random())
            entry = cls.get_or_insert(key_name=key_name, salt=salt)
            if entry.salt == salt:
                return entry
            if fail_cnt > 10:
                l += 1

    @classmethod
    def gen_key_name(cls, l):
        alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        num = "0123456789"
        # First char should be a number
        return "".join(random.sample(alpha, 1)) + \
            "".join(random.sample(alpha + num, l - 1))
