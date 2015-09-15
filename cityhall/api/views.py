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

from restless.views import Endpoint, HttpResponse
from django.conf import settings

from lib.db.connection import Connection
from lib.db.db import Rights
from api.cache import CACHE


DB = settings.CITY_HALL_DATABASE
CONN = Connection(DB)
CONN.connect()


def print_cache(request):
    print "dumping cache {}:".format(str(CACHE))

    if request is None:
        print "  request is None.  What the heck??"
        return

    method = request.method
    url = request.path
    print "    {} to url: {}".format(method, url)

    token = request.META.get('HTTP_AUTH_TOKEN', 'request has no auth token')

    for k in CACHE._LRUCacheDict__values:
        print "    " + k + ".  name: " + CACHE[k].name

    message = "in cache" if token in CACHE else "not in cache"
    print "    token " + str(token) + " is " + message


def auth_token_in_cache(request):
    cache_key = request.META.get('HTTP_AUTH_TOKEN', None)

    if cache_key in CACHE:
        return None

    if cache_key is None:
        return HttpResponse('Must specify Auth-Token in headers')
    return HttpResponse('Auth-Token specified is invalid/expired')


class Info(Endpoint):
    def get(self, request):
        return {'Database': str(DB), 'Status': 'Alive'}


class Create(Endpoint):
    def get(self, request):
        CONN.create_default_env()
        self._create_guest()
        return {'Response': 'Ok'}

    def _create_guest(self):
        auth = CONN.get_auth('cityhall', '')
        auth.create_user('guest', '')
        auth.grant('auto', 'guest', Rights.Read)
        CACHE['guest'] = CONN.get_auth('guest', '')
