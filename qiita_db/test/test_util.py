# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.util import check_table_cols, check_required_columns
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.exceptions import QiitaDBColumnError


@qiita_test_checker()
class DBUtilTests(TestCase):

    def setUp(self):
        self.conn_handler = SQLConnectionHandler()
        self.table = 'study'
        self.required = [
            'number_samples_promised', 'study_title', 'mixs_compliant',
            'metadata_complete', 'study_description', 'first_contact',
            'reprocess', 'study_status_id', 'portal_type_id',
            'timeseries_type_id', 'study_alias', 'study_abstract',
            'principal_investigator_id', 'email', 'number_samples_collected']

    def test_check_required_columns(self):
        check_required_columns(self.conn_handler, self.required, self.table)

    def test_check_required_columns_fail(self):
        self.required.remove('study_title')
        with self.assertRaises(QiitaDBColumnError):
            check_required_columns(self.conn_handler, self.required,
                                   self.table)

    def test_check_table_cols(self):
        check_table_cols(self.conn_handler, self.required, self.table)

    def test_check_table_cols_fail(self):
        self.required.append('BADTHINGNOINHERE')
        with self.assertRaises(QiitaDBColumnError):
            check_table_cols(self.conn_handler, self.required,
                             self.table)

if __name__ == "__main__":
    main()