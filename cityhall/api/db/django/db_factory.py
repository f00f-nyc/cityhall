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

from api.db import DbFactory
from api.db.django.db import Db
from api.models import User, Value


class Factory(DbFactory):
    def __str__(self):
        return "cityhall.Factory (users: {}, active values: {})"\
            .format(
                User.objects.count(),
                Value.objects.filter(active=True).count(),
            )

    def __init__(self, settings):
        super(Factory, self).__init__(settings)

    def open(self):
        pass

    def is_open(self):
        return True

    def get_db(self):
        return Db(self)

    def create_default_tables(self):
        return True

    def authenticate(self, user, passhash):
        user = User.objects.is_valid(user, passhash)

        if user:
            return user.user_root
