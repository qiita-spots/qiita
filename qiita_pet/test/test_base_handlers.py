from unittest import main
from tornado_test_base import TestHandlerBase
from base_handlers import (
    BaseHandler, MainHandler, MockupHandler, NoPageHandler)


class TestBaseHandler(TestHandlerBase):
    def test_get_current_user(self):
        raise NotImplementedError()

    def test_write_error(self):
        raise NotImplementedError()

    def test_head(self):
        raise NotImplementedError()


class TestMainHandler(TestHandlerBase):
    def test_get(self):
        raise NotImplementedError()


class TestMockupHandler(TestHandlerBase):
    def test_get(self):
        raise NotImplementedError()


class TestNoPageHandler(TestHandlerBase):
    def test_get(self):
        raise NotImplementedError()

    def test_head(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
