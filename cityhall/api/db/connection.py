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

import sys
from api.db.auth import Auth
from api.db.django.db_factory import Factory
from api.db.memory.db_factory import CityHallDbFactory


class Connection(object):
    def __init__(self, db):
        self.db_connection = db

    def connect(self):
        self.db_connection.open()

    def _ensure_open(self):
        return self.db_connection.is_open()

    def authenticate(self, user, passhash):
        if self._ensure_open():
            return self.db_connection.authenticate(user, passhash)
        return None

    def create_default_env(self):
        if self._ensure_open():
            self.db_connection.create_default_tables()

    def get_auth(self, user, passhash):
        opened = self._ensure_open()
        authenticated = self.db_connection.authenticate(user, passhash)
        if opened and authenticated:
            return Auth(self.db_connection.get_db(), user, authenticated)
        return None


def get_new_db():
    settings = sys.modules['django.conf'].settings

    if 'db_type' not in settings.CITY_HALL_OPTIONS:
        raise KeyError('Expected CITY_HALL_OPTIONS to contain "db_type"')

    db_type = settings.CITY_HALL_OPTIONS['db_type']

    if db_type == 'django':
        return Factory(settings.CITY_HALL_OPTIONS)
    elif db_type == 'memory':
        return CityHallDbFactory(settings.CITY_HALL_OPTIONS)

    raise KeyError(f'Attempting to get db of type {db_type}, which is not implemented')

Instance = Connection(get_new_db())
Instance.connect()
