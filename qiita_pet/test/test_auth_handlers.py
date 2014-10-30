from unittest import main
from tornado_test_base import TestHandlerBase
from auth_handlers import (AuthCreateHandler, AuthVerifyHandler,
                           AuthLoginHandler, AuthLogoutHandler)


class TestAuthCreateHandler(TestHandlerBase):
    database = True

    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()


class TestAuthVerifyHandler(TestHandlerBase):
    def test_get(self):
        raise NotImplementedError()


class TestAuthLoginHandler(TestHandlerBase):
    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()

    def test_set_current_user(self):
        raise NotImplementedError()


class TestAuthLogoutHandler(TestHandlerBase):
    def test_get(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
