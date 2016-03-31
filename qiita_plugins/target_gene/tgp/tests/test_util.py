# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os import getcwd

import httpretty
from qiita_client import QiitaClient

from tgp.util import system_call


class UtilTests(TestCase):
    @httpretty.activate
    def setUp(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')
        self.qclient = QiitaClient("https://test_server.com", 'client_id',
                                   'client_secret')

    def test_system_call(self):
        obs_out, obs_err, obs_val = system_call("pwd")
        self.assertEqual(obs_out, "%s\n" % getcwd())
        self.assertEqual(obs_err, "")
        self.assertEqual(obs_val, 0)

    def test_system_call_error(self):
        obs_out, obs_err, obs_val = system_call("IHopeThisCommandDoesNotExist")
        self.assertEqual(obs_out, "")
        self.assertTrue("command not found" in obs_err)
        self.assertEqual(obs_val, 127)


if __name__ == '__main__':
    main()
