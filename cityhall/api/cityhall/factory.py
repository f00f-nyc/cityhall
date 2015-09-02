from lib.db.db import DbFactory
from api.cityhall.db import Db
from api.models import User


class Factory(DbFactory):
    def open(self):
        pass

    def is_open(self):
        return True

    def get_db(self):
        return Db()

    def create_default_tables(self):
        return True

    def authenticate(self, user, passhash):
        user = User.objects.is_valid(user, passhash)

        if user:
            return user.user_root
