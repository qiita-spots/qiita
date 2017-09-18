# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from copy import deepcopy
from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestRedbiom(TestHandlerBase):

    def test_get(self):
        response = self.get('/redbiom/')
        self.assertEqual(response.code, 200)

    def test_post_metadata(self):
        post_args = {
            'search': 'Diesel',
            'search_on': 'metadata'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)

        samples = ['1.SKD6.640190', '1.SKD9.640182', '1.SKD8.640184',
                   '1.SKD5.640186', '1.SKD2.640178', '1.SKD4.640185',
                   '1.SKD1.640179', '1.SKD3.640198', '1.SKD7.640191']
        exp_artifact_biom_ids = {
            '5': samples, '4': samples, '7': samples, '6': samples}
        response_body = loads(response.body)
        obs_artifact_biom_ids = response_body['data'][0].pop(
            'artifact_biom_ids')
        self.assertDictEqual(obs_artifact_biom_ids, exp_artifact_biom_ids)
        exp = {'status': 'success', 'message': '', 'data': DATA}
        self.assertEqual(response_body, exp)

        post_args = {
            'search': 'inf',
            'search_on': 'metadata'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success',
               'message': 'No samples where found! Try again ...', 'data': []}
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'search': '4353076',
            'search_on': 'metadata'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success',
               'message': ('Not a valid search: "4353076", are you sure this '
                           'is a valid metadata value?'), 'data': []}
        self.assertEqual(loads(response.body), exp)

    def test_post_features(self):
        post_args = {
            'search': '4479944',
            'search_on': 'feature'
        }
        response = self.post('/redbiom/', post_args)
        data = deepcopy(DATA)
        data[0]['artifact_biom_ids'] = {
            '5': ['1.SKM3.640197'], '4': ['1.SKM3.640197']}
        exp = {'status': 'success', 'message': '', 'data': data}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'search': 'TT',
            'search_on': 'feature'
        }
        response = self.post('/redbiom/', post_args)
        exp = {'status': 'success',
               'message': 'No samples where found! Try again ...', 'data': []}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

    def test_post_taxon(self):
        post_args = {
            'search': 'o__0319-7L14',
            'search_on': 'taxon'
        }
        data = deepcopy(DATA)
        data[0]['artifact_biom_ids'] = {
            '5': ['1.SKM3.640197'], '4': ['1.SKM3.640197']}
        response = self.post('/redbiom/', post_args)
        exp = {'status': 'success', 'message': '', 'data': data}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'search': 'o_0319-7L14',
            'search_on': 'taxon'
        }
        response = self.post('/redbiom/', post_args)
        exp = {'status': 'success',
               'message': 'No samples where found! Try again ...', 'data': []}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

    def test_post_errors(self):
        post_args = {
            'search_on': 'metadata'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 400)

        post_args = {
            'search': 'infant',
            'search_on': 'error'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success',
               'message': ('Incorrect search by: you can use metadata, '
                           'features or taxon and you passed: error'),
               'data': []}
        self.assertEqual(loads(response.body), exp)


DATA = [
    {'status': 'private',
     'study_title': 'Identification of the Microbiomes for Cannabis Soils',
     'metadata_complete': True, 'publication_pid': ['123456', '7891011'],
     'ebi_submission_status': 'submitted',
     'study_id': 1, 'ebi_study_accession': 'EBI123456-BB',
     'study_abstract': ('This is a preliminary study to examine the '
                        'microbiota associated with the Cannabis plant. Soils '
                        'samples from the bulk soil, soil associated with the '
                        'roots, and the rhizosphere were extracted and the '
                        'DNA sequenced. Roots from three independent plants '
                        'of different strains were examined. These roots were '
                        'obtained November 11, 2011 from plants that had been '
                        'harvested in the summer. Future studies will attempt '
                        'to analyze the soils and rhizospheres from the same '
                        'location at different time points in the plant '
                        'lifecycle.'),
     'pi': ['PI_dude@foo.bar', 'PIDude'],
     'publication_doi': ['10.100/123456', '10.100/7891011'],
     'study_alias': 'Cannabis Soils', 'number_samples_collected': 27}]


if __name__ == "__main__":
    main()
