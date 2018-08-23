# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from qiita_pet.test.tornado_test_base import TestHandlerBase

from mock import Mock

from qiita_db.user import User
from qiita_pet.handlers.base_handlers import BaseHandler


class TestSoftware(TestHandlerBase):
    def test_get(self):
        response = self.get('/admin/software/')
        self.assertEqual(response.code, 405)

        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.get('/admin/software/')
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.body, "")


if __name__ == "__main__":
    main()
