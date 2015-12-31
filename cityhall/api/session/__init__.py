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
from api.views import CONN
from .serialize import serialize_auth, deserialize_auth
from lib.db.db import Rights
from six import text_type


SESSION_AUTH = 'cityhall-auth'
NOT_AUTHENTICATED = HttpResponse(
    'Session is not authenticated, '
    'and could not obtain get a guest credentials'
)


def get_auth_or_create_guest(request):
    auth_json = request.session.get(SESSION_AUTH, None)
    if auth_json is None:
        auth = CONN.get_auth('guest', '')
        if auth is not None:
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


def clean_data(request):
    if isinstance(request.data, dict):
        return True
    if request.data is None:
        return True
    if request.data == "":
        return True
    try:
        request.data = json.loads(text_type(request.data))
        return True
    except:
        return False


def is_valid(request):
    if not clean_data(request):
        return HttpResponse('Invalid request. Body: ' + str(request.data))

    if (request.method == 'POST') \
            or (request.method == 'DELETE')\
            or (request.method == 'PUT'):
        return None \
            if SESSION_AUTH in request.session \
            else HttpResponse('Must log in, first')
    elif request.method == 'GET':
        return authenticate_for_get(request)
    raise HttpResponse("Unsupported method type")


def end_request(request, auth):
    request.session[SESSION_AUTH] = serialize_auth(auth)



