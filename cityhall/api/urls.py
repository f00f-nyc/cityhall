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

from django.conf.urls import patterns, url
from api.views import (Info, Create)
from api.views.auth import (
    Authenticate, Environments, Users, GrantRights, UserDefaultEnv
)
from api.views.env import EnvView

urlpatterns = patterns(
    "",
    url(r"^info/$", Info.as_view(), name="info_home"),
    url(r"^create_default/$", Create.as_view(), name="create_def"),

    url(r"^auth/$", Authenticate.as_view(), name="authenticate"),
    url(
        r"^auth/env/(?P<env>[0-9a-zA-Z\-_.$]+)/$",
        Environments.as_view(),
        name="create_env"
    ),
    url(
        r"^auth/user/(?P<user>[0-9a-zA-Z\-_.$]+)/default/$",
        UserDefaultEnv.as_view(),
        name="user_default_env"
    ),
    url(
        r"^auth/user/(?P<user>[0-9a-zA-Z\-_.$]+)/$",
        Users.as_view(),
        name="view_user"
    ),
    url(r"^auth/grant/$", GrantRights.as_view(), name="grant_rights"),

    url(
        r"^env/(?P<env_path>.*)$",
        EnvView.as_view(),
        name="values"
    ),
)
