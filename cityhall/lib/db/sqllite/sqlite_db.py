from lib.db import db
from lib.db.db import Rights
from datetime import datetime
import calendar


class SqliteDb(db.Db):
    def __init__(self, cursor):
        self.cursor = cursor

    @staticmethod
    def _datetime_now_to_unixtime():
        return calendar.timegm(datetime.now().timetuple())

    @staticmethod
    def _unixtime_to_datetime_now(time):
        return datetime.utcfromtimestamp(time)

    def _first_row(self, sql, kwargs):
        print "Running: {} with {}".format(sql, str(kwargs))
        for row in self.cursor.execute(sql, kwargs):
            print "  +-> returning: {}".format(str(row))
            return row
        print "  +-> sql didn't return any rows"
        return None

    def _first_value(self, sql, kwargs):
        row = self._first_row(sql, kwargs)
        print "  +-> _first_row value: {}".format(
            row[0] if row else "None"
        )
        return row[0] if row else None

    def create_env(self, user, env):
        user_info = self._first_row(
            'select pass from cityhall_auth '
            'where user = :user and active = :active;',
            {'user': user, 'active': True, }
        )

        if not user_info:
            return

        auth = {'pass': user_info[0], }
        env_exists = self._first_value(
            'select count (*) from cityhall_vals '
            'where env = :env and active = :active;',
            {'env': env, 'active': True, }
        )

        if env_exists == 0:
            self._first_row(
                'begin;'
                '  insert into cityhall_auth '
                '  (active, datetime, env, author, user, pass, rights) '
                '  values '
                '  (:active, :datetime, :env, :author, :user, :pass, :rights);'
                ' '
                '  insert into cityhall_vals '
                '  (id, '
                '  env, parent, active, name, override, '
                '  author, datetime, value, protect)'
                '  values '
                '  (-1, :env,  -1, :active, :name, :override, '
                '  :author, :datetime, :value, :protect);'
                ' '
                '  update cityhall_vals set id = rowid, parent = rowid where '
                '  rowid = last_insert_rowid();'
                'end;',
                {
                    'active': True,
                    'datetime': self._datetime_now_to_unixtime(),
                    'env': env,
                    'user': user,
                    'pass': auth['pass'],
                    'rights': Rights.Grant,
                    'author': user,
                    'name': '/',
                    'override': '',
                    'value': '',
                    'protect': False,
                }
            )

    def get_children_of(self, index):
        ret = []
        for row in self.cursor.execute(
                'select id, env, name, override, author, datetime, '
                ' value, protect from cityhall_vals '
                'where '
                '  active = :active '
                '  and parent = :parent '
                '  and id != :parent;',
                {'active': True, 'parent': index}):
            ret.append({
                'active': True,
                'id': row[0],
                'env': row[1],
                'name': row[2],
                'override': row[3],
                'author': row[4],
                'datetime': datetime.utcfromtimestamp(row[5]),
                'value': row[6],
                'protect': row[7],
                'parent': index
            })
        return ret

    def get_value(self, index):
        return self._first_value(
            'select value from cityhall_vals '
            'where id = :id and active = :active;',
            {'active': True, 'id': index, }
        )

    def get_rights(self, env, user):
        ret = self._first_value(
            'select rights from cityhall_auth '
            'where active = :active and env = :env and user = :user;',
            {'active': True, 'env': env, 'user': user, }
        )
        return ret if ret is not None else Rights.DontExist

    def get_env_root(self, env):
        ret = self._first_value(
            'select id from cityhall_vals '
            'where env = :env and active = :active and parent = id;',
            {'active': True, 'env': env, }
        )
        return ret if ret is not None else -1

    def create_rights(self, author, env, user, rights):
        exist_auth = self._first_value(
            'select count(*) from cityhall_auth where '
            'user = :user and env = :env and active = :active '
            'and rights != :rights;',
            {'user': user, 'env': env, 'active': True, 'rights': rights, }
        )
        user_pass = self._first_value(
            'select pass from cityhall_auth where '
            'user = :user and active = :active '
            'order by rowid limit 1;',
            {'user': user, 'active': True}
        )

        if isinstance(user_pass, basestring) and (exist_auth == 0):
            self.cursor.execute(
                'insert into cityhall_auth'
                '(active, datetime, env, author, user, pass, rights)'
                'values '
                '(:active, :datetime, :env, :author, :user, :pass, :rights);',
                {
                    'active': True,
                    'datetime': self._datetime_now_to_unixtime(),
                    'env': env,
                    'author': author,
                    'user': user,
                    'pass': user_pass,
                    'rights': rights,
                }
            )

    def create(self, user, env, parent, name, value, override=''):
        self.cursor.execute(
            'begin;'
            ' '
            '  insert into cityhall_vals ( '
            '  id, env, parent, active, name, override, author, datetime, '
            '  value, protect) '
            '  values (-1, :env, :parent, :active, :name, :override, :author, '
            '  :datetime, :value, :protect);'
            ' '
            '  update cityhall_vals set id = rowid '
            '  where rowid = last_insert_rowid(); '
            'end',
            {
                'env': env,
                'parent': parent,
                'active': True,
                'name': name,
                'override': override,
                'author': user,
                'datetime': self._datetime_now_to_unixtime(),
                'value': value,
                'protect': False,
            })

    def update(self, user, index, value):
        first_row = self._first_row(
            'select rowid, env, parent, name, override '
            'from cityhall_vals where id = :val_id and active = :active;',
            {'val_id': index, 'active': True, }
        )

        if not first_row:
            return

        self.cursor.execute(
            'begin;'
            ' '
            '  update cityhall_vals set active = :false '
            '  where  id = :id and active = :true'
            ' '
            '  insert into cityhall_vals ( '
            '  id, env, parent, active, name, override, '
            '  author, datetime, value, protect) '
            '  values (:id, :env, :parent, :true, :name, :override, '
            '  :author, :datetime, :value, :protect); '
            ' '
            'end;',
            {
                'id': index,
                'env': first_row[1],
                'parent': first_row[2],
                'true': True,
                'name': first_row[3],
                'override': first_row[4],
                'author': user,
                'datetime': self._datetime_now_to_unixtime(),
                'value': value,
                'protect': False,
                'false': False,
            })

    def update_rights(self, author, env, user, rights):
        current = self._first_row(
            'select rowid, pass from cityhall_auth '
            'where active = :active and user = :user and '
            'env = :env and rights != :rights;',
            {'active': True, 'user': user, 'env': env, 'rights': rights, }
        )
        if current:
            self.cursor.execute(
                'update cityhall_auth '
                'set active = :inactive '
                'where user = :user and active = :active; '
                ' '
                'insert into cityhall_auth '
                '(active, datetime, env, author, user, pass, rights) '
                'values '
                '(:active, :datetime, :env, :author, :user, :pass, :rights);',
                {
                    'inactive': False,
                    'active': True,
                    'datetime': self._datetime_now_to_unixtime(),
                    'env': env,
                    'author': author,
                    'user': user,
                    'pass': current[1],
                    'rights': rights
                }
            )

    def create_user(self, author, user, passhash):
        if self.get_rights('auto', user) == Rights.DontExist:
            self.cursor.execute(
                'insert into cityhall_auth '
                '(active, datetime, env, author, user, pass, rights) '
                'values '
                '(:active, :datetime, :env, :author, :user, :pass, :rights);',
                {
                    'active': True,
                    'datetime': self._datetime_now_to_unixtime(),
                    'env': 'auto',
                    'author': author,
                    'user': user,
                    'pass': passhash,
                    'rights': Rights.NoRights
                }
            )

    def get_history(self, index):
        ret = []
        for row in self.cursor.execute(
                'select env, name, override, author, datetime, value, protect, '
                'active from cityhall_vals where id = :val_id;',
                {'val_id': index}):
            ret.append({
                'env': row[0],
                'name': row[1],
                'override': row[2],
                'author': row[3],
                'datetime': self._unixtime_to_datetime_now(row[4]),
                'value': row[5],
                'protect': row[6],
                'parent': index,
                'active': row[7],
            })
        return ret

    def get_value_for(self, parent_index, name, override):
        ret = None

        for row in self.cursor.execute(
            'select value, override from cityhall_vals '
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
            if row[1] == override:
                return ret

        return ret