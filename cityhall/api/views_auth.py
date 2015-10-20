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
from django.conf import settings
from .views import CONN
from session import (
    is_valid, get_auth_from_request, get_auth_or_create_guest,
    end_request, NOT_AUTHENTICATED, SESSION_AUTH
)


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

            end_request(request, auth)
            return {'Response': 'Ok', 'version': settings.API_VERSION}

        return {
            'Response': 'Failure',
            'Message': 'Request was incomplete, expected "username" and '
                       '"passhash"'
        }

    def delete(self, request, *args, **kwargs):
        auth_json = request.session.get(SESSION_AUTH, None)
        if auth_json is None:
            return {
                "Response": "Failure",
                "Message": "Not currently logged in"
            }

        del request.session[SESSION_AUTH]
        request.session.modified = True
        return {"Response": "Ok"}


class Environments(Endpoint):
    def authenticate(self, request):
        return is_valid(request)

    def get(self, request, *args, **kwargs):
        env = kwargs.get('env', '##unable to get ENV##')
        auth = get_auth_from_request(request, env)

        if not auth[0]:
            return auth[1]
        else:
            users = auth[1].get_users(env)
            return {
                'Response': 'Ok',
                'Users': users
            }

    def post(self, request, *args, **kwargs):
        name = kwargs.get('env', None)
        if name is None:
            return {
                'Response': 'Failure',
                'Message': 'Expected a name for environment to create'
            }


        auth = get_auth_or_create_guest(request)
        if auth is None:
            return NOT_AUTHENTICATED

        created = auth.create_env(name)
        if not created:
            return {
                'Response': 'Failure',
                'Message': 'Environment "'+name+'" already exists',
            }

        end_request(request, auth)
        return {
            'Response': 'Ok',
            'Message': 'Environment "'+name+'" created successfully',
        }


class Users(Endpoint):
    NO_USER = {'Response': 'Failure', 'Message': 'Expected a user to retrieve'}

    def authenticate(self, request):
        return is_valid(request)

    def get(self, request, *args, **kwargs):
        user = kwargs.get('user', None)
        if not user:
            return Users.NO_USER

        auth = get_auth_or_create_guest(request)
        if not auth:
            return NOT_AUTHENTICATED

        try:
            envs = auth.get_user(user)
            return {'Response': 'Ok', 'Environments': envs}
        except Exception as ex:
            return {
                'Response': 'Failure',
                'Message': ex.message,
            }

    def post(self, request, *args, **kwargs):
        user = kwargs.get('user', None)
        passhash = request.data.get('passhash', None)
        if (user is None) or (passhash is None):
            return {
                'Response': 'Failure',
                'Message': 'Expected a user and passhash to create user'
            }

        auth = get_auth_or_create_guest(request)
        if not auth:
            return NOT_AUTHENTICATED

        try:
            auth.create_user(user, passhash)
            end_request(request, auth)
            return {'Response': 'Ok'}
        except Exception as ex:
            return {'Response': 'Failure', 'Message': ex.message}

    def put(self, request, *args, **kwargs):
        user = kwargs.get('user', None)
        passhash = request.data.get('passhash', None)
        auth = get_auth_or_create_guest(request)

        if not auth:
            return NOT_AUTHENTICATED

        if auth.name != user:
            return {
                'Response': 'Failure',
                'Message': 'May only update your own user'
            }

        auth.update_user(user, passhash)
        end_request(request, auth)
        return {'Response': 'Ok'}

    def delete(self, request, *args, **kwargs):
        user = kwargs.get('user', None)

        if not user:
            return {
                'Response': 'Failure',
                'Message': 'Delete API call is invalid, no user specified'
            }

        auth = get_auth_or_create_guest(request)
        if not auth:
            return NOT_AUTHENTICATED

        try:
            if auth.delete_user(user):
                end_request(request, auth)
                return {'Response': 'Ok'}
            else:
                return {
                    'Response': 'Failure',
                    'Message': "Operation failed, user may not exist or you "
                               "don't have Grant permissions to all "
                               "environments of that user."
                }
        except Exception as ex:
            return {'Response': 'Failure', 'Message': ex.message}


class UserDefaultEnv(Endpoint):
    def authenticate(self, request):
        return is_valid(request)

    def get(self, request, *args, **kwargs):
        user = kwargs.get('user', None)
        if not user:
            return Users.NO_USER
        auth = get_auth_or_create_guest(request)
        return {
            'Response': 'Ok',
            'value': auth.get_default_env()
        }

    def post(self, request, *args, **kwargs):
        user = kwargs.get('user')
        if not user:
            return Users.NO_USER
        auth = get_auth_or_create_guest(request)
        default_env = request.data.get('env', None)
        if not default_env:
            return {
                'Response': 'Failure',
                'Message': 'Expected an "env" value to set.'
            }
        auth.set_default_env(default_env)
        return {'Response': 'Ok', 'Message': 'Default set to: ' + default_env}


class GrantRights(Endpoint):
    def authenticate(self, request):
        return is_valid(request)

    def post(self, request):
        env = request.data.get('env', None)
        user = request.data.get('user', None)
        rights = request.data.get('rights', None)
        if (user is None) or (env is None) or (rights is None):
            return {
                'Response': 'Failure',
                'Message': 'Expected a user, env, and rights for grant'
            }

        auth = get_auth_or_create_guest(request)
        if auth is None:
            return NOT_AUTHENTICATED

        try:
            rights = int(rights)
        except ValueError:
            return {
                'Response': 'Failure',
                'Message': 'rights value should be an integer (0-4)'
            }

        ret = auth.grant(env, user, rights)
        end_request(request, auth)
        return {'Response': ret[0], 'Message': ret[1]}
