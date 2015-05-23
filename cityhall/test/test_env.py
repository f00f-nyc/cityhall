from django.test import TestCase
from lib.db.memory.cityhall_db import CityHallDb
from lib.db.connection import Connection


class TestEnvironment(TestCase):
    def __init__(self, obj):
        super(TestCase, self).__init__(obj)
        self.db = None
        self.conn = None
        self.env = None

    def setUp(self):
        self.conn = Connection(CityHallDb())
        self.db = self.conn.db
        self.conn.connect()
        self.conn.create_default_env()
        self.env = self.conn.get_env('cityhall', '', 'auto')

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
        self.assertEqual(override_val['value'], self.env.get('/value', override_name))

    def test_can_add_overrides_to_children(self):
        global_val = 'global_val'
        override_val = 'override_val'

        self.env.set('/parent1', '')
        self.env.set('/parent1/parent2', '')
        self.env.set('/parent1/parent2/child', global_val)
        self.env.set('/parent1/parent2/child', override_val, 'cityhall')

        self.assertEqual(global_val, self.env.get('/parent1/parent2/child'))
        self.assertEqual(
            override_val,
            self.env.get('/parent1/parent2/child', 'cityhall')
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
        self.assertEqual(value_global, self.env.get('/value'))
        self.assertEqual(value_override, self.env.get('/value', 'cityhall'))

    def test_adding_a_new_value_makes_old_one_inactive(self):
        self.env.set('/value', 'old value')
        self.env.set('/value', 'new value')

        first_added = self.db.valsTable[-2]
        second_added = self.db.valsTable[-1]

        self.assertEqual(first_added['id'], second_added['id'])
        self.assertNotEqual(first_added['active'], second_added['active'])
