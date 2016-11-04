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

from api.models import User, Value
from api.db.django.environments import Environments
from api.db.django.users import Users
from api.db.django.values import Values


class TestEnvironments(TestCase):
    def setUp(self):
        self.envs = Environments()

    def test_create_root(self):
        root_id = self.envs.create_root('cityhall', 'test_root')
        entry = Value.objects.get(
            author='cityhall', parent=-1, name='test_root', active=True
        )
        self.assertGreater(entry.id, 0)
        self.assertEqual('', entry.override)
        self.assertIsNotNone(entry.datetime)
        self.assertEqual('', entry.entry)
        self.assertFalse(entry.protect)
        self.assertTrue(entry.first_last)
        self.assertEqual(root_id, entry.id)

    def test_get_env_root(self):
        self.envs.create_root('cityhall', 'test_root')
        entry = Value.objects.get(
            author='cityhall', parent=-1, name='test_root', active=True
        )
        env_root = self.envs.get_env_root('test_root')
        self.assertEqual(entry.id, env_root)

    def test_cannot_create_same_env_twice(self):
        id1 = self.envs.create_root('cityhall', 'test_root')
        id2 = self.envs.create_root('cityhall', 'test_root')
        self.assertTrue(id1)
        self.assertFalse(id2)


class TestUsers(TestCase):
    def setUp(self):
        self.users = Users()
        self.envs = Environments()
        self.values = Values()

    def test_create_user(self):
        users_root = self.envs.get_env_root('users')
        user_root = self.values.create('cityhall', users_root, 'test', '')
        self.users.create_user('cityhall', 'test', '', user_root)
        created = User.objects.get(
            active=True,
            name='test',
            author='cityhall',
            password='',
            user_root=user_root,
        )
        self.assertIsNotNone(created.datetime)

    def test_delete_user(self):
        users_root = self.envs.get_env_root('users')
        user_root = self.values.create('cityhall', users_root, 'test', '')
        self.users.create_user('cityhall', 'test', '', user_root)
        self.users.delete_user('cityhall', 'test')

        user_entries = User.objects.filter(name='test')
        self.assertEqual(2, len(user_entries))

    def test_deleted_user_is_invalid(self):
        users_root = self.envs.get_env_root('users')
        user_root = self.values.create('cityhall', users_root, 'test', '')
        self.users.create_user('cityhall', 'test', '', user_root)
        self.users.delete_user('cityhall', 'test')
        self.assertFalse(User.objects.is_valid('test', ''))

    def test_get_users(self):
        users_root = self.envs.get_env_root('users')
        user_root = self.values.create('cityhall', users_root, 'test', '')
        self.users.create_user('cityhall', 'test', '', user_root)

        users_before = self.users.get_users('auto')
        self.assertNotIn('test', users_before)

        self.values.create('cityhall', user_root, 'auto', '1')
        users_after = self.users.get_users('auto')
        self.assertIn('test', users_after)
        self.assertEqual(1, int(users_after['test']))

    def test_update_user(self):
        users_root = self.envs.get_env_root('users')
        user_root = self.values.create('cityhall', users_root, 'test', '')
        self.users.create_user('cityhall', 'test', '', user_root)

        before = User.objects.count()
        self.users.update_user('cityhall', 'test', 'password')
        after = User.objects.count()

        entries = list(User.objects.filter(name='test'))

        self.assertEqual(before+1, after)
        self.assertEqual(2, len(entries))
        self.assertFalse(entries[0].active)
        self.assertTrue(entries[1].active)
        self.assertEqual('password', entries[1].password)


