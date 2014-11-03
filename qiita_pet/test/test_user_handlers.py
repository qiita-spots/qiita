from unittest import main
from tornado_test_base import TestHandlerBase


class TestUserProfile(TestHandlerBase):
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
            'action': 'profile',
            'name': 'NEWNAME'
        }
        response = self.post('/profile/', post_args)
        self.assertEqual(response.code, 200)

if __name__ == "__main__":
    main()
