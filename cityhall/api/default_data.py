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


def load_default_data(apps, schema_editor):
    # We can't import the models directly as they may be a newer
    # version than this migration expects. We use the historical version.
    usermodel = apps.get_model("api", "User")
    valuemodel = apps.get_model("api", "Value")

    auto_env = valuemodel()
    auto_env.active = True
    auto_env.id = 1
    auto_env.parent = -1
    auto_env.name = 'auto'
    auto_env.override = ''
    auto_env.author = 'cityhall'
    auto_env.entry = ''
    auto_env.protect = False
    auto_env.first_last = True
    auto_env.save()

    users_env = valuemodel()
    users_env.active = True
    users_env.id = 2
    users_env.parent = -1
    users_env.name = 'users'
    users_env.override = ''
    users_env.author = 'cityhall'
    users_env.entry = ''
    users_env.protect = False
    users_env.first_last = True
    users_env.save()

    cityhall_user = valuemodel()
    cityhall_user.active = True
    cityhall_user.id = 3
    cityhall_user.parent = 2
    cityhall_user.name = 'cityhall'
    cityhall_user.override = ''
    cityhall_user.author = 'cityhall'
    cityhall_user.entry = ''
    cityhall_user.protect = False
    cityhall_user.first_last = True
    cityhall_user.save()

    cityhall_auto_rights = valuemodel()
    cityhall_auto_rights.active = True
    cityhall_auto_rights.id = 4
    cityhall_auto_rights.parent = 3
    cityhall_auto_rights.name = 'auto'
    cityhall_auto_rights.override = ''
    cityhall_auto_rights.author = 'cityhall'
    cityhall_auto_rights.entry = '4'
    cityhall_auto_rights.protect = False
    cityhall_auto_rights.first_last = True
    cityhall_auto_rights.save()

    cityhall_users_rights = valuemodel()
    cityhall_users_rights.active = True
    cityhall_users_rights.id = 5
    cityhall_users_rights.parent = 3
    cityhall_users_rights.name = 'users'
    cityhall_users_rights.override = ''
    cityhall_users_rights.author = 'cityhall'
    cityhall_users_rights.entry = '4'
    cityhall_users_rights.protect = False
    cityhall_users_rights.first_last = True
    cityhall_users_rights.save()

    cityhall = usermodel()
    cityhall.active = True
    cityhall.user_root = cityhall_user.id
    cityhall.author = 'cityhall'
    cityhall.name = 'cityhall'
    cityhall.password = ''
    cityhall.save()
