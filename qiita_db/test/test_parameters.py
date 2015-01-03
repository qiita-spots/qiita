# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.parameters import PreprocessedIlluminaParams
from qiita_db.exceptions import QiitaDBDuplicateError


@qiita_test_checker()
class PreprocessedIlluminaParamsTests(TestCase):

    def test_exists(self):
        obs = PreprocessedIlluminaParams.exists(
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

        obs = PreprocessedIlluminaParams.exists(
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
            PreprocessedIlluminaParams._check_columns(barcode_type=8)

        # Check extra columns
        with self.assertRaises(ValueError):
            PreprocessedIlluminaParams._check_columns(
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
        PreprocessedIlluminaParams._check_columns(
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
        obs_obj = PreprocessedIlluminaParams.create(
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
        with self.assertRaises(QiitaDBDuplicateError):
            PreprocessedIlluminaParams.create(
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
        params = PreprocessedIlluminaParams(1)
        obs = params.to_str()
        exp = ("--barcode_type golay_12 --max_bad_run_length 3 "
               "--max_barcode_errors 1.5 --min_per_read_length_fraction 0.75 "
               "--phred_quality_threshold 3 --sequence_max_n 0")
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
