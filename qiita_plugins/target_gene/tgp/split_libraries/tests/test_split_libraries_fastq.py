# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os.path import isdir, exists, join
from os import remove, close
from shutil import rmtree
from tempfile import mkstemp, mkdtemp

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
            f.write(MAPPING_FILE_2)
        self._clean_up_files.append(fp)

        with self.assertRaises(ValueError):
            get_sample_names_by_run_prefix(fp)

    def test_generate_per_sample_fastq_command(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            f.write(MAPPING_FILE)
        self._clean_up_files.append(fp)
        forward_seqs = ["s1.fastq.gz", "s2.fastq.gz", "s3.fastq.gz"]
        reverse_seqs = ["s1_rev.fastq.gz", "s2_rev.fastq.gz",
                        "s3_rev.fastq.gz"]
        barcode_fps = []
        mapping_file = fp
        output_dir = "/output/dir"
        params_str = (
            "--max_bad_run_length 3 --min_per_read_length_fraction 0.75 "
            "--sequence_max_n 0 --phred_quality_threshold 3 "
            "--barcode_type golay_12 --max_barcode_errors 1.5 "
            "--rev_comp_mapping_barcodes")
        obs = generate_per_sample_fastq_command(
            forward_seqs, reverse_seqs, barcode_fps,
            mapping_file, output_dir, params_str)
        exp = ("split_libraries_fastq.py --store_demultiplexed_fastq -i "
               "s1.fastq.gz,s2.fastq.gz,s3.fastq.gz --sample_ids "
               "SKB8.640193,SKD8.640184,SKB7.640196 -o /output/dir "
               "--max_bad_run_length 3 --min_per_read_length_fraction 0.75 "
               "--sequence_max_n 0 --phred_quality_threshold 3 "
               "--barcode_type golay_12 --max_barcode_errors 1.5 "
               "--rev_comp_mapping_barcodes")
        self.assertEqual(obs, exp)

    def test_generate_per_sample_fastq_command_regex(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            f.write(MAPPING_FILE)
        self._clean_up_files.append(fp)
        forward_seqs = ["1_s1.fastq.gz", "1_s2.fastq.gz", "1_s3.fastq.gz"]
        reverse_seqs = ["1_s1_rev.fastq.gz", "1_s2_rev.fastq.gz",
                        "1_s3_rev.fastq.gz"]
        barcode_fps = []
        mapping_file = fp
        output_dir = "/output/dir"
        params_str = (
            "--max_bad_run_length 3 --min_per_read_length_fraction 0.75 "
            "--sequence_max_n 0 --phred_quality_threshold 3 "
            "--barcode_type golay_12 --max_barcode_errors 1.5 "
            "--rev_comp_mapping_barcodes")
        obs = generate_per_sample_fastq_command(
            forward_seqs, reverse_seqs, barcode_fps,
            mapping_file, output_dir, params_str)
        exp = ("split_libraries_fastq.py --store_demultiplexed_fastq -i "
               "1_s1.fastq.gz,1_s2.fastq.gz,1_s3.fastq.gz --sample_ids "
               "SKB8.640193,SKD8.640184,SKB7.640196 -o /output/dir "
               "--max_bad_run_length 3 --min_per_read_length_fraction 0.75 "
               "--sequence_max_n 0 --phred_quality_threshold 3 "
               "--barcode_type golay_12 --max_barcode_errors 1.5 "
               "--rev_comp_mapping_barcodes")
        self.assertEqual(obs, exp)

    def test_generate_per_sample_fastq_command_error_barcodes(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            f.write(MAPPING_FILE)
        self._clean_up_files.append(fp)
        forward_seqs = ["s1.fastq.gz", "s2.fastq.gz", "s3.fastq.gz"]
        reverse_seqs = ["s1_rev.fastq.gz", "s2_rev.fastq.gz",
                        "s3_rev.fastq.gz"]
        barcode_fps = ["s1_barcodes.fastq.gz", "s2_barcodes.fastq.gz",
                       "s3_barcodes.fastq.gz"]
        mapping_file = fp
        output_dir = "/output/dir"
        params_str = (
            "--max_bad_run_length 3 --min_per_read_length_fraction 0.75 "
            "--sequence_max_n 0 --phred_quality_threshold 3 "
            "--barcode_type golay_12 --max_barcode_errors 1.5 "
            "--rev_comp_mapping_barcodes")
        with self.assertRaises(ValueError):
            generate_per_sample_fastq_command(
                forward_seqs, reverse_seqs, barcode_fps,
                mapping_file, output_dir, params_str)

    def test_generate_per_sample_fastq_command_error_prefixes(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            f.write(MAPPING_FILE)
        self._clean_up_files.append(fp)
        forward_seqs = ["s1.fastq.gz", "s2.fastq.gz", "sX.fastq.gz"]
        reverse_seqs = ["s1_rev.fastq.gz", "s2_rev.fastq.gz",
                        "sX_rev.fastq.gz"]
        barcode_fps = []
        mapping_file = fp
        output_dir = "/output/dir"
        params_str = (
            "--max_bad_run_length 3 --min_per_read_length_fraction 0.75 "
            "--sequence_max_n 0 --phred_quality_threshold 3 "
            "--barcode_type golay_12 --max_barcode_errors 1.5 "
            "--rev_comp_mapping_barcodes")
        with self.assertRaises(ValueError):
            generate_per_sample_fastq_command(
                forward_seqs, reverse_seqs, barcode_fps,
                mapping_file, output_dir, params_str)

    def test_generate_split_libraries_fastq_cmd_per_sample_FASTQ(self):
        fps = [("s1.fastq.gz", "raw_forward_seqs"),
               ("s2.fastq.gz", "raw_forward_seqs"),
               ("s3.fastq.gz", "raw_forward_seqs"),
               ("s1_rev.fastq.gz", "raw_reverse_seqs"),
               ("s2_rev.fastq.gz", "raw_reverse_seqs"),
               ("s3_rev.fastq.gz", "raw_reverse_seqs")]
        fd, fp = mkstemp()
        with open(fp, 'w') as f:
            f.write(MAPPING_FILE)
        self._clean_up_files.append(fp)
        mapping_file = fp
        atype = "per_sample_FASTQ"
        out_dir = "/output/dir"
        parameters = {
            "max_bad_run_length": 3, "min_per_read_length_fraction": 0.75,
            "sequence_max_n": 0, "rev_comp_barcode": False,
            "rev_comp_mapping_barcodes": True, "rev_comp": False,
            "phred_quality_threshold": 3, "barcode_type": "golay_12",
            "max_barcode_errors": 1.5, "input_data": 1}
        obs_cmd, obs_outdir = generate_split_libraries_fastq_cmd(
            fps, mapping_file, atype, out_dir, parameters)
        exp_cmd = (
            "split_libraries_fastq.py --store_demultiplexed_fastq -i "
            "s1.fastq.gz,s2.fastq.gz,s3.fastq.gz --sample_ids "
            "SKB8.640193,SKD8.640184,SKB7.640196 -o /output/dir/sl_out "
            "--max_bad_run_length 3 --min_per_read_length_fraction 0.75 "
            "--sequence_max_n 0 --phred_quality_threshold 3 "
            "--barcode_type golay_12 --max_barcode_errors 1.5 "
            "--rev_comp_mapping_barcodes")
        self.assertEqual(obs_cmd, exp_cmd)
        self.assertEqual(obs_outdir, "/output/dir/sl_out")

    def test_generate_split_libraries_fastq_cmd(self):
        out_dir = mkdtemp()
        fps = [("s1.fastq.gz", "raw_forward_seqs"),
               ("s2.fastq.gz", "raw_forward_seqs"),
               ("s3.fastq.gz", "raw_forward_seqs"),
               ("s1_rev.fastq.gz", "raw_reverse_seqs"),
               ("s2_rev.fastq.gz", "raw_reverse_seqs"),
               ("s3_rev.fastq.gz", "raw_reverse_seqs"),
               ("s1_barcodes.fastq.gz", "raw_barcodes"),
               ("s2_barcodes.fastq.gz", "raw_barcodes"),
               ("s3_barcodes.fastq.gz", "raw_barcodes")]
        self._clean_up_files.append(out_dir)
        fd, fp = mkstemp()
        with open(fp, 'w') as f:
            f.write(MAPPING_FILE)
        self._clean_up_files.append(fp)
        mapping_file = fp
        atype = "FASTQ"
        parameters = {
            "max_bad_run_length": 3, "min_per_read_length_fraction": 0.75,
            "sequence_max_n": 0, "rev_comp_barcode": False,
            "rev_comp_mapping_barcodes": True, "rev_comp": False,
            "phred_quality_threshold": 3, "barcode_type": "golay_12",
            "max_barcode_errors": 1.5, "input_data": 1}
        obs_cmd, obs_outdir = generate_split_libraries_fastq_cmd(
            fps, mapping_file, atype, out_dir, parameters)
        exp_cmd = (
            "split_libraries_fastq.py --store_demultiplexed_fastq -i "
            "s1.fastq.gz,s2.fastq.gz,s3.fastq.gz -b "
            "s1_barcodes.fastq.gz,s2_barcodes.fastq.gz,s3_barcodes.fastq.gz "
            "-m {0}/mappings/s1_mapping_file.txt,"
            "{0}/mappings/s2_mapping_file.txt,"
            "{0}/mappings/s3_mapping_file.txt "
            "-o {0}/sl_out --max_bad_run_length 3 "
            "--min_per_read_length_fraction 0.75 --sequence_max_n 0 "
            "--phred_quality_threshold 3 --barcode_type golay_12 "
            "--max_barcode_errors 1.5 "
            "--rev_comp_mapping_barcodes".format(out_dir))
        self.assertEqual(obs_cmd, exp_cmd)
        self.assertEqual(obs_outdir, join(out_dir, "sl_out"))

    def test_generate_split_libraries_fastq_cmd_notimplementederror(self):
        fps = [("s1.fastq.gz", "raw_forward_seqs"),
               ("s2.fastq.gz", "raw_forward_seqs"),
               ("s3.fastq.gz", "raw_forward_seqs"),
               ("s1_rev.fastq.gz", "raw_reverse_seqs"),
               ("s2_rev.fastq.gz", "raw_reverse_seqs"),
               ("s3_rev.fastq.gz", "raw_reverse_seqs"),
               ("s1_barcodes.fastq.gz", "raw_barcodes"),
               ("s2_barcodes.fastq.gz", "raw_barcodes"),
               ("s3_barcodes.fastq.gz", "whopsies")]
        with self.assertRaises(NotImplementedError):
            generate_split_libraries_fastq_cmd(fps, "", "", "", {})

    def test_generate_split_libraries_fastq_cmd_valueerror(self):
        out_dir = "/output/dir"
        fps = [("s1.fastq.gz", "raw_forward_seqs"),
               ("s2.fastq.gz", "raw_forward_seqs"),
               ("s3.fastq.gz", "raw_forward_seqs"),
               ("s1_rev.fastq.gz", "raw_reverse_seqs"),
               ("s2_rev.fastq.gz", "raw_reverse_seqs"),
               ("s3_rev.fastq.gz", "raw_reverse_seqs"),
               ("s1_barcodes.fastq.gz", "raw_barcodes"),
               ("s3_barcodes.fastq.gz", "raw_barcodes")]
        mapping_file = "mapping_file.txt"
        atype = "FASTQ"
        parameters = {
            "max_bad_run_length": 3, "min_per_read_length_fraction": 0.75,
            "sequence_max_n": 0, "rev_comp_barcode": False,
            "rev_comp_mapping_barcodes": True, "rev_comp": False,
            "phred_quality_threshold": 3, "barcode_type": "golay_12",
            "max_barcode_errors": 1.5, "input_data": 1}
        with self.assertRaises(ValueError):
            generate_split_libraries_fastq_cmd(
                fps, mapping_file, atype, out_dir, parameters)

    def test_split_libraries_fastq(self):
        # This requires to run split libraries fastq so I don't think that we
        # want to run a test in here - at least, not until we split up the
        # plugin to its own project
        pass


MAPPING_FILE = (
    "#SampleID\tplatform\tbarcode\texperiment_design_description\t"
    "library_construction_protocol\tcenter_name\tprimer\trun_prefix\t"
    "instrument_model\tDescription\n"
    "SKB7.640196\tILLUMINA\tA\tA\tA\tANL\tA\ts3\tIllumina MiSeq\tdesc1\n"
    "SKB8.640193\tILLUMINA\tA\tA\tA\tANL\tA\ts1\tIllumina MiSeq\tdesc2\n"
    "SKD8.640184\tILLUMINA\tA\tA\tA\tANL\tA\ts2\tIllumina MiSeq\tdesc3\n"
)

MAPPING_FILE_2 = (
    "#SampleID\tplatform\tbarcode\texperiment_design_description\t"
    "library_construction_protocol\tcenter_name\tprimer\t"
    "run_prefix\tinstrument_model\tDescription\n"
    "SKB7.640196\tILLUMINA\tA\tA\tA\tANL\tA\ts3\tIllumina MiSeq\tdesc1\n"
    "SKB8.640193\tILLUMINA\tA\tA\tA\tANL\tA\ts1\tIllumina MiSeq\tdesc2\n"
    "SKD8.640184\tILLUMINA\tA\tA\tA\tANL\tA\ts1\tIllumina MiSeq\tdesc3\n"
)

if __name__ == '__main__':
    main()
