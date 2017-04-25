from unittest import main
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestMainHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/')
        self.assertEqual(response.code, 200)


class TestNoPageHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/THISPAGENOEXIST')
        self.assertEqual(response.code, 404)


if __name__ == "__main__":
    main()
