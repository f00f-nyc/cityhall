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

from lib.db import db
from lib.db.db import DbState, Rights
from datetime import datetime
from .cityhall_db import CityHallDb


class CityHallDbFactory(db.DbFactory):
    def __init__(self):
        self.state = DbState.Closed
        self.authTable = None
        self.valsTable = None

    def open(self):
        if self.state == DbState.Closed:
            self.state = DbState.Open
        else:
            raise Exception("Cannot open new connection, already opened")

    def create_default_tables(self):
        self.valsTable = [{
            'id': 1,
            'env': 'auto',
            'parent': 0,
            'active': True,
            'name': '/',
            'override': '',
            'author': 'cityhall',
            'datetime': datetime.now(),
            'value': '',
            'protect': False,
        }]
        self.authTable = [{
            'id': 0,
            'active': True,
            'datetime': datetime.now(),
            'env': 'auto',
            'author': 'cityhall',
            'user': 'cityhall',
            'pass': '',
            'rights': Rights.Admin,
        }]

    def is_open(self):
        return self.state == DbState.Open

    def authenticate(self, user, passhash, env=None):
        if not self.authTable:
            return None

        check_env = lambda a: True if not env else a['env'] == env

        for auth in self.authTable:
            if auth['active'] and (auth['pass'] == passhash)\
                    and (auth['user'] == user) and check_env(auth):
                return auth['rights'] >= Rights.NoRights
        return False

        # return next(
        #     (auth['active'] for auth in self.db.authTable
        #         if auth['active'] and (auth['pass'] == passhash) and
        #         (auth['user'] == user) and check_env(auth)),
        #     False
        # )

    def get_db(self):
        if self.is_open():
            return CityHallDb(self)
        return None
