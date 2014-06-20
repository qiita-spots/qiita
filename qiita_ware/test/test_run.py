from unittest import TestCase, main

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import qiita_test_checker

from qiita_db.analysis import Analysis
from qiita_db.job import Job

from qiita_ware.run import run_analysis

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


@qiita_test_checker()
class TestAnalysis(TestCase):
    def setUp(self):
        pass

    def test_run_analysis(self):
        "testing the run analysis function"

        run_analysis(Analysis(2))

        self.assertEqual('1', "1")


if __name__ == "__main__":
    main()
