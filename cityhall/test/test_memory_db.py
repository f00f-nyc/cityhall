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

    def test_get_rights_on_non_user_fails(self):
        self.assertEqual(-1, self.conn.get_db().get_rights('test', 'auto'))

    def test_get_rights_works(self):
        self.assertEqual(
            Rights.Admin,
            self.conn.get_db().get_rights('auto', 'cityhall')
        )

    def test_create_user(self):
        count_before = len(self.conn.authTable)
        self.conn.get_db().create_user('cityhall', 'test', '')
        count_after = len(self.conn.authTable)
        self.assertEqual(count_before + 1, count_after)

        last_entry = self.conn.authTable[count_before]
        self.assertEqual(last_entry['user'], 'test')
        self.assertEqual(last_entry['env'], 'auto')
        self.assertEqual(last_entry['rights'], Rights.NoRights)

    def test_create_same_user_is_noop(self):
        self.conn.get_db().create_user('cityhall', 'test', '')

        count_before = len(self.conn.authTable)
        self.conn.get_db().create_user('cityhall', 'test', '')
        count_after = len(self.conn.authTable)
        self.assertEqual(count_before, count_after)

    def test_set_rights_works(self):
        db = self.conn.get_db()
        db.create_user('cityhall', 'test', '')
        original_auth = self.conn.authTable[len(self.conn.authTable)-1]

        db.update_rights('cityhall', 'auto', 'test', Rights.Read)
        new_auth = self.conn.authTable[len(self.conn.authTable)-1]

        self.assertFalse(original_auth['active'])
        self.assertTrue(new_auth['active'])
        self.assertGreater(new_auth['id'], original_auth['id'])
        self.assertNotEqual(new_auth['rights'], original_auth['rights'])
        self.assertEqual(Rights.Read, new_auth['rights'])

    def test_set_rights_to_itself_is_noop(self):
        db = self.conn.get_db()
        db.create_user('cityhall', 'test', '')
        before = len(self.conn.authTable)
        db.update_rights('cityhall', 'auto', 'test', Rights.NoRights)
        after = len(self.conn.authTable)
        self.assertEqual(before, after)

    def test_create_rights_to_different_env(self):
        db = self.conn.get_db()
        db.create_user('cityhall', 'test', '')
        db.create_env('cityhall', 'dev')
        before = len(self.conn.authTable)
        db.create_rights('cityhall', 'dev', 'test', Rights.Read)
        after = len(self.conn.authTable)
        self.assertEqual(before+1, after)

    def test_authenticate(self):
        self.assertFalse(self.conn.authenticate('test', ''))
        self.conn.get_db().create_user('cityhall', 'test', '')
        self.assertTrue(self.conn.authenticate('test', ''))
        self.assertTrue(self.conn.authenticate('test', '', 'auto'))
        self.assertFalse(self.conn.authenticate('test', '', 'dev'))

    def test_create_env(self):
        vals_before = len(self.conn.valsTable)
        auth_before = len(self.conn.authTable)
        self.conn.get_db().create_env('cityhall', 'dev')
        vals_after = len(self.conn.valsTable)
        auth_after = len(self.conn.authTable)

        self.assertEqual(vals_before+1, vals_after)
        self.assertEqual(auth_before+1, auth_after)

    def test_create_env_returns_status(self):
        self.assertTrue(
            self.conn.get_db().create_env('cityhall', 'dev'),
            "If the env is created, create_env returns true"
        )
        self.assertIsNot(
            self.conn.get_db().create_env('cityhall', 'dev'),
            "If creating the env fails, create_env returns false"
        )
        self.assertIsNot(
            self.conn.get_db().create_env('non_existant_user', 'dev'),
            "If creating the env fails, create_env returns false"
        )

    def test_create_same_env_is_noop(self):
        db = self.conn.get_db()
        db.create_env('cityhall', 'dev')

        vals_before = len(self.conn.valsTable)
        auth_before = len(self.conn.authTable)
        db.create_env('cityhall', 'dev')
        self.assertEqual(vals_before, len(self.conn.valsTable))
        self.assertEqual(auth_before, len(self.conn.authTable))

    def test_create_env_creates_root(self):
        self.conn.get_db().create_env('cityhall', 'dev')

        val = self.conn.valsTable[-1]
        self.assertEqual('dev', val['env'])
        self.assertEqual('/', val['name'])
        self.assertEqual(val['id'], val['parent'])
        self.assertEqual('', val['value'])
        self.assertEqual('cityhall', val['author'])
        self.assertEqual('', val['override'])
        self.assertTrue(val['active'])
        self.assertTrue(val['first_last'])

    def test_create_env_creates_authentications(self):
        self.conn.get_db().create_env('cityhall', 'dev')

        auth = self.conn.authTable[-1]
        self.assertEqual('dev', auth['env'])
        self.assertEqual(Rights.Grant, auth['rights'])
        self.assertEqual('cityhall', auth['user'])
        self.assertEqual('', auth['pass'])
        self.assertEqual('cityhall', auth['author'])

    def test_create_env_on_non_user_fails(self):
        before = len(self.conn.valsTable)
        self.conn.get_db().create_env('test', 'dev')
        self.assertEqual(before, len(self.conn.valsTable))

    def test_get_env_root_on_nonexistant(self):
        self.assertEqual(-1, self.conn.get_db().get_env_root('dev'))

    def test_get_env_root_on_existant(self):
        db = self.conn.get_db()
        db.create_env('cityhall', 'dev')
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
        self.db.create_user('cityhall', 'test', '')
        self.db.create_env('test', 'dev')

    def test_get_children_of_empty(self):
        val_id = self.db.get_env_root('test')
        children = self.db.get_children_of(val_id)
        self.assertIsInstance(children, list)
        self.assertEqual(0, len(children))

    def test_create_value(self):
        dev_root = self.db.get_env_root('dev')
        before = len(self.conn.valsTable)
        self.db.create('test', 'dev', dev_root, 'value1', 'some value')
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
        self.db.create('test', 'dev', dev_root, 'value1', 'some value')
        children = self.db.get_children_of(dev_root)

        self.assertEqual(1, len(children))
        self.assertEqual('value1', children[0]['name'])
        self.assertEqual('some value', children[0]['value'])

    def test_update(self):
        dev_root = self.db.get_env_root('dev')
        self.db.create('test', 'dev', dev_root, 'value1', 'some value')

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
        self.db.create('test', 'dev', dev_root, 'value1', 'some value')

        original_value = self.conn.valsTable[-1]
        before = len(self.conn.valsTable)
        self.db.create('test', 'dev', dev_root, 'value1', 'test value', 'test')
        after = len(self.conn.valsTable)
        new_value = self.conn.valsTable[before]

        self.assertEqual(before+1, after)
        self.assertNotEqual(original_value['id'], new_value['id'])
        self.assertTrue(original_value['active'])
        self.assertTrue(new_value['id'])
        self.assertEqual(original_value['parent'], new_value['parent'])

    def test_get_value(self):
        dev_root = self.db.get_env_root('dev')
        self.db.create('test', 'dev', dev_root, 'value1', 'some value')
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
        self.db.create('test', 'dev', dev_root, 'value1', 'abc')
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
        self.db.create('test', 'dev', dev_root, 'value1', 'some value')

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
        self.db.create('test', 'dev', dev_root, 'value1', 'some value')
        val_id = self.conn.valsTable[-1]['id']
        self.db.set_protect_status('dev', val_id, True)

        before = len(self.conn.valsTable)
        self.db.set_protect_status('dev', val_id, False)
        after = len(self.conn.valsTable)
        public = self.conn.valsTable[-1]

        self.assertEqual(before+1, after)
        self.assertFalse(public['protect'])
        self.assertTrue(public['active'])

    def test_get_user(self):
        self.db.create_rights('cityhall', 'test_env0', 'test', Rights.NoRights)
        self.db.create_rights('cityhall', 'test_env1', 'test', Rights.Read)
        self.db.create_rights('cityhall', 'test_env2', 'test', Rights.ReadProtected)
        self.db.create_rights('cityhall', 'test_env3', 'test', Rights.Write)
        self.db.create_rights('cityhall', 'test_env4', 'test', Rights.Grant)
        user_rights = self.db.get_user('test')

        for i in range(0, 4):
            env_name = 'test_env' + str(i)
            self.assertIn(env_name, user_rights)
            self.assertEqual(i, user_rights[env_name])

    def test_delete_user(self):
        self.db.update_rights('cityhall', 'test_env', 'test', Rights.Read)
        activate_index = len(self.conn.authTable)-1

        before = len(self.conn.authTable)
        self.db.delete_user('cityhall', 'test')
        after = len(self.conn.authTable)

        activate = self.conn.authTable[activate_index]
        entry2 = self.conn.authTable[-2]
        entry1 = self.conn.authTable[-1]

        self.assertEqual(before+2, after)
        self.assertEqual('cityhall', entry1['author'])
        self.assertFalse(activate['active'])
        self.assertTrue(entry1['active'])
        self.assertTrue(entry2['active'])
        self.assertEqual(-1, entry1['rights'])
        self.assertEqual(-1, entry2['rights'])

    def test_only_positive_rights_exist(self):
        self.db.update_rights('cityhall', 'dev', 'test', Rights.NoRights)
        before = self.db.get_user('test')
        self.assertIn('dev', before)

        self.db.update_rights('cityhall', 'dev', 'test', Rights.DontExist)
        after = self.db.get_user('test')
        self.assertNotIn('dev', after)

    def test_get_users(self):
        self.db.create_env('cityhall', 'test_env')
        test_env_users = self.db.get_users('test_env')
        self.assertEqual(1, len(test_env_users))
        self.assertEqual(Rights.Grant, test_env_users['cityhall'])

        self.db.create_rights('test', 'dev', 'cityhall', Rights.Read)
        dev_users = self.db.get_users('dev')
        self.assertEqual(2, len(dev_users))
        self.assertIn('cityhall', dev_users)
        self.assertIn('test', dev_users)
