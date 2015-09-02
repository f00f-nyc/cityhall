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
from model_mommy import mommy
from functools import partial


class TestModelsGet(TestCase):
    def test_user_is_valid(self):
        mommy.make(User, active=True, name='test', password='')
        self.assertIsNone(User.objects.is_valid('test', 'abc'))
        self.assertTrue(User.objects.is_valid('test', ''))

    def test_value_by_id(self):
        mommy.make(Value, entry='inactive', active=False, id=1000)
        mommy.make(Value, entry='active', active=True, id=1000)
        self.assertEqual(Value.objects.by_id(1000).entry, 'active')

    def test_get_children(self):
        mommy.make(Value, entry='parent', active=True, id=1000)
        mommy.make(Value, name='child 1a', active=False, id=1001, parent=1000)
        mommy.make(Value, name='child 1b', active=True, id=1001, parent=1000)
        mommy.make(Value, name='child 2', active=True, id=1002, parent=1000)

        children = Value.objects.children_of(1000)
        names = set([val.name for val in children])
        self.assertEqual(2, len(children))
        self.assertEqual(set(['child 1b', 'child 2']), names)

    def test_get_child(self):
        make = partial(mommy.make, Value, override='')
        make(entry='parent', active=True, id=1000)
        make(name='child 1', active=False, id=1001, parent=1000)
        make(name='child 1', active=True, id=1001, parent=1000)
        make(name='child 2', active=True, id=1002, parent=1000)

        child = Value.objects.child(1000, 'child 1')
        self.assertIsNotNone(child)

    def test_value_save(self):
        val = Value()
        val.active = True
        val.author = 'test_user'
        val.first_last = True
        val.name = 'test value'
        val.entry = ''
        val.override = ''
        val.parent = 1
        val.protect = False
        val.save()

        self.assertEqual(val.pk, val.id)
        self.assertIsNotNone(val.datetime)
