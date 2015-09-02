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


LOG_SQL = False


class SqliteFuncsMixin(object):
    def _first_row(self, sql, kwargs):
        if LOG_SQL:
            print "Running: {} with {}".format(sql, str(kwargs))
        for row in self.cursor.execute(sql, kwargs):
            if LOG_SQL:
                print "  +-> returning: {}".format(str(row))
            return row
        if LOG_SQL:
            print "  +-> sql didn't return any rows"
        return None

    def _first_value(self, sql, kwargs):
        row = self._first_row(sql, kwargs)
        if LOG_SQL:
            print "  +-> _first_row value: {}".format(
                row[0] if row else "None"
            )
        return row[0] if row else None
