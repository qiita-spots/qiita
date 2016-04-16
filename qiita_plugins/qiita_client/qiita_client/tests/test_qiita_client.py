# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os.path import exists
from os import remove, close
from tempfile import mkstemp

import httpretty

from qiita_client.qiita_client import QiitaClient, _format_payload


class UtilTests(TestCase):
    def test_format_payload(self):
        ainfo = [
            ("demultiplexed", "Demultiplexed",
             [("fp1", "preprocessed_fasta"), ("fp2", "preprocessed_fastq")])]
        obs = _format_payload(True, artifacts_info=ainfo, error_msg="Ignored")
        exp = {'success': True, 'error': '',
               'artifacts':
                   {'demultiplexed':
                       {'artifact_type': "Demultiplexed",
                        'filepaths': [("fp1", "preprocessed_fasta"),
                                      ("fp2", "preprocessed_fastq")]}}}
        self.assertEqual(obs, exp)

    def test_format_payload_error(self):
        obs = _format_payload(False, error_msg="Some error",
                              artifacts_info=['ignored'])
        exp = {'success': False, 'error': 'Some error', 'artifacts': None}
        self.assertEqual(obs, exp)


class QiitaClientTests(TestCase):
    @httpretty.activate
    def setUp(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')
        self.tester = QiitaClient(
            "https://test_server.com", 'client_id', 'client_secret')
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    @httpretty.activate
    def test_init(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')
        obs = QiitaClient(
            "https://test_server.com", 'client_id', 'client_secret')
        self.assertEqual(obs._server_url, "https://test_server.com")
        self.assertEqual(obs._client_id, "client_id")
        self.assertEqual(obs._client_secret, "client_secret")
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

        self._clean_up_files.append(cert_fp)

        obs = QiitaClient(
            "https://test_server.com", 'client_id', 'client_secret',
            server_cert=cert_fp)

        self.assertEqual(obs._server_url, "https://test_server.com")
        self.assertEqual(obs._client_id, "client_id")
        self.assertEqual(obs._client_secret, "client_secret")
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
        with self.assertRaises(RuntimeError):
            self.tester.get("/qiita_db/artifacts/1/type/")

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
        with self.assertRaises(RuntimeError):
            self.tester.post("/qiita_db/artifacts/1/type/")

    @httpretty.activate
    def test_patch(self):
        httpretty.register_uri(
            httpretty.PATCH,
            "https://test_server.com/qiita_db/artifacts/1/filepaths/",
            body='{"success": true, "error": ""}'
        )
        obs = self.tester.patch(
            '/qiita_db/artifacts/1/filepaths/', 'add',
            '/html_summary/', value='/path/to/html_summary')
        exp = {"success": True, "error": ""}
        self.assertEqual(obs, exp)

    @httpretty.activate
    def test_patch_error(self):
        httpretty.register_uri(
            httpretty.PATCH,
            "https://test_server.com/qiita_db/artifacts/1/filepaths/",
            status=500
        )
        with self.assertRaises(RuntimeError):
            self.tester.patch(
                '/qiita_db/artifacts/1/filepaths/', 'test',
                '/html_summary/', value='/path/to/html_summary')

    def test_patch_value_error(self):
        # Add, replace or test
        with self.assertRaises(ValueError):
            self.tester.patch(
                '/qiita_db/artifacts/1/filepaths/', 'add', '/html_summary/',
                from_p='/fastq/')

        # move or copy
        with self.assertRaises(ValueError):
            self.tester.patch(
                '/qiita_db/artifacts/1/filepaths/', 'move',
                '/html_summary/', value='/path/to/html_summary')

    @httpretty.activate
    def test_start_heartbeat(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/example-job/heartbeat/",
            body='{"success": false, "error": ""}'
        )
        job_id = "example-job"
        self.tester.start_heartbeat(job_id)

    @httpretty.activate
    def test_get_job_info(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://test_server.com/qiita_db/jobs/example-job",
            body='{"success": false, "error": ""}'
        )
        job_id = "example-job"
        self.tester.get_job_info(job_id)

    @httpretty.activate
    def test_update_job_step(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/example-job/step/",
            body='{"success": true, "error": ""}'
        )
        job_id = "example-job"
        new_step = "some new step"
        self.tester.update_job_step(job_id, new_step)

    @httpretty.activate
    def test_complete_job(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/example-job/complete/",
            body="")
        job_id = "example-job"
        ainfo = [
            ("demultiplexed", "Demultiplexed",
             [("fp1", "preprocessed_fasta"), ("fp2", "preprocessed_fastq")])]

        self.tester.complete_job(job_id, True, artifacts_info=ainfo)


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
