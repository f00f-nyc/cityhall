from lib.db import db
from lib.db.db import Rights
from datetime import datetime
import calendar
import apsw
from .sqlite_db import SqliteDb


class SqliteDbFactory(db.Db):
    def __init__(self, filename):
        self.filename = filename
        self.connection = None
        self.cursor = None

    def __str__(self):
        if not self.is_open():
            return "(Sqlite Db): Not connected"
        else:
            return "(Sqlite Db) Connected"

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

    def authenticate(self, user, passhash, env=None):
        if env is None:
            return 0 < self._first_value(
                'select count(*) from cityhall_auth '
                'where active = :active and user = :user and pass = :pass;',
                {'active': 1, 'user': user, 'pass': passhash, }
            )
        else:
            return 0 < self._first_value(
                'select count(*) from cityhall_auth where '
                'active > 0 and user = :user and pass = :pass '
                'and env = :env;',
                {'active': 1, 'user': user, 'pass': passhash, 'env': env, }
            )

    def get_db(self):
        if self.is_open():
            new_cursor = self.connection.cursor()
            return SqliteDb(new_cursor)
        return None
