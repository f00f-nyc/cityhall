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
    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.roots_cache = {}

    def create_env(self, env):
        if self.db.create_env(self.name, env):
            return self.get_env(env)
        return False

    def get_env(self, env):
        cached = self.roots_cache.get(env, None)

        if not cached:
            root_id = self.db.get_env_root(env)
            rights = self.db.get_rights(env, self.name)
            cached = Env(self.db, env, rights, self.name, root_id)
            self.roots_cache[env] = cached

        if cached.permissions > 0:
            return cached
        return None

    def create_user(self, user, passhash):
        if self.db.get_rights('auto', user) == Rights.DontExist:
            self.db.create_user(self.name, user, passhash)

    def delete_user(self, user):
        user_rights = self.db.get_user(user)
        user_deleted = True

        for rights in user_rights.values():
            if rights > Rights.DontExist:
                user_deleted = False

        if user_deleted:
            return False

        if self.db.get_rights('auto', self.name) >= Rights.Admin:
            self.db.delete_user(self.name, user)
            return True
        else:
            for env in user_rights:
                if self.db.get_rights(env, self.name) < Rights.Grant:
                    return False

            self.db.delete_user(self.name, user)
            return True

    def get_permissions(self, env):
        if env in self.roots_cache:
            return self.roots_cache[env].permissions

        return self.db.get_rights(env, self.name)

    def grant(self, env, user, rights):
        curr = self.db.get_rights(env, self.name)

        if curr >= Rights.Grant:
            existing = self.db.get_rights(env, user)
            if existing == rights:
                return (
                    'Ok',
                    "Rights for '{}' already at set level".format(user),
                )
            if existing == Rights.DontExist:
                self.db.create_rights(self.name, env, user, rights)
                return (
                    'Ok',
                    "Rights for '{}' created".format(user),
                )
            else:
                self.db.update_rights(self.name, env, user, rights)
                return (
                    'Ok',
                    "Rights for '{}' updated".format(user),
                )
        else:
            return (
                "Failure",
                "Insufficient rights to grant to environment '{}'".format(env),
            )

    def get_users(self, env_name):
        env = self.get_env(env_name)
        if env.permissions >= Rights.Read:
            return self.db.get_users(env_name)
        return 'Do not have permissions to ' + env_name

    def get_user(self, user):
        return self.db.get_user(user)
