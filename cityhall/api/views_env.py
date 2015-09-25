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
from session import is_valid, get_auth_from_request, end_request
from lib.db.db import Rights


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
        return is_valid(request)

    def delete(self, request, *args, **kwargs):
        info = EnvView.RequestInfo(request, *args, **kwargs)
        if not info.valid:
            return info.error_message

        env = info.auth.get_env(info.env)
        try:
            env.delete(info.path, info.override)
            end_request(request, info.auth)
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

        if int(env.permissions) < Rights.Write:
            return {
                'Response': 'Failure',
                'Message': 'Do not have write permissions to ' + info.env
            }

        try:
            if protect is not None:
                # cannot set protect if doesn't exist, so ensure it exists
                exist = env.get_explicit(info.path, info.override)
                if (exist is None) or (exist[0] is None):
                    env.set(info.path, '', info.override)

                env.set_protect(protect, info.path, info.override)
            if value is not None:
                env.set(info.path, value, info.override)

            end_request(request, info.auth)
            return {'Response': 'Ok'}
        except Exception as e:
            return {'Response': 'Failure', 'Message': e.message}

    def get(self, request, *args, **kwargs):
        info = EnvView.RequestInfo(request, *args, **kwargs)
        if not info.valid:
            return info.error_message

        call_args = [info.auth, info.env, info.path, info.override]

        if 'viewchildren' in request.GET:
            ret = EnvView.get_children_for(*call_args)
        elif 'viewhistory' in request.GET:
            ret = EnvView.get_history_for(*call_args)
        else:
            ret = EnvView.get_value_for(*call_args)

        end_request(request, info.auth)
        return ret

    @staticmethod
    def _sanitize(env, path):
        ret = '/' + env + path
        return ret if ret[-1] == '/' else ret + '/'

    @staticmethod
    def get_value_for(auth, env, path, override):
        value = auth.get_env(env).get(path) if override is None \
            else auth.get_env(env).get_explicit(path, override)
        return {
            'Response': 'Ok',
            'value': value[0],
            'protect': value[1],
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
