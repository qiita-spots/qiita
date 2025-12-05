# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads
from unittest import main

import pandas as pd
from mock import Mock

from qiita_db.metadata_template.sample_template import SampleTemplate as ST
from qiita_db.user import User
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.test.tornado_test_base import TestHandlerBase


class BaseAdminTests(TestHandlerBase):
    def setUp(self):
        super().setUp()
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))


class TestAdminProcessingJob(BaseAdminTests):
    def test_get(self):
        response = self.get("/admin/processing_jobs/")
        self.assertEqual(response.code, 200)
        self.assertIn("Available Commands", response.body.decode("ascii"))


class TestAJAXAdminProcessingJobListing(BaseAdminTests):
    def test_get(self):
        response = self.get("/admin/processing_jobs/list?sEcho=3&commandId=2")
        self.assertEqual(response.code, 200)

        exp = {"sEcho": "3", "recordsTotal": 0, "recordsFiltered": 0, "data": []}
        self.assertEqual(loads(response.body), exp)

    def test_get_missing_argument(self):
        response = self.get("/admin/processing_jobs/list?sEcho=1")
        self.assertEqual(response.code, 400)
        self.assertIn("Missing argument commandId", response.body.decode("ascii"))


class TestSampleValidation(BaseAdminTests):
    def test_get(self):
        response = self.get("/admin/sample_validation/")
        self.assertEqual(response.code, 200)

    def test_post(self):
        # Check success
        post_args = {"qid": 1, "snames": "SKB1.640202 SKB2.640194 BLANK.1A BLANK.1B"}
        response = self.post("/admin/sample_validation/", post_args)
        self.assertEqual(response.code, 200)
        snames = ["SKB1.640202", "SKB2.640194", "BLANK.1A", "BLANK.1B"]
        body = response.body.decode("ascii")
        for name in snames:
            self.assertIn(name, body)

        # Check success with tube_id
        md_dict = {"SKB1.640202": {"tube_id": "12345"}}
        md_ext = pd.DataFrame.from_dict(md_dict, orient="index", dtype=str)
        ST(1).extend(md_ext)
        post_args = {"qid": 1, "snames": "12345 SKB2.640194 BLANK.1A BLANK.1B"}
        response = self.post("/admin/sample_validation/", post_args)
        self.assertEqual(response.code, 200)
        snames = ["SKB2.640194", "SKB1.640202, tube_id: 12345"]
        body = response.body.decode("ascii")
        for name in snames:
            self.assertIn(name, body)

        # Check failure: invalid qiita id
        post_args = {"qid": 2, "snames": "SKB1.640202 SKB2.640194 BLANK.1A BLANK.1B"}
        response = self.post("/admin/sample_validation/", post_args)
        self.assertEqual(response.code, 200)
        self.assertIn("Study 2 does not exist", response.body.decode("ascii"))


if __name__ == "__main__":
    main()
