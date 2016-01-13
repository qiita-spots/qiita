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

from tgp.qiita_client import QiitaClient
from tgp.util import (system_call, start_heartbeat, update_job_step,
                      complete_job, format_payload)


class UtilTests(TestCase):
    @httpretty.activate
    def setUp(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')
        self.qclient = QiitaClient("https://test_server.com")

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

    @httpretty.activate
    def test_start_heartbeat(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/example-job/step/",
            body='{"success": true, "error": ""}'
        )
        job_id = "example-job"
        new_step = "some new step"
        update_job_step(self.qclient, job_id, new_step)

    @httpretty.activate
    def test_update_job_step(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/example-job/heartbeat/",
            body='{"success": false, "error": ""}'
        )
        job_id = "example-job"
        start_heartbeat(self.qclient, job_id)

    @httpretty.activate
    def test_complete_job(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/example-job/complete/",
            body='{"success": true, "error": ""}'
        )
        job_id = "example-job"
        payload = {
            'success': True, 'error': '',
            'artifacts': [
                {'artifact_type': "Demultiplexed",
                 'filepaths': [("fp1", "preprocessed_fasta"),
                               ("fp2", "preprocessed_fastq")],
                 'can_be_submitted_to_ebi': True,
                 'can_be_submitted_to_vamps': True}]}
        complete_job(self.qclient, job_id, payload)

    def test_format_payload(self):
        ainfo = [
            ("Demultiplexed",
             [("fp1", "preprocessed_fasta"), ("fp2", "preprocessed_fastq")],
             True, True)]
        obs = format_payload(True, artifacts_info=ainfo, error_msg="Ignored")
        exp = {'success': True, 'error': '',
               'artifacts': [{'artifact_type': "Demultiplexed",
                              'filepaths': [("fp1", "preprocessed_fasta"),
                                            ("fp2", "preprocessed_fastq")],
                              'can_be_submitted_to_ebi': True,
                              'can_be_submitted_to_vamps': True}]}
        self.assertEqual(obs, exp)

    def test_format_payload_error(self):
        obs = format_payload(False, error_msg="Some error",
                             artifacts_info=['ignored'])
        exp = {'success': False, 'error': 'Some error', 'artifacts': None}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
