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


class TestApiEnv(ApiTestCase):
    def setUp(self):
        self.client.post('/api/v1/auth/', {'username': 'cityhall', 'passhash': ''})

    def test_get_value(self):
        result = self.client.get('/api/v1/env/auto/')
        self.check_value(result)

    def test_get_for_env_that_doesnt_exist(self):
        result = self.client.get('/api/v1/env/environment/doesnt/exist/')
        self.check_failure(result)

    def test_set_value(self):
        result = self.client.post('/api/v1/env/auto/value/', {'value': 'some_value'})
        self.check_result(result)

        check_result = self.client.get('/api/v1/env/auto/value')
        check_dict = self.result_to_dict(check_result)
        self.assertEqual('some_value', check_dict['value'])

    def test_set_protect(self):
        result = self.client.post('/api/v1/env/auto/value/', {'protect': 'true'})
        self.check_result(result)

        check_result = self.client.get('/api/v1/env/auto/value')
        check_dict = self.result_to_dict(check_result)
        self.assertEqual(True, check_dict['protect'])

    def test_set_protect_and_value(self):
        result = self.client.post('/api/v1/env/auto/value/', {'protect': 'true', 'value': 'some_value'})
        self.check_result(result)

        check_result = self.client.get('/api/v1/env/auto/value/')
        check_dict = self.result_to_dict(check_result)
        self.assertEqual('some_value', check_dict['value'])
        self.assertEqual(True, check_dict['protect'])

    def test_set_value_override(self):
        result = self.client.post('/api/v1/env/auto/value/?override=cityhall', {'value': 'some_value'})
        self.check_result(result)

        result = self.client.get('/api/v1/env/auto/value/?override=cityhall')
        self.check_value(result, 'some_value')

    def test_get_value_doesnt_exist(self):
        result = self.client.get('/api/v1/env/auto/value/doesnt/exist')
        self.check_result(result)

        check_dict = self.result_to_dict(result)
        self.assertIn('value', check_dict)
        self.assertIsNone(check_dict['value'])

    def test_get_value_no_permissions(self):
        self.client.post('/api/v1/env/auto/value', {'value': 'some_value'})
        self.client.post('/api/v1/auth/user/new_user/', {'passhash': ''})
        self.client.delete('/api/v1/auth/')
        self.client.post('/api/v1/auth/', {'username': 'new_user', 'passhash': ''})
        result = self.client.get('/api/v1/env/auto/value')
        self.check_failure(result)

    def test_delete_value(self):
        self.client.post('/api/v1/env/auto/value', {'value': 'some_value'})
        result = self.client.delete('/api/v1/env/auto/value')
        self.check_result(result)

        result = self.client.get('/api/v1/env/auto/value')
        result_dict = self.result_to_dict(result)
        self.assertIsNone(result_dict['value'])

    def test_delete_value_override(self):
        self.client.post('/api/v1/env/auto/value?override=cityhall', {'value': 'some_value'})
        result = self.client.delete('/api/v1/env/auto/value/?override=cityhall')
        self.check_result(result)

    def test_get_history(self):
        result = self.client.get('/api/v1/env/auto/?viewhistory=true')
        self.check_result(result)

        result_dict = self.result_to_dict(result)
        self.assertIn('History', result_dict)
        self.assertLess(0, len(result_dict['History']))

    def test_children(self):
        self.client.post('/api/v1/env/auto/value/?override=cityhall', {'value': 'some_value'})
        result = self.client.get('/api/v1/env/auto/?viewchildren=true')
        self.check_result(result)

        result_dict = self.result_to_dict(result)
        children = [(c['name'], c['override']) for c in result_dict['children']]
        self.assertIn(('value', 'cityhall'), children)
