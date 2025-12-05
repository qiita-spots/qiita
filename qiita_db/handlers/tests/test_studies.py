# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads
from unittest import main

from qiita_db.handlers.tests.oauthbase import OauthTestingBase


class TestAPIStudiesListing(OauthTestingBase):
    def setUp(self):
        super(TestAPIStudiesListing, self).setUp()

    def test_get_studies_failure(self):
        obs = self.get("/qiita_db/studies/not-valid", headers=self.header)
        self.assertEqual(obs.code, 403)
        self.assertEqual(
            str(obs.error), "HTTP 403: You can only request public or private studies"
        )

    def test_get_studies_private(self):
        obs = self.get("/qiita_db/studies/private", headers=self.header)
        exp = {"data": {"1": [4, 5, 6, 7]}}
        self.assertEqual(loads(obs.body), exp)

    def test_get_studies_public(self):
        obs = self.get("/qiita_db/studies/public", headers=self.header)
        exp = {"data": {}}
        self.assertEqual(loads(obs.body), exp)


if __name__ == "__main__":
    main()
