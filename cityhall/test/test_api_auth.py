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

from test.test_api import ApiTestCase
from django.conf import settings


class TestApiLogin(ApiTestCase):
    def test_login(self):
        result = self.client.post('/api/v1/auth/', {'username': 'cityhall', 'passhash': ''})
        self.check_result(result)
        content = self.result_to_dict(result)
        self.assertEqual(settings.API_VERSION, content['version'])

    def test_incomplete_login(self):
        result = self.client.post('/api/v1/auth/', {})
        self.check_failure(result)

    def test_incorrect_login(self):
        result = self.client.post('/api/v1/auth/', {'username': 'cityhall', 'passhash': 'incorrect'})
        self.check_failure(result)

    def test_logout(self):
        self.client.post('/api/v1/auth/', {'username': 'cityhall', 'passhash': ''})
        result = self.client.delete('/api/v1/auth/')
        self.check_result(result)

    def test_access_without_login(self):
        result = self.client.get('/api/v1/env/connect/')
        self.check_failure(result)


class TestApiAuthUsers(ApiTestCase):
    def setUp(self):
        self.client.post('/api/v1/auth/', {'username': 'cityhall', 'passhash': ''})

    def test_get_user(self):
        result = self.client.get('/api/v1/auth/user/cityhall/')
        self.check_result(result)

        content = self.result_to_dict(result)
        self.assertIn('Environments', content)
        self.assertIsInstance(content['Environments'], dict)

    def test_get_user_doesnt_exist(self):
        result = self.client.get('/api/v1/auth/user/doesntexist/')
        self.check_failure(result)

    def test_create_user(self):
        result = self.client.post('/api/v1/auth/user/new_user/', {'passhash': ''})
        self.check_result(result)

    def test_incomplete_create_user(self):
        result = self.client.post('/api/v1/auth/user/new_user/', {})
        self.check_failure(result)

    def test_update_password(self):
        result = self.client.put('/api/v1/auth/user/cityhall/', '{"passhash": ""}')
        self.check_result(result)

    def test_incomplete_update_password(self):
        result = self.client.put('/api/v1/auth/user/cityhall/', {})
        self.check_failure(result)

    def test_updating_another_user_password(self):
        self.client.post('/api/v1/auth/user/new_user/', {"passhash": ""})
        result = self.client.put('/api/v1/auth/user/new_user/', '{"passhash": ""}')
        self.check_failure(result)

    def test_delete_user(self):
        self.client.post('/api/v1/auth/user/new_user/', {"passhash": ""})
        result = self.client.delete('/api/v1/auth/user/new_user/')
        self.check_result(result)

    def test_delete_user_doesnt_exist(self):
        result = self.client.delete('/api/v1/auth/user/new_user/', '{"passhash": ""}')
        self.check_failure(result)


class TestApiAuthUserDefaultEnv(ApiTestCase):
    def setUp(self):
        self.client.post('/api/v1/auth/', {'username': 'cityhall', 'passhash': ''})

    def test_set_default_env(self):
        result = self.client.post('/api/v1/auth/user/cityhall/default/', {'env': 'auto'})
        self.check_result(result)

    def test_set_defeault_on_another_user(self):
        self.client.post('/api/v1/auth/user/new_user/', {"passhash": ""})
        result = self.client.post('/api/v1/auth/user/new_user/default/', {'env': 'auto'})
        self.check_failure(result)

    def test_incomplete_set_default_env(self):
        result = self.client.post('/api/v1/auth/user/cityhall/default/', {})
        self.check_failure(result)

    def test_get_default_env(self):
        result = self.client.get('/api/v1/auth/user/cityhall/default/')
        self.check_value(result)

        self.client.post('/api/v1/auth/user/cityhall/default/', {'env': 'auto'})
        result = self.client.get('/api/v1/auth/user/cityhall/default/')
        self.check_value(result, 'auto')


class TestApiAuthGrant(ApiTestCase):
    def setUp(self):
        self.client.post('/api/v1/auth/', {'username': 'cityhall', 'passhash': ''})

    def test_grant_permissions(self):
        self.client.post('/api/v1/auth/user/new_user/', {"passhash": ""})
        result = self.client.post('/api/v1/auth/grant/', {'env': 'auto', 'user': 'new_user', 'rights': '2'})
        self.check_result(result)

    def test_incomplete_grant_permissions(self):
        self.client.post('/api/v1/auth/user/new_user/', {"passhash": ""})

        result = self.client.post('/api/v1/auth/grant/', {'env': 'auto', 'user': 'new_user',})
        self.check_failure(result)
        result = self.client.post('/api/v1/auth/grant/', {'env': 'auto', 'rights': '2'})
        self.check_failure(result)
        result = self.client.post('/api/v1/auth/grant/', {'user': 'new_user', 'rights': '2'})
        self.check_failure(result)

    def test_invalid_grant_permissions(self):
        self.client.post('/api/v1/auth/user/new_user/', {"passhash": ""})

        result = self.client.post('/api/v1/auth/grant/', {'env': 'auto', 'user': 'invalid_user', 'rights': '1'})
        self.check_failure(result)

        result = self.client.post('/api/v1/auth/grant/', {'env': 'invalid_env', 'user': 'new_user', 'rights': '1'})
        self.check_failure(result)
