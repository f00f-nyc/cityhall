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
from api.db.memory.db_factory import CityHallDbFactory
from lib.db.connection import Connection


class TestConnection(TestCase):
    def __init__(self, obj):
        super(TestCase, self).__init__(obj)
        self.db_conn = None
        self.conn = None

    def setUp(self):
        self.conn = Connection(CityHallDbFactory())
        self.db_conn = self.conn.db_connection

    def test_create_env(self):
        self.conn.connect()
        self.conn.create_default_env()
        self.assertIsInstance(self.db_conn.valsTable, list)
        self.assertIsInstance(self.db_conn.authTable, list)

    def test_open_required(self):
        authenticate = self.conn.authenticate('cityhall', '')
        self.assertTrue(authenticate is None)

        self.conn.connect()
        self.conn.create_default_env()
        self.assertTrue(self.conn.authenticate('cityhall', ''))

    def test_get_auth(self):
        self.conn.connect()
        self.conn.create_default_env()
        auth = self.conn.get_auth('cityhall', '')
        self.assertTrue(auth is not None)