class TestValues(TestCase):
    def setUp(self):
        self.values = Values()
        self.auto_root = Value.objects.get(
            active=True, name='auto', parent=-1
        )
        self.auto_id = self.auto_root.id

    def _create(self, name, value, override=''):
        return self.values.create(
            'cityhall', self.auto_id, name, value, override
        )

    def test_create(self):
        values_before = Value.objects.count()
        ret = self._create('test', '123', '')
        values_after = Value.objects.count()

        self.assertEqual(1+values_before, values_after)
        created = Value.objects.get(
            active=True,
            name='test',
            parent=self.auto_id,
            override='',
            author='cityhall',
            entry='123',
            protect=False,
            first_last=True
        )
        self.assertIsNotNone(created.datetime)
        self.assertEqual(ret, created.id)

    def test_create_override(self):
        values_before = Value.objects.count()
        self._create('test', '123', 'cityhall')
        values_after = Value.objects.count()

        created_override = Value.objects.get(
            active=True,
            name='test',
            parent=self.auto_id,
            override='cityhall',
            author='cityhall',
            entry='123',
            protect=False,
            first_last=True
        )
        self.assertEqual(1+values_before, values_after)
        self.assertIsNotNone(created_override.datetime)

    def test_update(self):
        index = self._create('test', '')
        before = Value.objects.count()
        self.values.update('cityhall', index, '123')
        after = Value.objects.count()
        inactive = Value.objects.get(active=False, id=index)
        active = Value.objects.get(active=True, id=index)

        self.assertEqual(before+1, after)
        self.assertEqual('', inactive.entry)
        self.assertEqual('123', active.entry)
        self.assertIsNotNone(active.datetime)
        self.assertEqual(inactive.parent, active.parent)
        self.assertEqual(inactive.name, active.name)
        self.assertFalse(active.first_last)
        self.assertEqual(inactive.protect, active.protect)
        self.assertEqual(active.override, inactive.override)
        self.assertEqual('cityhall', active.author)

    def test_delete(self):
        index = self._create('test', '')
        before = Value.objects.count()
        self.values.delete('cityhall', index)
        after = Value.objects.count()

        entries = list(Value.objects.filter(id=index).order_by('entry_id'))
        created = entries[0]
        deleted = entries[1]

        self.assertEqual(before+1, after)
        self.assertEqual(2, len(entries))
        self.assertFalse(created.active)
        self.assertFalse(deleted.active)
        self.assertEqual(created.id, deleted.id)
        self.assertEqual(created.parent, deleted.parent)
        self.assertEqual(created.name, deleted.name)
        self.assertEqual(created.override, deleted.override)
        self.assertEqual(created.protect, deleted.protect)
        self.assertTrue(deleted.first_last)
        self.assertEqual('cityhall', deleted.author)
        self.assertIsNotNone(deleted.datetime)

    def test_set_protect(self):
        index = self._create('test', '')
        before = Value.objects.count()
        self.values.set_protect_status('cityhall', index, True)
        after = Value.objects.count()
        inactive = Value.objects.get(active=False, id=index)
        active = Value.objects.get(active=True, id=index)

        self.assertEqual(before+1, after)
        self.assertEqual(active.entry, inactive.entry)
        self.assertIsNotNone(active.datetime)
        self.assertEqual(inactive.parent, active.parent)
        self.assertEqual(inactive.name, active.name)
        self.assertFalse(active.first_last)
        self.assertTrue(active.protect)
        self.assertEqual(active.override, inactive.override)
        self.assertEqual('cityhall', active.author)

    def test_get_value(self):
        val1 = '123'
        index = self._create('test', val1)
        back = self.values.get_value(index)
        self.assertEqual(val1, back[0])
        self.assertFalse(back[1])

        val2 = 'def'
        self.values.update('cityhall', index, val2)
        back = self.values.get_value(index)
        self.assertEqual(val2, back[0])
        self.assertFalse(back[1])

        self.values.set_protect_status('cityhall', index, True)
        back = self.values.get_value(index)
        self.assertEqual(val2, back[0])
        self.assertTrue(back[1])

        invalid_index = self.values.get_value(1000000)
        self.assertIsNone(invalid_index[0])
        self.assertIsNone(invalid_index[1])

    def test_get_children_of(self):
        index = self._create('test', '123')

        children = self.values.get_children_of(self.auto_id)
        first = children[1]
        self.assertEqual(2, len(children))
        self.assertTrue(first['active'])
        self.assertEqual(index, first['id'])
        self.assertEqual('test', first['name'])
        self.assertEqual('', first['override'])
        self.assertEqual('cityhall', first['author'])
        self.assertIsNotNone(first['datetime'])
        self.assertEqual('123', first['value'])
        self.assertFalse(first['protect'])
        self.assertEqual(self.auto_id, first['parent'])

        index = self.values.create(
            'cityhall', self.auto_id, 'test', '456', 'test'
        )
        children = self.values.get_children_of(self.auto_id)
        children = [child for child in children if child['name'] == 'test']
        override = children[0] \
            if children[0]['override'] == 'test' else children[1]
        self.assertEqual(2, len(children))
        self.assertEqual(index, override['id'])
        self.assertEqual('456', override['value'])
        self.assertFalse(override['protect'])

        self.values.set_protect_status('cityhall', index, True)
        children = self.values.get_children_of(self.auto_id)
        children = [child for child in children if child['name'] == 'test']
        override = children[0] \
            if children[0]['override'] == 'test' else children[1]
        self.assertEqual(2, len(children))
        self.assertTrue(override['protect'])

        self.values.delete('cityhall', index)
        children = self.values.get_children_of(self.auto_id)
        children = [child for child in children if child['name'] == 'test']
        self.assertEqual(1, len(children))

    def test_get_value_for(self):
        self._create('test', '123')
        self._create('test', '456', 'cityhall')

        back = self.values.get_value_for(self.auto_id, 'test', '')
        self.assertEqual('123', back[0])
        self.assertFalse(back[1])

        back = self.values.get_value_for(self.auto_id, 'test', 'cityhall')
        self.assertEqual('456', back[0])
        self.assertFalse(back[1])

        back = self.values.get_value_for(self.auto_id, 'non existent', '')
        self.assertIsNone(back[0])
        self.assertIsNone(back[1])

    def test_get_child(self):
        self._create('test', '123')
        self._create('test', '456', 'cityhall')

        back = self.values.get_child(self.auto_id, 'test', '')
        self.assertEqual('', back['override'])
        self.assertEqual('123', back['value'])

        back = self.values.get_child(self.auto_id, 'test', 'cityhall')
        self.assertEqual('cityhall', back['override'])
        self.assertEqual('456', back['value'])

    def test_get_history(self):
        index = self._create('test', '123')
        history = self.values.get_history(index)

        self.assertEqual(1, len(history))
        self.assertEqual(history[0]['id'], index)
        self.assertEqual(history[0]['name'], 'test')
        self.assertEqual(history[0]['override'], '')
        self.assertEqual(history[0]['author'], 'cityhall')
        self.assertIsNotNone(history[0]['datetime'])
        self.assertEqual(history[0]['value'], '123')
        self.assertFalse(history[0]['protect'])
        self.assertEqual(history[0]['parent'], self.auto_id)
        self.assertTrue(history[0]['active'])

        self.values.set_protect_status(
            'cityhall', index, True
        )
        history = self.values.get_history(index)
        self.assertEqual(2, len(history))

        self.values.update('cityhall', index, '456')
        history = self.values.get_history(index)
        self.assertEqual(3, len(history))

        history = self.values.get_history(self.auto_id)
        self.assertEqual(3, len(history))
        self.assertEqual(history[2]['id'], index)

        self.values.delete('cityhall', index)
        history = self.values.get_history(index)
        self.assertEqual(4, len(history))
        history = self.values.get_history(self.auto_id)
        self.assertEqual(4, len(history))
