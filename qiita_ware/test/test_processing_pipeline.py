# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from unittest import TestCase, main
from tempfile import mkdtemp, mkstemp
from os.path import exists, join, basename
from os import remove, close, mkdir
from functools import partial
from shutil import rmtree

import pandas as pd

from qiita_core.util import qiita_test_checker
from qiita_db.util import (get_db_files_base_dir, get_mountpoint,
                           convert_to_id, get_count)

from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.data import RawData, PreprocessedData
from qiita_db.study import Study
from qiita_db.parameters import (PreprocessedIlluminaParams,
                                 ProcessedSortmernaParams,
                                 Preprocessed454Params)

from qiita_db.metadata_template import PrepTemplate
from qiita_ware.processing_pipeline import (_get_preprocess_fastq_cmd,
                                            _get_preprocess_fasta_cmd,
                                            _insert_preprocessed_data,
                                            generate_demux_file,
                                            _get_qiime_minimal_mapping,
                                            _get_process_target_gene_cmd,
                                            _insert_processed_data_target_gene)


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

    def test_get_qiime_minimal_mapping_single_no_run_prefix(self):
        conn_handler = SQLConnectionHandler()
        sql = """DELETE FROM qiita.prep_columns
                 WHERE prep_template_id = 1 AND column_name = 'run_prefix';
                 ALTER TABLE qiita.prep_1 DROP COLUMN run_prefix"""
        conn_handler.execute(sql)
        prep_template = PrepTemplate(1)
        prep_template.generate_files()
        out_dir = mkdtemp()

        obs_fps = _get_qiime_minimal_mapping(prep_template, out_dir)
        exp_fps = [join(out_dir, 'prep_1_MMF.txt')]

        # Check that the returned list is as expected
        self.assertEqual(obs_fps, exp_fps)
        # Check that the file exists
        self.assertTrue(exists(exp_fps[0]))
        # Check the contents of the file
        with open(exp_fps[0], "U") as f:
            self.assertEqual(f.read(), EXP_PREP)

    def test_get_qiime_minimal_mapping_single_reverse_primer(self):
        conn_handler = SQLConnectionHandler()
        conn_handler
        sql = """INSERT INTO qiita.prep_columns
                        (prep_template_id, column_name, column_type)
                    VALUES (1, 'reverselinkerprimer', 'varchar');
                 ALTER TABLE qiita.prep_1
                    ADD COLUMN reverselinkerprimer varchar;
                 DELETE FROM qiita.prep_columns
                 WHERE prep_template_id = 1 AND column_name = 'run_prefix';
                 ALTER TABLE qiita.prep_1 DROP COLUMN run_prefix;
                 UPDATE qiita.prep_1 SET reverselinkerprimer = %s
                 """
        conn_handler.execute(sql, ('GTGCCAGCM',))
        prep_template = PrepTemplate(1)
        prep_template.generate_files()
        out_dir = mkdtemp()

        obs_fps = _get_qiime_minimal_mapping(prep_template, out_dir)
        exp_fps = [join(out_dir, 'prep_1_MMF.txt')]

        # Check that the returned list is as expected
        self.assertEqual(obs_fps, exp_fps)
        # Check that the file exists
        self.assertTrue(exists(exp_fps[0]))
        # Check the contents of the file
        with open(exp_fps[0], "U") as f:
            self.assertEqual(f.read(), EXP_PREP_RLP)

    def test_get_qiime_minimal_mapping_multiple(self):
        # We need to create a prep template in which we have different run
        # prefix values, so we can test this case
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 1',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAA',
                            'experiment_design_description': 'BBB'},
            'SKD8.640184': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 2',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'CGTAGAGCTCTC',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAA',
                            'experiment_design_description': 'BBB'},
            'SKB7.640196': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 3',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'CCTCTGAGAGCT',
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

    def test_get_preprocess_fasta_cmd_sff_no_run_prefix(self):
        raw_data = RawData(3)
        params = Preprocessed454Params(1)
        prep_template = PrepTemplate(1)
        obs_cmd, obs_output_dir = _get_preprocess_fasta_cmd(
            raw_data, prep_template, params)

        get_raw_path = partial(join, self.db_dir, 'raw_data')
        seqs_fp = [get_raw_path('1_preprocess_test1.sff'),
                   get_raw_path('1_preprocess_test2.sff')]

        exp_cmd_1 = ' '.join(["process_sff.py",
                              "-i %s" % seqs_fp[0],
                              "-o %s" % obs_output_dir])
        exp_cmd_2 = ' '.join(["process_sff.py",
                              "-i %s" % seqs_fp[1],
                              "-o %s" % obs_output_dir])

        fasta_files = ','.join([
            join(obs_output_dir, "1_preprocess_test1.fna"),
            join(obs_output_dir, "1_preprocess_test2.fna")])
        qual_files = ','.join([
            join(obs_output_dir, "1_preprocess_test1.qual"),
            join(obs_output_dir, "1_preprocess_test2.qual")])
        exp_cmd_3a = ' '.join(["split_libraries.py",
                               "-f %s" % fasta_files])

        exp_cmd_3b = ' '.join(["-q %s" % qual_files,
                               "-d",
                               "-o %s" % obs_output_dir,
                               params.to_str()])
        exp_cmd_4 = ' '.join(["convert_fastaqual_fastq.py",
                              "-f %s/seqs.fna" % obs_output_dir,
                              "-q %s/seqs_filtered.qual" % obs_output_dir,
                              "-o %s" % obs_output_dir,
                              "-F"])

        obs_cmds = obs_cmd.split('; ')

        # We are splitting the command into two parts because there is no way
        # that we can know the filepath of the mapping file. We thus split the
        # command on the mapping file path and we check that the two parts
        # of the commands is correct
        obs_cmd_3a, obs_cmd_3b_temp = obs_cmds[2].split(' -m ', 1)
        obs_cmd_3b = obs_cmd_3b_temp.split(' ', 1)[1]
        self.assertEqual(obs_cmds[0], exp_cmd_1)
        self.assertEqual(obs_cmds[1], exp_cmd_2)
        self.assertEqual(obs_cmd_3a, exp_cmd_3a)
        self.assertEqual(obs_cmd_3b, exp_cmd_3b)
        self.assertEqual(obs_cmds[3], exp_cmd_4)

    def test_get_preprocess_fasta_cmd_sff_run_prefix(self):
        # Need to alter the run_prefix of one sample so we can test the
        # multiple values
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.prep_1 SET run_prefix='test1' WHERE "
               "sample_id = '1.SKM9.640192'")
        conn_handler.execute(sql)

        raw_data = RawData(3)
        params = Preprocessed454Params(1)
        prep_template = PrepTemplate(1)
        prep_template.generate_files()

        obs_cmd, obs_output_dir = _get_preprocess_fasta_cmd(
            raw_data, prep_template, params)

        obs_cmds = obs_cmd.split('; ')
        # assumming that test_get_preprocess_fasta_cmd_sff_no_run_prefix is
        # working we only need to test for the commands being ran and
        # that n is valid
        self.assertEqual(len(obs_cmds), 8)
        self.assertTrue(obs_cmds[0].startswith('process_sff.py'))
        self.assertTrue(obs_cmds[1].startswith('process_sff.py'))
        self.assertTrue(obs_cmds[2].startswith('split_libraries.py'))
        self.assertIn('-n 1', obs_cmds[2])
        self.assertTrue(obs_cmds[3].startswith('split_libraries.py'))
        self.assertIn('-n 800000', obs_cmds[3])
        self.assertTrue(obs_cmds[4].startswith('cat'))
        self.assertIn('split_library_log.txt', obs_cmds[4])
        self.assertTrue(obs_cmds[5].startswith('cat'))
        self.assertTrue('seqs.fna', obs_cmds[5])
        self.assertTrue(obs_cmds[6].startswith('cat'))
        self.assertIn('seqs_filtered.qual', obs_cmds[6])

    def test_get_preprocess_fasta_cmd_sff_run_prefix_match(self):
        # Test that the run prefixes in the prep_template and the file names
        # actually match and raise an error if not
        new_fp_id = get_count('qiita.filepath') + 1
        conn_handler = SQLConnectionHandler()
        sql = ("""
            INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum,
                    checksum_algorithm_id, data_directory_id)
                VALUES ('1_new.sff', 17, 852952723, 1, 5);
            INSERT INTO qiita.raw_filepath (raw_data_id , filepath_id)
                VALUES (3, %s);
            UPDATE qiita.prep_1 SET run_prefix='preprocess_test';
            UPDATE qiita.prep_1 SET run_prefix='new'
                WHERE sample_id = '1.SKB8.640193';
        """)
        conn_handler.execute(sql, (new_fp_id,))

        raw_data = RawData(3)
        params = Preprocessed454Params(1)
        prep_template = PrepTemplate(1)
        prep_template.generate_files()

        obs_cmd, obs_output_dir = _get_preprocess_fasta_cmd(
            raw_data, prep_template, params)

        obs_cmds = obs_cmd.split('; ')
        # assumming that test_get_preprocess_fasta_cmd_sff_no_run_prefix is
        # working we only need to test for the commands being ran and
        # that n is valid
        self.assertEqual(len(obs_cmds), 9)
        self.assertTrue(obs_cmds[0].startswith('process_sff.py'))
        self.assertTrue(obs_cmds[1].startswith('process_sff.py'))
        self.assertTrue(obs_cmds[2].startswith('process_sff.py'))
        self.assertTrue(obs_cmds[3].startswith('split_libraries.py'))
        self.assertIn('-n 1', obs_cmds[3])
        self.assertTrue(obs_cmds[4].startswith('split_libraries.py'))
        self.assertIn('-n 800000', obs_cmds[4])
        self.assertTrue(obs_cmds[5].startswith('cat'))
        self.assertIn('split_library_log.txt', obs_cmds[5])
        self.assertTrue(obs_cmds[6].startswith('cat'))
        self.assertIn('seqs.fna', obs_cmds[6])
        self.assertEqual(len(obs_cmds[6].split(' ')), 5)
        self.assertTrue(obs_cmds[7].startswith('cat'))
        self.assertIn('seqs_filtered.qual', obs_cmds[7])
        self.assertEqual(len(obs_cmds[7].split(' ')), 5)

    def test_get_preprocess_fasta_cmd_sff_run_prefix_match_error_1(self):
        # Test that the run prefixes in the prep_template and the file names
        # actually match and raise an error if not
        fp_count = get_count('qiita.filepath')
        conn_handler = SQLConnectionHandler()
        sql = ("""
            INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum,
                    checksum_algorithm_id, data_directory_id)
                VALUES ('1_new.sff', 17, 852952723, 1, 5);
            INSERT INTO qiita.raw_filepath (raw_data_id , filepath_id)
                VALUES (3, %s);
            INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum,
                    checksum_algorithm_id, data_directory_id)
                VALUES ('1_error.sff', 17, 852952723, 1, 5);
            INSERT INTO qiita.raw_filepath (raw_data_id , filepath_id)
                VALUES (3, %s);
            UPDATE qiita.prep_1 SET run_prefix='preprocess_test';
            UPDATE qiita.prep_1 SET run_prefix='new' WHERE
                sample_id = '1.SKB8.640193';
        """)
        conn_handler.execute(
            sql, (fp_count + 1, fp_count + 2))

        raw_data = RawData(3)
        params = Preprocessed454Params(1)
        prep_template = PrepTemplate(1)
        prep_template.generate_files()

        with self.assertRaises(ValueError):
            _get_preprocess_fasta_cmd(raw_data, prep_template, params)

    def test_get_preprocess_fasta_cmd_sff_run_prefix_match_error_2(self):
        # Should raise error
        conn_handler = SQLConnectionHandler()
        sql = ("""
            UPDATE qiita.prep_1 SET run_prefix='test1';
            UPDATE qiita.prep_1 SET run_prefix='test2' WHERE
                sample_id = '1.SKB2.640194';
            UPDATE qiita.prep_1 SET run_prefix='error' WHERE
                sample_id = '1.SKB8.640193';
        """)
        conn_handler.execute(sql)

        raw_data = RawData(3)
        params = Preprocessed454Params(1)
        prep_template = PrepTemplate(1)
        prep_template.generate_files()

        with self.assertRaises(ValueError):
            _get_preprocess_fasta_cmd(raw_data, prep_template, params)

    def test_insert_preprocessed_data(self):
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

        _insert_preprocessed_data(study, params, prep_template,
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

        obs_fp = generate_demux_file(prep_out_dir)

        exp_fp = join(prep_out_dir, 'seqs.demux')
        self.assertEqual(obs_fp, exp_fp)
        self.assertTrue(exists(exp_fp))

    def test_get_process_target_gene_cmd(self):
        preprocessed_data = PreprocessedData(1)
        params = ProcessedSortmernaParams(1)

        obs_cmd, obs_output_dir = _get_process_target_gene_cmd(
            preprocessed_data, params)

        _, ref_dir = get_mountpoint('reference')[0]
        _, preprocessed_dir = get_mountpoint('preprocessed_data')[0]

        exp_cmd = ("pick_closed_reference_otus.py -i {}1_seqs.fna -r "
                   "{}GreenGenes_13_8_97_otus.fasta -o {} -p placeholder -t "
                   "{}GreenGenes_13_8_97_otu_taxonomy.txt".format(
                       preprocessed_dir, ref_dir, obs_output_dir, ref_dir))

        obs_tokens = obs_cmd.split()[::-1]
        exp_tokens = exp_cmd.split()[::-1]
        self.assertEqual(len(obs_tokens), len(exp_tokens))
        while obs_tokens:
            o_t = obs_tokens.pop()
            e_t = exp_tokens.pop()
            if o_t == '-p':
                # skip parameters file
                obs_tokens.pop()
                exp_tokens.pop()
            else:
                self.assertEqual(o_t, e_t)

    def test_insert_processed_data_target_gene(self):
        fd, fna_fp = mkstemp(suffix='_seqs.fna')
        close(fd)
        fd, qual_fp = mkstemp(suffix='_seqs.qual')
        close(fd)
        filepaths = [
            (fna_fp, convert_to_id('preprocessed_fasta', 'filepath_type')),
            (qual_fp, convert_to_id('preprocessed_fastq', 'filepath_type'))]

        preprocessed_data = PreprocessedData.create(
            Study(1), "preprocessed_sequence_illumina_params", 1,
            filepaths, data_type="18S")

        params = ProcessedSortmernaParams(1)
        pick_dir = mkdtemp()
        path_builder = partial(join, pick_dir)
        db_path_builder = partial(join, get_mountpoint('processed_data')[0][1])

        # Create a placeholder for the otu table
        with open(path_builder('otu_table.biom'), 'w') as f:
            f.write('\n')

        # Create a placeholder for the directory
        mkdir(path_builder('sortmerna_picked_otus'))

        # Create the log file
        fd, fp = mkstemp(dir=pick_dir, prefix='log_', suffix='.txt')
        close(fd)
        with open(fp, 'w') as f:
            f.write('\n')

        _insert_processed_data_target_gene(preprocessed_data, params, pick_dir)

        new_id = get_count('qiita.processed_data')

        # Check that the files have been copied
        db_files = [db_path_builder("%s_otu_table.biom" % new_id),
                    db_path_builder("%s_sortmerna_picked_otus" % new_id),
                    db_path_builder("%s_%s" % (new_id, basename(fp)))]
        for fp in db_files:
            self.assertTrue(exists(fp))

        # Check that a new preprocessed data has been created
        self.assertTrue(self.conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.processed_data WHERE "
            "processed_data_id=%s)", (new_id, ))[0])


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

