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

from qiita_core.util import qiita_test_checker
from qiita_db.util import get_db_files_base_dir
from qiita_db.data import RawData
from qiita_db.study import Study
from qiita_db.parameters import PreprocessedIlluminaParams
from qiita_ware.processing_pipeline import (_get_preprocess_illumina_cmd,
                                            _insert_preprocessed_data_illumina,
                                            _clean_up, _generate_demux_file)


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

    def test_get_preprocess_illumina_cmd(self):
        raw_data = RawData(1)
        params = PreprocessedIlluminaParams(1)
        obs_cmd, obs_output_dir = _get_preprocess_illumina_cmd(raw_data,
                                                               params)
        exp_cmd_1 = ("split_libraries_fastq.py --store_demultiplexed_fastq -i "
                     "{0}/raw_data/1_s_G1_L001_sequences.fastq.gz -b "
                     "{0}/raw_data/1_s_G1_L001_sequences_barcodes.fastq.gz "
                     "-m ".format(self.db_dir))
        exp_cmd_2 = ("-o {0} --barcode_type golay_12 --max_bad_run_length 3 "
                     "--max_barcode_errors 1.5 "
                     "--min_per_read_length_fraction 0.75 "
                     "--phred_quality_threshold 3 --preprocessed_params_id 1 "
                     "--sequence_max_n 0 "
                     "--trim_length 151".format(obs_output_dir))

        # We are splitting the command into two parts because there is no way
        # that we can know the filepath of the mapping file. We thus split the
        # command on the mapping file path and we check that the two parts
        # of the commands is correct
        obs_cmd_1 = obs_cmd[:len(exp_cmd_1)]
        obs_cmd_2 = obs_cmd[len(exp_cmd_1):].split(" ", 1)[1]

        self.assertEqual(obs_cmd_1, exp_cmd_1)
        self.assertEqual(obs_cmd_2, exp_cmd_2)

    def test_insert_preprocessed_data_illumina(self):
        study = Study(1)
        params = PreprocessedIlluminaParams(1)
        raw_data = RawData(1)
        prep_out_dir = mkdtemp()
        self.dirs_to_remove.append(prep_out_dir)
        path_builder = partial(join, prep_out_dir)
        db_path_builder = partial(join, join(self.db_dir, "preprocessed_data"))

        file_suffixes = ['seqs.fna', 'seqs.fastq', 'seqs.demux']
        db_files = []
        for f_suff in file_suffixes:
            fp = path_builder(f_suff)
            with open(fp, 'w') as f:
                f.write("\n")
            self.files_to_remove.append(fp)
            db_files.append(db_path_builder("3_%s" % f_suff))
        self.files_to_remove.extend(db_files)

        _insert_preprocessed_data_illumina(study, params, raw_data,
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

    def test_clean_up(self):
        dir1 = mkdtemp()
        dir2 = mkdtemp()

        _clean_up([dir1, dir2])

        self.assertFalse(exists(dir1))
        self.assertFalse(exists(dir2))


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

if __name__ == '__main__':
    main()
