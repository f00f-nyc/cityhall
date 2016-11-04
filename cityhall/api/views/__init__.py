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
from api.db import Connection, Rights


def get_new_db():
    if settings.DATABASE_TYPE == 'django':
        from api.db.django.db_factory import Factory
        return Factory()
    elif settings.DATABASE_TYPE == 'memory':
        from api.db.memory.db_factory import CityHallDbFactory
        return CityHallDbFactory()

    raise KeyError('Attempting to get database of type {}, which is not implemented'.format(settings.DATABASE_TYPE))
CONN = Connection(get_new_db())

CONN.connect()


class Info(Endpoint):
    def get(self, request):
        return {'Database': settings.DATABASE_TYPE, 'Status': 'Alive'}


class Create(Endpoint):
    def get(self, request):
        CONN.create_default_env()
        self._create_guest()
        return {'Response': 'Ok'}

    def _create_guest(self):
        auth = CONN.get_auth('cityhall', '')
        auth.create_user('guest', '')
        auth.grant('auto', 'guest', Rights.Read)
