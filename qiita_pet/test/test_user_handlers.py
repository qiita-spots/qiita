from unittest import main
from tornado_test_base import TestHandlerBase


class TestUserProfile(TestHandlerBase):
    pass


class TestUserProfileHandler(TestHandlerBase):
    database = True

    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()


class TestForgotPasswordHandler(TestHandlerBase):
    database = True

    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()


class TestChangeForgotPasswordHandler(TestHandlerBase):
    database = True

    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
