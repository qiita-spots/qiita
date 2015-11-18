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
import qiita_db as qdb


@qiita_test_checker()
class PreprocessedIlluminaParamsTests(TestCase):

    def test_exists(self):
        obs = qdb.parameters.PreprocessedIlluminaParams.exists(
            max_bad_run_length=3,
            min_per_read_length_fraction=0.75,
            sequence_max_n=0,
            rev_comp_barcode=False,
            rev_comp_mapping_barcodes=False,
            rev_comp=False,
            phred_quality_threshold=3,
            barcode_type="golay_12",
            max_barcode_errors=1.5)
        self.assertTrue(obs)

        obs = qdb.parameters.PreprocessedIlluminaParams.exists(
            max_bad_run_length=3,
            min_per_read_length_fraction=0.75,
            sequence_max_n=0,
            rev_comp_barcode=False,
            rev_comp_mapping_barcodes=False,
            rev_comp=False,
            phred_quality_threshold=3,
            barcode_type="hamming_8",
            max_barcode_errors=1.5)
        self.assertFalse(obs)

    def test_check_columns(self):
        # Check missing columns
        with self.assertRaises(ValueError):
            qdb.parameters.PreprocessedIlluminaParams._check_columns(
                barcode_type=8)

        # Check extra columns
        with self.assertRaises(ValueError):
            qdb.parameters.PreprocessedIlluminaParams._check_columns(
                max_bad_run_length=3,
                min_per_read_length_fraction=0.75,
                sequence_max_n=0,
                rev_comp_barcode=False,
                rev_comp_mapping_barcodes=False,
                rev_comp=False,
                phred_quality_threshold=3,
                barcode_type="hamming_8",
                max_barcode_errors=1.5,
                extra_columns="Foo")

        # Does not raise any error
        qdb.parameters.PreprocessedIlluminaParams._check_columns(
            max_bad_run_length=3,
            min_per_read_length_fraction=0.75,
            sequence_max_n=0,
            rev_comp_barcode=False,
            rev_comp_mapping_barcodes=False,
            rev_comp=False,
            phred_quality_threshold=3,
            barcode_type="hamming_8",
            max_barcode_errors=1.5)

    def test_create(self):
        obs_obj = qdb.parameters.PreprocessedIlluminaParams.create(
            "test_create",
            max_bad_run_length="3",
            min_per_read_length_fraction="0.75",
            sequence_max_n="0",
            rev_comp_barcode="False",
            rev_comp_mapping_barcodes="False",
            rev_comp="False",
            phred_quality_threshold="3",
            barcode_type="hamming_8",
            max_barcode_errors="1.5")

        obs = obs_obj.to_str()
        exp = ("--barcode_type hamming_8 --max_bad_run_length 3 "
               "--max_barcode_errors 1.5 --min_per_read_length_fraction 0.75 "
               "--phred_quality_threshold 3 --sequence_max_n 0")
        self.assertEqual(obs, exp)

    def test_create_duplicate(self):
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.parameters.PreprocessedIlluminaParams.create(
                "test_error",
                max_bad_run_length=3,
                min_per_read_length_fraction=0.75,
                sequence_max_n=0,
                rev_comp_barcode=False,
                rev_comp_mapping_barcodes=False,
                rev_comp=False,
                phred_quality_threshold=3,
                barcode_type="golay_12",
                max_barcode_errors=1.5)

    def test_to_str(self):
        params = qdb.parameters.PreprocessedIlluminaParams(1)
        obs = params.to_str()
        exp = ("--barcode_type golay_12 --max_bad_run_length 3 "
               "--max_barcode_errors 1.5 --min_per_read_length_fraction 0.75 "
               "--phred_quality_threshold 3 --sequence_max_n 0")
        self.assertEqual(obs, exp)

    def test_iter(self):
        obs = list(qdb.parameters.PreprocessedIlluminaParams.iter())
        exp = [qdb.parameters.PreprocessedIlluminaParams(1)]

        for o, e in zip(obs, exp):
            self.assertEqual(o.id, e.id)

    def test_name(self):
        obs = qdb.parameters.PreprocessedIlluminaParams(1).name
        self.assertEqual(obs, "Defaults")

    def test_values(self):
        obs = qdb.parameters.PreprocessedIlluminaParams(1).values
        exp = {'max_barcode_errors': 1.5, 'sequence_max_n': 0,
               'max_bad_run_length': 3, 'rev_comp': False,
               'phred_quality_threshold': 3, 'rev_comp_barcode': False,
               'rev_comp_mapping_barcodes': False,
               'min_per_read_length_fraction': 0.75,
               'barcode_type': 'golay_12'}
        self.assertEqual(obs, exp)


@qiita_test_checker()
class ProcessedSortmernaParamsTests(TestCase):
    def test_to_str(self):
        params = qdb.parameters.ProcessedSortmernaParams(1)
        obs = params.to_str()
        exp = ("--similarity 0.97 --sortmerna_coverage 0.97 "
               "--sortmerna_e_value 1.0 --sortmerna_max_pos 10000 --threads 1")
        self.assertEqual(obs, exp)

    def test_to_file(self):
        params = qdb.parameters.ProcessedSortmernaParams(1)
        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            params.to_file(f)
        with open(fp, 'U') as f:
            obs = f.read()

        self.assertEqual(obs, EXP_SMR_PARAMS_FILE)

EXP_SMR_PARAMS_FILE = """pick_otus:otu_picking_method\tsortmerna
pick_otus:similarity\t0.97
pick_otus:sortmerna_coverage\t0.97
pick_otus:sortmerna_e_value\t1.0
pick_otus:sortmerna_max_pos\t10000
pick_otus:threads\t1
"""

if __name__ == '__main__':
    main()
