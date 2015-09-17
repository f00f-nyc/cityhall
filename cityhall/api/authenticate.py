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

import simplejson as json
from restless.views import HttpResponse
from .views import CONN
from lib.db.db import Rights
from lib.db.auth import Auth


SESSION_AUTH = 'cityhall-auth'
NOT_AUTHENTICATED = HttpResponse(
    'Session is not authenticated, '
    'and could not obtain get a guest credentials'
)


def serialize_auth(auth):
    auth_dict = {
        'name': auth.name,
        'roots_cache': {},
        'user_root': auth.user_root,
        'users_env': auth.users_env,
    }
    return json.dumps(auth_dict)


def deserialize_auth(auth_json):
    auth_dict = json.loads(auth_json)
    ret = Auth(
        db=CONN.db_connection.get_db(),
        name=auth_dict['name'],
        user_root=auth_dict['user_root']
    )
    ret.roots_cache = auth_dict['roots_cache']
    ret.users_env = auth_dict['users_env']
    return ret


def get_auth_or_create_guest(request):
    auth_json = request.session.get(SESSION_AUTH, None)
    if auth_json is None:
        auth = CONN.get_auth('guest', '')
        request.session[SESSION_AUTH] = serialize_auth(auth)
    else:
        auth = deserialize_auth(auth_json)
    return auth


def authenticate_for_get(request):
    auth = get_auth_or_create_guest(request)

    if auth is None:
        return NOT_AUTHENTICATED

    return None


def get_auth_from_request(request, env):
    auth = get_auth_or_create_guest(request)

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
        return None \
            if SESSION_AUTH in request.session \
            else HttpResponse('Must log in, first')
    elif request.method == 'GET':
        return authenticate_for_get(request)
    raise HttpResponse("Unsupported method type")
