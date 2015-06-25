from restless.views import Endpoint, HttpResponse
from .views import CACHE, CONN, auth_token_in_cache
from lib.db.db import Rights


def ensure_guest_exists():
    if CACHE.has_key('guest'):
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
        auth = CACHE[cache_key] if CACHE.has_key(cache_key) else None

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


class EnvCreate(Endpoint):
    def authenticate(self, request):
        return auth_token_in_cache(request)

    def post(self, request, *args, **kwargs):
        env = request.data.get('env', None)
        name = request.data.get('name', None)
        value = request.data.get('value', None)
        override = request.data.get('override', '')
        cache_key = request.META.get('HTTP_AUTH_TOKEN', None)
        auth = CACHE[cache_key]

        print "{}/{} [{}] -> {}".format(env, name, override, value)

        if (name is None) or (value is None) or (env is None):
            return {
                'Response': 'Failure',
                'Message': 'Expected an environment, name and value to create'
            }

        if auth is None:
            return {
                'Response': 'Failure',
                'Message': 'Given token "' + cache_key +
                           '" could not be found in cache'
            }

        env = auth.get_env(env)
        try:
            env.set(name, value, override)
            return {'Response': 'Ok'}
        except Exception as e:
            return {'Response': 'Failure', 'Message': e.message}


class EnvView(Endpoint):
    def authenticate(self, request):
        return authenticate_for_get(request)

    def get(self, request, *args, **kwargs):
        env_path = kwargs.get('env_path', None)

        first_slash = env_path.find('/')
        if first_slash < 1:
            return {
                'Response': 'Failure',
                'Message': 'Expected the path to include environment name'
            }

        env = env_path[:first_slash]
        path = env_path[first_slash:]
        auth = get_auth_from_request(request, env)
        override = request.GET.get('override', None)

        if auth[0]:
            if 'viewchildren' in request.GET:
                return EnvView.get_children_for(auth[1], env, path)
            elif 'viewhistory' in request.GET:
                return EnvView.get_history_for(auth[1], env, path, override)
            else:
                return EnvView.get_value_for(auth[1], env, path, override)

        return auth[1]

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
    def _sanitize(env, path):
        ret = '/' + env + path
        return ret if ret[-1] == '/' else ret + '/'

    @staticmethod
    def get_children_for(auth, env, path):
        sanitized_path = EnvView._sanitize(env, path)
        children = auth.get_env(env).get_children(path)

        return {
            'Response': 'Ok',
            'path': sanitized_path,
            'children': children
        }
