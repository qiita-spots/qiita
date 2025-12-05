# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from tornado.escape import json_decode

import qiita_db
from qiita_pet.handlers.rest.study_samples import _sample_details
from qiita_pet.test.rest.test_base import RESTHandlerTestCase


class SupportTests(TestCase):
    def test_samples_detail(self):
        exp = [
            {
                "sample_id": "1.SKD7.640191",
                "sample_found": True,
                "ebi_sample_accession": "ERS000021",
                "preparation_id": 1,
                "ebi_experiment_accession": "ERX0000021",
                "preparation_visibility": "private",
                "preparation_type": "18S",
            },
            {
                "sample_id": "1.SKD7.640191",
                "sample_found": True,
                "ebi_sample_accession": "ERS000021",
                "preparation_id": 2,
                "ebi_experiment_accession": "ERX0000021",
                "preparation_visibility": "private",
                "preparation_type": "18S",
            },
            {
                "sample_id": "doesnotexist",
                "sample_found": False,
                "ebi_sample_accession": None,
                "preparation_id": None,
                "ebi_experiment_accession": None,
                "preparation_visibility": None,
                "preparation_type": None,
            },
        ]
        obs = _sample_details(
            qiita_db.study.Study(1), ["1.SKD7.640191", "doesnotexist"]
        )
        self.assertEqual(len(obs), len(exp))
        self.assertCountEqual(obs, exp)


class SampleDetailHandlerTests(RESTHandlerTestCase):
    def test_get_missing_sample(self):
        exp = [
            {
                "sample_id": "doesnotexist",
                "sample_found": False,
                "ebi_sample_accession": None,
                "preparation_id": None,
                "ebi_experiment_accession": None,
                "preparation_visibility": None,
                "preparation_type": None,
            },
        ]

        response = self.get(
            "/api/v1/study/1/sample/doesnotexist/status", headers=self.headers
        )
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_valid_sample(self):
        exp = [
            {
                "sample_id": "1.SKD7.640191",
                "sample_found": True,
                "ebi_sample_accession": "ERS000021",
                "preparation_id": 1,
                "ebi_experiment_accession": "ERX0000021",
                "preparation_visibility": "private",
                "preparation_type": "18S",
            },
            {
                "sample_id": "1.SKD7.640191",
                "sample_found": True,
                "ebi_sample_accession": "ERS000021",
                "preparation_id": 2,
                "ebi_experiment_accession": "ERX0000021",
                "preparation_visibility": "private",
                "preparation_type": "18S",
            },
        ]

        response = self.get(
            "/api/v1/study/1/sample/1.SKD7.640191/status", headers=self.headers
        )
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertCountEqual(obs, exp)

    def test_post_samples_status_bad_request(self):
        body = {"malformed": "with garbage"}
        response = self.post(
            "/api/v1/study/1/samples/status",
            headers=self.headers,
            data=body,
            asjson=True,
        )
        self.assertEqual(response.code, 400)

    def test_post_samples_status(self):
        exp = [
            {
                "sample_id": "1.SKD7.640191",
                "sample_found": True,
                "ebi_sample_accession": "ERS000021",
                "preparation_id": 1,
                "ebi_experiment_accession": "ERX0000021",
                "preparation_visibility": "private",
                "preparation_type": "18S",
            },
            {
                "sample_id": "1.SKD7.640191",
                "sample_found": True,
                "ebi_sample_accession": "ERS000021",
                "preparation_id": 2,
                "ebi_experiment_accession": "ERX0000021",
                "preparation_visibility": "private",
                "preparation_type": "18S",
            },
            {
                "sample_id": "doesnotexist",
                "sample_found": False,
                "ebi_sample_accession": None,
                "preparation_id": None,
                "ebi_experiment_accession": None,
                "preparation_visibility": None,
                "preparation_type": None,
            },
            {
                "sample_id": "1.SKM5.640177",
                "sample_found": True,
                "ebi_sample_accession": "ERS000005",
                "preparation_id": 1,
                "ebi_experiment_accession": "ERX0000005",
                "preparation_visibility": "private",
                "preparation_type": "18S",
            },
            {
                "sample_id": "1.SKM5.640177",
                "sample_found": True,
                "ebi_sample_accession": "ERS000005",
                "preparation_id": 2,
                "ebi_experiment_accession": "ERX0000005",
                "preparation_visibility": "private",
                "preparation_type": "18S",
            },
        ]

        body = {"sample_ids": ["1.SKD7.640191", "doesnotexist", "1.SKM5.640177"]}
        response = self.post(
            "/api/v1/study/1/samples/status",
            headers=self.headers,
            data=body,
            asjson=True,
        )
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertCountEqual(obs, exp)


if __name__ == "__main__":
    main()
