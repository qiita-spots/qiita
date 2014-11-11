# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from unittest import TestCase, main
from tempfile import mkdtemp
from os.path import exists, join
from os import remove
from functools import partial
from shutil import rmtree

import pandas as pd

from qiita_core.util import qiita_test_checker
from qiita_db.util import get_db_files_base_dir
from qiita_db.data import RawData
from qiita_db.study import Study
from qiita_db.parameters import PreprocessedIlluminaParams
from qiita_db.metadata_template import PrepTemplate
from qiita_ware.processing_pipeline import (_get_preprocess_fastq_cmd,
                                            _insert_preprocessed_data_fastq,
                                            _generate_demux_file,
                                            _get_qiime_minimal_mapping)


@qiita_test_checker()
class ProcessingPipelineTests(TestCase):
    def setUp(self):
        self.db_dir = get_db_files_base_dir()
        self.files_to_remove = []
        self.dirs_to_remove = []

    def tearDown(self):
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)
        for dp in self.dirs_to_remove:
            if exists(dp):
                rmtree(dp)

    def test_get_qiime_minimal_mapping_single(self):
        prep_template = PrepTemplate(1)
        out_dir = mkdtemp()

        obs_fps = _get_qiime_minimal_mapping(prep_template, out_dir)
        exp_fps = [join(out_dir, 's_G1_L001_sequences_MMF.txt')]

        # Check that the returned list is as expected
        self.assertEqual(obs_fps, exp_fps)
        # Check that the file exists
        self.assertTrue(exists(exp_fps[0]))
        # Check the contents of the file
        with open(exp_fps[0], "U") as f:
            self.assertEqual(f.read(), EXP_PREP)

    def test_get_qiime_minimal_mapping_multiple(self):
        # We need to create a prep template in which we have different run
        # prefix values, so we can test this case
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 1',
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAA',
                            'experiment_design_description': 'BBB'},
            'SKD8.640184': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 2',
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'CGTAGAGCTCTC',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAA',
                            'experiment_design_description': 'BBB'},
            'SKB7.640196': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 3',
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'CCTCTGAGAGCT',
                            'run_prefix': "s_G1_L002_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAA',
                            'experiment_design_description': 'BBB'}
            }
        md_template = pd.DataFrame.from_dict(metadata_dict, orient='index')
        prep_template = PrepTemplate.create(md_template, RawData(2), Study(1),
                                            '16S')

        out_dir = mkdtemp()

        obs_fps = sorted(_get_qiime_minimal_mapping(prep_template, out_dir))
        exp_fps = sorted([join(out_dir, 's_G1_L001_sequences_MMF.txt'),
                          join(out_dir, 's_G1_L002_sequences_MMF.txt')])

        # Check that the returned list is as expected
        self.assertEqual(obs_fps, exp_fps)
        # Check that the file exists
        for fp in exp_fps:
            self.assertTrue(exists(fp))
        # Check the contents of the file
        for fp, contents in zip(exp_fps, [EXP_PREP_1, EXP_PREP_2]):
            with open(fp, "U") as f:
                self.assertEqual(f.read(), contents)

    def test_get_preprocess_fastq_cmd(self):
        raw_data = RawData(1)
        params = PreprocessedIlluminaParams(1)
        prep_template = PrepTemplate(1)
        obs_cmd, obs_output_dir = _get_preprocess_fastq_cmd(
            raw_data, prep_template, params)

        get_raw_path = partial(join, self.db_dir, 'raw_data')
        seqs_fp = get_raw_path('1_s_G1_L001_sequences.fastq.gz')
        bc_fp = get_raw_path('1_s_G1_L001_sequences_barcodes.fastq.gz')

        exp_cmd_1 = ("split_libraries_fastq.py --store_demultiplexed_fastq -i "
                     "{} -b {} "
                     "-m ".format(seqs_fp, bc_fp))
        exp_cmd_2 = ("-o {0} --barcode_type golay_12 --max_bad_run_length 3 "
                     "--max_barcode_errors 1.5 "
                     "--min_per_read_length_fraction 0.75 "
                     "--phred_quality_threshold 3 "
                     "--sequence_max_n 0".format(obs_output_dir))

        # We are splitting the command into two parts because there is no way
        # that we can know the filepath of the mapping file. We thus split the
        # command on the mapping file path and we check that the two parts
        # of the commands is correct
        obs_cmd_1 = obs_cmd[:len(exp_cmd_1)]
        obs_cmd_2 = obs_cmd[len(exp_cmd_1):].split(" ", 1)[1]

        self.assertEqual(obs_cmd_1, exp_cmd_1)
        self.assertEqual(obs_cmd_2, exp_cmd_2)

    def test_insert_preprocessed_data_fastq(self):
        study = Study(1)
        params = PreprocessedIlluminaParams(1)
        prep_template = PrepTemplate(1)
        prep_out_dir = mkdtemp()
        self.dirs_to_remove.append(prep_out_dir)
        path_builder = partial(join, prep_out_dir)
        db_path_builder = partial(join, join(self.db_dir, "preprocessed_data"))

        file_suffixes = ['seqs.fna', 'seqs.fastq', 'seqs.demux',
                         'split_library_log.txt']
        db_files = []
        for f_suff in file_suffixes:
            fp = path_builder(f_suff)
            with open(fp, 'w') as f:
                f.write("\n")
            self.files_to_remove.append(fp)
            db_files.append(db_path_builder("3_%s" % f_suff))
        self.files_to_remove.extend(db_files)

        _insert_preprocessed_data_fastq(study, params, prep_template,
                                        prep_out_dir)

        # Check that the files have been copied
        for fp in db_files:
            self.assertTrue(exists(fp))

        # Check that a new preprocessed data has been created
        self.assertTrue(self.conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.preprocessed_data WHERE "
            "preprocessed_data_id=%s)", (3, ))[0])

    def test_generate_demux_file(self):
        prep_out_dir = mkdtemp()
        with open(join(prep_out_dir, 'seqs.fastq'), "w") as f:
            f.write(DEMUX_SEQS)

        _generate_demux_file(prep_out_dir)

        self.assertTrue(exists(join(prep_out_dir, 'seqs.demux')))


