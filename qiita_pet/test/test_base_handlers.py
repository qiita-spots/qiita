# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestMainHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/')
        self.assertEqual(response.code, 200)


class TestNoPageHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/THISPAGENOEXIST')
        self.assertEqual(response.code, 404)


class TestIFrame(TestHandlerBase):
    def test_get(self):
        response = self.get('/iframe/')
        self.assertEqual(response.code, 200)
        self.assertIn("<b>No content</b>", response.body)

        response = self.get('/iframe/?iframe=qiita-terms')
        self.assertEqual(response.code, 200)
        self.assertIn('src="/static/qiita_data_terms_of_use.html"',
                      response.body)


if __name__ == "__main__":
    main()
