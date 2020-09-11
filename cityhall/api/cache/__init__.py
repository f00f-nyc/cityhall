# Copyright 2015 Digital Borderlands Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from datetime import timedelta

import collections
import pickle
import redis
import uuid


class CacheDict:
    def __init__(self, capacity):
        self.capacity = capacity
        self.values = collections.OrderedDict()

    def __contains__(self, item):
        return item in self.values

    def get(self, key, default):
        try:
            value = self.values.pop(key)
            self.values[key] = value
            return value
        except KeyError:
            if default:
                return default
            return None

    def set(self, key, value):
        try:
            self.values.pop(key)
        except KeyError:
            if len(self.values) >= self.capacity:
                self.values.popitem(last=False)
        self.values[key] = value

    def delete(self, key):
        try:
            del self.values[key]
        except KeyError:
            pass
    
    def items(self):
        return self.values.items()

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __getitem__(self, item):
        return self.get(item, None)


class RedisDict:
    def __init__(self, host, lifetime_seconds, prefix):
        self.lifetime = timedelta(seconds=lifetime_seconds)
        self.redis = redis.Redis(host=host)
        self.prefix = prefix

    def __contains__(self, item):
        return self.redis.exists(f"{self.prefix}::{item}")

    def get(self, key, default):
        try:
            ret = self.redis.get(f"{self.prefix}::{key}")
            print(f"Attempted to get `{self.prefix}::{key}` and got back an item of {len(ret)} bytes")
            return default if ret is None and default else pickle.loads(ret)
        except:
            print(f"Caught exception during get")
            return None

    def set(self, key, value):
        try:
            pickled = pickle.dumps(value)
            print(f"Attempting to set `{self.prefix}::{key}` to an array of {len(pickled)} bytes)")
            self.redis.setex(f"{self.prefix}::{key}", self.lifetime, pickled)
        except:
            print("Caught exception during set")
            pass

    def delete(self, key):
        try:
            self.redis.delete(f"{self.prefix}::{key}")
        except:
            pass

    def items(self):
        return ()

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __getitem__(self, item):
        return self.get(item, None)
    

class CacheFactory:
    @staticmethod
    def GetCache(db, prefix=None):
        if prefix is None:
            prefix = uuid.uuid4().hex

        if db.settings('cache_type') == 'redis':
            lifetime_seconds = int(db.settings('redis_cache', 'lifetime_seconds'))
            host = db.settings('redis_cache', 'host')
            return RedisDict(host, lifetime_seconds, prefix)
        else:
            capacity = db.settings('cache', 'env_capacity')
            return CacheDict(capacity)
