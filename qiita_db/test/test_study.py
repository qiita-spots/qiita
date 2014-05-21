from unittest import TestCase, main

from ..qiita_db.study import Study
from ..exceptions import QiitaDBExecutionError, QiitaDBConnectionError
from ..sql_connection import SQLConnectionHandler


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

#ASSUMING EMPTY DATABASE ALREADY MADE
class TestStudy(TestCase):
    def SetUp(self):
        conn = SQLConnectionHandler()
        populate_test_db(conn)

    def TearDown(self):
        pass

    def test_create_study():


if __name__ == "__main__":
    main()
