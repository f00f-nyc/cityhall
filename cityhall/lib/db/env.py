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

from django.conf import settings
from api.cache import CacheDict
from .db import Rights


def sanitize_path(path):
    sanitized = '/'+path if path[0] != '/' else path
    return sanitized+'/' if path[-1] != '/' else sanitized


def get_name_of_value(path):
    name = path[:-1] if path[-1] == '/' else path
    return name[name.rindex('/')+1:]


def path_split(path):
    split = path[1:] if path[0] == '/' else path
    split = split[:-1] if split[-1] == '/' else split
    return split.split('/')


class Env(object):
    def __init__(self, db, env, permissions, name, root_id):
        self.db = db
        self.cache = CacheDict(
            capacity=settings.CACHE_OPTIONS['PATH_CAPACITY'],
        )
        self.env = env
        self.root_id = root_id
        self.permissions = permissions
        self.name = name

    def get_auth(self):
        from .auth import Auth
        users_root = self.db.get_env_root('users')
        self_root = self.db.get_child(users_root, self.name)
        if self_root:
            return Auth(self.db, self.name, self_root['id'])

    @staticmethod
    def _get_parent_path(sanitized_path):
        prev_slash = sanitized_path[:-1].rindex('/')
        if prev_slash:
            return sanitized_path[:prev_slash]
        return '/'

    def _get_parent_id(self, sanitized_path):
        parent_path = Env._get_parent_path(sanitized_path)
        if parent_path == '/':
            return self.root_id
        return self._get_index_of(parent_path)

    def _index_from_cache(self, cache_key):
        """
        Attempts to retrieve the index of this path from cache

        :param cache_key: The string representation of the cahce key in
         the form of /fully/sanatized/path/:override
        :return: the int() index_id or None
        """
        return self.cache.get(cache_key, None)

    def _get_index_of(self, path, override=None,
                      parent_id=None, parent_path=None):
        """
        Returns the index of the given path.

        It searches out from /, recursively calling itself with the next item
        in the path.  As it searches, it greedily caches all paths it finds.

        :param path: This should be a string.  When _get_index_of() calls
         itself it is an array of strings (broken up by '/'). which must be
         walked. When len(path) == 1, we're at the end of the search
        :param override: This should be a string. Only override == '' may have
         children, so this override only applies to the last item in the path
        :param parent_id: the current parent id to search from.  Starts out
         from self.root_id
        :param parent_path: the current parent path we are searching from.
         Starts out from /
        :return: the index of the path, or -1 if the path doesn't exist
        """
        override = '' if override is None else override

        if isinstance(path, basestring):
            if path == '/':
                return self.root_id

            path = sanitize_path(path)
            cache_key = "{}:{}".format(path, override)
            index = self._index_from_cache(cache_key)

            if index is None:
                return self._get_index_of(
                    path_split(path), override, self.root_id, '/'
                )

            return index

        children = self.db.get_children_of(parent_id)

        # only global values may have children, so we only invoke the override
        # when we get to the end of the search
        seek_override = ''

        if len(path) == 1:
            # we are at the end of the search, must invoke the override
            seek_override = override

        first_item_id = -1

        for child in children:
            cache_key = "{}{}/:{}".format(
                parent_path, child['name'], child['override']
            )
            self.cache[cache_key] = child['id']

            if child['name'] == path[0] and child['override'] == seek_override:
                if len(path) == 1:
                    return child['id']

                first_item_id = child['id']

        if first_item_id == -1:
            return -1

        return self._get_index_of(
            path[1:], override, first_item_id,
            "{}{}/".format(parent_path, path[0])
        )

    def _honor_permissions(self, val_pair):
        if self.permissions >= Rights.ReadProtected:
            return val_pair
        if self.permissions >= Rights.Read and not val_pair[1]:
            return val_pair
        return None, None

    def set(self, path, value, override=None):
        override = '' if override is None else override
        value = '' if value is None else value

        if self.permissions < Rights.Write:
            return False

        if (path == '/') and (override == ''):
            self.db.update(self.name, self.root_id, value)
            return True

        if path == '/':
            return False    # Cannot create overrides for root

        path = sanitize_path(path)
        cache_key = "{}:{}".format(path, override)
        cached = self._index_from_cache(cache_key)

        if cached is not None:
            self.db.update(self.name, cached, value)
            return True

        parent_index = self._get_parent_id(path)

        if parent_index < 0:
            return False

        children = self.db.get_children_of(parent_index)
        search = get_name_of_value(path)
        global_entry_must_be_created = override != ''

        for child in children:
            if (child['name'] == search) and (child['override'] == override):
                self.cache[cache_key] = child['id']
                self.db.update(self.name, child['id'], value)
                return True
            if (child['name'] == search) and (child['override'] == ''):
                global_entry_must_be_created = False

        if global_entry_must_be_created:
            self.db.create(self.name, parent_index, search, '', '')

        self.db.create(
            self.name, parent_index, search, value, override,
        )

        return True

    def delete(self, path, override=None):
        sanitized_path = sanitize_path(path)
        if sanitized_path == '/':
            return

        if not override:
            parent_path = Env._get_parent_path(sanitized_path)
            children = self.get_children(parent_path)
            name = get_name_of_value(sanitized_path)

            for child in children:
                if child['name'] == name:
                    self.db.delete(self.name, child['id'])
        else:
            index = self._get_index_of(path, override)
            if index >= 0:
                self.db.delete(self.name, index)

    def get_explicit(self, path, override=None):
        index = self._get_index_of(path, override)
        if index >= 0:
            return self._honor_permissions(self.db.get_value(index))

    def get(self, path):
        if path == '/':
            return self._honor_permissions(self.db.get_value(self.root_id))

        path = sanitize_path(path)
        parent_id = self._get_parent_id(path)
        value_name = get_name_of_value(path)

        if parent_id >= 0:
            return self._honor_permissions(
                self.db.get_value_for(parent_id, value_name, self.name)
            )

    def get_children(self, path):
        index = self._get_index_of(path)
        path = sanitize_path(path)
        can_read = lambda i: True

        if self.permissions < Rights.Read:
            return []
        elif self.permissions == Rights.Read:
            can_read = lambda i: not i['protect']

        if index:
            return [
                {
                    'name': child['name'],
                    'id': child['id'],
                    'override': child['override'],
                    'path': path + child['name'] + '/',
                    'value': child['value'],
                    'protect': child['protect'],
                }
                for child in self.db.get_children_of(index) if can_read(child)
            ]
        return []

    def get_history(self, path, override=None):
        if self.permissions < Rights.ReadProtected:
            return []

        index = self._get_index_of(path, override)

        return [
            {
                'id': item['id'],
                'name': item['name'],
                'value': item['value'],
                'author': item['author'],
                'datetime': item['datetime'],
                'active': item['active'],
                'protect': item['protect'],
                'override': item['override'],
            }
            for item in self.db.get_history(index)
        ]

    def set_protect(self, status, path, override):
        if self.permissions < Rights.Write:
            return False

        override = '' if override is None else override

        if (path == '/') and (override == ''):
            self.db.set_protect_status(self.name, self.root_id, status)
            return True

        if path == '/':
            return False    # Cannot create overrides for root

        index = self._get_index_of(path, override)
        if index > -1:
            self.db.set_protect_status(self.name, index, status)
            return True

        return False
