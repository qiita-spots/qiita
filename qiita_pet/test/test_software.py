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
from qiita_db.sql_connection import TRN
from qiita_pet.handlers.base_handlers import BaseHandler


class TestSoftware(TestHandlerBase):
    def test_get(self):
        response = self.get('/software/')
        self.assertEqual(response.code, 200)
        body = response.body.decode('ascii')
        self.assertNotEqual(body, "")
        # checking that this software is not displayed
        self.assertNotIn('Target Gene', body)

        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.get('/software/')
        self.assertEqual(response.code, 200)
        body = response.body.decode('ascii')
        self.assertNotEqual(body, "")
        # checking that this software is displayed
        self.assertIn('Target Gene', body)


class TestWorkflowsHandler(TestHandlerBase):
    def test_get(self):
        with TRN:
            TRN.add("""UPDATE qiita.default_workflow
                       SET active = false
                       WHERE default_workflow_id = 2""")
            TRN.execute()
        response = self.get('/workflows/')
        self.assertEqual(response.code, 200)
        body = response.body.decode('ascii')
        self.assertNotEqual(body, "")
        # checking that this software is not displayed
        self.assertNotIn('FASTA upstream workflow', body)

        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.get('/workflows/')
        self.assertEqual(response.code, 200)
        body = response.body.decode('ascii')
        self.assertNotEqual(body, "")
        # checking that this software is displayed
        self.assertIn('FASTA upstream workflow', body)


if __name__ == "__main__":
    main()
