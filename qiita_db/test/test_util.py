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
from qiita_db.util import (exists_table, exists_dynamic_table, scrub_data,
                           compute_checksum, check_table_cols,
                           check_required_columns, convert_to_id)
from qiita_db.exceptions import QiitaDBColumnError
from tempfile import mkstemp
from os import close


@qiita_test_checker()
class DBUtilTests(TestCase):
    def setUp(self):
        self.table = 'study'
        self.required = [
            'number_samples_promised', 'study_title', 'mixs_compliant',
            'metadata_complete', 'study_description', 'first_contact',
            'reprocess', 'study_status_id', 'portal_type_id',
            'timeseries_type_id', 'study_alias', 'study_abstract',
            'principal_investigator_id', 'email', 'number_samples_collected']

    def test_check_required_columns(self):
        # Doesn't do anything if correct info passed, only errors if wrong info
        check_required_columns(self.conn_handler, self.required, self.table)

    def test_check_required_columns_fail(self):
        self.required.remove('study_title')
        with self.assertRaises(QiitaDBColumnError):
            check_required_columns(self.conn_handler, self.required,
                                   self.table)

    def test_check_table_cols(self):
        # Doesn't do anything if correct info passed, only errors if wrong info
        check_table_cols(self.conn_handler, self.required, self.table)

    def test_check_table_cols_fail(self):
        self.required.append('BADTHINGNOINHERE')
        with self.assertRaises(QiitaDBColumnError):
            check_table_cols(self.conn_handler, self.required,
                             self.table)

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

    def test_convert_to_id(self):
        """Tests that ids are returned correctly"""
        self.assertEqual(convert_to_id("tar", "filepath_type"), 7)

    def test_convert_to_id_bad_value(self):
        """Tests that ids are returned correctly"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            convert_to_id("FAKE", "filepath_type")


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

    def test_scrub_data_nothing(self):
        """Returns the same string without changes"""
        self.assertEqual(scrub_data("nothing_changes"), "nothing_changes")

    def test_scrub_data_semicolon(self):
        """Correctly removes the semicolon from the string"""
        self.assertEqual(scrub_data("remove_;_char"), "remove__char")

    def test_scrub_data_single_quote(self):
        """Correctly removes single quotes from the string"""
        self.assertEqual(scrub_data("'quotes'"), "quotes")

if __name__ == '__main__':
    main()
