# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestListAnalysesHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/analysis/list/')
        self.assertEqual(response.code, 200)


if __name__ == '__main__':
    main()
