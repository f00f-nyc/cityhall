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

from django.test import TestCase
from lib.db.db import DbState, Rights
from lib.db.memory.cityhall_db_factory import CityHallDbFactory


class TestMemoryDb(TestCase):
    def test_open(self):
        db = CityHallDbFactory()
        db.open()
        self.assertEqual(DbState.Open, db.state)

    def test_cannot_open_twice(self):
        db = CityHallDbFactory()
        db.open()
        with self.assertRaises(Exception):
            db.open()

    def test_can_create_default_env(self):
        db = CityHallDbFactory()
        db.open()
        db.create_default_tables()
        self.assertIsInstance(db.authTable, list)
        self.assertIsInstance(db.valsTable, list)
        self.assertEqual(1, len(db.authTable))
        self.assertEqual(1, len(db.authTable))
        self.assertIsInstance(db.authTable[0], dict)
        self.assertIsInstance(db.valsTable[0], dict)

    def test_is_open(self):
        db = CityHallDbFactory()
        self.assertFalse(db.is_open())
        db.open()
        self.assertTrue(db.is_open())


class TestMemoryDbWithEnv(TestCase):
    def __init__(self, obj):
        super(TestCase, self).__init__(obj)
        self.conn = None

    def setUp(self):
        self.conn = CityHallDbFactory()
        self.conn.open()
        self.conn.create_default_tables()

    def test_create_user(self):
        count_before = len(self.conn.authTable)
        db = self.conn.get_db()
        users_root = db.get_env_root('users')
        db.create('cityhall', users_root, 'test', '')
        test_folder = db.get_child(users_root, 'test')
        test_id = test_folder['id']
        self.conn.get_db().create_user('cityhall', 'test', '', test_id)
        count_after = len(self.conn.authTable)
        self.assertEqual(count_before + 1, count_after)

        last_entry = self.conn.authTable[count_before]
        self.assertEqual(last_entry['user'], 'test')
        self.assertTrue(last_entry['active'])
        self.assertEqual(last_entry['user_root'], test_id)
        self.assertEqual(last_entry['author'], 'cityhall')

    def test_create_same_user_is_noop(self):
        db = self.conn.get_db()
        users_root = db.get_env_root('users')
        db.create('cityhall', users_root, 'test', '')
        test_folder = db.get_child(users_root, 'test')
        id = test_folder['id']

        self.conn.get_db().create_user('cityhall', 'test', '', id)

        count_before = len(self.conn.authTable)
        self.conn.get_db().create_user('cityhall', 'test', '', id)
        count_after = len(self.conn.authTable)
        self.assertEqual(count_before, count_after)

    def test_authenticate(self):
        self.assertFalse(self.conn.authenticate('test', ''))
        db = self.conn.get_db()
        users_env = db.get_env_root('users')
        db.create('cityhall', users_env, 'test', '')
        created = db.get_child(users_env, 'test')
        self.conn.get_db().create_user('cityhall', 'test', '', created['id'])
        self.assertTrue(self.conn.authenticate('test', ''))

    def test_create_root(self):
        vals_before = len(self.conn.valsTable)
        self.conn.get_db().create_root('cityhall', 'dev')
        vals_after = len(self.conn.valsTable)

        self.assertEqual(vals_before+1, vals_after)

    def test_create_env_returns_status(self):
        self.assertTrue(
            self.conn.get_db().create_root('cityhall', 'dev'),
            "If the root is created, create_env returns true"
        )
        self.assertIsNot(
            self.conn.get_db().create_root('cityhall', 'dev'),
            "If creating the root fails, create_env returns false"
        )

    def test_create_same_env_is_noop(self):
        db = self.conn.get_db()
        db.create_root('cityhall', 'dev')

        vals_before = len(self.conn.valsTable)
        auth_before = len(self.conn.authTable)
        db.create_root('cityhall', 'dev')
        self.assertEqual(vals_before, len(self.conn.valsTable))
        self.assertEqual(auth_before, len(self.conn.authTable))

    def test_create_root_is_complete(self):
        self.conn.get_db().create_root('cityhall', 'dev')

        val = self.conn.valsTable[-1]
        self.assertEqual('dev', val['name'])
        self.assertEqual(val['id'], val['parent'])
        self.assertEqual('', val['value'])
        self.assertEqual('cityhall', val['author'])
        self.assertEqual('', val['override'])
        self.assertTrue(val['active'])
        self.assertTrue(val['first_last'])

    def test_get_env_root_on_nonexistant(self):
        self.assertEqual(-1, self.conn.get_db().get_env_root('dev'))

    def test_get_env_root_on_existant(self):
        db = self.conn.get_db()
        db.create_root('cityhall', 'dev')
        val = self.conn.valsTable[-1]
        self.assertEqual(val['id'], db.get_env_root('dev'))


