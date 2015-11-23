# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from datetime import datetime

import qiita_db as qdb
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class ProcessingJobTest(TestCase):
    def setUp(self):
        self.tester1 = qdb.processing_job.ProcessingJob(
            "063e553b-327c-4818-ab4a-adfe58e49860")
        self.tester2 = qdb.processing_job.ProcessingJob(
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d")
        self.tester3 = qdb.processing_job.ProcessingJob(
            "b72369f9-a886-4193-8d3d-f7b504168e75")
        self.tester4 = qdb.processing_job.ProcessingJob(
            "d19f76ee-274e-4c1b-b3a2-a12d73507c55")

    def test_exists(self):
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "063e553b-327c-4818-ab4a-adfe58e49860"))
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d"))
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "b72369f9-a886-4193-8d3d-f7b504168e75"))
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "d19f76ee-274e-4c1b-b3a2-a12d73507c55"))
        self.assertFalse(qdb.processing_job.ProcessingJob.exists(
            "d19f76ee-274e-4c1b-b3a2-b12d73507c55"))
        self.assertFalse(qdb.processing_job.ProcessingJob.exists(
            "some-other-string"))

    def test_create(self):
        exp_command = qdb.software.Command(1)
        exp_params = qdb.software.Parameters(1, exp_command)
        exp_user = qdb.user.User('test@foo.bar')
        obs = qdb.processing_job.ProcessingJob.create(exp_user, exp_params)
        self.assertEqual(obs.user, exp_user)
        self.assertEqual(obs.command, exp_command)
        self.assertEqual(obs.parameters, exp_params)
        self.assertEqual(obs.status, 'queued')
        self.assertEqual(obs.log, None)
        self.assertEqual(obs.heartbeat, None)
        self.assertEqual(obs.step, None)

    def test_user(self):
        exp_user = qdb.user.User('test@foo.bar')
        self.assertEqual(self.tester1.user, exp_user)
        self.assertEqual(self.tester2.user, exp_user)
        exp_user = qdb.user.User('shared@foo.bar')
        self.assertEqual(self.tester3.user, exp_user)
        self.assertEqual(self.tester4.user, exp_user)

    def test_command(self):
        cmd1 = qdb.software.Command(1)
        cmd2 = qdb.software.Command(2)
        self.assertEqual(self.tester1.command, cmd1)
        self.assertEqual(self.tester2.command, cmd2)
        self.assertEqual(self.tester3.command, cmd1)
        self.assertEqual(self.tester4.command, cmd2)

    def test_parameters(self):
        exp_params = qdb.software.Parameters(1, qdb.software.Command(1))
        self.assertEqual(self.tester1.parameters, exp_params)
        exp_params = qdb.software.Parameters(1, qdb.software.Command(2))
        self.assertEqual(self.tester2.parameters, exp_params)
        exp_params = qdb.software.Parameters(2, qdb.software.Command(1))
        self.assertEqual(self.tester3.parameters, exp_params)
        exp_params = qdb.software.Parameters(1, qdb.software.Command(2))
        self.assertEqual(self.tester4.parameters, exp_params)

    def test_status(self):
        self.assertEqual(self.tester1.status, 'queued')
        self.assertEqual(self.tester2.status, 'running')
        self.assertEqual(self.tester3.status, 'success')
        self.assertEqual(self.tester4.status, 'error')

    def test_status_setter(self):
        self.assertEqual(self.tester1.status, 'queued')
        self.tester1.status = 'running'
        self.assertEqual(self.tester1.status, 'running')
        self.tester1.status = 'error'
        self.assertEqual(self.tester1.status, 'error')
        self.tester1.status = 'running'
        self.assertEqual(self.tester1.status, 'running')
        self.tester1.status = 'success'
        self.assertEqual(self.tester1.status, 'success')

    def test_status_setter_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.tester2.status = 'queued'

        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.tester3.status = 'running'

    def test_log(self):
        self.assertIsNone(self.tester1.log)
        self.assertIsNone(self.tester2.log)
        self.assertIsNone(self.tester3.log)
        self.assertEqual(self.tester4.log, qdb.logger.LogEntry(1))

    def test_log_setter(self):
        self.tester2.status = 'error'
        exp = qdb.logger.LogEntry(1)
        self.tester2.log = exp
        self.assertEqual(self.tester2.log, exp)

    def test_log_setter_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester2.log = qdb.logger.LogEntry(1)

    def test_heartbeat(self):
        self.assertIsNone(self.tester1.heartbeat)
        self.assertEqual(self.tester2.heartbeat,
                         datetime(2015, 11, 22, 21, 00, 00))
        self.assertEqual(self.tester3.heartbeat,
                         datetime(2015, 11, 22, 21, 15, 00))
        self.assertEqual(self.tester4.heartbeat,
                         datetime(2015, 11, 22, 21, 30, 00))

    def test_heartbeat_setter(self):
        self.assertEqual(self.tester2.heartbeat,
                         datetime(2015, 11, 22, 21, 00, 00))
        exp = datetime(2015, 11, 22, 21, 00, 10)
        self.tester2.heartbeat = exp
        self.assertEqual(self.tester2.heartbeat, exp)

    def test_step(self):
        self.assertIsNone(self.tester1.step)
        self.assertEqual(self.tester2.step, 'demultiplexing')
        self.assertIsNone(self.tester3.step)
        self.assertEqual(self.tester4.step, 'generating demux file')

    def test_step_setter(self):
        self.assertEqual(self.tester2.step, 'demultiplexing')
        self.tester2.step = 'generating demux file'
        self.assertEqual(self.tester2.step, 'generating demux file')

    def test_step_setter_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester1.step = 'demultiplexing'

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester3.step = 'demultiplexing'

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester4.step = 'demultiplexing'

if __name__ == '__main__':
    main()
