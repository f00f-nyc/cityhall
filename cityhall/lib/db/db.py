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

from abc import abstractmethod


class DbState(object):
    Closed = 0
    Open = 1
    Error = 2


class Rights(object):
    DontExist = -1
    NoRights = 0
    Read = 1
    ReadProtected = 2
    Write = 3
    Grant = 4
    Admin = 5


class DbFactory(object):
    """
    This class is the factory which will create light-weight Db classes which
    will be used to actually do the work of City Hall.
    """
    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def is_open(self):
        pass

    @abstractmethod
    def get_db(self):
        pass

    @abstractmethod
    def create_default_tables(self):
        pass

    @abstractmethod
    def authenticate(self, user, passhash, env=None):
        pass


class Db(object):
    """
    The class in this directory wil be expecting to pass around a object that
    implements these methods.  The idea is to take these and implement them
    for any database.

    To get a good idea of what the database should be doing behind the scenes,
    see lib/db/memory/cityhall_db.py and, for a slightly higher-level overview,
    see its corresponding tests: /test/tests_connection.py
    """
    @abstractmethod
    def create_env(self, user, env):
        pass

    @abstractmethod
    def get_children_of(self, index):
        pass

    @abstractmethod
    def update(self, user, index, value):
        pass

    @abstractmethod
    def create(self, user, env, parent, name, value, override=''):
        pass

    @abstractmethod
    def get_value(self, index):
        pass

    @abstractmethod
    def get_value_for(self, parent_index, name, override):
        pass

    @abstractmethod
    def get_rights(self, env, user):
        pass

    @abstractmethod
    def update_rights(self, author, env, user, rights):
        pass

    @abstractmethod
    def create_rights(self, author, env, user, rights):
        pass

    @abstractmethod
    def create_user(self, author, user, passhash):
        pass

    @abstractmethod
    def get_env_root(self, env):
        pass

    @abstractmethod
    def get_history(self, index):
        pass

    @abstractmethod
    def delete(self, author, index):
        pass

    @abstractmethod
    def set_protect_status(self, author, index, status):
        pass

    @abstractmethod
    def get_user(self, user):
        pass

    @abstractmethod
    def delete_user(self, author, user):
        pass

    @abstractmethod
    def get_users(self, env):
        pass
