# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
import qiita_db as qdb


class ResetAPItestHandler(OauthTestingBase):
    def test_post(self):
        qdb.user.User.create('new_user@test.foo', 'password')
        self.assertTrue(qdb.user.User.exists('new_user@test.foo'))
        obs = self.post('/apitest/reset/', headers=self.header, data="")
        self.assertEqual(obs.code, 200)
        self.assertFalse(qdb.user.User.exists('new_user@test.foo'))

if __name__ == '__main__':
    main()
