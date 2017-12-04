# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from os.path import exists, isdir
from os import remove
from shutil import rmtree

from qiita_core.util import qiita_test_checker
import qiita_db as qdb
from qiita_pet.handlers.api_proxy.user import (user_jobs_get_req)


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
        obs = user_jobs_get_req(qdb.user.User('shared@foo.bar'))
        exp = {
            'status': 'success',
            'message': '',
            'jobs': [
                {'id': 'd19f76ee-274e-4c1b-b3a2-a12d73507c55',
                 'status': 'error',
                 'heartbeat': '2015-11-22 21:30:00',
                 'params': {
                    'reference': 1,
                    'similarity': 0.97,
                    'sortmerna_e_value': 1,
                    'sortmerna_max_pos': 10000,
                    'input_data': 2,
                    'threads': 1,
                    'sortmerna_coverage': 0.97},
                 'name': 'Pick closed-reference OTUs',
                 'step': 'generating demux file',
                 'processing_job_workflow_id': 1}]}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
