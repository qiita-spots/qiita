# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from datetime import datetime

from tornado.escape import json_decode
from moi import r_client

from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_pet.test.tornado_test_base import TestHandlerBase


class StudySamplesHandlerTests(TestHandlerBase):
    def setUp(self):
        self.client_token = 'SOMEAUTHTESTINGTOKENHERE2122'
        r_client.hset(self.client_token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.client_token, 'client_id', 'test123123123')
        r_client.hset(self.client_token, 'grant_type', 'client')
        r_client.expire(self.client_token, 5)

        self.headers = {'Authorization': 'Bearer ' + self.client_token}
        super(StudySamplesHandlerTests, self).setUp()

    def test_get_valid(self):
        exp = sorted(['1.SKB2.640194', '1.SKM4.640180', '1.SKB3.640195',
                      '1.SKB6.640176', '1.SKD6.640190', '1.SKM6.640187',
                      '1.SKD9.640182', '1.SKM8.640201', '1.SKM2.640199',
                      '1.SKD2.640178', '1.SKB7.640196', '1.SKD4.640185',
                      '1.SKB8.640193', '1.SKM3.640197', '1.SKD5.640186',
                      '1.SKB1.640202', '1.SKM1.640183', '1.SKD1.640179',
                      '1.SKD3.640198', '1.SKB5.640181', '1.SKB4.640189',
                      '1.SKB9.640200', '1.SKM9.640192', '1.SKD8.640184',
                      '1.SKM5.640177', '1.SKM7.640188', '1.SKD7.640191'])
        response = self.get('/api/v1/study/1/samples', headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(sorted(obs), exp)

    def test_get_invalid_no_study(self):
        exp = {'message': 'Study not found'}
        response = self.get('/api/v1/study/0/samples', headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_study_no_samples(self):
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": StudyPerson(3),
            'first_contact': datetime(2015, 5, 19, 16, 10),
            'most_recent_contact': datetime(2015, 5, 19, 16, 11),
        }

        new_study = Study.create(User('test@foo.bar'),
                                 "Some New Study for test", [1],
                                 info)

        exp = []
        response = self.get('/api/v1/study/%d/samples' % new_study.id,
                            headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)


class StudySamplesInfoHandlerTests(TestHandlerBase):
    def setUp(self):
        self.client_token = 'SOMEAUTHTESTINGTOKENHERE2122'
        r_client.hset(self.client_token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.client_token, 'client_id', 'test123123123')
        r_client.hset(self.client_token, 'grant_type', 'client')
        r_client.expire(self.client_token, 5)

        self.headers = {'Authorization': 'Bearer ' + self.client_token}
        super(StudySamplesInfoHandlerTests, self).setUp()

    def test_get_valid(self):
        exp = {'number-of-samples': 27,
               'categories': ['season_environment',
                              'assigned_from_geo', 'texture', 'taxon_id',
                              'depth', 'host_taxid', 'common_name',
                              'water_content_soil', 'elevation', 'temp',
                              'tot_nitro', 'samp_salinity', 'altitude',
                              'env_biome', 'country', 'ph', 'anonymized_name',
                              'tot_org_carb', 'description_duplicate',
                              'env_feature', 'physical_specimen_location',
                              'physical_specimen_remaining', 'dna_extracted',
                              'sample_type', 'collection_timestamp',
                              'host_subject_id', 'description',
                              'latitude', 'longitude', 'scientific_name']}
        response = self.get('/api/v1/study/1/samples/info',
                            headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs.keys(), exp.keys())
        self.assertEqual(obs['number-of-samples'], exp['number-of-samples'])
        self.assertItemsEqual(obs['categories'], exp['categories'])

    def test_get_study_does_not_exist(self):
        exp = {'message': 'Study not found'}
        response = self.get('/api/v1/study/0/samples/info',
                            headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_no_samples(self):
        # /api/v1/study/%d/samples/info -> {'number-of-samples':<int>,
                                        #   'categories': [<str>]}
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": StudyPerson(3),
            'first_contact': datetime(2015, 5, 19, 16, 10),
            'most_recent_contact': datetime(2015, 5, 19, 16, 11),
        }

        new_study = Study.create(User('test@foo.bar'),
                                 "Some New Study for test", [1],
                                 info)
        exp = {'number-of-samples': 0, 'categories': []}
        response = self.get('/api/v1/study/%d/samples/info' % new_study.id,
                            headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)


class StudySamplesCategoriesHandlerTests(TestHandlerBase):
    def setUp(self):
        self.client_token = 'SOMEAUTHTESTINGTOKENHERE2122'
        r_client.hset(self.client_token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.client_token, 'client_id', 'test123123123')
        r_client.hset(self.client_token, 'grant_type', 'client')
        r_client.expire(self.client_token, 5)

        self.headers = {'Authorization': 'Bearer ' + self.client_token}
        super(StudySamplesCategoriesHandlerTests, self).setUp()

    def test_get_valid_two_arg(self):
        df = Study(1).sample_template.to_dataframe()
        df = df[['ph','country']]
        df = {idx: [row['ph'], row['country']]
               for idx, row in df.iterrows()}
        exp = {'header': ['ph', 'country'],
               'samples': df}

        response = self.get('/api/v1/study/1/samples/categories=ph,country',
                            headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_valid_one_arg(self):
        df = Study(1).sample_template.to_dataframe()
        df = df[['ph','country']]
        df = {idx: [row['country']]
               for idx, row in df.iterrows()}
        exp = {'header': ['country'],
               'samples': df}

        response = self.get('/api/v1/study/1/samples/categories=country',
                            headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_valid_two_arg_one_bad(self):
        exp = {'message': 'Category not found'}
        response = self.get('/api/v1/study/1/samples/categories=country,foo',
                            headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_study_does_not_exist(self):
        exp = {'message': 'Study not found'}
        response = self.get('/api/v1/study/0/samples/categories=foo',
                            headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_bad_category(self):
        exp = {'message': 'Category not found'}
        response = self.get('/api/v1/study/1/samples/categories=foo',
                            headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_no_category(self):
        exp = {'message': 'No categories specified'}
        response = self.get('/api/v1/study/1/samples/categories=',
                            headers=self.headers)
        self.assertEqual(response.code, 405)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_no_samples(self):
        # /api/v1/study/%d/samples/info -> {'number-of-samples':<int>,
                                        #   'categories': [<str>]}
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": StudyPerson(3),
            'first_contact': datetime(2015, 5, 19, 16, 10),
            'most_recent_contact': datetime(2015, 5, 19, 16, 11),
        }

        new_study = Study.create(User('test@foo.bar'),
                                 "Some New Study for test", [1],
                                 info)

        exp = {'message': 'Category not found'}
        response = self.get('/api/v1/study/%d/samples/categories=foo' % new_study.id,
                            headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
