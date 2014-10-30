from unittest import main
from tornado_test_base import TestHandlerBase
from upload import UploadFileHandler


class TestUploadFileHandler(TestHandlerBase):
    database = True

    def test_post(self):
        raise NotImplementedError()

    def test_get(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
