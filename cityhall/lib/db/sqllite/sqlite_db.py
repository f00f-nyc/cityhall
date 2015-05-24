from lib.db import db
from lib.db.db import DbState, Rights
from datetime import datetime


class CityHallDb(db.Db):
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        pass

    def is_open(self):
        pass

    def get_children_of(self, index):
        pass

    def create_env(self, user, env):
        pass

    def get_value(self, index):
        pass

    def get_rights(self, env, user):
        pass

    def get_env_root(self, env):
        pass

    def create_rights(self, author, env, user, rights):
        pass

    def authenticate(self, user, passhash, env):
        pass

    def create(self, user, env, parent, name, value, override=''):
        pass

    def update(self, user, index, value):
        pass

    def update_rights(self, author, env, user, rights):
        pass

    def create_default_tables(self):
        pass

    def create_user(self, author, user, passhash):
        pass