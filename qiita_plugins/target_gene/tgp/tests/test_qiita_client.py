# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os.path import exists
from os import remove, environ, close
from tempfile import mkstemp

import httpretty

from tgp.qiita_client import QiitaClient


class QiitaClientTests(TestCase):
    def setUp(self):
        self.tester = QiitaClient("https://test_server.com")
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    def test_init(self):
        obs = QiitaClient("https://test_server.com")
        self.assertEqual(obs._server_url, "https://test_server.com")
        self.assertTrue(obs._verify)

    def test_init_cert(self):
        fd, conf_fp = mkstemp()
        close(fd)
        with open(conf_fp, 'w') as f:
            f.write(CONF_FP)

        self._clean_up_files.append(conf_fp)
        old_fp = environ.get('QP_TARGET_GENE_CONFIG_FP')
        environ['QP_TARGET_GENE_CONFIG_FP'] = conf_fp
        try:
            obs = QiitaClient("https://test_server.com")
        finally:
            if old_fp:
                environ['QP_TARGET_GENE_CONFIG_FP'] = old_fp
            else:
                del environ['QP_TARGET_GENE_CONFIG_FP']

        self.assertEqual(obs._server_url, "https://test_server.com")
        self.assertEqual(obs._verify, "/path/to/test_certificate.crt")

    @httpretty.activate
    def test_get(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://test_server.com/qiita_db/artifacts/1/type/",
            body='{"type": "FASTQ", "success": true, "error": ""}')
        obs = self.tester.get("/qiita_db/artifacts/1/type/")
        exp = {"type": "FASTQ", "success": True, "error": ""}
        self.assertEqual(obs, exp)

    @httpretty.activate
    def test_get_error(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://test_server.com/qiita_db/artifacts/1/type/",
            status=500)
        obs = self.tester.get("/qiita_db/artifacts/1/type/")
        self.assertIsNone(obs)

    @httpretty.activate
    def test_post(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/artifacts/1/type/",
            body='{"type": "FASTQ", "success": true, "error": ""}')
        obs = self.tester.post("/qiita_db/artifacts/1/type/", data="")
        exp = {"type": "FASTQ", "success": True, "error": ""}
        self.assertEqual(obs, exp)

    @httpretty.activate
    def test_post_error(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/artifacts/1/type/",
            status=500)
        obs = self.tester.post("/qiita_db/artifacts/1/type/")
        self.assertIsNone(obs)

CONF_FP = """
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

[main]
# If the Qiita server certificate is not a valid certificate,
# put here the path to the certificate so it can be verified
SERVER_CERT = /path/to/test_certificate.crt
"""

if __name__ == '__main__':
    main()
