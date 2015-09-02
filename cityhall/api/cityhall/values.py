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

from django.db import transaction
from django.db.models import Q
from copy import copy
from api.models import Value


class Values(object):
    def get_value(self, index):
        ret = Value.objects.by_id(index)
        if ret:
            return ret.entry, ret.protect
        return None, None

    @transaction.atomic
    def update(self, author, index, value):
        existing = Value.objects.by_id(index)
        existing.first_last = False
        new_value = copy(existing)

        existing.active = False
        existing.save()

        new_value.pk = None
        new_value.author = author
        new_value.entry = value
        new_value.datetime = None
        new_value.save()

    def get_children_of(self, index):
        return [
            {
                'active': True,
                'id': child.id,
                'name': child.name,
                'override': child.override or '',
                'author': child.author,
                'datetime': child.datetime,
                'value': child.entry,
                'protect': child.protect,
                'parent': index,
            }
            for child in Value.objects.children_of(index)
        ]

    def get_value_for(self, parent_index, name, override):
        ret = None
        protect = None

        try:
            vals = Value.objects.\
                filter(parent=parent_index, name=name, active=True).\
                filter(Q(override='') | Q(override=override))

            for item in vals:
                ret = item.entry
                protect = item.protect

                if item.override == override:
                    return ret, protect
        except Exception:
            pass
        return ret, protect

    @transaction.atomic
    def delete(self, author, index):
        existing = Value.objects.by_id(index)

        existing.active = False
        existing.save()

        new_value = copy(existing)
        new_value.pk = None
        new_value.datetime = None
        new_value.author = author
        new_value.first_last = True
        new_value.save()

    @transaction.atomic
    def set_protect_status(self, author, index, status):
        existing = Value.objects.by_id(index)
        new_value = copy(existing)

        existing.active = False
        existing.save()

        new_value.pk = None
        new_value.author = author
        new_value.protect = status
        new_value.datetime = None
        new_value.first_last = False
        new_value.save()

    def create(self, user, parent, name, value, override=''):
        create = Value()
        create.active = True
        create.parent = parent
        create.protect = False
        create.author = user
        create.name = name
        create.entry = value
        create.override = override
        create.first_last = True
        create.save()
        return create.id

    def get_history(self, index):
        history = Value.objects.filter(id=index) | \
            Value.objects.filter(Q(parent=index) & Q(first_last=True))

        return [
            {
                'id': child.id,
                'name': child.name,
                'override': child.override,
                'author': child.author,
                'datetime': child.datetime,
                'value': child.entry,
                'protect': child.protect,
                'parent': child.parent,
                'active': child.active
            }
            for child in history
        ]

    def get_child(self, parent, name, override=''):
        child = Value.objects.child(parent, name, override)

        if child:
            return {
                'active': True,
                'id': child.id,
                'name': child.name,
                'override': child.override or '',
                'author': child.author,
                'datetime': child.datetime,
                'value': child.entry,
                'protect': child.protect,
                'parent': parent,
            }
        return None
