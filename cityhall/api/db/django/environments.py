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
from django.db.models import ObjectDoesNotExist
from api.models import Value


class Environments(object):
    @transaction.atomic
    def create_root(self, author, env):
        if self.get_env_root(env) < 0:
            root = Value()
            root.name = env
            root.active = True
            root.author = author
            root.first_last = True
            root.override = ''
            root.protect = False
            root.parent = -1
            root.save()
            return root.id
        return False

    def get_env_root(self, env):
        try:
            return Value.objects.get(active=True, parent=-1, name=env).id
        except ObjectDoesNotExist:
            return -1
