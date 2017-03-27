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
from qiita_db.handlers.tests.oauthbase import OauthTestingBase


class StudyIndexHandlerTests(TestHandlerBase):
    def test_get_exists(self):
        response = self.get('/study/description/1')
        self.assertEqual(response.code, 200)

    def test_get_no_exists(self):
        response = self.get('/study/description/245')
        self.assertEqual(response.code, 404)


class StudyBaseInfoAJAX(TestHandlerBase):
    # TODO: Missing tests
    pass


class StudyDeleteAjaxTests(TestHandlerBase):
    def test_delete_study(self):
        response = self.post('/study/delete/', {'study_id': 1})
        self.assertEqual(response.code, 200)
        exp = {'status': 'error',
               'message': 'Unable to delete study: Study "Identification of '
                          'the Microbiomes for Cannabis Soils" cannot be '
                          'erased because it has a sample template'}
        self.assertEqual(loads(response.body), exp)


class DataTypesMenuAJAXTests(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/description/data_type_menu/',
                            {'study_id': '1'})
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.body, "")

    def test_get_no_exists(self):
        response = self.get('/study/description/data_type_menu/',
                            {'study_id': '245'})
        self.assertEqual(response.code, 404)


class StudyFilesAJAXTests(TestHandlerBase):
    def test_get(self):
        args = {'study_id': 1, 'artifact_type': 'FASTQ', 'prep_template_id': 1}
        response = self.get('/study/files/', args)
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.body, "")


class TestStudyGetTags(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/get_tags/')
        exp = ('{"status": "success", "message": "", "tags": '
               '{"admin": [], "user": []}}')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, exp)


class TestStudyTags(OauthTestingBase):
    def test_get(self):
        response = self.get('/study/tags/1')
        exp = ('{"status": "success", "message": "", "tags": []}')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, exp)

        # test error
        response = self.get('/study/tags/bla')
        self.assertEqual(response.code, 400)

    def test_patch(self):
        arguments = {'op': 'replace', 'path': '/tags',
                     'value[]': "['testA', 'testB']"}
        obs = self.patch('/study/tags/1', headers=self.header, data=arguments)

        self.assertEqual(obs.code, 200)
        self.assertEqual(obs.body, '{"status": "success", "message": ""}')
        # checking the tags were added
        response = self.get('/study/tags/1')
        exp = ('{"status": "success", "message": "", "tags": '
               '["[\'testA\', \'testB\']"]}')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, exp)

        arguments = {'op': 'replace', 'path': '/tags',
                     'value[]': "['testA', 'testB']"}
        obs = self.patch('/study/tags/b', headers=self.header, data=arguments)
        self.assertEqual(obs.code, 400)


if __name__ == "__main__":
    main()
