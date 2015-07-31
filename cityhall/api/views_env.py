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
from .views import CACHE, CONN, auth_token_in_cache
from lib.db.db import Rights


def ensure_guest_exists():
    if 'guest' in CACHE:
        return True

    guest_auth = CONN.get_auth('guest', '')

    if guest_auth:
        CACHE['guest'] = guest_auth
        return True

    return False


def authenticate_for_get(request):
    cache_key = request.META.get('HTTP_AUTH_TOKEN', None)

    if cache_key is None:
        auth = CACHE['guest'] if ensure_guest_exists() else None
    else:
        auth = CACHE.get(cache_key, None)

    if auth is None:
        if cache_key is None:
            return HttpResponse('No guest account was created')
        else:
            return HttpResponse('Auth-Token specified is invalid/expired')

    return None


def get_auth_from_request(request, env):
    cache_key = request.META.get('HTTP_AUTH_TOKEN', None)
    auth = CACHE['guest'] \
        if (cache_key is None) and ensure_guest_exists() \
        else CACHE[cache_key]

    if auth.get_permissions(env) < Rights.Read:
        return [
            False,
            {
                'Response': 'Failure',
                'Message': 'Do not have read permissions to ' + env
            }
        ]

    return [True, auth]


class EnvView(Endpoint):
    class RequestInfo(object):
        def __init__(self, request, *args, **kwargs):
            self.env_path = kwargs.get('env_path', None)
            if not self.env_path:
                self.valid = False
                self.error_message = {
                    'Response': 'Failure',
                    'Message': 'Expected environment and path to be included'
                }
                return

            first_slash = self.env_path.find('/')
            if first_slash < 1:
                self.valid = False
                self.error_message = {
                    'Response': 'Failure',
                    'Message': 'Expected the path to include environment name'
                }
                return

            self.env = self.env_path[:first_slash]
            self.path = self.env_path[first_slash:]
            auth = get_auth_from_request(request, self.env)
            self.override = request.GET.get('override', None)

            if not auth[0]:
                self.valid = False
                self.error_message = auth[1]
            else:
                self.auth = auth[1]
                self.valid = True

    def authenticate(self, request):
        if (request.method == 'POST') or (request.method == 'DELETE'):
            return auth_token_in_cache(request)
        elif request.method == 'GET':
            return authenticate_for_get(request)
        raise HttpResponse("Unsupported method type")

    def delete(self, request, *args, **kwargs):
        info = EnvView.RequestInfo(request, *args, **kwargs)
        if not info.valid:
            return info.error_message

        env = info.auth.get_env(info.env)
        try:
            env.delete(info.path, info.override)
            return {'Response': 'Ok'}
        except Exception as e:
            return {'Response': 'Failure', 'Message': e.message}

    def post(self, request, *args, **kwargs):
        info = EnvView.RequestInfo(request, *args, **kwargs)
        if not info.valid:
            return info.error_message

        value = request.data.get('value', None)
        protect = request.data.get('protect', None)

        if (info.path is None) or (info.env is None) or\
                ((value is None) and (protect is None)):
            return {
                'Response': 'Failure',
                'Message': 'Expected an environment, name, and value or '
                           'protect to create'
            }

        if protect is not None:
            protect = str(protect).upper() in ['1', 'TRUE', 'Y', 'YES', ]

        env = info.auth.get_env(info.env)
        try:
            if protect is not None:
                env.set_protect(protect, info.path, info.override)
            if value is not None:
                env.set(info.path, value, info.override)
            return {'Response': 'Ok'}
        except Exception as e:
            return {'Response': 'Failure', 'Message': e.message}

    def get(self, request, *args, **kwargs):
        info = EnvView.RequestInfo(request, *args, **kwargs)
        if not info.valid:
            return info.error_message

        call_args = [info.auth, info.env, info.path, info.override]

        if 'viewchildren' in request.GET:
            return EnvView.get_children_for(*call_args)
        elif 'viewhistory' in request.GET:
            return EnvView.get_history_for(*call_args)

        return EnvView.get_value_for(*call_args)

    @staticmethod
    def _sanitize(env, path):
        ret = '/' + env + path
        return ret if ret[-1] == '/' else ret + '/'

    @staticmethod
    def get_value_for(auth, env, path, override):
        if override is None:
            return {
                'Response': 'Ok',
                'value': auth.get_env(env).get(path)
            }
        else:
            return {
                'Response': 'Ok',
                'value': auth.get_env(env).get_explicit(path, override)
            }

    @staticmethod
    def get_history_for(auth, env, path, override):
        override = '' if not override else override
        return {
            'Response': 'Ok',
            'History': auth.get_env(env).get_history(path, override)
        }

    @staticmethod
    def get_children_for(auth, env, path, override=None):
        if override:
            return {
                'Response': 'Failure',
                'Message': 'Cannot get children for an override',
            }

        sanitized_path = EnvView._sanitize(env, path)
        children = auth.get_env(env).get_children(path)

        return {
            'Response': 'Ok',
            'path': sanitized_path,
            'children': children
        }
