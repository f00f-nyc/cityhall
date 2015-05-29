from restless.views import Endpoint
from lib.db.connection import Connection
from django.conf import settings
from lru import LRUCacheDict
from lib.db.db import Rights


CACHE = LRUCacheDict(
    max_size=settings.ENV_CACHE['SIZE'],
    expiration=settings.ENV_CACHE['EXPIRATION_SEC'],
    thread_clear=settings.ENV_CACHE['MULTI_THREAD'],
    thread_clear_min_check=settings.ENV_CACHE['MULTI_THREAD_POLL_SEC'],
    concurrent=settings.ENV_CACHE['MULTI_THREAD'],
)
DB = settings.CITY_HALL_DATABASE
CONN = Connection(DB)
CONN.connect()


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
        CACHE['guest'] = CONN.get_auth('guest', '')
