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

from restless.views import HttpResponse
from .views import CONN, auth_token_in_cache
from lib.db.db import Rights
from django.core.cache import cache


def ensure_guest_exists():
    have_guest = cache['guest']

    if have_guest:
        return True

    guest_auth = CONN.get_auth('guest', '')

    if guest_auth:
        cache.set('guest', guest_auth)
        return True

    return False


def authenticate_for_get(request):
    cache_key = request.META.get('HTTP_AUTH_TOKEN', None)

    if cache_key is None:
        auth = cache.get('guest') if ensure_guest_exists() else None
    else:
        auth = cache.get(cache_key, None)

    if auth is None:
        if cache_key is None:
            return HttpResponse('No guest account was created')
        else:
            return HttpResponse('Auth-Token specified is invalid/expired')

    return None


def get_auth_from_request(request, env):
    cache_key = request.META.get('HTTP_AUTH_TOKEN', None)
    auth = cache.get('guest') \
        if (cache_key is None) and ensure_guest_exists() \
        else cache.get(cache_key)

    if auth.get_permissions(env) < Rights.Read:
        return [
            False,
            {
                'Response': 'Failure',
                'Message': 'Do not have read permissions to ' + env
            }
        ]

    return [True, auth]


def is_valid(request):
    if (request.method == 'POST') \
            or (request.method == 'DELETE')\
            or (request.method == 'PUT'):
        return auth_token_in_cache(request)
    elif request.method == 'GET':
        return authenticate_for_get(request)
    raise HttpResponse("Unsupported method type")