EXP_PREP_RLP = (
    "#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tReverseLinkerPrimer"
    "\tDescription\n"
    "1.SKB1.640202\tGTCCGCAAGTTA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKB2.640194\tCGTAGAGCTCTC\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKB3.640195\tCCTCTGAGAGCT\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKB4.640189\tCCTCGATGCAGT\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKB5.640181\tGCGGACTATTCA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKB6.640176\tCGTGCACAATTG\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKB7.640196\tCGGCCTAAGTTC\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKB8.640193\tAGCGCTCACATC\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKB9.640200\tTGGTTATGGCAC\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKD1.640179\tCGAGGTTCTGAT\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKD2.640178\tAACTCCTGTGGA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKD3.640198\tTAATGGTCGTAG\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKD4.640185\tTTGCACCGTCGA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKD5.640186\tTGCTACAGACGT\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKD6.640190\tATGGCCTGACTA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKD7.640191\tACGCACATACAA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKD8.640184\tTGAGTGGTCTGT\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKD9.640182\tGATAGCACTCGT\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKM1.640183\tTAGCGCGAACTT\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKM2.640199\tCATACACGCACC\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKM3.640197\tACCTCAGTCAAG\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKM4.640180\tTCGACCAAACAC\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKM5.640177\tCCACCCAGTAAC\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKM6.640187\tATATCGCGATGA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKM7.640188\tCGCCGGTAATCT\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKM8.640201\tCCGATGCCTTGA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n"
    "1.SKM9.640192\tAGCAGGCACGAA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCM\tQiita MMF\n")

EXP_PREP_1 = (
    "#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tDescription\n"
    "1.SKB8.640193\tGTCCGCAAGTTA\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n"
    "1.SKD8.640184\tCGTAGAGCTCTC\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n")

EXP_PREP_2 = (
    "#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tDescription\n"
    "1.SKB7.640196\tCCTCTGAGAGCT\tGTGCCAGCMGCCGCGGTAA\tQiita MMF\n")

if __name__ == '__main__':
    main()