DEMUX_SEQS = """@a_1 orig_bc=abc new_bc=abc bc_diffs=0
xyz
+
ABC
@b_1 orig_bc=abw new_bc=wbc bc_diffs=4
qwe
+
DFG
@b_2 orig_bc=abw new_bc=wbc bc_diffs=4
qwe
+
DEF
"""

EXP_PREP = (
    "#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tDescription\n"
    "1.SKB1.640202\tGTCCGCAAGTTA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKB2.640194\tCGTAGAGCTCTC\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKB3.640195\tCCTCTGAGAGCT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKB4.640189\tCCTCGATGCAGT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKB5.640181\tGCGGACTATTCA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKB6.640176\tCGTGCACAATTG\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKB7.640196\tCGGCCTAAGTTC\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKB8.640193\tAGCGCTCACATC\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKB9.640200\tTGGTTATGGCAC\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD1.640179\tCGAGGTTCTGAT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD2.640178\tAACTCCTGTGGA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD3.640198\tTAATGGTCGTAG\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD4.640185\tTTGCACCGTCGA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD5.640186\tTGCTACAGACGT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD6.640190\tATGGCCTGACTA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD7.640191\tACGCACATACAA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD8.640184\tTGAGTGGTCTGT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD9.640182\tGATAGCACTCGT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKM1.640183\tTAGCGCGAACTT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKM2.640199\tCATACACGCACC\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKM3.640197\tACCTCAGTCAAG\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKM4.640180\tTCGACCAAACAC\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKM5.640177\tCCACCCAGTAAC\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKM6.640187\tATATCGCGATGA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKM7.640188\tCGCCGGTAATCT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKM8.640201\tCCGATGCCTTGA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKM9.640192\tAGCAGGCACGAA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n")

EXP_PREP_1 = (
    "#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tDescription\n"
    "1.SKB8.640193\tGTCCGCAAGTTA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD8.640184\tCGTAGAGCTCTC\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n")

EXP_PREP_2 = (
    "#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tDescription\n"
    "1.SKB7.640196\tCCTCTGAGAGCT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n")

if __name__ == '__main__':
    main()
