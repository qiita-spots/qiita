from unittest import main
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestLogEntryViewerHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/admin/error/')
        self.assertEqual(response.code, 405)

    def test_post(self):
        response = self.post('/admin/error/', {'numrecords': -5})
        self.assertEqual(response.code, 405)

        response = self.post('/admin/error/', {'numrecords': 20})
        self.assertEqual(response.code, 405)


if __name__ == "__main__":
    main()
