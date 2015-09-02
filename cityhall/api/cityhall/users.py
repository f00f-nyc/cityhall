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

from copy import copy
from django.db import transaction
from api.models import User
from django.db import models


class EnvUsers(models.Model):
    name = models.TextField(max_length=64)
    entry = models.TextField(max_length=2048)


class Users(object):
    def get_users(self, env):
        ret = EnvUsers.objects.raw(
            'SELECT u.id, u.name, v.entry '
            'FROM api_user u, api_value v '
            'WHERE u.user_root = v.parent '
            '      and u.active = %s '
            '      and v.active = %s '
            '      and v.name = %s ',
            [True, True, env]
        )

        return {u.name: u.entry for u in ret}

    def create_user(self, author, user, passhash, user_root):
        u = User()
        u.author = author
        u.user_root = user_root
        u.active = True
        u.name = user
        u.password = passhash
        u.save()

    @transaction.atomic
    def delete_user(self, author, user):
        existing = User.objects.get(active=True, name=user)
        existing.active = False
        existing.save()

        new_value = copy(existing)
        new_value.pk = None
        new_value.author = author
        new_value.save()
