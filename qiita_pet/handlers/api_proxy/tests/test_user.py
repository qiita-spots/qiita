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
                 'name': 'Pick closed-reference OTUs'},
                {'id': 'b72369f9-a886-4193-8d3d-f7b504168e75',
                 'status': 'success',
                 'heartbeat': '2015-11-22 21:15:00',
                 'params': {
                    'max_barcode_errors': 1.5,
                    'sequence_max_n': 0,
                    'max_bad_run_length': 3,
                    'phred_offset': u'auto',
                    'rev_comp': False,
                    'phred_quality_threshold': 3,
                    'input_data': 1,
                    'rev_comp_barcode': False,
                    'rev_comp_mapping_barcodes': True,
                    'min_per_read_length_fraction': 0.75,
                    'barcode_type': u'golay_12'},
                 'name': 'Split libraries FASTQ'}]}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
