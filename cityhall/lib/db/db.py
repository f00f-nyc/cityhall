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
    def get_value(self, parent_id, name, override):
        pass

    @abstractmethod
    def get_history(self, index):
        pass
