from lib.db import db
from lib.db.db import DbState, Rights
from datetime import datetime


def get_next_id(table):
    max_id = -1
    for item in table:
        max_id = item['id'] if item['id'] > max_id else max_id
    return max_id + 1


class CityHallDb(db.Db):
    def __init__(self):
        self.state = DbState.Closed
        self.authTable = None
        self.valsTable = None

    def __str__(self):
        return "(In-Memory Db): Values: {}, Authorizations: {}".format(
            len(self.valsTable) if self.valsTable else 'None',
            len(self.authTable) if self.authTable else 'None'
        )

    def open(self):
        if self.state == DbState.Closed:
            self.state = DbState.Open
        else:
            raise Exception("Cannot open new connection, already opened")

    def create_default_tables(self):
        self.valsTable = [{
            'id': 1,
            'env': 'auto',
            'parent': 0,
            'active': True,
            'name': '/',
            'override': '',
            'author': 'cityhall',
            'datetime': datetime.now(),
            'value': '',
            'protect': False,
        }]
        self.authTable = [{
            'id': 0,
            'active': True,
            'datetime': datetime.now(),
            'env': 'auto',
            'author': 'cityhall',
            'user': 'cityhall',
            'pass': '',
            'rights': Rights.Grant,
        }]

    def get_rights(self, env, user):
        for auth in self.authTable:
            if auth['active'] and (auth['env'] == env) and\
                    (auth['user'] == user):
                return auth['rights']
        return Rights.DontExist

        # return next(
        #     (auth['rights'] for auth in self.authTable
        #         if auth['active'] and (auth['env'] == env) and
        #         (auth['user'] == user)),
        #     Rights.DontExist
        # )

    def create_user(self, author, user, passhash):
        if self.get_rights('auto', user) == Rights.DontExist:
            self.authTable.append({
                'id': len(self.authTable),
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
            (auth['id'] for auth in self.authTable
                if auth['active'] and (auth['user'] == user) and
                (auth['env'] == env) and auth['rights'] != rights),
            Rights.DontExist
        )
        if auth_id > 0:
            auth = self.authTable[auth_id]
            auth['active'] = False
            self.authTable.append({
                'id': len(self.authTable),
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
            (auth['id'] for auth in self.authTable
                if auth['active'] and (auth['user'] == user) and
                (auth['env'] == env) and auth['rights'] != rights),
            Rights.DontExist
        )
        auth_pass = next(
            (auth['pass'] for auth in self.authTable
                if auth['active'] and auth['user'] == user),
            None
        )

        if isinstance(auth_pass, basestring) and (auth_id == Rights.DontExist):
            self.authTable.append({
                'id': len(self.authTable),
                'active': True,
                'datetime': datetime.now(),
                'env': env,
                'author': author,
                'user': user,
                'pass': auth_pass,
                'rights': rights
            })

    def authenticate(self, user, passhash, env=None):
        if not self.authTable:
            return None

        check_env = lambda a: True if not env else a['env'] == env

        for auth in self.authTable:
            if auth['active'] and (auth['pass'] == passhash) and\
                    (auth['user'] == user) and check_env(auth):
                return True
        return False

        # return next(
        #     (auth['active'] for auth in self.authTable
        #         if auth['active'] and (auth['pass'] == passhash) and
        #         (auth['user'] == user) and check_env(auth)),
        #     False
        # )

    def is_open(self):
        return self.state == DbState.Open

    def create_env(self, user, env):
        auth_id = next(
            (auth['id'] for auth in self.authTable
                if auth['active'] and (auth['user'] == user)),
            -1
        )
        user_exists = auth_id >= 0
        env_exists = self.get_env_root(env) >= 0

        if user_exists and not env_exists:
            auth = self.authTable[auth_id]
            val_id = get_next_id(self.valsTable)
            self.authTable.append({
                'id': len(self.authTable),
                'active': True,
                'datetime': datetime.now(),
                'env': env,
                'author': user,
                'user': user,
                'pass': auth['pass'],
                'rights': Rights.Grant,
            })
            self.valsTable.append({
                'id': val_id,
                'env': env,
                'parent': val_id,
                'active': True,
                'name': '/',
                'override': '',
                'author': user,
                'datetime': datetime.now(),
                'value': '',
                'protect': False,
            })

    def get_env_root(self, env):
        return next(
            (val['id'] for val in self.valsTable
                if val['active'] and val['env'] == env),
            -1
        )

    def get_children_of(self, index):
        return [
            child for child in self.valsTable
            if child['active'] and child['parent'] == index
            and child['id'] != index        # do not return roots
        ]

    def create(self, user, env, parent, name, value, override=''):
        self.valsTable.append({
            'id': get_next_id(self.valsTable),
            'env': env,
            'parent': parent,
            'active': True,
            'name': name,
            'override': override,
            'author': user,
            'datetime': datetime.now(),
            'value': value,
            'protect': False,
        })

    def update(self, user, index, value):
        original = next((
            val for val in self.valsTable
            if val['active'] and val['id'] == index),
            None
        )

        if original:
            original['active'] = False
            self.valsTable.append({
                'id': index,
                'env': original['env'],
                'parent': original['parent'],
                'active': True,
                'name': original['name'],
                'override': original['override'],
                'author': user,
                'datetime': datetime.now(),
                'value': value,
                'protect': False,
            })

    def get_value(self, index):
        return next((
            val['value'] for val in self.valsTable
            if val['active'] and val['id'] == index),
            None
        )

    def get_history(self, index):
        return [value for value in self.valsTable if value['id'] == index]

    def get_value_for(self, parent_index, name, override):
        value_with_no_override = None

        for val in self.valsTable:
            if val['parent'] == parent_index and val['name'] == name and \
                    val['active']:
                if val['override'] == override:
                    return val['value']
                elif val['override'] == '':
                    value_with_no_override = val['value']

        return value_with_no_override