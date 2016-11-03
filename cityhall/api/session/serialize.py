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

import simplejson as json
from api.db.auth import Auth
from api.db.env import Env
from api.views import CONN


def serialize_env(env):
    env_dict = {
        'env': env.env,
        'permissions': env.permissions,
        'name': env.name,
        'root_id': env.root_id,
        'cache': {name: value for name, value in env.cache.values.iteritems()}
    }
    return json.dumps(env_dict)


def deserialize_env(env_json):
    env_dict = json.loads(env_json)
    ret = Env(
        db=CONN.db_connection.get_db(),
        env=env_dict['env'],
        permissions=env_dict['permissions'],
        name=env_dict['name'],
        root_id=env_dict['root_id']
    )

    for k, v in env_dict['cache'].iteritems():
        ret.cache[k] = v

    return ret


def serialize_auth(auth):
    auth_dict = {
        'name': auth.name,
        'user_root': auth.user_root,
        'users_env': auth.users_env,
        'roots_cache': {
            name: serialize_env(value)
            for name, value in auth.roots_cache.values.iteritems()
        }
    }
    return json.dumps(auth_dict)


def deserialize_auth(auth_json):
    auth_dict = json.loads(auth_json)
    ret = Auth(
        db=CONN.db_connection.get_db(),
        name=auth_dict['name'],
        user_root=auth_dict['user_root']
    )
    ret.users_env = auth_dict['users_env']
    for name, value in auth_dict['roots_cache'].iteritems():
        ret.roots_cache[name] = deserialize_env(value)
    return ret