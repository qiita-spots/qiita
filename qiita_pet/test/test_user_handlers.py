from unittest import main
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestUserProfile(TestHandlerBase):
    # TODO: add proper test for this once figure out how. Issue 567
    pass


class TestUserProfileHandler(TestHandlerBase):
    database = True

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

if __name__ == "__main__":
    main()
