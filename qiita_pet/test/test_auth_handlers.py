# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.user import User


class TestAuthCreateHandler(TestHandlerBase):

    def test_get(self):
        response = self.get('/auth/create/')
        self.assertEqual(response.code, 200)

    def test_post(self):
        post_args = {
            'email': 'newuser@foo.bar',
            'newpass': 'password'
        }
        response = self.post('/auth/create/', post_args)
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)


class TestAuthVerifyHandler(TestHandlerBase):

    def test_get(self):
        response = self.get('/auth/verify/SOMETHINGHERE?email=test%40foo.bar')
        self.assertEqual(response.code, 200)

        User.create('new@test.com', 'Somesortofpass')
        response = self.get('/auth/verify/SOMETHINGHERE?email=new%40test.bar')
        self.assertEqual(response.code, 200)


class TestAuthLoginHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/auth/login/')
        self.assertEqual(response.code, 200)
        # make sure redirect happened properly
        port = self.get_http_port()
        self.assertEqual(response.effective_url, 'http://localhost:%d/' % port)

    def test_post_correct_pass(self):
        post_args = {
            'username': 'test@foo.bar',
            'passwd': 'password',
            'next': '/'
        }
        response = self.post('/auth/login/', post_args)
        self.assertEqual(response.code, 200)

    def test_post_wrong_pass(self):
        post_args = {
            'username': 'test@foo.bar',
            'passwd': 'wrongpass',
            'next': '/'
        }
        response = self.post('/auth/login/', post_args)
        self.assertEqual(response.code, 200)

    def test_set_current_user(self):
        # TODO: add proper test for this once figure out how. Issue 567
        pass


class TestAuthLogoutHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/auth/login/')
        self.assertEqual(response.code, 200)
        # make sure redirect happened properly
        port = self.get_http_port()
        self.assertEqual(response.effective_url, 'http://localhost:%d/' % port)


if __name__ == "__main__":
    main()
