from unittest import main
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestStudyUploadFileHandler(TestHandlerBase):
    def test_get_exists(self):
        response = self.get('/study/upload/1')
        self.assertEqual(response.code, 200)

    def test_get_no_exists(self):
        response = self.get('/study/upload/245')
        self.assertEqual(response.code, 404)


class TestUploadFileHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/upload/')
        self.assertEqual(response.code, 400)


if __name__ == "__main__":
    main()
