from .env import Env
from .db import Rights

class Auth(object):
    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.roots_cache = {}

    def create_env(self, env):
        if self.db.create_env(self.name, env):
            return self.get_env(env)
        return False

    def get_env(self, env):
        if env in self.roots_cache:
            rights = self.roots_cache[env]
        else:
            rights = self.db.get_rights(env, self.name)
            self.roots_cache[env] = rights

        if rights:
            return Env(self.db, env, rights, self.name)
        return None

    def create_user(self, user, passhash):
        if self.db.get_rights('auto', user) == Rights.DontExist:
            self.db.create_user(self.name, user, passhash)

    def get_permissions(self, env):
        if env in self.roots_cache:
            return self.roots_cache[env]

        return self.db.get_rights(env, self.name)

    def grant(self, env, user, rights):
        curr = self.db.get_rights(env, self.name)

        if curr >= Rights.Grant:
            existing = self.db.get_rights(env, user)
            if existing == Rights.DontExist:
                self.db.create_rights(self.name, env, user, rights)
            else:
                self.db.update_rights(self.name, env, user, rights)
