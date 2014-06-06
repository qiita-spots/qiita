# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from datetime import datetime
from os import close, remove
from os.path import join, basename, exists
from tempfile import mkstemp

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.study import Study
from qiita_db.util import get_db_files_base_dir
from qiita_db.data import RawData, PreprocessedData, ProcessedData

# @qiita_test_checker()
# class BaseDataTests(TestCase):
#     """Tests the BaseData class"""

#     def setUp(self):
#         self.filepaths = [('foo/bar.fna', 1), ('bar/foo.fna', 1)]
#         self.conn_handler = SQLConnectionHandler()

#     def test_insert_filepath(self):
#         """Correctly inserts the filepaths on the DB and returns the id"""
#         obs = BaseData._insert_filepaths(self.filepaths, self.conn_handler)
#         exp = [8, 9]
#         self.assertEqual(obs, exp)

#     def test_link_data_filepaths(self):
#         """It should raise an error if called from the base class"""
#         with self.assertRaises(IncompetentQiitaDeveloperError):
#             BaseData._link_data_filepaths(1, [1, 2, 3], self.conn_handler)

#     def tesst_check_data_filepath_attributes(self):
#         """It should raise an error if called from the base class"""
#         with self.assertRaises(IncompetentQiitaDeveloperError):
#             BaseData._check_data_filepath_attributes()

#     def test_get_filepaths(self):
#         """It should raise an error if called from the base class"""
#         bd = BaseData(1)
#         with self.assertRaises(IncompetentQiitaDeveloperError):
#             bd.get_filepaths()


@qiita_test_checker()
class RawDataTests(TestCase):
    """Tests the RawData class"""

    def setUp(self):
        fd, self.seqs_fp = mkstemp(suffix='_seqs.fastq')
        close(fd)
        fd, self.barcodes_fp = mkstemp(suffix='_barcodes.fastq')
        close(fd)
        self.filetype = 2
        self.filepaths = [(self.seqs_fp, 1), (self.barcodes_fp, 2)]
        self.studies = [Study(1)]
        self.conn_handler = SQLConnectionHandler()
        self.db_test_raw_dir = join(get_db_files_base_dir(), 'raw_data')
        self._clean_up_files = [self.seqs_fp, self.barcodes_fp]

    def tearDown(self):
        map(remove, self._clean_up_files)

    def test_create(self):
        """Correctly creates all the rows in the DB for the raw data"""
        # Check that the returned object has the correct id
        obs = RawData.create(self.filetype, self.filepaths, self.studies)
        self.assertEqual(obs.id, 3)

        # Check that the raw data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchone(
            "SELECT * FROM qiita.raw_data WHERE raw_data_id=3")
        # raw_data_id, filetype, submitted_to_insdc
        self.assertEqual(obs, [3, 2, False])

        # Check that the raw data have been correctly linked with the study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_raw_data WHERE raw_data_id=3")
        # study_id , raw_data_id
        self.assertEqual(obs, [[1, 3]])

        # Check that the files have been copied to right location
        exp_seqs_fp = join(self.db_test_raw_dir,
                           "3_%s" % basename(self.seqs_fp))
        self.assertTrue(exists(exp_seqs_fp))
        self._clean_up_files.append(exp_seqs_fp)

        exp_bc_fp = join(self.db_test_raw_dir,
                         "3_%s" % basename(self.barcodes_fp))
        self.assertTrue(exists(exp_bc_fp))
        self._clean_up_files.append(exp_bc_fp)

        # Check that the filepaths have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=8 or "
            "filepath_id=9")
        # filepath_id, path, filepath_type_id
        exp = [[8, exp_seqs_fp, 1], [9, exp_bc_fp, 2]]
        self.assertEqual(obs, exp)

        # Check that the raw data have been correctly linked with the filepaths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_filepath WHERE raw_data_id=3")
        # raw_data_id, filepath_id
        self.assertEqual(obs, [[3, 8], [3, 9]])

    def test_is_submitted_to_insdc(self):
        """is_submitted_to_insdc works correctly"""
        # False case
        rd = RawData(1)
        self.assertFalse(rd.is_submitted_to_insdc())
        # True case
        rd = RawData(2)
        self.assertTrue(rd.is_submitted_to_insdc())

    def test_get_filepaths(self):
        """Correctly returns the filepaths to the raw files"""
        # Check test data
        rd = RawData(1)
        obs = rd.get_filepaths()
        exp = [
            (join(self.db_test_raw_dir, '1_s_G1_L001_sequences.fastq.gz'), 1),
            (join(self.db_test_raw_dir,
                  '1_s_G1_L001_sequences_barcodes.fastq.gz'), 2)]
        self.assertEqual(obs, exp)


