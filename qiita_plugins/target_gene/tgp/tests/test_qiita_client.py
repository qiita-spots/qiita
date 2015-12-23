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
    @httpretty.activate
    def setUp(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')
        self.tester = QiitaClient("https://test_server.com")
        self._clean_up_files = []
        self._old_fp = environ.get('QP_TARGET_GENE_CONFIG_FP')

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)
        if self._old_fp:
            environ['QP_TARGET_GENE_CONFIG_FP'] = self._old_fp
        else:
            del environ['QP_TARGET_GENE_CONFIG_FP']

    @httpretty.activate
    def test_init(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')
        obs = QiitaClient("https://test_server.com")
        self.assertEqual(obs._server_url, "https://test_server.com")
        self.assertTrue(obs._verify)

    @httpretty.activate
    def test_init_cert(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')
        fd, cert_fp = mkstemp()
        close(fd)
        with open(cert_fp, 'w') as f:
            f.write(CERT_FP)
        fd, conf_fp = mkstemp()
        close(fd)
        with open(conf_fp, 'w') as f:
            f.write(CONF_FP % cert_fp)

        self._clean_up_files.append(conf_fp)

        environ['QP_TARGET_GENE_CONFIG_FP'] = conf_fp
        obs = QiitaClient("https://test_server.com")

        self.assertEqual(obs._server_url, "https://test_server.com")
        self.assertEqual(obs._verify, cert_fp)

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
SERVER_CERT = %s

# Oauth2 plugin configuration
CLIENT_ID = client_id
CLIENT_SECRET = client_secret
"""

CERT_FP = """-----BEGIN CERTIFICATE-----
MIIDVjCCAj4CCQCP4XnDqToF2zANBgkqhkiG9w0BAQUFADBtMQswCQYDVQQGEwJV
UzETMBEGA1UECBMKQ2FsaWZvcm5pYTESMBAGA1UEBxMJU2FuIERpZWdvMQ0wCwYD
VQQKEwRVQ1NEMRIwEAYDVQQLEwlLbmlnaHRMYWIxEjAQBgNVBAMTCWxvY2FsaG9z
dDAeFw0xNTEyMTgyMjE3MzBaFw0xNjEyMTcyMjE3MzBaMG0xCzAJBgNVBAYTAlVT
MRMwEQYDVQQIEwpDYWxpZm9ybmlhMRIwEAYDVQQHEwlTYW4gRGllZ28xDTALBgNV
BAoTBFVDU0QxEjAQBgNVBAsTCUtuaWdodExhYjESMBAGA1UEAxMJbG9jYWxob3N0
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt1ggW4M/l3Wpru4+2Cro
nnqaUWD0ImLnkdAbmDjhGiCdKqdb8yzLeKipGaRY383gd5vMWHsKB1I3t+EzFWiY
fxd12Evx6MUIXVZSkdConk+8xlmJ5ba1Hgy7qzErY7+HOtgqm1ylyqTuOZyv3Umv
0W6ETLVz/alfzxTlqAkvuJn7I7RrbY81I3b5SOUxJTtj9pPwkZtVOD0ha3FH0LBu
lE4oi6rQQhzIbUDWLITZRCteplV5ikbC3JqaJ7pDiYnOIPnRR0UF+xdyTiOvSNH8
WrKuAdGGN+90PDt8fgQOwptE5l/RGyoJ2on7nlSj5crDtYzXXDYw0DCzuFG12nZV
FwIDAQABMA0GCSqGSIb3DQEBBQUAA4IBAQBTQJ8WYpSfsXsgmDa2uIYX5E+8ECGn
patQJuxYfOEp9knnBBe+QcaBMY6E7uH6EZz2QwS/gdhfY8e8QXw9sh9ZrQKQlIAK
Q5l5qxAtek0C90qdseYWoomBhpmqMUicF0OgecbdZ4X6Tfc4hvN5IXUTMn9ZJEaV
fduah3c7xEkSbHQl6iHnJswNKTc7Amm+BIwuYJjCZxVgKxAgvYzzg/TFU03gqzfE
h7ARs1p4WdHH+WTMqCZq8+sju3Lum4uwjYaiLaFE7psDkWWAYOu6Jv/o0V1zER/S
LzNaDfkm5kq4VURhPMQzdAiVdiTNKDFnLB3erg6wG95q5OiGNO1WYSw2
-----END CERTIFICATE-----"""

if __name__ == '__main__':
    main()
