from .env import Env
from .db import Rights

class Auth(object):
    def __init__(self, db, name):
        self.db = db
        self.name = name

    def create_env(self, env):
        self.db.create_env(self.name, env)
        return self.get_env(env)

    def get_env(self, env):
        rights = self.db.get_rights(env, self.name)
        if rights:
            return Env(self.db, env, rights, self.name)
        return None

    def create_user(self, user, passhash):
        self.db.create_user(self.name, user, passhash)

    def get_permissions(self, env):
        return self.db.get_rights(env, self.name)

    def grant(self, env, user, rights):
        curr = self.db.get_rights(env, self.name)

        if curr >= Rights.Grant:
            existing = self.db.get_rights(env, user)
            if existing == -1:
                self.db.create_rights(self.name, env, user, rights)
            else:
                self.db.update_rights(self.name, env, user, rights)
