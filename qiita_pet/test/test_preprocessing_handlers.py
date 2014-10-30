from unittest import main
from tornado_test_base import TestHandlerBase
from preprocessing_handlers import PreprocessHandler


class TestPreprocessHandler(TestHandlerBase):
    database = True

    def test_post(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
