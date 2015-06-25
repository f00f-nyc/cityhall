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

from restless.views import Endpoint
from .views import CONN, CACHE, auth_token_in_cache
import shortuuid


class Authenticate(Endpoint):
    def authenticate(self, request):
        """
        This method always returns true, since it's the authenticate endpoint.

        :param request: The method is expected to take this, but it is unused
        :return: True
        """
        return None

    def post(self, request):
        if 'username' in request.data and \
                'passhash' in request.data:
            user = request.data['username']
            passhash = request.data['passhash']
            auth = CONN.get_auth(user, passhash)

            if auth is None:
                return {
                    'Response': 'Failure',
                    'Message': 'Invalid username/password'
                }

            key = str(shortuuid.uuid())
            CACHE[key] = auth
            return {'Response': 'Ok', 'Token': key}

        return {
            'Response': 'Failure',
            'Message': 'Request was incomplete, expected "username" and '
                       '"passhash"'
        }


class CreateEnvironment(Endpoint):
    def authenticate(self, request):
        return auth_token_in_cache(request)

    def post(self, request):
        name = request.data.get('name', None)
        cache_key = request.META.get('HTTP_AUTH_TOKEN', None)
        auth = CACHE[cache_key]

        if name is None:
            return {
                'Response': 'Failure',
                'Message': 'Expected a name for environment to create'
            }

        if auth is None:
            return {
                'Response': 'Failure',
                'Message': 'Given token "' + cache_key +
                           '" could not be found in cache'
            }

        created = auth.create_env(name)
        if not created:
            return {
                'Response': 'Failure',
                'Message': 'Environment "'+name+'" already exists',
            }
        return {
            'Response': 'Ok',
            'Message': 'Environment "'+name+'" created successfully',
        }


class CreateUser(Endpoint):
    def authenticate(self, request):
        return auth_token_in_cache(request)

    def post(self, request):
        user = request.data.get('user', None)
        passhash = request.data.get('passhash', None)
        cache_key = request.META.get('HTTP_AUTH_TOKEN', None)
        auth = CACHE[cache_key]

        if (user is None) or (passhash is None):
            return {
                'Response': 'Failure',
                'Message': 'Expected a user and passhash to create user'
            }

        if auth is None:
            return {
                'Response': 'Failure',
                'Message': 'Given token "' + cache_key +
                           '" could not be found in cache'
            }

        auth.create_user(user, passhash)
        return {'Response': 'Ok'}


class GrantRights(Endpoint):
    def authenticate(self, request):
        return auth_token_in_cache(request)

    def post(self, request):
        env = request.data.get('env', None)
        user = request.data.get('user', None)
        rights = request.data.get('rights', None)
        cache_key = request.META.get('HTTP_AUTH_TOKEN', None)
        auth = CACHE[cache_key]

        if (user is None) or (env is None) or (rights is None):
            return {
                'Response': 'Failure',
                'Message': 'Expected a user, env, and rights for grant'
            }

        if auth is None:
            return {
                'Response': 'Failure',
                'Message': 'Given token "' + cache_key +
                           '" could not be found in cache'
            }

        try:
            rights = int(rights)
        except ValueError:
            return {
                'Return': 'Failure',
                'Message': 'rights value should be an integer (0-4)'
            }

        auth.grant(env, user, rights)
        return {'Response': 'Ok'}
