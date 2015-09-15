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
from django.core.cache import cache


DB = settings.CITY_HALL_DATABASE
CONN = Connection(DB)
CONN.connect()


def auth_token_in_cache(request):
    cache_key = request.META.get('HTTP_AUTH_TOKEN', None)

    if cache_key in cache:
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
        cache.set('guest', CONN.get_auth('guest', ''))
