# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from tornado.escape import json_decode

from qiita_pet.test.tornado_test_base import TestHandlerBase


class StudyHandlerTests(TestHandlerBase):

    def test_get_valid(self):
        response = self.get('/api/v1/study/1')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, "")

    def test_get_invalid(self):
        response = self.get('/api/v1/study/0')
        self.assertEqual(response.code, 404)
        self.assertEqual(json_decode(response.body),
                         {'message': 'Study not found'})

    def test_get_invalid_negative(self):
        response = self.get('/api/v1/study/-1')
        self.assertEqual(response.code, 404)
        # not asserting the body content as this is not a valid URI according
        # to the regex associating the handler to the webserver

    def test_get_invalid_namespace(self):
        response = self.get('/api/v1/study/1.11111')
        self.assertEqual(response.code, 404)
        # not asserting the body content as this is not a valid URI according


if __name__ == '__main__':
    main()
