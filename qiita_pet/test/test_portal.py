from unittest import main
from qiita_pet.test.tornado_test_base import TestHandlerBase

from mock import Mock

from qiita_db.user import User
from qiita_pet.handlers.base_handlers import BaseHandler


class TestPortal(TestHandlerBase):
    def test_get(self):
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.get('/admin/portals/studies/')
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.code, "")

    def test_post_add(self):
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.post('/admin/portals/studies/', {'portal': 'EMP',
                                                         'selected': [1],
                                                         'action': 'Add'})
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.code, "")

    def test_post_remove(self):
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.post('/admin/portals/studies/', {'portal': 'EMP',
                                                         'selected': [1],
                                                         'action': 'Remove'})
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.code, "")

    def test_get_not_valid_user(self):
        response = self.get('/admin/portals/studies/')
        self.assertEqual(response.code, 403)

    def test_post_not_valid_user(self):
        response = self.post('/admin/portals/studies/', {'portal': 'EMP',
                                                         'selected': [1],
                                                         'action': 'Add'})
        self.assertEqual(response.code, 403)

    def test_post_not_valid_portal(self):
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.post('/admin/portals/studies/', {'portal': 'not-valid',
                                                         'selected': [1],
                                                         'action': 'Add'})
        self.assertEqual(response.code, 400)

    def test_post_not_valid_action(self):
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.post('/admin/portals/studies/', {'portal': 'EMP',
                                                         'selected': [1],
                                                         'action': 'Error'})
        self.assertEqual(response.code, 400)

    def test_get_AJAX(self):
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        page = '/admin/portals/studiesAJAX/'
        response = self.get(page, {'sEcho': '1001', 'view-portal': 'QIITA'})
        self.assertEqual(response.code, 200)

        exp = "Identification of the Microbiomes for Cannabis Soils"
        self.assertIn(exp, response.body)

    def test_get_AJAX_not_valid_user(self):
        page = '/admin/portals/studiesAJAX/'
        response = self.get(page, {'sEcho': '1001', 'view-portal': 'QIITA'})
        self.assertEqual(response.code, 403)


if __name__ == "__main__":
    main()
