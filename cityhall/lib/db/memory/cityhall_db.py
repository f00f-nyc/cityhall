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

from lib.db.db import Db
from lib.db.db import Rights
from datetime import datetime


def get_next_id(table):
    max_id = -1
    for item in table:
        max_id = item['id'] if item['id'] > max_id else max_id
    return max_id + 1


class CityHallDb(Db):
    def __init__(self, db):
        self.db = db

    @property
    def __str__(self):
        from lib.db.memory.cityhall_db_factory import CityHallDbFactory
        assert isinstance(self.db, CityHallDbFactory)
        return "(In-Memory Db): Values: {}, Authorizations: {}".format(
            len(self.db.valsTable) if self.db.valsTable else 'None',
            len(self.db.authTable) if self.db.authTable else 'None'
        )

    def get_rights(self, env, user):
        for auth in self.db.authTable:
            if auth['active'] and (auth['env'] == env) and\
                    (auth['user'] == user):
                return auth['rights']
        return Rights.DontExist

        # return next(
        #     (auth['rights'] for auth in self.db.authTable
        #         if auth['active'] and (auth['env'] == env) and
        #         (auth['user'] == user)),
        #     Rights.DontExist
        # )

    def create_user(self, author, user, passhash):
        if self.get_rights('auto', user) == Rights.DontExist:
            self.db.authTable.append({
                'id': len(self.db.authTable),
                'active': True,
                'datetime': datetime.now(),
                'env': 'auto',
                'author': author,
                'user': user,
                'pass': passhash,
                'rights': Rights.NoRights,
            })

    def update_rights(self, author, env, user, rights):
        auth_id = next(
            (auth['id'] for auth in self.db.authTable
                if auth['active'] and (auth['user'] == user) and
                (auth['env'] == env) and auth['rights'] != rights),
            Rights.DontExist
        )
        if auth_id > 0:
            auth = self.db.authTable[auth_id]
            auth['active'] = False
            self.db.authTable.append({
                'id': len(self.db.authTable),
                'active': True,
                'datetime': datetime.now(),
                'env': env,
                'author': author,
                'user': user,
                'pass': auth['pass'],
                'rights': rights
            })

    def create_rights(self, author, env, user, rights):
        auth_id = next(
            (auth['id'] for auth in self.db.authTable
                if auth['active'] and (auth['user'] == user) and
                (auth['env'] == env) and auth['rights'] != rights),
            Rights.DontExist
        )
        auth_pass = next(
            (auth['pass'] for auth in self.db.authTable
                if auth['active'] and auth['user'] == user),
            None
        )

        if isinstance(auth_pass, basestring) and (auth_id == Rights.DontExist):
            self.db.authTable.append({
                'id': len(self.db.authTable),
                'active': True,
                'datetime': datetime.now(),
                'env': env,
                'author': author,
                'user': user,
                'pass': auth_pass,
                'rights': rights
            })

    def create_env(self, user, env):
        auth_id = next(
            (auth['id'] for auth in self.db.authTable
                if auth['active'] and (auth['user'] == user)),
            -1
        )
        user_exists = auth_id >= 0
        env_exists = self.get_env_root(env) >= 0

        if user_exists and not env_exists:
            auth = self.db.authTable[auth_id]
            val_id = get_next_id(self.db.valsTable)
            self.db.authTable.append({
                'id': len(self.db.authTable),
                'active': True,
                'datetime': datetime.now(),
                'env': env,
                'author': user,
                'user': user,
                'pass': auth['pass'],
                'rights': Rights.Grant,
            })
            self.db.valsTable.append({
                'id': val_id,
                'env': env,
                'parent': val_id,
                'active': True,
                'name': '/',
                'override': '',
                'author': user,
                'datetime': datetime.now(),
                'value': '',
                'first_last': True,
                'protect': False,
            })
            return True
        return False

    def get_env_root(self, env):
        return next(
            (val['id'] for val in self.db.valsTable
                if val['active'] and val['env'] == env),
            -1
        )

    def get_children_of(self, index):
        return [
            child for child in self.db.valsTable
            if child['active'] and child['parent'] == index
            and child['id'] != index        # do not return roots
        ]

    def create(self, user, env, parent, name, value, override=''):
        self.db.valsTable.append({
            'id': get_next_id(self.db.valsTable),
            'env': env,
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

    def update(self, user, index, value):
        original = next((
            val for val in self.db.valsTable
            if val['active'] and val['id'] == index),
            None
        )

        if original:
            original['active'] = False
            self.db.valsTable.append({
                'id': index,
                'env': original['env'],
                'parent': original['parent'],
                'active': True,
                'name': original['name'],
                'override': original['override'],
                'author': user,
                'datetime': datetime.now(),
                'value': value,
                'first_last': False,
                'protect': False,
            })

    def delete(self, user, index):
        original = next((
            val for val in self.db.valsTable
            if val['active'] and val['id'] == index),
            None
        )

        if original:
            original['active'] = False
            self.db.valsTable.append({
                'id': index,
                'env': original['env'],
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
            (val['value'], val['protect']) for val in self.db.valsTable
            if val['active'] and val['id'] == index),
            (None, None)
        )

    def get_history(self, index):
        return [
            value
            for value in self.db.valsTable
            if ((value['id'] == index) or
                (value['parent'] == index and value['first_last']))
        ]

    def get_value_for(self, parent_index, name, override):
        value_with_no_override = None, None

        for val in self.db.valsTable:
            if val['parent'] == parent_index and val['name'] == name and \
                    val['active']:
                if val['override'] == override:
                    return val['value'], val['protect']
                elif val['override'] == '':
                    value_with_no_override = val['value'], val['protect']

        return value_with_no_override

    def set_protect_status(self, user, index, status):
        original = next((
            val for val in self.db.valsTable
            if (val['active']
                and val['id'] == index
                and val['protect'] != status)),
            None
        )

        if original:
            original['active'] = False
            self.db.valsTable.append({
                'id': index,
                'env': original['env'],
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
