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
from qiita_db.study import Study
from qiita_db.util import get_db_files_base_dir
from qiita_db.data import BaseData, RawData, PreprocessedData, ProcessedData


@qiita_test_checker()
class BaseDataTests(TestCase):
    """Tests the BaseData class"""

    def test_init(self):
        """Raises an error if trying to instantiate the base data"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            BaseData(1)


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
        self.db_test_raw_dir = join(get_db_files_base_dir(), 'raw_data')

        with open(self.seqs_fp, "w") as f:
            f.write("\n")
        with open(self.barcodes_fp, "w") as f:
            f.write("\n")
        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_create(self):
        """Correctly creates all the rows in the DB for the raw data"""
        # Check that the returned object has the correct id
        obs = RawData.create(self.filetype, self.filepaths, self.studies)
        self.assertEqual(obs.id, 3)

        # Check that the raw data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_data WHERE raw_data_id=3")
        # raw_data_id, filetype, submitted_to_insdc
        self.assertEqual(obs, [[3, 2]])

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
            "SELECT * FROM qiita.filepath WHERE filepath_id=15 or "
            "filepath_id=16")
        # filepath_id, path, filepath_type_id
        exp = [[15, exp_seqs_fp, 1, '852952723', 1],
               [16, exp_bc_fp, 2, '852952723', 1]]
        self.assertEqual(obs, exp)

        # Check that the raw data have been correctly linked with the filepaths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_filepath WHERE raw_data_id=3")
        # raw_data_id, filepath_id
        self.assertEqual(obs, [[3, 15], [3, 16]])

    def test_get_filepaths(self):
        """Correctly returns the filepaths to the raw files"""
        rd = RawData(1)
        obs = rd.get_filepaths()
        exp = [
            (join(self.db_test_raw_dir, '1_s_G1_L001_sequences.fastq.gz'),
             "raw_sequences"),
            (join(self.db_test_raw_dir,
                  '1_s_G1_L001_sequences_barcodes.fastq.gz'), "raw_barcodes")]
        self.assertEqual(obs, exp)

    def test_studies(self):
        """Correctly returns the study ids"""
        rd = RawData(1)
        self.assertEqual(rd.studies, [1])

    def test_data_type(self):
        """Correctly returns the data_type of raw_data"""
        rd = RawData(1)
        self.assertEqual(rd.data_type(), "18S")

    def test_data_type_id(self):
        """Correctly returns the data_type of raw_data"""
        rd = RawData(1)
        self.assertEqual(rd.data_type(ret_id=True), 2)


@qiita_test_checker()
class PreprocessedDataTests(TestCase):
    """Tests the PreprocessedData class"""
    def setUp(self):
        self.raw_data = RawData(1)
        self.study = Study(1)
        self.params_table = "preprocessed_sequence_illumina_params"
        self.params_id = 1
        fd, self.fna_fp = mkstemp(suffix='_seqs.fna')
        close(fd)
        fd, self.qual_fp = mkstemp(suffix='_seqs.qual')
        close(fd)
        self.filepaths = [(self.fna_fp, 4), (self.qual_fp, 5)]
        self.db_test_ppd_dir = join(get_db_files_base_dir(),
                                    'preprocessed_data')
        self.ebi_submission_accession = "EBI123456-A"
        self.ebi_study_accession = "EBI123456-B"

        with open(self.fna_fp, "w") as f:
            f.write("\n")
        with open(self.qual_fp, "w") as f:
            f.write("\n")
        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_create(self):
        """Correctly creates all the rows in the DB for preprocessed data"""
        # Check that the returned object has the correct id
        obs = PreprocessedData.create(self.study, self.params_table,
            self.params_id, self.filepaths, raw_data=self.raw_data,
            ebi_submission_accession=self.ebi_submission_accession,
            ebi_study_accession=self.ebi_study_accession)
        self.assertEqual(obs.id, 3)

        # Check that the preprocessed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_data WHERE "
            "preprocessed_data_id=3")
        exp = [[3, "preprocessed_sequence_illumina_params", 1, False,
                "EBI123456-A", "EBI123456-B", 2]]
        self.assertEqual(obs, exp)

        # Check that the preprocessed data has been linked with its study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_preprocessed_data WHERE "
            "preprocessed_data_id=3")
        exp = [[1, 3]]
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
            "SELECT * FROM qiita.filepath WHERE filepath_id=15 or "
            "filepath_id=16")
        # filepath_id, path, filepath_type_id
        exp = [[15, exp_fna_fp, 4, '852952723', 1],
               [16, exp_qual_fp, 5, '852952723', 1]]
        self.assertEqual(obs, exp)

    def test_create_data_type_only(self):
        # Check that the returned object has the correct id
        obs = PreprocessedData.create(self.study, self.params_table,
                                      self.params_id, self.filepaths,
                                      data_type="18S")
        self.assertEqual(obs.id, 3)

        # Check that the preprocessed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_data WHERE "
            "preprocessed_data_id=3")
        exp = [[3, "preprocessed_sequence_illumina_params", 1, False, None,
                None, 2]]
        self.assertEqual(obs, exp)

        # Check that the preprocessed data has been linked with its study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_preprocessed_data WHERE "
            "preprocessed_data_id=3")
        exp = [[1, 3]]
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
            "SELECT * FROM qiita.filepath WHERE filepath_id=15 or "
            "filepath_id=16")
        # filepath_id, path, filepath_type_id
        exp = [[15, exp_fna_fp, 4, '852952723', 1],
               [16, exp_qual_fp, 5, '852952723', 1]]
        self.assertEqual(obs, exp)

        # Check that the preprocessed data have been correctly
        # linked with the filepaths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_filepath WHERE "
            "preprocessed_data_id=3")
        # preprocessed_data_id, filepath_id
        self.assertEqual(obs, [[3, 15], [3, 16]])

    def test_create_error_dynamic_table(self):
        """Raises an error if the preprocessed_params_table does not exist"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study, "foo", self.params_id,
                                    self.filepaths, data_type="18S")
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study, "preprocessed_foo",
                                    self.params_id, self.filepaths,
                                    data_type="18S")
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study, "foo_params", self.params_id,
                                    self.filepaths, data_type="18S")
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study, "preprocessed_foo_params",
                                    self.params_id, self.filepaths,
                                    data_type="18S")

    def test_create_error_data_type(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study,
                                    "preprocessed_sequence_illumina_params",
                                    self.params_id, self.filepaths,
                                    data_type="Metabolomics")
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study,
                                    "preprocessed_sequence_illumina_params",
                                    self.params_id, self.filepaths,
                                    data_type="Metabolomics",
                                    raw_data=self.raw_data)

    def test_get_filepaths(self):
        """Correctly returns the filepaths to the preprocessed files"""
        ppd = PreprocessedData(1)
        obs = ppd.get_filepaths()
        exp = [(join(self.db_test_ppd_dir, '1_seqs.fna'),
                "preprocessed_sequences"),
               (join(self.db_test_ppd_dir, '1_seqs.qual'),
                "preprocessed_sequences_qual")]
        self.assertEqual(obs, exp)

    def test_raw_data(self):
        """Correctly returns the raw data"""
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.raw_data, 1)

    def test_study(self):
        """Correctly returns the study"""
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.study, 1)

    def test_ebi_submission_accession(self):
        """Correctly returns the ebi_submission_accession"""
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.ebi_submission_accession, 'EBI123456-AA')

    def test_ebi_ebi_study_accession(self):
        """Correctly returns the ebi_study_accession"""
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.ebi_study_accession, 'EBI123456-BB')

    def test_is_submitted_to_insdc(self):
        """is_submitted_to_insdc works correctly"""
        # False case
        pd = PreprocessedData(1)
        self.assertTrue(pd.is_submitted_to_insdc())
        # True case
        pd = PreprocessedData(2)
        self.assertFalse(pd.is_submitted_to_insdc())

    def test_data_type(self):
        """Correctly returns the data_type of preprocessed_data"""
        pd = ProcessedData(1)
        self.assertEqual(pd.data_type(), "18S")

    def test_data_type_id(self):
        """Correctly returns the data_type of preprocessed_data"""
        pd = ProcessedData(1)
        self.assertEqual(pd.data_type(ret_id=True), 2)


