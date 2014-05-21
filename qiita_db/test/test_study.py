from unittest import TestCase, main

from ..study import Study
from qiita_db.util import populate_test_db, teardown_qiita_schema
from ..exceptions import QiitaDBExecutionError, QiitaDBConnectionError
from ..sql_connection import SQLConnectionHandler


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


# ALL TESTS ASSUME EMPTY qiita DATABASE EXISTS
class TestStudy(TestCase):
    def SetUp(self):
        conn = SQLConnectionHandler()
        populate_test_db(conn)

        self.info = {

        }

    def TearDown(self):
        conn = SQLConnectionHandler()
        teardown_qiita_schema(conn)

    def test_create_study():
        """Insert a study into the database"""
        Study.create('test@foo.bar', self.info)

    def test_create_study_with_investigation(self):
        """Insert a study into the database"""
        Study.create('test@foo.bar', self.info, 0)

    def test_insert_missing_requred(self):
        """ Insert a study that is missing a required info key"""
        raise NotImplementedError()

    def test_insert_unknown_db_col(self):
        """ Insert a study with an info key not in the database"""
        raise NotImplementedError()

    def test_retrieve_name(self):
        raise NotImplementedError()

    def test_set_name(self):
        raise NotImplementedError()

    def test_retrieve_info(self):
        raise NotImplementedError()

    def test_set_info(self):
        raise NotImplementedError()

    def test_retrieve_status(self):
        raise NotImplementedError()

    def test_set_status(self):
        raise NotImplementedError()

    def test_retrieve_sample_ids(self):
        raise NotImplementedError()

    def test_retrieve_shared_with(self):
        raise NotImplementedError()

    def test_retrieve_pmids(self):
        raise NotImplementedError()

    def test_retrieve_investigations(self):
        raise NotImplementedError()

    def test_retrieve_metadata(self):
        raise NotImplementedError()

    def test_retrieve_raw_data(self):
        raise NotImplementedError()

    def test_retrieve_preprocessed_data(self):
        raise NotImplementedError()

    def test_retrieve_processed_data(self):
        raise NotImplementedError()

    def test_share_with(self):
        raise NotImplementedError()

    def test_add_raw_data(self):
        raise NotImplementedError()

    def test_add_pmid(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
