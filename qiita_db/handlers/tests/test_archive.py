# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, exists, isfile
from os import close, remove
from shutil import rmtree

from unittest import main, TestCase
from json import loads

from qiita_db.handlers.tests.oauthbase import OauthTestingBase


class APIArchiveObservationsTests(OauthTestingBase):
    def setUp(self):
        super(APIArchiveObservationsTests, self).setUp()

        self._clean_up_files = []

    def tearDown(self):
        super(APIArchiveObservationsTests, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isfile(fp):
                    remove(fp)
                else:
                    rmtree(fp)

    def test_post(self):
        obs = self.post('/qiita_db/archive/observations/', headers=self.header,
                        data={'job_id': 'a_job_id', 'features': ['AA', 'CA']})
        self.assertEqual(obs.code, 200)
        self.assertEqual(loads(obs.body), {'AA': [], 'CA': []})


if __name__ == '__main__':
    main()
