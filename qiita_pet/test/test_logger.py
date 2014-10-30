from unittest import main
from tornado_test_base import TestHandlerBase
from logger_handlers import LogEntryViewerHandler


class TestLogEntryViewerHandler(TestHandlerBase):
    def test__check_access(self):
        raise NotImplementedError()

    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
