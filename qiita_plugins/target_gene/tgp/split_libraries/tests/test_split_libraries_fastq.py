# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os.path import isdir, exists
from os import remove, close
from shutil import rmtree
from tempfile import mkstemp

from tgp.split_libraries.split_libraries_fastq import (
    generate_parameters_string, get_sample_names_by_run_prefix,
    generate_per_sample_fastq_command, generate_split_libraries_fastq_cmd)


class SplitLibrariesFastqTests(TestCase):
    def setUp(self):
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_generate_parameters_string(self):
        parameters = {
            "max_bad_run_length": 3, "min_per_read_length_fraction": 0.75,
            "sequence_max_n": 0, "rev_comp_barcode": False,
            "rev_comp_mapping_barcodes": True, "rev_comp": False,
            "phred_quality_threshold": 3, "barcode_type": "golay_12",
            "max_barcode_errors": 1.5, "input_data": 1}

        obs = generate_parameters_string(parameters)
        exp = ("--max_bad_run_length 3 --min_per_read_length_fraction 0.75 "
               "--sequence_max_n 0 --phred_quality_threshold 3 "
               "--barcode_type golay_12 --max_barcode_errors 1.5 "
               "--rev_comp_mapping_barcodes")
        self.assertEqual(obs, exp)

    def test_get_sample_names_by_run_prefix(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            f.write(MAPPING_FILE)
        self._clean_up_files.append(fp)

        obs = get_sample_names_by_run_prefix(fp)
        exp = {'s3': 'SKB7.640196', 's2': 'SKD8.640184', 's1': 'SKB8.640193'}
        self.assertEqual(obs, exp)

    def test_get_sample_names_by_run_prefix_error(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            f.write(MAPPING_FILE_ERROR)
        self._clean_up_files.append(fp)

        with self.assertRaises(ValueError):
            get_sample_names_by_run_prefix(fp)

    def test_generate_per_sample_fastq_command(self):
        pass

    def test_generate_split_libraries_fastq_cmd(self):
        pass

    def test_split_libraries_fastq(self):
        pass


MAPPING_FILE = (
    "#SampleID\tplatform\tbarcode\texperiment_design_description\t"
    "library_construction_protocol\tcenter_name\tprimer\trun_prefix\t"
    "instrument_model\tDescription\n"
    "SKB7.640196\tILLUMINA\tA\tA\tA\tANL\tA\ts3\tIllumina MiSeq\tdesc1\n"
    "SKB8.640193\tILLUMINA\tA\tA\tA\tANL\tA\ts1\tIllumina MiSeq\tdesc2\n"
    "SKD8.640184\tILLUMINA\tA\tA\tA\tANL\tA\ts2\tIllumina MiSeq\tdesc3\n"
)

MAPPING_FILE_ERROR = (
    "#SampleID\tplatform\tbarcode\texperiment_design_description\t"
    "library_construction_protocol\tcenter_name\tprimer\t"
    "run_prefix\tinstrument_model\tDescription\n"
    "SKB7.640196\tILLUMINA\tA\tA\tA\tANL\tA\ts3\tIllumina MiSeq\tdesc1\n"
    "SKB8.640193\tILLUMINA\tA\tA\tA\tANL\tA\ts1\tIllumina MiSeq\tdesc2\n"
    "SKD8.640184\tILLUMINA\tA\tA\tA\tANL\tA\ts1\tIllumina MiSeq\tdesc3\n"
)

if __name__ == '__main__':
    main()
