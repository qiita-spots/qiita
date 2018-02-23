# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestUserProfile(TestHandlerBase):
    # TODO: add proper test for this once figure out how. Issue 567
    pass


class TestUserProfileHandler(TestHandlerBase):

    def test_get(self):
        response = self.get('/profile/')
        self.assertEqual(response.code, 200)

    def test_post_password(self):
        post_args = {
            'action': 'password',
            'oldpass': 'password',
            'newpass': 'newpass'
        }
        response = self.post('/profile/', post_args)
        self.assertEqual(response.code, 200)

    def test_post_profile(self):
        post_args = {
            'action': ['profile'],
            'affiliation': ['NEWNAME'],
            'address': ['ADDRESS'],
            'name': ['TESTDUDE'],
            'phone': ['111-222-3333']}
        response = self.post('/profile/', post_args)
        self.assertEqual(response.code, 200)


class TestUserJobsHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/user/jobs/')
        self.assertEqual(response.code, 200)


if __name__ == "__main__":
    main()
