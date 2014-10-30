from unittest import TestCase, main
from base_handlers import BaseHandler, MainHandler, MockupHandler, NoPageHandler


class TestBaseHandler(TestCase):
    def test_get_current_user(self):
        raise NotImplementedError()

    def test_write_error(self):
        raise NotImplementedError()

    def test_head(self):
        raise NotImplementedError()


class TestMainHandler(TestCase):
    def test_get(self):
        raise NotImplementedError()


class TestMockupHandler(TestCase):
    def test_get(self):
        raise NotImplementedError()


class TestNoPageHandler(TestCase):
    def test_get(self):
        raise NotImplementedError()

    def test_head(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
