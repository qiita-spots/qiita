from unittest import main

from moi import r_client

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

    def test_post_select_samples(self):
        # just making sure that the key is not set in redis
        r_client.delete('maintenance')
        response = self.get('/auth/reset/')
        self.assertEqual(response.code, 200)
        self.assertIn(('<label for="newpass2" class="col-sm-2 '
                       'control-label">Repeat New Password'
                       '</label>'), response.body)

        # not displaying due to maintenance
        r_client.set('maintenance', 'This is my error message')
        response = self.get('/auth/reset/')
        self.assertEqual(response.code, 200)
        self.assertNotIn(('<label for="newpass2" class="col-sm-2 '
                          'control-label">Repeat New Password'
                          '</label>'), response.body)
        r_client.delete('maintenance')

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
