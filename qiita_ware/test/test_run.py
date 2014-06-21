from unittest import TestCase, main

from qiita_core.util import qiita_test_checker


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
        # unsure what to test here at this time
        pass


if __name__ == "__main__":
    main()
