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
from lib.db.connection import Connection
from lib.db.db import Rights


class TestAuthentication(TestCase):
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
        self.env = self.conn.get_env('cityhall', '', 'auto')
        self.auth = self.conn.get_auth('cityhall', '')

    def test_can_get_env(self):
        env = self.auth.get_env('auto')
        self.assertTrue(env is not None)

    def test_create_env(self):
        env = self.auth.create_env('dev')
        self.assertTrue(env is not None)

    def test_create_env_returns_false_if_env_exists(self):
        self.auth.create_env('dev')
        create = self.auth.create_env('dev')
        self.assertIsInstance(create, bool)
        self.assertFalse(create)

    def test_create_user(self):
        self.auth.create_user('test', '')
        test_auth = self.conn.get_auth('test', '')
        self.assertTrue(test_auth is not None)

    def test_get_permissions(self):
        self.auth.create_user('test', '')
        self.auth.create_env('dev')
        test_auth = self.conn.get_auth('test', '')
        rights = test_auth.get_permissions('dev')
        self.assertEqual(Rights.DontExist, rights)

    def test_grant_permissions(self):
        self.auth.create_user('test', '')
        self.auth.create_env('dev')
        test_auth = self.conn.get_auth('test', '')

        self.auth.grant('dev', 'test', Rights.Write)
        rights = test_auth.get_permissions('dev')
        self.assertEqual(Rights.Write, rights)

    def test_grant_permissions_is_noop_without_proper_level(self):
        self.auth.create_user('test', '')
        test_auth = self.conn.get_auth('test', '')
        test_auth.grant('auto', 'test', Rights.Write)
        rights = test_auth.get_permissions('auto')
        self.assertEqual(Rights.NoRights, rights)

    def test_get_users(self):
        users = self.auth.get_users('auto')
        before = len(users)

        self.auth.create_user('test', '')
        self.auth.grant('auto', 'test', Rights.ReadProtected)
        users = self.auth.get_users('auto')
        after = len(users)

        self.assertEqual(before+1, after)
        self.assertIn('test', users)
        self.assertEqual(users['test'], Rights.ReadProtected)

    def test_get_user(self):
        self.auth.create_env('add')
        self.auth.create_user('test', '')

        environments = self.auth.get_user('test')
        self.assertEqual(1, len(environments))
        self.assertIn('auto', environments)
        self.assertEqual(Rights.NoRights, environments['auto'])

        self.auth.grant('add', 'test', Rights.Read)
        environments = self.auth.get_user('test')
        self.assertEqual(2, len(environments))

    def test_delete_user(self):
        """
        A user can only be deleted if the author has Grant permissions on
        all environments of that user, or that user has Admin rights on auto
        """
        self.auth.create_user('test1', '')
        self.auth.create_user('test2', '')
        self.auth.grant('auto', 'test2', Rights.Grant)

        test1_auth = self.conn.get_auth('test1', '')
        test1_auth.create_env('test1_env')
        test2_auth = self.conn.get_auth('test2', '')
        test2_auth.create_env('test2_env')

        self.assertFalse(test2_auth.delete_user('test1'))
        test1_auth.grant('test1_env', 'test2', Rights.Grant)
        self.assertTrue(test2_auth.delete_user('test1'))

        self.assertFalse(self.db.authenticate('test1', ''))
        self.assertTrue(self.auth.delete_user('test2'))

    def test_cannot_delete_user_twice(self):
        self.auth.create_user('test', '')
        self.assertTrue(self.auth.delete_user('test'))
        self.assertFalse(self.auth.delete_user('test'))
