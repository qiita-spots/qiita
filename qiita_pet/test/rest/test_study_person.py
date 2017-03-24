# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from tornado.escape import json_decode
from moi import r_client

from qiita_pet.test.tornado_test_base import TestHandlerBase


class StudyPersonHandlerTests(TestHandlerBase):
    def setUp(self):
        self.client_token = 'SOMEAUTHTESTINGTOKENHERE2122'
        r_client.hset(self.client_token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.client_token, 'client_id', 'test123123123')
        r_client.hset(self.client_token, 'grant_type', 'client')
        r_client.expire(self.client_token, 5)

        self.headers = {'Authorization': 'Bearer ' + self.client_token}
        super(StudyPersonHandlerTests, self).setUp()

    def test_exist(self):
        exp = {'email': 'lab_dude@foo.bar', 'phone': '121-222-3333',
               'address': '123 lab street', 'id': 1}
        response = self.get('/api/v1/person?name=LabDude&'
                            'affiliation=knight%20lab', headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_does_not_exist(self):
        exp = {'message': 'Person not found'}
        response = self.get('/api/v1/person?name=Boaty%20McBoatFace&'
                            'affiliation=UCSD', headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_does_not_exist_affiliation(self):
        exp = {'message': 'Person not found'}
        response = self.get('/api/v1/person?name=LabDude%20&affiliation=UCSD',
                            headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_invalid_query_string(self):
        response = self.get('/api/v1/person?name=LabDude', headers=self.headers)
        self.assertEqual(response.code, 400)

    def test_get_valid_extra_arguments(self):
        exp = {'email': 'lab_dude@foo.bar', 'phone': '121-222-3333',
               'address': '123 lab street', 'id': 1}
        response = self.get('/api/v1/person?name=LabDude&'
                            'affiliation=knight%20lab&foo=bar',
                            headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
