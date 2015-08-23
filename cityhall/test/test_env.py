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
from lib.db.memory.cityhall_db_factory import CityHallDbFactory
from lib.db.db import Rights
from lib.db.connection import Connection


class TestEnvironment(TestCase):
    def __init__(self, obj):
        super(TestCase, self).__init__(obj)
        self.db = None
        self.conn = None
        self.env = None

    def setUp(self):
        self.conn = Connection(CityHallDbFactory())
        self.db = self.conn.db_connection
        self.conn.connect()
        self.conn.create_default_env()
        self.auth = self.conn.get_auth('cityhall', '')
        self.env = self.auth.get_env('auto')

    def test_can_get_auth_from_env(self):
        auth = self.env.get_auth()
        self.assertTrue(auth is not None)

    def test_setting(self):
        self.env.set('/new_item', '')
        self.assertEqual('new_item', self.db.valsTable[-1]['name'])

    def test_add_children(self):
        self.env.set('/parent', '')
        self.env.set('/parent/child', '')
        parent = self.db.valsTable[-2]
        child = self.db.valsTable[-1]
        self.assertEqual(child['parent'], parent['id'])
        self.assertEqual(child['name'], 'child')

    def test_adding_overrides(self):
        before = len(self.db.valsTable)
        override_name = 'cityhall'
        override_val = 'some other value'
        self.env.set('/value', 'global value')
        self.env.set('/value', override_val, override_name)
        after = len(self.db.valsTable)

        global_val = self.db.valsTable[-2]
        override_val = self.db.valsTable[-1]

        self.assertEqual(before+2, after)
        self.assertEqual(override_val['override'], override_name)
        self.assertTrue(override_val['active'])
        self.assertTrue(global_val['active'])
        self.assertTrue(global_val['name'], override_val['name'])
        self.assertNotEqual(global_val['id'], override_val['id'])
        self.assertEqual(
            override_val['value'],
            self.env.get_explicit('/value', override_name)
        )

    def test_can_add_overrides_to_children(self):
        global_val = 'global_val'
        override_val = 'override_val'

        self.env.set('/parent1', '')
        self.env.set('/parent1/parent2', '')
        self.env.set('/parent1/parent2/child', global_val)
        self.env.set('/parent1/parent2/child', override_val, 'cityhall')

        self.assertEqual(
            global_val,
            self.env.get_explicit('/parent1/parent2/child')
        )
        self.assertEqual(
            override_val,
            self.env.get_explicit('/parent1/parent2/child', 'cityhall')
        )

    def test_able_to_add_global_val_to_root(self):
        before = len(self.db.valsTable)
        self.env.set('/value', 'abc')
        after = len(self.db.valsTable)
        self.assertEqual(before+1, after)

    def test_able_to_add_override_val_to_root(self):
        before = len(self.db.valsTable)
        self.env.set('/value', 'abc', 'cityhall')
        after = len(self.db.valsTable)

        val1 = self.db.valsTable[-2]
        val2 = self.db.valsTable[-1]

        self.assertTrue(val1['name'], val2['name'])
        self.assertTrue(val1['override'] == '' or val2['override'] == '')
        self.assertTrue(
            val1['override'] == 'cityhall' or val2['override'] == 'cityhall'
        )
        self.assertEqual(before+2, after)
        self.assertNotEqual(val1['id'], val2['id'])
        self.assertEqual(val1['parent'], val2['parent'])

    def test_cannot_add_children_to_items_that_do_not_exist(self):
        self.assertFalse(self.env.set('/parent/child', 'abc'))

    def test_able_to_read_values_set(self):
        value_global = 'some value'
        value_override = 'global value'
        self.env.set('/value', value_global)
        self.env.set('/value', value_override, 'cityhall')
        self.assertEqual(value_global, self.env.get_explicit('/value'))
        self.assertEqual(
            value_override,
            self.env.get_explicit('/value', 'cityhall')
        )

    def test_adding_a_new_value_makes_old_one_inactive(self):
        self.env.set('/value', 'old value')
        self.env.set('/value', 'new value')

        first_added = self.db.valsTable[-2]
        second_added = self.db.valsTable[-1]

        self.assertEqual(first_added['id'], second_added['id'])
        self.assertNotEqual(first_added['active'], second_added['active'])

    def test_library_get(self):
        # this is the get that most libraries will use,
        # they will expect to just provide the path and get either the global
        # or their specific one
        self.env.set('/value', 'abc')
        self.env.set('/value', 'def', 'cityhall')
        self.assertEqual('def', self.env.get('/value'))

        auth = self.env.get_auth()
        auth.create_user('test', '')
        auth.grant('auto', 'test', Rights.Read)
        test_auth = self.conn.get_auth('test', '')
        test_env = test_auth.get_env('auto')
        self.assertEqual('abc', test_env.get('/value'))

    def children_match_value1_value2_value3(self, children):
        self.assertEqual(3, len(children))
        names = [child['name'] for child in children]
        self.assertTrue('value1' in names)
        self.assertTrue('value2' in names)
        self.assertTrue('value3' in names)
        self.assertTrue('id' in children[0])
        self.assertTrue('name' in children[0])
        self.assertTrue('override' in children[0])

    def test_get_children_of_root(self):
        self.env.set('/value1', 'abc')
        self.env.set('/value2', 'def')
        self.env.set('/value3', 'ghi')

        children = self.env.get_children('/')
        self.children_match_value1_value2_value3(children)

    def test_get_children_of_sub_value(self):
        self.env.set('/parent', '')
        self.env.set('/parent/value1', 'abc')
        self.env.set('/parent/value2', 'def')
        self.env.set('/parent/value3', 'ghi')

        children = self.env.get_children('/parent')
        self.children_match_value1_value2_value3(children)

    def test_get_history(self):
        self.env.set('/value1', 'abc')
        self.env.set('/value1', 'def')
        self.env.set('/value1', 'ghi')
        hist = self.env.get_history('/value1')

        self.assertEqual(3, len(hist))
        first = hist[0]
        self.assertTrue('id' in first)
        self.assertTrue('name' in first)
        self.assertTrue('value' in first)
        self.assertTrue('author' in first)
        self.assertTrue('datetime' in first)
        self.assertTrue('active' in first)
        self.assertTrue('protect' in first)

    def test_get_history_must_have_elevated_permissions(self):
        self.env.set('/value1', 'abc')

        auth = self.env.get_auth()
        auth.create_user('test_read', '')
        auth.grant('auto', 'test_read', Rights.Read)
        auth.create_user('test_read_protect', '')
        auth.grant('auto', 'test_read_protect', Rights.ReadProtected)

        read_auth = self.conn.get_auth('test_read', '')
        env = read_auth.get_env('auto')
        hist = env.get_history('/value1')
        self.assertEqual(0, len(hist))

        read_protected_auth = self.conn.get_auth('test_read_protect', '')
        env = read_protected_auth.get_env('auto')
        hist = env.get_history('/value1')
        self.assertEqual(1, len(hist))

    def test_get_history_of_override(self):
        self.env.set('/value1', 'abc')
        self.env.set('/value1', '123', 'cityhall')
        self.env.set('/value1', '456', 'cityhall')

        hist_global = self.env.get_history('/value1')
        hist_override = self.env.get_history('/value1', 'cityhall')

        self.assertEqual(1, len(hist_global))
        self.assertEqual(2, len(hist_override))

    def test_delete(self):
        self.env.set('/value1', 'abc')
        self.env.delete('value1')
        children = self.env.get_children('/')
        self.assertEqual(0, len(children))

    def test_children_created_show_up_in_history(self):
        self.env.set('/value1', '')
        hist_before = self.env.get_history('/value1')
        self.env.set('/value1/child', 'abc')
        hist_after = self.env.get_history('/value1')
        self.assertEqual(len(hist_before)+1, len(hist_after))

    def test_children_deleted_show_up_in_history(self):
        self.env.set('/value1', '')
        self.env.set('/value1/child', 'abc')
        hist_before = self.env.get_history('/value1')
        self.env.delete('/value1/child')
        hist_after = self.env.get_history('/value1')
        self.assertEqual(len(hist_before)+1, len(hist_after))

    def test_children_value_do_not_show_up_in_history(self):
        self.env.set('/value1', '')
        self.env.set('/value1/child', 'abc')
        hist_before = self.env.get_history('/value1')
        self.env.set('/value1/child', 'def')
        hist_after = self.env.get_history('/value1')
        self.assertEqual(len(hist_before), len(hist_after))

    def test_deleting_global_also_deletes_overrides(self):
        self.env.set('/value1', 'abc')
        self.env.set('/value1', 'def', 'cityhall')
        self.env.delete('/value1', '')
        get = self.env.get_explicit('/value1', 'cityhall')
        self.assertIsNone(get)

    def test_deleted_values_no_longer_returned(self):
        self.env.set('/value1', 'abc')
        self.env.delete('/value1', '')
        deleted = self.env.get('/value1')
        does_not_exist = self.env.get('/key_doesnt_exist')
        self.assertEqual(deleted, does_not_exist)
        self.assertIsNone(deleted)

    def test_cannot_delete_root(self):
        self.env.set('/', 'abc')
        self.env.delete('/', '')
        self.assertEqual('abc', self.env.get('/'))

    def test_can_protect(self):
        self.env.set('/value1', 'abc')
        self.env.set_protect(True, '/value1', '')
        protect = self.db.valsTable[-1]
        self.assertEqual('value1', protect['name'])
        self.assertTrue(protect['protect'])

    def test_can_unprotect(self):
        self.env.set('/value1', 'abc')
        self.env.set_protect(True, '/value1', '')
        self.env.set_protect(False, '/value1', '')
        unprotect = self.db.valsTable[-1]
        self.assertEqual('value1', unprotect['name'])
        self.assertFalse(unprotect['protect'])

    def test_can_protect_override(self):
        self.env.set('/value1', 'abc', 'test')
        self.env.set_protect(True, '/value1', 'test')
        protect = self.db.valsTable[-1]
        self.assertEqual('test', protect['override'])
        self.assertTrue(protect['protect'])

    def test_protect_requires_write_permissions(self):
        auth = self.conn.get_auth('cityhall', '')
        auth.create_user('test', '')
        auth.grant('auto', 'test', Rights.Read)
        auth_test = self.conn.get_auth('test', '')
        test_env = auth_test.get_env('auto')

        self.env.set('/value1', 'abc')
        before = len(self.db.valsTable)
        self.assertFalse(test_env.set_protect(True, '/value1', ''))
        after = len(self.db.valsTable)
        self.assertEqual(before, after)

    def test_protect_again_is_noop(self):
        self.env.set('/value1', 'abc')
        self.env.set_protect(True, '/value1', '')
        before = len(self.db.valsTable)
        self.assertTrue(self.env.set_protect(True, '/value1', ''))
        after = len(self.db.valsTable)
        self.assertEqual(before, after)

    def test_protect_shows_up_in_history(self):
        self.env.set('/value1', 'abc')
        self.env.set_protect(True, '/value1', '')
        hist = self.env.get_history('/value1')
        self.assertEqual(2, len(hist))
        self.assertTrue(hist[1]['protect'])

    def test_protect_is_honored(self):
        auth = self.conn.get_auth('cityhall', '')
        self.env.set('/value1', 'abc')
        self.env.set_protect(True, '/value1', '')

        auth.create_user('test', '')
        auth.grant('auto', 'test', Rights.Read)
        test_auth = self.conn.get_auth('test', '')
        test_env = test_auth.get_env('auto')
        self.assertIsNone(test_env.get('/value1'))
