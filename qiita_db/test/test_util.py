# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from tempfile import mkstemp
from os.path import dirname, abspath, join
from os import close

from qiita_core.util import qiita_test_checker
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.util import (exists_table, exists_dynamic_table,
                           get_db_files_base_dir, compute_checksum,
                           __file__ as util_file)


@qiita_test_checker()
class DBUtilTests(TestCase):
    """Tests for the util functions that need to access the DB"""

    def setUp(self):
        self.conn_handler = SQLConnectionHandler()

    def test_exists_table(self):
        """Correctly checks if a table exists"""
        # True cases
        self.assertTrue(exists_table("filepath", self.conn_handler))
        self.assertTrue(exists_table("qiita_user", self.conn_handler))
        self.assertTrue(exists_table("analysis", self.conn_handler))
        self.assertTrue(exists_table("prep_1", self.conn_handler))
        self.assertTrue(exists_table("sample_1", self.conn_handler))
        # False cases
        self.assertFalse(exists_table("sample_2", self.conn_handler))
        self.assertFalse(exists_table("prep_2", self.conn_handler))
        self.assertFalse(exists_table("foo_table", self.conn_handler))
        self.assertFalse(exists_table("bar_table", self.conn_handler))

    def test_exists_dynamic_table(self):
        """Correctly checks if a dynamic table exists"""
        # True cases
        self.assertTrue(exists_dynamic_table(
            "preprocessed_sequence_illumina_params", "preprocessed_",
            "_params", self.conn_handler))
        self.assertTrue(exists_dynamic_table("prep_1", "prep_", "",
                                             self.conn_handler))
        self.assertTrue(exists_dynamic_table("filepath", "", "",
                                             self.conn_handler))
        # False cases
        self.assertFalse(exists_dynamic_table(
            "preprocessed_foo_params", "preprocessed_", "_params",
            self.conn_handler))
        self.assertFalse(exists_dynamic_table(
            "preprocessed__params", "preprocessed_", "_params",
            self.conn_handler))
        self.assertFalse(exists_dynamic_table(
            "foo_params", "preprocessed_", "_params",
            self.conn_handler))
        self.assertFalse(exists_dynamic_table(
            "preprocessed_foo", "preprocessed_", "_params",
            self.conn_handler))
        self.assertFalse(exists_dynamic_table(
            "foo", "preprocessed_", "_params",
            self.conn_handler))


class UtilTests(TestCase):
    """Tests for the util functions that do not need to access the DB"""

    def setUp(self):
        fh, self.filepath = mkstemp()
        close(fh)
        with open(self.filepath, "w") as f:
            f.write("Some text so we can actually compute a checksum")

    def test_compute_checksum(self):
        """Correctly returns the file checksum"""
        obs = compute_checksum(self.filepath)
        exp = 1719580229
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
