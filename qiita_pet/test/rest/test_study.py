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


class StudyHandlerTests(TestHandlerBase):
    def setUp(self):
        self.client_token = 'SOMEAUTHTESTINGTOKENHERE2122'
        r_client.hset(self.client_token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.client_token, 'client_id', 'test123123123')
        r_client.hset(self.client_token, 'grant_type', 'client')
        r_client.expire(self.client_token, 5)

        self.headers = {'Authorization': 'Bearer ' + self.client_token}
        super(StudyHandlerTests, self).setUp()

    def test_get_valid(self):
        exp = {u'title': u'Identification of the Microbiomes for Cannabis Soils',
               u'contacts': {'principal-investigator': [u'PIDude',
                                                        u'PI_dude@foo.bar'],
                             'lab-person': [u'LabDude', u'lab_dude@foo.bar']},
               u'abstract': (u'This is a preliminary study to examine the '
                              'microbiota associated with the Cannabis plant. '
                              'Soils samples from the bulk soil, soil '
                              'associated with the roots, and the rhizosphere '
                              'were extracted and the DNA sequenced. Roots '
                              'from three independent plants of different '
                              'strains were examined. These roots were '
                              'obtained November 11, 2011 from plants that '
                              'had been harvested in the summer. Future '
                              'studies will attempt to analyze the soils and '
                              'rhizospheres from the same location at '
                              'different time points in the plant lifecycle.')}

        response = self.get('/api/v1/study/1', headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_invalid(self):
        response = self.get('/api/v1/study/0', headers=self.headers)
        self.assertEqual(response.code, 404)
        self.assertEqual(json_decode(response.body),
                         {'message': 'Study not found'})

    def test_get_invalid_negative(self):
        response = self.get('/api/v1/study/-1', headers=self.headers)
        self.assertEqual(response.code, 404)
        # not asserting the body content as this is not a valid URI according
        # to the regex associating the handler to the webserver

    def test_get_invalid_namespace(self):
        response = self.get('/api/v1/study/1.11111', headers=self.headers)
        self.assertEqual(response.code, 404)
        # not asserting the body content as this is not a valid URI according


if __name__ == '__main__':
    main()
