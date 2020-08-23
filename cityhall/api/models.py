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

from django.db import models, transaction


class ValueManager(models.Manager):
    def by_id(self, id):
        try:
            return self.get(active=True, id=id)
        except models.ObjectDoesNotExist:
            return None

    def children_of(self, id):
        try:
            return self.filter(active=True, parent=id)
        except models.ObjectDoesNotExist:
            return None

    def child(self, parent, child, override=''):
        try:
            return self.get(
                active=True,
                parent=parent,
                name=child,
                override=override
            )
        except models.ObjectDoesNotExist:
            return None


class Value(models.Model):
    entry_id = models.AutoField(primary_key=True)
    active = models.BooleanField()
    id = models.IntegerField()
    parent = models.IntegerField()
    name = models.TextField(max_length=128)
    override = models.TextField(max_length=64)
    author = models.TextField(max_length=64)
    datetime = models.DateTimeField(auto_now=True)
    entry = models.TextField(max_length=2048)
    protect = models.BooleanField()
    first_last = models.BooleanField()

    objects = ValueManager()

    class Meta:
        index_together = [
            ['active', 'id'],
            ['active', 'parent', 'id'],
            ['active', 'parent', 'name', 'override'],
        ]

    @transaction.atomic
    def save(self, *args, **kwargs):
        need_new_id = (self.id is None) or (self.id < 0)

        if need_new_id:
            self.datetime = None

        self.id = -1 if need_new_id else self.id
        self.override = self.override or ''

        super(Value, self).save(*args, **kwargs)

        if need_new_id:
            self.id = self.pk
            super(Value, self).save(*args, **kwargs)


class UserManager(models.Manager):
    def is_valid(self, user, password):
        try:
            return self.get(active=True, name=user, password=password)
        except models.ObjectDoesNotExist:
            return None

    def get_users_for_env(self, env):
        return self.raw(
            'SELECT u.id, u.name, v.entry '
            'FROM api_user u, api_value v '
            'WHERE u.user_root = v.parent '
            '      and u.active = %s '
            '      and v.active = %s '
            '      and v.name = %s ',
            [True, True, env]
        )


class User(models.Model):
    active = models.BooleanField()
    datetime = models.DateTimeField(auto_now=True)
    user_root = models.IntegerField()
    author = models.TextField(max_length=64)
    name = models.TextField(max_length=64)
    password = models.TextField(max_length=64)

    objects = UserManager()

    class Meta:
        index_together = [
            ['name', 'password', 'active'],
        ]
