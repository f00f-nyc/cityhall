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
from api.db import Connection, Rights
from api.db.memory.db_factory import CityHallDbFactory


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
        self.auth = self.conn.get_auth('cityhall', '')
        self.env = self.auth.get_env('auto')

    def test_can_get_env(self):
        self.assertTrue(self.env is not None)

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
        self.assertEqual(Rights.DontExist, rights)

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
        self.assertEqual(0, len(environments))

        self.auth.grant('add', 'test', Rights.Read)
        environments = self.auth.get_user('test')
        self.assertEqual(1, len(environments))
        self.assertIn('add', environments)

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
        self.auth.grant('auto', 'test', Rights.Read)
        self.assertTrue(self.auth.delete_user('test'))
        self.assertFalse(self.auth.delete_user('test'))

    def test_grant_response_insufficient_privileges(self):
        self.auth.create_user('grants', '')
        self.auth.create_user('user1', '')

        grant_auth = self.conn.get_auth('grants', '')
        resp = grant_auth.grant('auto', 'user1', Rights.Read)
        self.assertEqual(resp[0], "Failure")
        self.assertEqual(
            resp[1], "Insufficient rights to grant to environment 'auto'"
        )

    def test_grant_response_noop(self):
        self.auth.create_user('grants', '')
        self.auth.create_user('user1', '')
        self.auth.grant('auto', 'grants', Rights.Grant)
        self.auth.grant('auto', 'user1', Rights.Read)

        grant_auth = self.conn.get_auth('grants', '')
        resp = grant_auth.grant('auto', 'user1', Rights.Read)
        self.assertEqual(resp[0], "Ok")
        self.assertEqual(
            resp[1], "Rights for 'user1' already at set level"
        )

    def test_grant_response_created(self):
        self.auth.create_user('grants', '')
        self.auth.create_user('user1', '')

        grant_auth = self.conn.get_auth('grants', '')
        grant_auth.create_env('test')
        resp = grant_auth.grant('test', 'user1', Rights.Read)
        self.assertEqual(resp[0], "Ok")
        self.assertEqual(
            resp[1], "Rights for 'user1' created"
        )

    def test_grant_response_updated(self):
        self.auth.create_user('grants', '')
        self.auth.create_user('user1', '')

        grant_auth = self.conn.get_auth('grants', '')
        grant_auth.create_env('test')
        grant_auth.grant('test', 'user1', Rights.Write)
        resp = grant_auth.grant('test', 'user1', Rights.Read)
        self.assertEqual(resp[0], "Ok")
        self.assertEqual(
            resp[1], "Rights for 'user1' updated"
        )

    def test_update_user(self):
        self.auth.create_user('test', '123')

        test_auth_before = self.conn.get_auth('test', '123')
        self.auth.update_user('test', 'abc')
        test_auth_after_wrong_pass = self.conn.get_auth('test', '123')
        test_auth_after_correct_pass = self.conn.get_auth('test', 'abc')

        self.assertIsNotNone(test_auth_before)
        self.assertIsNone(test_auth_after_wrong_pass)
        self.assertIsNotNone(test_auth_after_correct_pass)

    def test_set_get_default_env(self):
        """
        This is a back door entry to the auto environment, so that a user
        can still set a default environment without getting read/write
        permissions to 'auto'.
        """
        self.auth.create_env('dev')
        self.env.set('/connect', '')
        self.auth.create_user('test', '123')
        test_auth = self.conn.get_auth('test', '123')

        env = test_auth.get_default_env()
        self.assertEqual(None, env)

        test_auth.set_default_env('dev')
        env = test_auth.get_default_env()
        self.assertEqual('dev', env)

        self.assertEqual(
            ('dev', False),
            self.env.get_explicit('/connect/test')
        )

    def test_get_default_env_doesnt_honor_overrides(self):
        self.auth.create_env('dev')
        self.env.set('/connect', '')
        self.auth.create_user('test', '123')
        test_auth = self.conn.get_auth('test', '123')
        test_auth.set_default_env('dev')

        self.env.set('/connect/test', 'some other val', 'test')
        self.assertEqual('dev', test_auth.get_default_env())
