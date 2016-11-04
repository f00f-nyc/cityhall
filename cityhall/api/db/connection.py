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

from api.db.auth import Auth
import cityhall.settings as settings


class Connection(object):
    def __init__(self, db):
        self.db_connection = db

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is not None:
            return cls._instance

        if settings.DATABASE_TYPE == 'django':
            from api.db.django.db_factory import Factory
            cls._instance = Connection(Factory())
        elif settings.DATABASE_TYPE == 'memory':
            from api.db.memory.db_factory import CityHallDbFactory
            cls._instance = Connection(CityHallDbFactory())
        else:
            raise KeyError(
                'Attempting to get db of type {}, which is not implemented'.\
                format(settings.DATABASE_TYPE)
            )

        cls._instance.connect()
        return cls._instance

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
        open = self._ensure_open()
        authenticated = self.db_connection.authenticate(user, passhash)
        if open and authenticated:
            return Auth(self.db_connection.get_db(), user, authenticated)
        return None
