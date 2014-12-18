# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from tempfile import mkstemp
from os import close

from qiita_core.util import qiita_test_checker
from qiita_db.parameters import (PreprocessedIlluminaParams,
                                 ProcessedSortmernaParams)


@qiita_test_checker()
class PreprocessedIlluminaParamsTests(TestCase):

    def test_to_str(self):
        params = PreprocessedIlluminaParams(1)
        obs = params.to_str()
        exp = ("--barcode_type golay_12 --max_bad_run_length 3 "
               "--max_barcode_errors 1.5 --min_per_read_length_fraction 0.75 "
               "--phred_quality_threshold 3 --sequence_max_n 0")
        self.assertEqual(obs, exp)


@qiita_test_checker()
class ProcessedSortmernaParamsTests(TestCase):
    def test_to_str(self):
        params = ProcessedSortmernaParams(1)
        obs = params.to_str()
        exp = ("--coverage 0.97 --evalue 1.0 --max_pos 10000 "
               "--similarity 0.97 --threads 1")
        self.assertEqual(obs, exp)

    def test_to_file(self):
        params = ProcessedSortmernaParams(1)
        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            params.to_file(f)
        with open(fp, 'U') as f:
            obs = f.read()

        self.assertEqual(obs, EXP_SMR_PARAMS_FILE)

EXP_SMR_PARAMS_FILE = """pick_otus:max_pos\t10000
pick_otus:similarity\t0.97
pick_otus:evalue\t1.0
pick_otus:coverage\t0.97
pick_otus:threads\t1
"""

if __name__ == '__main__':
    main()
