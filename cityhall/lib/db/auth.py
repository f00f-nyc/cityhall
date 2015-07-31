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

from .env import Env
from .db import Rights


class Auth(object):
    class EnvCache(object):
        def __init__(self, root_id, rights):
            self.root_id = root_id
            self.rights = rights

    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.roots_cache = {}

    def create_env(self, env):
        if self.db.create_env(self.name, env):
            return self.get_env(env)
        return False

    def get_env(self, env):
        cached = self.roots_cache.get('env', None)

        if not cached:
            root_id = self.db.get_env_root(env)
            rights = self.db.get_rights(env, self.name)
            cached = Auth.EnvCache(root_id, rights)
            self.roots_cache[env] = cached

        if cached.rights:
            return Env(self.db, env, cached.rights, self.name, cached.root_id)
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
