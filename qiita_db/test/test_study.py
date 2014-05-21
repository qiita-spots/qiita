from unittest import TestCase, main

from ..qiita_db.study import Study
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

    def TearDown(self):
        conn = SQLConnectionHandler()
        teardown_qiita_schema(conn)

    def test_create_study():
        """Insert a study into the database"""
        Study.create('qiita@foo.bar', )


if __name__ == "__main__":
    main()
