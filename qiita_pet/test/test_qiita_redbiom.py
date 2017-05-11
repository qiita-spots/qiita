# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

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
        exp = {'status': 'success', 'message': '', 'data': OBSERVATION}
        self.assertEqual(loads(response.body), exp)

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

    def test_post_observations(self):
        post_args = {
            'search': '4479944',
            'search_on': 'observations'
        }
        response = self.post('/redbiom/', post_args)
        exp = {'status': 'success', 'message': '', 'data': SEQUENCE}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'search': 'TT',
            'search_on': 'observations'
        }
        response = self.post('/redbiom/', post_args)
        exp = {'status': 'success',
               'message': 'No samples where found! Try again ...', 'data': []}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

    def test_post_categories(self):
        post_args = {
            'search': 'texture',
            'search_on': 'categories'
        }
        response = self.post('/redbiom/', post_args)
        exp = {'status': 'success', 'message': '', 'data': CATEGORIES}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'search': 'longtext',
            'search_on': 'categories'
        }
        response = self.post('/redbiom/', post_args)
        exp = {'status': 'success',
               'message': 'No samples where found! Try again ...', 'data': []}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'search': '4353076',
            'search_on': 'categories'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success',
               'message': ('Not a valid search: "4353076", are you sure this '
                           'is a valid metadata category?'), 'data': []}
        self.assertEqual(loads(response.body), exp)

    def test_post_errors(self):
        post_args = {
            'search_on': 'metadata'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success', 'message': "Nothing to search for ...",
               'data': []}
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'search': 'infant',
            'search_on': 'error'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success',
               'message': 'Not a valid option for search_on', 'data': []}
        self.assertEqual(loads(response.body), exp)


OBSERVATION = [
    {'artifact_id': 4, 'study_id': 1, 'version': '1.9.1',
     'command': 'Pick closed-reference OTUs', 'samples': [
        '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198', '1.SKD4.640185',
        '1.SKD5.640186', '1.SKD6.640190', '1.SKD7.640191', '1.SKD8.640184',
        '1.SKD9.640182'],
     'study_title': 'Identification of the Microbiomes for Cannabis Soils',
     'aname': 'BIOM', 'software': 'QIIME'},
    {'artifact_id': 5, 'study_id': 1, 'version': '1.9.1',
     'command': 'Pick closed-reference OTUs', 'samples': [
        '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198', '1.SKD4.640185',
        '1.SKD5.640186', '1.SKD6.640190', '1.SKD7.640191', '1.SKD8.640184',
        '1.SKD9.640182'],
     'study_title': 'Identification of the Microbiomes for Cannabis Soils',
     'aname': 'BIOM', 'software': 'QIIME'},
    {'artifact_id': 6, 'study_id': 1, 'version': u'1.9.1',
     'command': 'Pick closed-reference OTUs', 'samples': [
        '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198', '1.SKD4.640185',
        '1.SKD5.640186', '1.SKD6.640190', '1.SKD7.640191', '1.SKD8.640184',
        '1.SKD9.640182'],
     'study_title': 'Identification of the Microbiomes for Cannabis Soils',
     'aname': 'BIOM', 'software': 'QIIME'}]

SEQUENCE = [
    {'artifact_id': 4, 'study_id': 1, 'version': '1.9.1',
     'command': 'Pick closed-reference OTUs', 'samples': ['1.SKM3.640197'],
     'study_title': 'Identification of the Microbiomes for Cannabis Soils',
     'aname': 'BIOM', 'software': 'QIIME'},
    {'artifact_id': 5, 'study_id': 1, 'version': '1.9.1',
     'command': 'Pick closed-reference OTUs', 'samples': ['1.SKM3.640197'],
     'study_title': 'Identification of the Microbiomes for Cannabis Soils',
     'aname': 'BIOM', 'software': 'QIIME'},
    {'artifact_id': 6, 'study_id': 1, 'version': u'1.9.1',
     'command': 'Pick closed-reference OTUs', 'samples': ['1.SKM3.640197'],
     'study_title': 'Identification of the Microbiomes for Cannabis Soils',
     'aname': 'BIOM', 'software': 'QIIME'}]

CATEGORIES = [
    {'artifact_id': None, 'study_id': 1, 'version': None,
     'command': 'texture', 'samples': ['texture'],
     'study_title': 'Identification of the Microbiomes for Cannabis Soils',
     'aname': None, u'software': None}]

if __name__ == "__main__":
    main()
