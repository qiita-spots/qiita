from unittest import TestCase, main
from auth_handlers import (AuthCreateHandler, AuthVerifyHandler,
                           AuthLoginHandler, AuthLogoutHandler)


class TestAuthCreateHandler(TestCase):
    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()


class TestAuthVerifyHandler(TestCase):
    def test_get(self):
        raise NotImplementedError()


class TestAuthLoginHandler(TestCase):
    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()

    def test_set_current_user(self):
        raise NotImplementedError()


class TestAuthLogoutHandler(TestCase):
    def test_get(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