@qiita_test_checker()
class ProcessedDataTests(TestCase):
    """Tests the ProcessedData class"""
    def setUp(self):
        self.preprocessed_data = PreprocessedData(1)
        self.params_table = "processed_params_uclust"
        self.params_id = 1
        fd, self.biom_fp = mkstemp(suffix='_table.biom')
        close(fd)
        self.filepaths = [(self.biom_fp, 6)]
        self.date = datetime(2014, 5, 29, 12, 24, 51)
        self.db_test_pd_dir = join(get_db_files_base_dir(), 'processed_data')

        with open(self.biom_fp, "w") as f:
            f.write("\n")
        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_create(self):
        """Correctly creates all the rows in the DB for the processed data"""
        # Check that the returned object has the correct id
        obs = ProcessedData.create(self.params_table, self.params_id,
                                   self.filepaths,
                                   preprocessed_data=self.preprocessed_data,
                                   processed_date=self.date)
        self.assertEqual(obs.id, 2)

        # Check that the processed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.processed_data WHERE processed_data_id=2")
        # processed_data_id, preprocessed_data_id, processed_params_table,
        # processed_params_id, processed_date
        exp = [[2, "processed_params_uclust", 1, self.date, 2]]
        self.assertEqual(obs, exp)

        # Check that the files have been copied to right location
        exp_biom_fp = join(self.db_test_pd_dir,
                           "2_%s" % basename(self.biom_fp))
        self.assertTrue(exists(exp_biom_fp))
        self._clean_up_files.append(exp_biom_fp)

        # Check that the filepaths have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=15")
        # Filepath_id, path, filepath_type_id
        exp = [[15, exp_biom_fp, 6, '852952723', 1]]
        self.assertEqual(obs, exp)

        # Check that the processed data have been correctly linked
        # with the fileapths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.processed_filepath WHERE processed_data_id=2")
        # processed_data_id, filepath_id
        self.assertEqual(obs, [[2, 15]])

        # Check that the processed data have been correctly linked with the
        # study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_processed_data WHERE "
            "processed_data_id=2")
        # study_id, processed_data
        self.assertEqual(obs, [[1, 2]])

        # Check that the processed data have been correctly linked with the
        # preprocessed data
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_processed_data WHERE "
            "processed_data_id=2")
        # preprocessed_data_id, processed_Data_id
        self.assertEqual(obs, [[1, 2]])

    def test_create_no_date(self):
        """Correctly adds a processed data with no date on it"""
        # All the other settings have been already tested on test_create
        # here we will only check that the code added a good date
        before = datetime.now()
        ProcessedData.create(self.params_table, self.params_id, self.filepaths,
                             preprocessed_data=self.preprocessed_data)
        after = datetime.now()
        obs = self.conn_handler.execute_fetchone(
            "SELECT processed_date FROM qiita.processed_data WHERE "
            "processed_data_id=2")[0]

        # Make sure that we clean up the environment
        exp_biom_fp = join(self.db_test_pd_dir,
                           "2_%s" % basename(self.biom_fp))
        self._clean_up_files.append(exp_biom_fp)

        self.assertTrue(before <= obs <= after)

    def test_create_w_study(self):
        """Correctly adds a processed data passing a study"""
        obs = ProcessedData.create(self.params_table, self.params_id,
                                   self.filepaths, study=Study(1),
                                   processed_date=self.date, data_type="18S")

        # Check that the processed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.processed_data WHERE processed_data_id=2")
        # processed_data_id, preprocessed_data_id, processed_params_table,
        # processed_params_id, processed_date
        exp = [[2, "processed_params_uclust", 1, self.date, 2]]
        self.assertEqual(obs, exp)

        # Check that the files have been copied to right location
        exp_biom_fp = join(self.db_test_pd_dir,
                           "2_%s" % basename(self.biom_fp))
        self.assertTrue(exists(exp_biom_fp))
        self._clean_up_files.append(exp_biom_fp)

        # Check that the filepaths have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=15")
        # Filepath_id, path, filepath_type_id
        exp = [[15, exp_biom_fp, 6, '852952723', 1]]
        self.assertEqual(obs, exp)

        # Check that the processed data have been correctly linked
        # with the fileapths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.processed_filepath WHERE processed_data_id=2")
        # processed_data_id, filepath_id
        self.assertTrue(obs, [[2, 10]])

        # Check that the processed data have been correctly linked with the
        # study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_processed_data WHERE "
            "processed_data_id=2")
        # study_id, processed_data
        self.assertEqual(obs, [[1, 2]])

    def test_create_params_table_error(self):
        """Raises an error if the processed_params_table does not exist"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create("foo", self.params_id, self.filepaths,
                                 preprocessed_data=self.preprocessed_data)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create("processed_params_foo", self.params_id,
                                 self.filepaths,
                                 preprocessed_data=self.preprocessed_data)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create("processed_params_", self.params_id,
                                 self.filepaths,
                                 preprocessed_data=self.preprocessed_data)

    def test_create_no_preprocessed_no_study_error(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create(self.params_table, self.params_id,
                                 self.filepaths)

    def test_create_preprocessed_and_study_error(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create(self.params_table, self.params_id,
                                 self.filepaths,
                                 preprocessed_data=self.preprocessed_data,
                                 study=Study(1))

    def test_create_preprocessed_and_data_type_error(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create(self.params_table, self.params_id,
                                 self.filepaths,
                                 preprocessed_data=self.preprocessed_data,
                                 data_type="Metabolomics",)

    def test_create_no_preprocessed_and_study_error(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create(self.params_table, self.params_id,
                                 self.filepaths)

    def test_get_filepath(self):
        """Correctly returns the filepaths to the processed files"""
        # check the test data
        pd = ProcessedData(1)
        obs = pd.get_filepaths()
        exp = [(join(self.db_test_pd_dir,
                     '1_study_1001_closed_reference_otu_table.biom'), "biom")]
        self.assertEqual(obs, exp)

    def test_get_filepath_ids(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.get_filepath_ids(), [10])

    def test_preprocessed_data(self):
        """Correctly returns the preprocessed_data"""
        pd = ProcessedData(1)
        self.assertEqual(pd.preprocessed_data, 1)

    def test_data_type(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.data_type(), "18S")

    def test_data_type_id(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.data_type(ret_id=True), 2)


if __name__ == '__main__':
    main()
