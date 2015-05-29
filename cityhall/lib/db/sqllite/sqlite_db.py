from lib.db import db
from lib.db.db import DbState, Rights
from datetime import datetime
import calendar
import apsw


class SqliteDb(db.Db):
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
        self.cursor= self.connection.cursor()

    def is_open(self):
        return self.connection is not None

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
            'where id = :index and active = :active;',
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

    def authenticate(self, user, passhash, env=None):
        if env is None:
            return 0 < self._first_value(
                'select count(*) from cityhall_auth '
                'where active = :active and user = :user and pass = "";',
                {'active': 1, 'user': user, 'pass': passhash, }
            )
        else:
            return 0 < self._first_value(
                'select count(*) from cityhall_auth where '
                'active > 0 and user = :user and pass = :passhash '
                'and env = :env;',
                {'active': 1, 'user': user, 'pass': passhash, 'env': env, }
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
            'from cityhall_vals where id = :index and active = :active;',
            {'index': index, 'active': True, }
        )

        if not first_row:
            return

        self.cursor.execute(
            'begin;'
            ' '
            '  insert into cityhall_vals ( '
            '  id, env, parent, active, name, override, '
            '  author, datetime, value, protect) '
            '  values (:id, :env, :parent, :true, :name, :override, '
            '  :author, :datetime, :value, :protect); '
            ' '
            ' update cityhall_vals set active = :false where rowid = :rowid; '
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
                'rowid': first_row[0],
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
                'where rowid = :rowid; '
                ' '
                'insert into cityhall_auth '
                '(active, datetime, env, author, user, pass, rights) '
                'values '
                '(:active, :datetime, :env, :author, :user, :pass, :rights);',
                {
                    'inactive': False,
                    'rowid': current[0],
                    'active': True,
                    'datetime': self._datetime_now_to_unixtime(),
                    'env': env,
                    'author': author,
                    'user': user,
                    'pass': current[1],
                    'rights': rights
                }
            )

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
                '   active INT,'
                '   datetime INT,'
                '   env TEXT,'
                '   author TEXT,'
                '   user TEXT,'
                '   pass TEXT,'
                '   rights INT);'
                ' '
                ' insert into cityhall_auth'
                ' (active, datetime, env, author, user, pass, rights)'
                ' values '
                ' (:active, :datetime, :env, :author, :user, :pass, :rights);'
                ' '
                ' create table cityhall_vals('
                '   id INT,'
                '   env TEXT,'
                '   parent INT,'
                '   active INT,'
                '   name TEXT,'
                '   override TEXT,'
                '   author TEXT,'
                '   datetime INT,'
                '   value TEXT,'
                '   protect INT);'
                ' '
                ' insert into cityhall_vals'
                ' (id, env, parent, active, name, override, author, datetime,'
                '  value, protect)'
                ' values '
                ' (:val_id, :env, :val_id, :active, :val_name, :val_override,'
                '  :user, :datetime, :value, :protect);'
                ' '
                ' create index cityhall_auth_user_env_active on '
                '   cityhall_auth (user, env, active); '
                ' '
                ' create index cityhall_vals_active_id on '
                '   cityhall_vals (active, id); '
                ' create index cityhall_vals_active_parent_id on '
                '   cityhall_vals (active, parent, id); '
                ' create index cityhall_vals_active_parent_name_override on '
                '   cityhall_vals (active, parent, name, override); '
                ' '
                'end;',
                {
                    'active': True,
                    'datetime': calendar.timegm(datetime.now().timetuple()),
                    'env': 'auto',
                    'author': 'cityhall',
                    'user': 'cityhall',
                    'pass': '',
                    'rights': Rights.Grant,
                    'val_id': 1,
                    'val_name': '/',
                    'val_override': '',
                    'value': '',
                    'protect': 0
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
                'active from cityhall_vals where id = :index;',
                {'id': index}):
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