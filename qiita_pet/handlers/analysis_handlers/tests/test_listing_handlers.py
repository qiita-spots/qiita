# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestListingHandlers(TestHandlerBase):
    def test_get_list_analyses_handler(self):
        response = self.get('/analysis/list/')
        self.assertEqual(response.code, 200)

    def test_get_analysis_summary_ajax(self):
        response = self.get('/analysis/dflt/sumary/')
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body),
                         {"artifacts": 1, "studies": 1, "samples": 4})

    def test_get_selected_samples_handler(self):
        response = self.get('/analysis/selected/')
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)


if __name__ == '__main__':
    main()
