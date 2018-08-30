# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from tornado.web import HTTPError

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
import qiita_db as qdb


class UtilTests(OauthTestingBase):
    def test_get_sample_info(self):
        ST = qdb.metadata_template.sample_template.SampleTemplate
        exp = ST(1)
        obs = qdb.handlers.util._get_instance(ST, 1, 'error')
        self.assertEqual(obs, exp)

        # It does not exist
        with self.assertRaises(HTTPError):
            qdb.handlers.util._get_instance(ST, 100, 'error')

    def test_get_user_info(self):
        US = qdb.user.User
        obs = qdb.handlers.util._get_instance(US, 'shared@foo.bar', 'error')
        exp = US('shared@foo.bar')
        self.assertEqual(obs, exp)

        # It does not exist
        with self.assertRaises(HTTPError):
            qdb.handlers.util._get_instance(US, 'no-exists@foo.bar', 'error')


if __name__ == '__main__':
    main()
