from restless.views import Endpoint
from .views import CONN, CACHE


class EnvCreate(Endpoint):
    def post(self, request, *args, **kwargs):
        env = request.data.get('env', None)
        name = request.data.get('name', None)
        value = request.data.get('value', None)
        override = request.data.get('override', '')
        cache_key = request.META.get('HTTP_AUTH_TOKEN', None)
        auth = CACHE[cache_key] if CACHE.has_key(cache_key) else None

        if cache_key is None:
            return {
                'Response': 'Failure',
                'Message': 'Expected Auth-Token header'
            }

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
        env.set(name, value, override)
        return {'Response': 'Ok'}


class EnvView(Endpoint):
    def get(self, request, *args, **kwargs):
        env_path = kwargs.get('env_path', None)
        cache_key = request.META.get('HTTP_AUTH_TOKEN', None)

        first_slash = env_path.find('/')
        if first_slash < 1:
            return {
                'Response': 'Failure',
                'Message': 'Expected the path to include environment name'
            }

        env = env_path[:first_slash]
        path = env_path[first_slash:]

        if cache_key is None:
            auth = CACHE['guest']
        else:
            auth = CACHE[cache_key] if CACHE.has_key(cache_key) else None

        if auth is None:
            return {
                'Response': 'Failure',
                'Message': 'Unable to get authorization for env: ' + env
            }

        return {
            'Response': 'Ok',
            'value': auth.get_env(env).get(path)
        }
