from google.appengine.ext import db

import random
import time

class ChunkedBlob(db.Model):
    """Blob for over 1MB. GAE limits the size of each entity to
    1MB. It also limits the size of Blob to 1MB.
    """

    CHUNK_SIZE = 900 * 1000 # byte
    
    is_start = db.BooleanProperty()
    data = db.BlobProperty() # Max size of this field is CHUNK_SIZE
    next_entity = db.SelfReferenceProperty() # Empty if the end of blob.

    @classmethod
    def put_binary(cls, data):
        """Save large data as ChunkedBlob and returns the starting
        entity.
        """
        prev_entity = None
        starting_entity = None
        offset = 0
        while offset < len(data):
            entity = ChunkedBlob()
            if not prev_entity:
                entity.is_start = True
                starting_entity = entity
            entity.data = data[offset:offset + cls.CHUNK_SIZE]
            entity.put()
            if prev_entity:
                prev_entity.next_entity = entity
                prev_entity.put()
            prev_entity = entity
            offset += cls.CHUNK_SIZE
        return starting_entity

    def get_binary(self):
        """Returns concatenated data"""
        result = ''
        entity = self
        while True:
            result += entity.data
            if not entity.next_entity:
                break
            entity = entity.next_entity
        return result

    def delete_binary(self):
        entity = self
        while entity:
            to_be_deleted = entity
            entity = entity.next_entity
            to_be_deleted.delete()

class ApkEntry(db.Model):
    owner = db.UserProperty()
    fname = db.StringProperty()
    data = db.BlobProperty() # deprecated for new data. refer chunked_blob
    chunked_blob = db.ReferenceProperty(ChunkedBlob)
    ipaddrs = db.StringProperty()
    accounts = db.StringProperty()
    basic_id = db.StringProperty()
    basic_pw = db.StringProperty()
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
