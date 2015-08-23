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

from .sqlite_funcs_mixin import SqliteFuncsMixin
from lib.db import db
from lib.db.db import Rights
from datetime import datetime
import calendar


class SqliteDb(db.Db, SqliteFuncsMixin):
    def __init__(self, cursor):
        self.cursor = cursor

    @staticmethod
    def _datetime_now_to_unixtime():
        return calendar.timegm(datetime.now().timetuple())

    @staticmethod
    def _unixtime_to_datetime_now(time):
        return datetime.utcfromtimestamp(time)

    def create_root(self, author, env):
        if self.get_env_root(env) < 0:
            self._first_row(
                'begin;'
                ' '
                '  insert into cityhall_vals '
                '  (id, parent, active, name, override, '
                '  author, datetime, value, first_last, protect)'
                '  values '
                '  (-1, -1, :active, :name, :override, '
                '  :author, :datetime, :value, :first_last, :protect);'
                ' '
                '  update cityhall_vals set id = rowid, parent = rowid where '
                '  rowid = last_insert_rowid();'
                'end;',
                {
                    'active': True,
                    'name': env,
                    'override': '',
                    'author': author,
                    'datetime': self._datetime_now_to_unixtime(),
                    'value': '',
                    'first_last': True,
                    'protect': False,
                }
            )
            return True
        return False

    def get_children_of(self, index):
        ret = []
        for row in self.cursor.execute(
                'select id, name, override, author, datetime, '
                ' value, protect from cityhall_vals '
                'where '
                '  active = :active '
                '  and parent = :parent '
                '  and id != parent;',
                {'active': True, 'parent': index}):
            ret.append({
                'active': True,
                'id': row[0],
                'name': row[1],
                'override': row[2] or '',
                'author': row[3],
                'datetime': datetime.utcfromtimestamp(row[4]),
                'value': row[5],
                'protect': row[6],
                'parent': index
            })
        return ret

    def get_value(self, index):
        val = self._first_row(
            'select value, protect from cityhall_vals '
            'where id = :id and active = :active;',
            {'active': True, 'id': index, }
        )
        if val is None:
            return None, None
        return val[0], val[1]

    def get_env_root(self, env):
        ret = self._first_value(
            'select id from cityhall_vals '
            'where name = :env and active = :active and parent = id;',
            {'active': True, 'env': env, }
        )
        return ret if ret is not None else -1

    def create(self, user, parent, name, value, override=''):
        self.cursor.execute(
            'begin;'
            ' '
            '  insert into cityhall_vals ( '
            '  id, parent, active, name, override, author, datetime, '
            '  value, first_last, protect) '
            '  values (-1, :parent, :active, :name, :override, :author, '
            '  :datetime, :value, :first_last, :protect);'
            ' '
            '  update cityhall_vals set id = rowid '
            '  where rowid = last_insert_rowid(); '
            'end;',
            {
                'parent': parent,
                'active': True,
                'name': name,
                'override': override,
                'author': user,
                'datetime': self._datetime_now_to_unixtime(),
                'value': value,
                'first_last': True,
                'protect': False,
            })

    def update(self, user, index, value):
        first_row = self._first_row(
            'select rowid, parent, name, override, protect '
            'from cityhall_vals where id = :val_id and active = :active;',
            {'val_id': index, 'active': True, }
        )

        if not first_row:
            return

        self.cursor.execute(
            'begin;'
            ' '
            '  update cityhall_vals set active = :false '
            '  where  id = :id and active = :true; '
            ' '
            '  insert into cityhall_vals ( '
            '  id, parent, active, name, override, '
            '  author, datetime, value, first_last, protect) '
            '  values (:id, :parent, :true, :name, :override, '
            '  :author, :datetime, :value, :false, :protect); '
            ' '
            'end;',
            {
                'id': index,
                'parent': first_row[1],
                'true': True,
                'name': first_row[2],
                'override': first_row[3],
                'author': user,
                'datetime': self._datetime_now_to_unixtime(),
                'value': value,
                'protect': first_row[4],
                'false': False,
            })

    def create_user(self, author, user, passhash, user_root):
        if self._first_value(
                'select count(*) from cityhall_auth '
                'where active = :active and user = :user;',
                {
                    'active': True,
                    'user': user,
                }
        ):
            return

        self.cursor.execute(
            'insert into cityhall_auth '
            '(active, datetime, user_root, author, user, pass) '
            'values '
            '(:active, :datetime, :user_root, :author, :user, :pass);',
            {
                'active': True,
                'datetime': self._datetime_now_to_unixtime(),
                'user_root': user_root,
                'author': author,
                'user': user,
                'pass': passhash,
            }
        )

    def get_history(self, index):
        ret = []
        for row in self.cursor.execute(
                'select '
                ' id, name, override, author, '
                ' datetime, value, protect, active '
                'from cityhall_vals where '
                '(id = :val_id) or (first_last = :true and parent = :val_id);',
                {'val_id': index, 'true': True}):
            ret.append({
                'id': row[0],
                'name': row[1],
                'override': row[2],
                'author': row[3],
                'datetime': self._unixtime_to_datetime_now(row[4]),
                'value': row[5],
                'protect': row[6],
                'parent': index,
                'active': row[7]
            })
        return ret

    def get_value_for(self, parent_index, name, override):
        ret = None
        protect = None

        for row in self.cursor.execute(
            'select value, override, protect from cityhall_vals '
            'where parent = :parent and name = :name and active = :active '
            ' and (override = :override or override = :global);',
            {
                'parent': parent_index,
                'name': name,
                'active': True,
                'override': override,
                'global': ''
            }
        ):
            ret = row[0]
            protect = row[2]
            if row[1] == override:
                return ret, protect

        return ret, protect

    def delete(self, user, index):
        first_row = self._first_row(
            'select rowid, parent, name, override, value '
            'from cityhall_vals where id = :val_id and active = :active;',
            {'val_id': index, 'active': True, }
        )

        if not first_row:
            return

        self.cursor.execute(
            'begin;'
            ' '
            '  update cityhall_vals set active = :false '
            '  where  id = :id and active = :true; '
            ' '
            '  insert into cityhall_vals ( '
            '  id, parent, active, name, override, '
            '  author, datetime, value, first_last, protect) '
            '  values (:id, :parent, :false, :name, :override, '
            '  :author, :datetime, :value, :true, :protect); '
            ' '
            'end;',
            {
                'id': index,
                'parent': first_row[1],
                'true': True,
                'name': first_row[2],
                'override': first_row[3],
                'author': user,
                'datetime': self._datetime_now_to_unixtime(),
                'value': first_row[4],
                'protect': False,
                'false': False,
            })

    def set_protect_status(self, user, index, status):
        first_row = self._first_row(
            'select rowid, parent, name, override, value '
            'from cityhall_vals where id = :val_id and active = :active '
            '     and protect != :status;',
            {'val_id': index, 'active': True, 'status': status}
        )

        if not first_row:
            return

        self.cursor.execute(
            'begin;'
            ' '
            '  update cityhall_vals set active = :false '
            '  where  id = :id and active = :true; '
            ' '
            '  insert into cityhall_vals ( '
            '  id, parent, active, name, override, '
            '  author, datetime, value, first_last, protect) '
            '  values (:id, :parent, :true, :name, :override, '
            '  :author, :datetime, :value, :false, :protect); '
            ' '
            'end;',
            {
                'id': index,
                'parent': first_row[1],
                'true': True,
                'name': first_row[2],
                'override': first_row[3],
                'author': user,
                'datetime': self._datetime_now_to_unixtime(),
                'value': first_row[4],
                'protect': status,
                'false': False,
            })

    def delete_user(self, author, user):
        self.cursor.execute(
            'begin;'
            ' '
            'update cityhall_auth '
            'set active = :inactive '
            'where active = :active and user = :user;'
            ' '
            'insert into cityhall_auth '
            '(active, datetime, author, user, pass) '
            'values '
            '(:inactive, :datetime, :author, :user, :pass);'
            ' '
            'end;',
            {
                'inactive': False,
                'active': True,
                'datetime': self._datetime_now_to_unixtime(),
                'author': author,
                'user': user,
                'pass': '',
            }
        )

    def get_users(self, env):
        return {
            row[0]: row[1]
            for row in self.cursor.execute(
                'select a.user, v.value from cityhall_auth a '
                'join cityhall_vals v '
                'where '
                '   a.user_root = v.parent '
                '   and v.active = :active '
                '   and v.name = :env;',
                {
                    'active': True,
                    'env': env,
                }
            )
        }

    def get_child(self, parent, name, override=''):
        ret = self._first_row(
            'select id, name, override, author, datetime, '
            ' value, protect '
            ' from cityhall_vals '
            ' where active = :active and parent = :parent and'
            '       name = :name and override = :override;',
            {
                'active': True,
                'parent': parent,
                'name': name,
                'override': override,
            }
        )
        if ret is not None:
            return {
                'active': True,
                'id': ret[0],
                'name': ret[1],
                'override': ret[2] or '',
                'author': ret[3],
                'datetime': datetime.utcfromtimestamp(ret[4]),
                'value': ret[5],
                'protect': ret[6],
                'parent': parent,
            }
        return None
