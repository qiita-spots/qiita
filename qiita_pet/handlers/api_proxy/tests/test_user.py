# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from os import remove
from os.path import exists, isdir
from shutil import rmtree
from unittest import TestCase, main

import qiita_db as qdb
from qiita_core.util import qiita_test_checker
from qiita_pet.handlers.api_proxy.user import user_jobs_get_req


@qiita_test_checker()
class TestSUserAPI(TestCase):
    def setUp(self):
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_user_jobs_get_req(self):
        obs = user_jobs_get_req(qdb.user.User("shared@foo.bar"))
        exp = {"status": "success", "message": "", "jobs": []}
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    main()
