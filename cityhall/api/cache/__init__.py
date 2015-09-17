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

import collections


class CacheDict:
    def __init__(self, capacity):
        self.capacity = capacity
        self.values = collections.OrderedDict()

    def __contains__(self, item):
        return item in self.values

    def get(self, key, default):
        try:
            value = self.values.pop(key)
            self.values[key] = value
            return value
        except KeyError:
            if default:
                return default
            return None

    def set(self, key, value):
        try:
            self.values.pop(key)
        except KeyError:
            if len(self.values) >= self.capacity:
                self.values.popitem(last=False)
        self.values[key] = value

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __getitem__(self, item):
        return self.get(item, None)
