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

from api.db import DbFactory, DbState
from datetime import datetime
from api.db.memory.db import CityHallDb


class CityHallDbFactory(DbFactory):
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
        self.valsTable = [
            {
                'id': 1,
                'parent': 1,
                'active': True,
                'name': 'auto',
                'override': '',
                'author': 'cityhall',
                'datetime': datetime.now(),
                'value': '',
                'protect': False,
                'first_last': True,
            },
            {
                'id': 2,
                'parent': 2,
                'active': True,
                'name': 'users',
                'override': '',
                'author': 'cityhall',
                'datetime': datetime.now(),
                'value': '',
                'protect': False,
                'first_last': True,
            },
            {
                'id': 3,
                'parent': 2,
                'active': True,
                'name': 'cityhall',
                'override': '',
                'author': 'cityhall',
                'datetime': datetime.now(),
                'value': '',
                'protect': False,
                'first_last': True,
            },
            {
                'id': 4,
                'parent': 3,
                'active': True,
                'name': 'auto',
                'override': '',
                'author': 'cityhall',
                'datetime': datetime.now(),
                'value': '4',
                'protect': False,
                'first_last': True,
            },
            {
                'id': 5,
                'parent': 3,
                'active': True,
                'name': 'users',
                'override': '',
                'author': 'cityhall',
                'datetime': datetime.now(),
                'value': '4',
                'protect': False,
                'first_last': True,
            },
            {
                'id': 6,
                'parent': 1,
                'active': True,
                'name': 'connect',
                'override': '',
                'author': 'cityhall',
                'datetime': datetime.now(),
                'value': '4',
                'protect': False,
                'first_last': True,
            },
        ]
        self.authTable = [{
            'id': 0,
            'active': True,
            'datetime': datetime.now(),
            'user_root': 3,
            'author': 'cityhall',
            'user': 'cityhall',
            'pass': '',
        }]

    def is_open(self):
        return self.state == DbState.Open

    def authenticate(self, user, passhash):
        if not self.authTable:
            return None

        for auth in self.authTable:
            if auth['active'] and (auth['pass'] == passhash)\
                    and (auth['user'] == user):
                return auth['user_root']
        return False

    def get_db(self):
        if self.is_open():
            return CityHallDb(self)
        return None
