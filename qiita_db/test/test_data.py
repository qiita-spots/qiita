# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.study import Study
from qiita_db.data import BaseData, RawData, PreprocessedData


@qiita_test_checker()
class BaseDataTests(TestCase):
    """Tests the BaseData class"""

    def setUp(self):
        self.filepaths = [('foo/bar.fna', 1), ('bar/foo.fna', 1)]
        self.conn_handler = SQLConnectionHandler()

    def test_insert_filepath(self):
        """Correctly inserts the data on the DB and returns the id"""
        obs = BaseData.insert_filepaths(self.filepaths, self.conn_handler)
        exp = [6, 7]
        self.assertEqual(obs, exp)

    def test_link_data_filepaths(self):
        """It should raise an error because this is a base class"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            BaseData.link_data_filepaths(1, [1, 2, 3], self.conn_handler)


@qiita_test_checker()
class RawDataTests(TestCase):
    """Tests the RawData class"""
    def setUp(self):
        self.filetype = 2
        self.filepaths = [('foo/seq.fastq', 1), ('foo/bar.fastq', 2)]
        self.study = Study(1)
        self.conn_handler = SQLConnectionHandler()

    def test_create(self):
        """Correctly creates all the rows in the DB for the raw data"""
        # Check that the returned object has the correct id
        obs = RawData.create(self.filetype, self.filepaths, self.study)
        self.assertEqual(obs.id, 2)
        # Check that the raw data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchone(
            "SELECT * FROM qiita.raw_data WHERE raw_data_id=2")
        # raw_data_id, filetype, submitted_to_insdc
        self.assertEqual(obs, [2, 2, False])
        # Check that the raw data have been correctly linked with the study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_raw_data WHERE raw_data_id=2")
        # study_id , raw_data_id
        self.assertEqual(obs, [[1, 2]])
        # Check that the filepaths have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=6 or "
            "filepath_id=7")
        # filepath_id, path, filepath_type_id
        exp = [[6, 'foo/seq.fastq', 1], [7, 'foo/bar.fastq', 2]]
        self.assertEqual(obs, exp)
        # Check that the raw data have been correctly linked with the filepaths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_filepath WHERE raw_data_id=2")
        # raw_data_id, filepath_id
        self.assertEqual(obs, [[2, 6], [2, 7]])

    def test_delete(self):
        """Correctly removes the RawData row from the DB"""
        # RawData.delete(1)
        pass

    def test_is_submitted_to_insdc(self):
        """is_submitted_to_insdc works correctly"""
        # False case
        rd = RawData.create(self.filetype, self.filepaths, self.study)
        self.assertFalse(rd.is_submitted_to_insdc())
        # True case
        rd = RawData.create(self.filetype, self.filepaths, self.study,
                            submitted_to_insdc=True)
        self.assertTrue(rd.is_submitted_to_insdc())


@qiita_test_checker()
class PreprocessedDataTests(TestCase):
    """Tests the PreprocessedData class"""
    def setUp(self):
        self.conn_handler = SQLConnectionHandler()
        # Insert a new RawData object
        self.raw_data = RawData.create(2, [('foo/seq.fastq', 1),
                                           ('foo/bar.fastq', 2)], Study(1))
        self.params_table = "preprocessed_sequence_illumina_params"
        self.params_id = 1
        self.filepaths = [('foo/seq.fna', 4), ('foo/bar.qual', 5)]

    def test_create(self):
        """Correctly creates all the rows in the DB for the preprocessed
        data"""
        # Check that the returned object has the correct id
        obs = PreprocessedData.create(self.raw_data, self.params_table,
                                      self.params_id, self.filepaths)
        self.assertEqual(obs.id, 2)
        # Check that the preprocessed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchone(
            "SELECT * FROM qiita.preprocessed_data WHERE "
            "preprocessed_data_id=2")
        # preprocessed_data_id, raw_data_id, preprocessed_params_tables,
        # preprocessed_params_id
        exp = [2, 2, "preprocessed_sequence_illumina_params", 1]
        self.assertEqual(obs, exp)
        # Check that the filepaths have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=8 or "
            "filepath_id=9")
        # filepath_id, path, filepath_type_id
        exp = [[8, 'foo/seq.fna', 4], [9, 'foo/bar.qual', 5]]
        self.assertEqual(obs, exp)
        # Check that the preprocessed data have been correctly
        # linked with the filepaths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_filepath WHERE "
            "preprocessed_data_id=2")
        # raw_data_id, filepath_id
        self.assertEqual(obs, [[2, 8], [2, 9]])

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

if __name__ == '__main__':
    main()