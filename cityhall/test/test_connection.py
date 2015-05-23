from django.test import TestCase
from lib.db.memory.cityhall_db import CityHallDb
from lib.db.connection import Connection


class TestConnection(TestCase):
    def __init__(self, obj):
        super(TestCase, self).__init__(obj)
        self.db = None
        self.conn = None

    def setUp(self):
        self.conn = Connection(CityHallDb())
        self.db = self.conn.db

    def test_create_env(self):
        self.conn.connect()
        self.conn.create_default_env()
        self.assertIsInstance(self.db.valsTable, list)
        self.assertIsInstance(self.db.authTable, list)

    def test_open_required(self):
        authenticate = self.conn.authenticate('cityhall', '')
        self.assertTrue(authenticate is None)

        self.conn.connect()
        self.conn.create_default_env()
        self.assertTrue(self.conn.authenticate('cityhall', ''))

    def test_get_env(self):
        self.conn.connect()
        self.assertTrue(self.conn.get_env('cityhall', '', 'auto') is None)
        self.conn.create_default_env()
        self.assertTrue(self.conn.get_env('cityhall', '', 'auto') is not None)

    def test_cannot_get_env_if_not_granted_rights(self):
        self.conn.connect()
        self.conn.create_default_env()

        self.db.create_user('cityhall', 'test', '')
        self.db.create_env('test', 'dev')

        self.assertTrue(self.conn.get_env('cityhall', '', 'dev') is None)
        self.assertTrue(self.conn.get_env('test', '', 'dev') is not None)

    def test_get_auth(self):
        self.conn.connect()
        self.conn.create_default_env()
        auth = self.conn.get_auth('cityhall', '')
        self.assertTrue(auth is not None)
