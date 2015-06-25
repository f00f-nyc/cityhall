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


