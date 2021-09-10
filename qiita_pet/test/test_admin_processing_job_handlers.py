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


if __name__ == "__main__":
    main()
