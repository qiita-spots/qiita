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
        self.fail('The return content needs to be expanded')

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

    def test_post_malformed_study(self):
        response = self.post('/api/v1/study', data={'foo': 'bar'})
        self.assertEqual(response.code, 400)

    def test_post_already_exists(self):
        response = self.post('/api/v1/study',
                             data={u'title': (u'Identification of the '
                                               'Microbiomes for Cannabis '
                                               'Soils')})
        self.assertEqual(response.code, 409)

    def test_post_valid(self):
        payload = {'title': 'foo',
                   'study_abstract': 'stuff',
                   'study_description': 'asdasd',
                   'efo': [1],
                   'owner': 'admin@foo.bar',
                   'study_alias': 'blah',
                   'contacts': {'principal_investigator': [u'PIDude',
                                                           u'PI_dude@foo.bar'],
                                'lab_person': [u'LabDude',
                                               u'lab_dude@foo.bar']}}
        response = self.post('/api/v1/study', data=payload)
        self.assertEqual(response.code, 201)
        study_id = json_decode(response.body)
        study = Study(int(study_id))

        self.assertEqual(study.info['title'], payload['title'])
        self.assertEqual(study.info['study_abstract'],
                         payload['study_abstract'])
        self.assertEqual(study.info['study_description'],
                         payload['study_description'])
        self.assertEqual(study.info['study_alias'], payload['study_alias'])
        self.assertEqual(study.efo, payload['efo'])
        self.assertEqual(study.owner.email, payload['owner'])
        self.assertEqual(study.info['principal_investigator'].name,
                         payload['contacts']['principal_investigator'][0])
        self.assertEqual(study.info['principal_investigator'].email,
                         payload['contacts']['principal_investigator'][1])
        self.assertEqual(study.info['lab_person'].name,
                         payload['contacts']['lab_person'][0])
        self.assertEqual(study.info['lab_person'].email,
                         payload['contacts']['lab_person'][1])

    def test_post_invalid_user(self):
        payload = {'title': 'foo',
                   'study_abstract': 'stuff',
                   'study_description': 'asdasd',
                   'study_alias': 'asd',
                   'efo': [1],
                   'user': 'does-not-exist@foo.bar',
                   'contacts': {'principal-investigator': [u'PIDude',
                                                           u'PI_dude@foo.bar'],
                                'lab-person': [u'LabDude',
                                               u'lab_dude@foo.bar']}}
        response = self.post('/api/v1/study', data=payload)
        self.assertEqual(response.code, 403)
        obs = json_decode(response.body)
        self.assertEqual(obs, {'message': 'Unknown user'})

if __name__ == '__main__':
    main()
