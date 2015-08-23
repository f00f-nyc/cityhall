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
from lib.db.db import Rights
from datetime import datetime
import calendar
import apsw
from .sqlite_db import SqliteDb
from .sqlite_funcs_mixin import SqliteFuncsMixin


class SqliteDbFactory(db.Db, SqliteFuncsMixin):
    def __init__(self, filename):
        self.filename = filename
        self.connection = None
        self.cursor = None

    def __str__(self):
        if not self.is_open():
            return "(Sqlite Db): Not connected"
        else:
            return "(Sqlite Db) Connected"

    def open(self):
        self.connection = apsw.Connection(self.filename)
        self.cursor = self.connection.cursor()

    def is_open(self):
        return self.cursor is not None

    def create_default_tables(self):
        exists = False
        for row in self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE "
                "type='table' and name = :authTable;",
                {'authTable': 'cityhall_auth'}):
            exists = True

        if not exists:
            self.cursor.execute(
                'begin;'
                ' '
                ' create table cityhall_auth('
                '   active INT, '
                '   datetime INT,'
                '   user_root INT,'
                '   author TEXT,'
                '   user TEXT,'
                '   pass TEXT);'
                ' '
                ' create table cityhall_vals('
                '   id INT,'
                '   parent INT,'
                '   active INT,'
                '   name TEXT,'
                '   override TEXT,'
                '   author TEXT,'
                '   datetime INT,'
                '   value TEXT,'
                '   protect INT,'
                '   first_last INT);'
                ' '
                ' create index cityhall_auth_user_active on '
                '   cityhall_auth (user, pass, active); '
                ''
                ' create index cityhall_vals_active_id on '
                '   cityhall_vals (active, id); '
                ' create index cityhall_vals_active_parent_id on '
                '   cityhall_vals (active, parent, id); '
                ' create index cityhall_vals_active_parent_name_override on '
                '   cityhall_vals (active, parent, name, override); '
                ' '
                'end;'
            )

            self_db = self.get_db()

            self_db.create_root('cityhall', 'auto')
            self_db.create_root('cityhall', 'users')
            root_id = self_db.get_env_root('users')
            self_db.create('cityhall', root_id, 'cityhall', '')
            children = self_db.get_children_of(root_id)
            cityhall_id = children[0]['id']
            self_db.create('cityhall', cityhall_id, 'auto', Rights.Grant)
            self_db.create('cityhall', cityhall_id, 'users', Rights.Grant)

            self_db.create_user('cityhall', 'cityhall', '', cityhall_id)

    def authenticate(self, user, passhash):
        if not self._first_value(
            'select count(*) from cityhall_auth '
            'where active = :active and user = :user and pass = :pass;',
            {
                'active': 1,
                'user': user,
                'pass': passhash
            }
        ):
            return False

        return self._first_value(
            'select user_root from cityhall_auth '
            'where active = :active and user = :user and pass = :pass;',
            {
                'active': 1,
                'user': user,
                'pass': passhash
            }
        )

    def get_db(self):
        if self.is_open():
            new_cursor = self.connection.cursor()
            return SqliteDb(new_cursor)
        return None
