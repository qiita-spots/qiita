# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.util import exists_table, exists_dynamic_table
from qiita_db.sql_connection import SQLConnectionHandler


@qiita_test_checker()
class DBUtilTests(TestCase):

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

if __name__ == '__main__':
    main()
