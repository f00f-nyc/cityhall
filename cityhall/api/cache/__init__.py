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

from lru import LRUCacheDict
from django.conf import settings


class CacheDict(LRUCacheDict):
    def __contains__(self, item):
        return self.has_key(item)  # noqa

    def get(self, key, default):
        return self[key] if self.has_key(key) else default  # noqa


_cache = None
_instantiated = False


def instance():
    print "### getting cache instance"
    global _instantiated

    if not _instantiated:
        print "### creating cache"
        global _cache
        _cache = CacheDict(
            max_size=settings.ENV_CACHE['SIZE'],
            expiration=settings.ENV_CACHE['EXPIRATION_SEC'],
            thread_clear=False,
            thread_clear_min_check=settings.ENV_CACHE['MULTI_THREAD_POLL_SEC'],
            concurrent=settings.ENV_CACHE['MULTI_THREAD'],
        )
        _instantiated = True

    return _cache
