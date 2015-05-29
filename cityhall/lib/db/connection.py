from .env import Env
from .auth import Auth


class Connection(object):
    def __init__(self, db):
        self.db = db

    def connect(self):
        self.db.open()

    def _ensure_open(self):
        return self.db.is_open()

    def authenticate(self, user, passhash):
        if self._ensure_open():
            return self.db.authenticate(user, passhash)
        return None

    def create_default_env(self):
        if self._ensure_open():
            self.db.create_default_tables()

    def get_env(self, user, passhash, env):
        if self._ensure_open() and\
                self.db.authenticate(user, passhash, env):
            permissions = self.db.get_rights(env, user)
            if permissions is not None:
                return Env(self.db, env, permissions, user)
        return None

    def get_auth(self, user, passhash):
        open = self._ensure_open()
        authenticated = self.db.authenticate(user, passhash)
        if open and authenticated:
            return Auth(self.db, user)
        return None
