from api.db.constants import DbFactory
from api.db.django.db import Db
from api.models import User, Value


class Factory(DbFactory):
    def __str__(self):
        return "cityhall.Factory (users: {}, active values: {})"\
            .format(
                User.objects.count(),
                Value.objects.filter(active=True).count(),
            )

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
