# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import main

from tornado.escape import json_decode

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
        self.assertEqual(response.body.decode('ascii'), exp)


class TestStudyTags(OauthTestingBase):
    def test_get(self):
        response = self.get('/study/tags/1')
        exp = ('{"status": "success", "message": "", "tags": []}')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body.decode('ascii'), exp)

        # test error
        response = self.get('/study/tags/bla')
        self.assertEqual(response.code, 400)


class TestStudy(OauthTestingBase):
    def test_patch_tags(self):
        arguments = {'op': 'replace', 'path': '/tags',
                     'value': ['testA', 'testB']}
        obs = self.patch('/study/1', headers=self.header,
                         data=arguments, asjson=True)

        self.assertEqual(obs.code, 200)
        self.assertEqual(obs.body.decode('ascii'),
                         '{"status": "success", "message": ""}')

        # checking the tags were added
        response = self.get('/study/tags/1')
        exp = ({"status": "success", "message": "",
                "tags": ['testA', 'testB']})
        self.assertEqual(response.code, 200)
        self.assertEqual(json_decode(response.body), exp)

    def test_patch_tags_not_found(self):
        arguments = {'op': 'replace', 'path': '/tags',
                     'value': ['testA', 'testB']}
        obs = self.patch('/study/100000000000', headers=self.header,
                         data=arguments, asjson=True)
        self.assertEqual(json_decode(obs.body), {'status': 'error', 'message':
                         'Study does not exist'})
        self.assertEqual(obs.code, 200)

    def test_patch_not_allowed(self):
        arguments = {'op': 'replace', 'path': '/tags',
                     'value': ['testA', 'testB']}
        obs = self.patch('/study/b', headers=self.header,
                         data=arguments, asjson=True)
        self.assertEqual(obs.code, 405)

    def test_patch_specimen_id_column(self):
        data = {'op': 'replace', 'path': '/specimen_id_column',
                'value': "anonymized_name"}
        obs = self.patch('/study/1', headers=self.header,
                         data=data, asjson=True)
        self.assertEqual(obs.code, 200)
        self.assertEqual(json_decode(obs.body), {"status": "success",
                         "message": "Successfully updated specimen id column"})


if __name__ == "__main__":
    main()
