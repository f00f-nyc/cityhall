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
    def __init__(self, db, name, user_root):
        self.db = db
        self.name = name
        self.roots_cache = {}
        self.user_root = user_root
        self.users_env = None

    def _ensure_users_env(self):
        if self.users_env is None:
            self.users_env = self.db.get_env_root('users')

    def create_env(self, env):
        if self.db.create_root(self.name, env):
            self.db.create(self.name, self.user_root, env, Rights.Grant)
            return self.get_env(env)
        return False

    def get_env(self, env):
        cached = self.roots_cache.get(env, None)

        if not cached:
            root_id = self.db.get_env_root(env)
            rights = self.get_permissions(env)
            cached = Env(self.db, env, rights, self.name, root_id)
            self.roots_cache[env] = cached

        if cached.permissions > 0:
            return cached
        return None

    def create_user(self, user, passhash):
        self._ensure_users_env()
        exists = self.db.get_child(self.users_env, user)

        if not exists:
            self.db.create(self.name, self.users_env, user, '')
            created = self.db.get_child(self.users_env, user)
            self.db.create_user(self.name, user, passhash, created['id'])

    def _delete_user(self, delete, delete_rights, delete_root):
        for right in delete_rights:
            self.db.delete(self.name, right['id'])
        self.db.delete(self.name, delete_root['id'])
        self.db.delete_user(self.name, delete)

    def delete_user(self, delete):
        self._ensure_users_env()
        delete_root = self.db.get_child(self.users_env, delete)

        if not delete_root:
            return False

        delete_rights = self.db.get_children_of(delete_root['id'])
        already_deleted = True

        for right in delete_rights:
            if right['value'] > Rights.DontExist:
                already_deleted = False

        if not already_deleted:
            users_permissions = self.get_permissions('users')

            if users_permissions >= Rights.Write:
                self._delete_user(delete, delete_rights, delete_root)
            else:
                self_rights = self.get_user(self.name)
                for right in delete_rights:
                    env = right['name']
                    if env not in self_rights:
                        return False
                    if self_rights[env] < Rights.Grant:
                        return False
                self._delete_user(delete, delete_rights, delete_root)
            return True
        return False

    def get_permissions(self, env):
        if env in self.roots_cache:
            return self.roots_cache[env].permissions

        rights = self.db.get_child(self.user_root, env)
        if rights:
            return rights['value']
        return Rights.DontExist

    def grant(self, env, user, rights):
        curr = self.get_permissions(env)

        if curr >= Rights.Grant:
            self._ensure_users_env()
            user_folder = self.db.get_child(self.users_env, user)
            existing = self.db.get_child(user_folder['id'], env)

            if not existing:
                self.db.create(self.name, user_folder['id'], env, rights)
                return (
                    'Ok',
                    "Rights for '{}' created".format(user),
                )

            if existing['value'] == rights:
                return (
                    'Ok',
                    "Rights for '{}' already at set level".format(user),
                )
            else:
                self.db.update(self.name, existing['id'], rights)
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
        self._ensure_users_env()
        user_folder = self.db.get_child(self.users_env, user)
        children = self.db.get_children_of(user_folder['id'])
        return {
            val['name']: val['value'] for val in children
        }