class TestMemoryDbWithEnvAndUser(TestCase):
    def __init__(self, obj):
        super(TestCase, self).__init__(obj)
        self.conn = None
        self.db = None

    def setUp(self):
        self.conn = CityHallDbFactory()
        self.conn.open()
        self.conn.create_default_tables()
        self.db = self.conn.get_db()
        self.users_root = self.db.get_env_root('users')
        self.user_root = self.db.get_child(self.users_root, 'cityhall')

        self._create_user('test')
        self.db.create_root('test', 'dev')
        self._give_user_rights('test', 'dev', Rights.Grant)

    def _create_user(self, name):
        self.db.create('cityhall', self.users_root, name, '')
        created = self.db.get_child(self.users_root, name)
        self.db.create_user('cityhall', name, '', created['id'])

    def _give_user_rights(self, name, env, rights):
        user_folder = self.db.get_child(self.users_root, name)
        exists = self.db.get_child(user_folder['id'], env)
        if exists:
            self.db.update('cityhall', exists['id'], rights)
        else:
            self.db.create('cityhall', user_folder['id'], env, rights)

    def test_get_children_of_empty(self):
        val_id = self.db.get_env_root('test')
        children = self.db.get_children_of(val_id)
        self.assertIsInstance(children, list)
        self.assertEqual(0, len(children))

    def test_create_value(self):
        dev_root = self.db.get_env_root('dev')
        before = len(self.conn.valsTable)
        self.db.create('test', dev_root, 'value1', 'some value')
        after = len(self.conn.valsTable)
        val = self.conn.valsTable[-1]

        self.assertEqual(before+1, after)
        self.assertTrue(val['active'])
        self.assertEqual('value1', val['name'])
        self.assertEqual(dev_root, val['parent'])
        self.assertEqual('some value', val['value'])
        self.assertNotEqual(dev_root, val['id'])
        self.assertTrue(val['first_last'])

    def test_child_value_is_returned(self):
        dev_root = self.db.get_env_root('dev')
        self.db.create('test', dev_root, 'value1', 'some value')
        children = self.db.get_children_of(dev_root)

        self.assertEqual(1, len(children))
        self.assertEqual('value1', children[0]['name'])
        self.assertEqual('some value', children[0]['value'])

    def test_update(self):
        dev_root = self.db.get_env_root('dev')
        self.db.create('test', dev_root, 'value1', 'some value')

        original_value = self.conn.valsTable[-1]
        before = len(self.conn.valsTable)
        self.db.update('test', original_value['id'], 'another value')
        after = len(self.conn.valsTable)
        new_value = self.conn.valsTable[-1]

        self.assertEqual(before+1, after)
        self.assertEqual(original_value['id'], new_value['id'])
        self.assertFalse(original_value['active'])
        self.assertTrue(new_value['id'])
        self.assertEqual('another value', new_value['value'])
        self.assertFalse(new_value['first_last'])

    def test_create_override(self):
        dev_root = self.db.get_env_root('dev')
        self.db.create('test', dev_root, 'value1', 'some value')

        original_value = self.conn.valsTable[-1]
        before = len(self.conn.valsTable)
        self.db.create('test', dev_root, 'value1', 'test value', 'test')
        after = len(self.conn.valsTable)
        new_value = self.conn.valsTable[before]

        self.assertEqual(before+1, after)
        self.assertNotEqual(original_value['id'], new_value['id'])
        self.assertTrue(original_value['active'])
        self.assertTrue(new_value['id'])
        self.assertEqual(original_value['parent'], new_value['parent'])

    def test_get_value(self):
        dev_root = self.db.get_env_root('dev')
        self.db.create('test', dev_root, 'value1', 'some value')
        item_in_db = self.conn.valsTable[-1]

        val_from_db = self.db.get_value(item_in_db['id'])
        self.assertEqual('some value', val_from_db[0])
        self.assertFalse(val_from_db[1])

    def test_get_value_of_nonexistant_returns_none(self):
        val = self.db.get_value(1000)
        self.assertIsNone(val[0])
        self.assertIsNone(val[1])

    def test_delete(self):
        dev_root = self.db.get_env_root('dev')
        self.db.create('test', dev_root, 'value1', 'abc')
        before = len(self.conn.valsTable)
        val_id = self.conn.valsTable[-1]['id']
        self.db.delete('test', val_id)
        after = len(self.conn.valsTable)
        entry = self.conn.valsTable[-1]

        self.assertEqual(before+1, after)
        self.assertFalse(entry['active'])
        self.assertTrue(entry['first_last'])

    def test_protect(self):
        dev_root = self.db.get_env_root('dev')
        self.db.create('test', dev_root, 'value1', 'some value')

        before = len(self.conn.valsTable)
        created = self.conn.valsTable[-1]
        self.db.set_protect_status('dev', created['id'], True)
        after = len(self.conn.valsTable)
        updated = self.conn.valsTable[-1]

        self.assertEqual(before+1, after)
        self.assertEqual(created['id'], updated['id'])
        self.assertFalse(created['protect'])
        self.assertTrue(updated['protect'])
        self.assertEqual(created['value'], updated['value'])
        self.assertFalse(updated['first_last'])
        self.assertFalse(created['active'])
        self.assertTrue(updated['active'])

    def test_unprotect(self):
        dev_root = self.db.get_env_root('dev')
        self.db.create('test', dev_root, 'value1', 'some value')
        val_id = self.conn.valsTable[-1]['id']
        self.db.set_protect_status('dev', val_id, True)

        before = len(self.conn.valsTable)
        self.db.set_protect_status('dev', val_id, False)
        after = len(self.conn.valsTable)
        public = self.conn.valsTable[-1]

        self.assertEqual(before+1, after)
        self.assertFalse(public['protect'])
        self.assertTrue(public['active'])

    def test_delete_user(self):
        self.db.delete_user('cityhall', 'test')
        entries = [
            auth for auth in self.conn.authTable
            if auth['user'] == 'test'
        ]

        self.assertEqual(2, len(entries))
        self.assertFalse(entries[0]['active'])
        self.assertFalse(entries[1]['active'])

    def test_get_users(self):
        self.db.create_root('cityhall', 'test_env')
        self._give_user_rights('cityhall', 'test_env', Rights.Grant)
        test_env_users = self.db.get_users('test_env')

        self.assertEqual(1, len(test_env_users))
        self.assertEqual(Rights.Grant, test_env_users['cityhall'])

        self._give_user_rights('cityhall', 'dev', Rights.Read)
        dev_users = self.db.get_users('dev')
        self.assertEqual(2, len(dev_users))
        self.assertIn('cityhall', dev_users)
        self.assertIn('test', dev_users)

    def test_update_user(self):
        before = len(self.conn.authTable)
        self.db.update_user('cityhall', 'test', 'password')
        after = len(self.conn.authTable)

        entries = [
            entry
            for entry in self.conn.authTable
            if entry['user'] == 'test'
        ]

        self.assertEqual(before+1, after)
        self.assertEqual(2, len(entries))
        self.assertFalse(entries[0]['active'])
        self.assertTrue(entries[1]['active'])
        self.assertEqual('password', entries[1]['pass'])
