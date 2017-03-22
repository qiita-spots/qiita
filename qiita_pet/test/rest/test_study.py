# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from qiita_pet.test.tornado_test_base import TestHandlerBase


class StudyHandlerTests(TestHandlerBase):

    def test_get_valid(self):
        response = self.get('/api/v1/study/10317')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.content, {'exists': True})

    def test_get_invalid(self):
        response = self.get('/api/v1/study/0')
        self.assertEqual(response.code, 404)
        self.assertEqual(response.content, {'message': 'Study not found'})

    def test_get_invalid_negative(self):
        response = self.get('/api/v1/study/-1')
        self.assertEqual(response.code, 404)
        self.assertEqual(response.content, {'message': 'Study not found'})

    def test_get_invalid_namespace(self):
        response = self.get('/api/v1/study/1.11111')

        # we think this will be wrong, and it will really be Tornado vomit
        self.assertEqual(response.code, 404)
        self.assertEqual(response.content, {'message': 'Study not found'})


if __name__ == '__main__':
    main()
