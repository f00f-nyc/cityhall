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

from api.db import Db
from datetime import datetime


def get_next_id(table):
    max_id = -1
    for item in table:
        max_id = item['id'] if item['id'] > max_id else max_id
    return max_id + 1


class CityHallDb(Db):
    def __init__(self, db):
        super(CityHallDb, self).__init__(db)

    @property
    def __str__(self):
        from api.db.memory.db_factory import CityHallDbFactory
        assert isinstance(self.parent, CityHallDbFactory)
        valsCount = len(self.parent.valsTable) if self.parent.valsTable else 'None'
        authCount = len(self.parent.authTable) if self.parent.authTable else 'None'
        return f"(In-Memory Db): Values: {valsCount}, Authorizations: {authCount}"

    def create_user(self, author, user, passhash, user_root):
        for auth in self.parent.authTable:
            if auth['active'] and auth['user'] == user:
                return

        self.parent.authTable.append({
            'id': len(self.parent.authTable),
            'active': True,
            'datetime': datetime.now(),
            'user_root': user_root,
            'author': author,
            'user': user,
            'pass': passhash,
        })

    def create_root(self, author, env):
        if self.get_env_root(env) < 0:
            val_id = get_next_id(self.parent.valsTable)
            self.parent.valsTable.append({
                'id': val_id,
                'parent': val_id,
                'active': True,
                'name': env,
                'override': '',
                'author': author,
                'datetime': datetime.now(),
                'value': '',
                'first_last': True,
                'protect': False,
            })
            return val_id
        return False

    def get_env_root(self, env):
        return next(
            (val['id'] for val in self.parent.valsTable
                if val['id'] == val['parent'] and val['name'] == env),
            -1
        )

    def get_children_of(self, index):
        return [
            child for child in self.parent.valsTable
            if child['active'] and child['parent'] == index
            and child['id'] != index        # do not return roots
        ]

    def create(self, user, parent, name, value, override=''):
        created_id = get_next_id(self.parent.valsTable)
        self.parent.valsTable.append({
            'id': created_id,
            'parent': parent,
            'active': True,
            'name': name,
            'override': override,
            'author': user,
            'datetime': datetime.now(),
            'value': value,
            'first_last': True,
            'protect': False,
        })
        return created_id

    def update_user(self, author, user, passhash):
        for auth in self.parent.authTable:
            if auth['active'] and auth['user'] == user:
                auth['active'] = False
                self.parent.authTable.append({
                    'id': len(self.parent.authTable),
                    'active': True,
                    'datetime': datetime.now(),
                    'author': author,
                    'user': user,
                    'pass': passhash,
                    'user_root': auth['user_root']
                })
                return True
        return False

    def update(self, user, index, value):
        original = next((
            val for val in self.parent.valsTable
            if val['active'] and val['id'] == index),
            None
        )

        if original:
            original['active'] = False
            self.parent.valsTable.append({
                'id': index,
                'parent': original['parent'],
                'active': True,
                'name': original['name'],
                'override': original['override'],
                'author': user,
                'datetime': datetime.now(),
                'value': value,
                'first_last': False,
                'protect': original['protect'],
            })

    def delete(self, user, index):
        original = next((
            val for val in self.parent.valsTable
            if val['active'] and val['id'] == index),
            None
        )

        if original:
            original['active'] = False
            self.parent.valsTable.append({
                'id': index,
                'parent': original['parent'],
                'active': False,
                'name': original['name'],
                'override': original['override'],
                'author': user,
                'datetime': datetime.now(),
                'value': original['value'],
                'first_last': True,
                'protect': original['protect']
            })

    def get_value(self, index):
        return next((
            (val['value'], val['protect']) for val in self.parent.valsTable
            if val['active'] and val['id'] == index),
            (None, None)
        )

    def get_history(self, index):
        return [
            value
            for value in self.parent.valsTable
            if ((value['id'] == index) or
                (value['parent'] == index and value['first_last']))
        ]

    def get_value_for(self, parent_index, name, override):
        value_with_no_override = None, None

        for val in self.parent.valsTable:
            if val['parent'] == parent_index and val['name'] == name and \
                    val['active']:
                if val['override'] == override:
                    return val['value'], val['protect']
                elif val['override'] == '':
                    value_with_no_override = val['value'], val['protect']

        return value_with_no_override

    def set_protect_status(self, user, index, status):
        original = next((
            val for val in self.parent.valsTable
            if (val['active']
                and val['id'] == index
                and val['protect'] != status)),
            None
        )

        if original:
            original['active'] = False
            self.parent.valsTable.append({
                'id': index,
                'parent': original['parent'],
                'active': True,
                'name': original['name'],
                'override': original['override'],
                'author': user,
                'datetime': datetime.now(),
                'value': original['value'],
                'first_last': False,
                'protect': status
            })

    def delete_user(self, author, user):
        for auth in self.parent.authTable:
            if auth['active'] and auth['user'] == user:
                auth['active'] = False
                self.parent.authTable.append({
                    'id': len(self.parent.authTable),
                    'active': False,
                    'datetime': datetime.now(),
                    'author': author,
                    'user': user,
                    'pass': '',
                    'user_root': auth['user_root']
                })
                return True
        return False

    def get_users(self, env):
        ret = {}
        users_root = self.get_env_root('users')
        all_users = self.get_children_of(users_root)

        for user in all_users:
            permissions = self.get_children_of(user['id'])

            for permission in permissions:
                if permission['name'] == env:
                    ret[user['name']] = permission['value']
        return ret

    def get_child(self, parent, name, override=''):
        children = self.get_children_of(parent)

        for child in children:
            if child['active'] and child['name'] == name \
                    and child['override'] == override:
                return child
