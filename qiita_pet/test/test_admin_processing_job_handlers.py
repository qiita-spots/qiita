# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from json import loads

from mock import Mock

from qiita_db.user import User
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.test.tornado_test_base import TestHandlerBase


class BaseAdminTests(TestHandlerBase):
    def setUp(self):
        super().setUp()
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))


class TestAdminProcessingJob(BaseAdminTests):
    def test_get(self):
        response = self.get('/admin/processing_jobs/')
        self.assertEqual(response.code, 200)
        self.assertIn("Available Commands", response.body.decode('ascii'))


class TestAJAXAdminProcessingJobListing(BaseAdminTests):
    def test_get(self):
        response = self.get('/admin/processing_jobs/list?sEcho=3&commandId=1')
        self.assertEqual(response.code, 200)

        exp = {'sEcho': '3', 'recordsTotal': 0, 'recordsFiltered': 0,
               'data': []}
        self.assertEqual(loads(response.body), exp)

    def test_get_missing_argument(self):
        response = self.get('/admin/processing_jobs/list?sEcho=1')
        self.assertEqual(response.code, 400)
        self.assertIn("Missing argument commandId",
                      response.body.decode('ascii'))


class TestSampleValidation(BaseAdminTests):
    def test_get(self):
        response = self.get('/admin/sample_validation/')
        self.assertEqual(response.code, 200)

    def test_post(self):
        post_args = {
            'qid': 1,
            'snames': 'SKB1.640202 SKB2.640194 BLANK.1A BLANK.1B'
        }
        response = self.post('/admin/sample_validation/', post_args)
        self.assertEqual(response.code, 200)
        snames = ['SKB1.640202', 'SKB2.640194', 'BLANK.1A', 'BLANK.1B']
        body = response.body.decode('ascii')
        for name in snames:
            self.assertIn(name, body)

        post_args = {
            'qid': 2,
            'snames': 'SKB1.640202 SKB2.640194 BLANK.1A BLANK.1B'
        }
        response = self.post('/admin/sample_validation/', post_args)
        self.assertEqual(response.code, 500)


if __name__ == "__main__":
    main()
