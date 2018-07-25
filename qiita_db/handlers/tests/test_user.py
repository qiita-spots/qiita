# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from json import loads

from qiita_db.handlers.tests.oauthbase import OauthTestingBase


class UserInfoDBHandlerTests(OauthTestingBase):
    def test_get_does_not_exist(self):
        obs = self.get('/qiita_db/user/no-exists@foo.bar/data/',
                       headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get_no_header(self):
        obs = self.get('/qiita_db/user/no-exists@foo.bar/data/')
        self.assertEqual(obs.code, 400)

    def test_get(self):
        obs = self.get('/qiita_db/user/shared@foo.bar/data/',
                       headers=self.header)
        self.assertEqual(obs.code, 200)

        obs = loads(obs.body)
        self.assertEqual(obs.keys(), ['data'])

        # for simplicity we will only test that the keys are the same
        # and that one of the key's info is correct
        obs = obs['data']
        exp = {"password": "$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJk"
               "UM8nXG9Efe", "email": "shared@foo.bar", "level": "user"}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
