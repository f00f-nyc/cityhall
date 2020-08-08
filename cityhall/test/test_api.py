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
from simplejson.decoder import JSONDecodeError
from django.test import TestCase, override_settings


@override_settings(DATABASE_TYPE='memory')
class ApiTestCase(TestCase):
    def post(self, *args, **kwargs):
        return self.client.post(*args, content_type="application/json", **kwargs)

    def put(self, *args, **kwargs):
        return self.client.put(*args, content_type="application/json", **kwargs)

    def result_to_dict(self, result):
        try:
            return json.loads(result.content)
        except JSONDecodeError as ex:
            self.assertTrue(False, f'Caught an error decoding "{result.content}": {ex.doc}')

    def check_result(self, result):
        self.assertEqual(200, result.status_code)
        self.assertGreater(len(result.content), 0)
        content = self.result_to_dict(result)
        self.assertIn('Response', content)
        self.assertEqual('Ok', content['Response'])

    def check_value(self, result, expected=None):
        self.check_result(result)

        content = self.result_to_dict(result)
        self.assertIn('value', content)

        if expected is not None:
            self.assertEqual(expected, content['value'])

    def check_failure(self, result):
        self.assertEqual(200, result.status_code)

        content = self.result_to_dict(result)
        self.assertIn('Response', content)
        self.assertEqual('Failure', content['Response'])


class TestApiInfo(ApiTestCase):
    def test_get(self):
        info = self.client.get('/api/v1/info/')
        self.assertEqual(200, info.status_code)
        result = json.loads(info.content)
        self.assertEqual(2, len(result))
        self.assertIn('Database', result)
        self.assertIn('Status', result)
        self.assertEqual('Alive', result['Status'])


class TestApiCreate(ApiTestCase):
    def test_get(self):

        before = self.client.get('/api/v1/env/auto/')
        self.client.get('/api/v1/create_default/')
        after = self.client.get('/api/v1/env/auto/')

        before_dict = self.result_to_dict(before)
        self.assertEqual('Failure', before_dict['Response'])
        self.assertEqual(
            'Session is not authenticated, and could not obtain get a guest credentials',
            before_dict['Message'],
        )
        self.check_value(after, '')
