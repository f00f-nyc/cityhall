from .env import Env
from .auth import Auth


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

    def get_env(self, user, passhash, env):
        if self._ensure_open() and\
                self.db_connection.authenticate(user, passhash, env):
            db = self.db_connection.get_db()
            permissions = db.get_rights(env, user)
            if permissions is not None:
                return Env(db, env, permissions, user)
        return None

    def get_auth(self, user, passhash):
        open = self._ensure_open()
        authenticated = self.db_connection.authenticate(user, passhash)
        if open and authenticated:
            return Auth(self.db_connection.get_db(), user)
        return None
