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
from qiita_db.data import BaseData, RawData


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
        self.filepaths = [('foo/seq.qual', 1), ('foo/bar.qual', 2)]
        self.study_id = 1
        self.conn_handler = SQLConnectionHandler()

    def test_create(self):
        """Correctly creates the RawData row in the DB"""
        # Check that the returned object has the correct id
        obs = RawData.create(self.filetype, self.filepaths, self.study_id)
        exp = 2
        self.assertEqual(obs.id, exp)
        # Check that the raw data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchone(
            "SELECT * FROM qiita.raw_data WHERE raw_data_id=2")
        # raw_data_id, filetype, submitted_to_insdc
        exp = [2, 2, False]
        self.assertEqual(obs, exp)
        # Check that the raw data have been correctly linked with the study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_raw_data WHERE raw_data_id=2")
        # study_id , raw_data_id
        exp = [[1, 2]]
        self.assertEqual(obs, exp)
        # Check that the filepaths have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=6 or "
            "filepath_id=7")
        # filepath_id, path, filepath_type_id
        exp = [[6, 'foo/seq.qual', 1], [7, 'foo/bar.qual', 2]]
        self.assertEqual(obs, exp)
        # Check that the raw data have been correctly linked with the filepaths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_filepath WHERE raw_data_id=2")
        exp = [[2, 6], [2, 7]]
        self.assertEqual(obs, exp)

    def test_is_submitted_to_insdc(self):
        """is_submitted_to_insdc works correctly"""
        rd = RawData.create(self.filetype, self.filepaths, self.study_id)
        self.assertFalse(rd.is_submitted_to_insdc())

        rd = RawData.create(self.filetype, self.filepaths, self.study_id,
                            submitted_to_insdc=True)
        self.assertTrue(rd.is_submitted_to_insdc())


if __name__ == '__main__':
    main()