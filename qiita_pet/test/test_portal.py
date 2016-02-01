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

    def test_post(self):
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.post('/admin/portals/studies/', {'portal': 'EMP',
                                                         'selected': [1],
                                                         'action': 'Add'})
        self.assertEqual(response.code, 200)

        response = self.post('/admin/portals/studies/', {'portal': 'EMP',
                                                         'selected': [1],
                                                         'action': 'Remove'})
        self.assertEqual(response.code, 200)

    def test_get_errors(self):
        # not valid user
        response = self.get('/admin/portals/studies/')
        self.assertEqual(response.code, 403)

    def test_post_errors(self):
        # not valid user
        response = self.post('/admin/portals/studies/', {'portal': 'EMP',
                                                         'selected': [1],
                                                         'action': 'Add'})
        self.assertEqual(response.code, 403)

        # making an admin the valid user so the next tests actually test
        # what they should
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))

        # not valid portal
        response = self.post('/admin/portals/studies/', {'portal': 'not-valid',
                                                         'selected': [1],
                                                         'action': 'Add'})
        self.assertEqual(response.code, 400)

        # not a valid action
        response = self.post('/admin/portals/studies/', {'portal': 'EMP',
                                                         'selected': [1],
                                                         'action': 'Error'})
        self.assertEqual(response.code, 400)


if __name__ == "__main__":
    main()