@qiita_test_checker()
class PreprocessedDataTests(TestCase):
    """Tests the PreprocessedData class"""
    def setUp(self):
        self.conn_handler = SQLConnectionHandler()
        self.raw_data = RawData(1)
        self.params_table = "preprocessed_sequence_illumina_params"
        self.params_id = 1
        fd, self.fna_fp = mkstemp(suffix='_seqs.fna')
        close(fd)
        fd, self.qual_fp = mkstemp(suffix='_seqs.qual')
        close(fd)
        self.filepaths = [(self.fna_fp, 4), (self.qual_fp, 5)]
        self.db_test_ppd_dir = join(get_db_files_base_dir(),
                                    'preprocessed_data')
        self._clean_up_files = [self.fna_fp, self.qual_fp]

    def tearDown(self):
        map(remove, self._clean_up_files)

    def test_create(self):
        """Correctly creates all the rows in the DB for preprocessed data"""
        # Check that the returned object has the correct id
        obs = PreprocessedData.create(self.raw_data, self.params_table,
                                      self.params_id, self.filepaths)
        self.assertEqual(obs.id, 3)

        # Check that the preprocessed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchone(
            "SELECT * FROM qiita.preprocessed_data WHERE "
            "preprocessed_data_id=3")
        # preprocessed_data_id, raw_data_id, preprocessed_params_tables,
        # preprocessed_params_id
        exp = [3, 1, "preprocessed_sequence_illumina_params", 1]
        self.assertEqual(obs, exp)

        # Check that the files have been copied to right location
        exp_fna_fp = join(self.db_test_ppd_dir,
                          "3_%s" % basename(self.fna_fp))
        self.assertTrue(exists(exp_fna_fp))
        self._clean_up_files.append(exp_fna_fp)

        exp_qual_fp = join(self.db_test_ppd_dir,
                           "3_%s" % basename(self.qual_fp))
        self.assertTrue(exists(exp_qual_fp))
        self._clean_up_files.append(exp_qual_fp)

        # Check that the filepaths have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=8 or "
            "filepath_id=9")
        # filepath_id, path, filepath_type_id
        exp = [[8, exp_fna_fp, 4], [9, exp_qual_fp, 5]]
        self.assertEqual(obs, exp)

        # Check that the preprocessed data have been correctly
        # linked with the filepaths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_filepath WHERE "
            "preprocessed_data_id=3")
        # preprocessed_data_id, filepath_id
        self.assertEqual(obs, [[3, 8], [3, 9]])

    def test_create_error(self):
        """Raises an error if the preprocessed_params_table does not exists"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.raw_data, "foo", self.params_id,
                                    self.filepaths)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.raw_data, "preprocessed_foo",
                                    self.params_id, self.filepaths)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.raw_data, "foo_params",
                                    self.params_id, self.filepaths)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.raw_data, "preprocessed_foo_params",
                                    self.params_id, self.filepaths)

    def test_get_filepaths(self):
        """Correctly returns the filepaths to the preprocessed files"""
        # Check test data
        ppd = PreprocessedData(1)
        obs = ppd.get_filepaths()
        exp = [(join(self.db_test_ppd_dir, '1_seqs.fna'), 4),
               (join(self.db_test_ppd_dir, '1_seqs.qual'), 5)]
        self.assertEqual(obs, exp)


# @qiita_test_checker()
# class ProcessedDataTests(TestCase):
#     """Tests the ProcessedData class"""
#     def setUp(self):
#         self.conn_handler = SQLConnectionHandler()
#         self.preprocessed_data = PreprocessedData(1)
#         self.params_table = "processed_params_uclust"
#         self.params_id = 1
#         self.filepaths = [('foo/table.biom', 6)]
#         self.date = datetime(2014, 5, 29, 12, 24, 51)

#     def test_create(self):
#         """Correctly creates all the rows in the DB for the processed data"""
#         # Check that the returned object has the correct id
#         obs = ProcessedData.create(self.preprocessed_data, self.params_table,
#                                    self.params_id, self.filepaths, self.date)
#         self.assertEqual(obs.id, 2)
#         # Check that the processed data have been correctly added to the DB
#         obs = self.conn_handler.execute_fetchone(
#             "SELECT * FROM qiita.processed_data WHERE processed_data_id=2")
#         # processed_data_id, preprocessed_data_id, processed_params_table,
#         # processed_params_id, processed_date
#         exp = [2, 1, "processed_params_uclust", 1, self.date]
#         self.assertEqual(obs, exp)
#         # Check that the filepaths have been correctly added to the DB
#         obs = self.conn_handler.execute_fetchall(
#             "SELECT * FROM qiita.filepath WHERE filepath_id=8")
#         # Filepath_id, path, filepath_type_id
#         exp = [[8, 'foo/table.biom', 6]]
#         self.assertEqual(obs, exp)
#         # Check that the processed data have been correctly linked
#         # with the fileapths
#         obs = self.conn_handler.execute_fetchall(
#             "SELECT * FROM qiita.processed_filepath WHERE processed_data_id=2")
#         # processed_data_id, filepath_id
#         self.assertTrue(obs, [[2, 8]])

#     def test_create_params_table_error(self):
#         """Raises an error ig the processed_params_table does not exists"""
#         with self.assertRaises(IncompetentQiitaDeveloperError):
#             ProcessedData.create(self.preprocessed_data, "foo", self.params_id,
#                                  self.filepaths)
#         with self.assertRaises(IncompetentQiitaDeveloperError):
#             ProcessedData.create(self.preprocessed_data,
#                                  "processed_params_foo", self.params_id,
#                                  self.filepaths)
#         with self.assertRaises(IncompetentQiitaDeveloperError):
#             ProcessedData.create(self.preprocessed_data, "processed_params_",
#                                  self.params_id, self.filepaths)

#     def test_get_filepath(self):
#         """Correctly returns the filepaths to the processed files"""
#         # check the test data
#         pd = ProcessedData(1)
#         obs = pd.get_filepaths()
#         exp = [['study_1001_closed_reference_otu_table.biom', 6]]
#         self.assertEqual(obs, exp)
#         # Check with a new added processed data
#         pd = ProcessedData.create(self.preprocessed_data, self.params_table,
#                                   self.params_id, self.filepaths, self.date)
#         obs = pd.get_filepaths()
#         exp = [['foo/table.biom', 6]]
#         self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
