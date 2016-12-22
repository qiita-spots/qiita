# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main, TestCase
from tempfile import mkstemp
from json import loads, dumps
from datetime import datetime
from os import close, remove, environ
from os.path import exists

from tornado.web import HTTPError
import numpy.testing as npt
import pandas as pd

from qiita_core.testing import wait_for_processing_job
from qiita_db.handlers.tests.oauthbase import OauthTestingBase
import qiita_db as qdb
from qiita_db.handlers.processing_job import _get_job


class UtilTests(TestCase):
    def test_get_job(self):
        obs = _get_job('6d368e16-2242-4cf8-87b4-a5dc40bb890b')
        exp = qdb.processing_job.ProcessingJob(
            '6d368e16-2242-4cf8-87b4-a5dc40bb890b')
        self.assertEqual(obs, exp)

        with self.assertRaises(HTTPError):
            _get_job('do-not-exist')


class JobHandlerTests(OauthTestingBase):
    def test_get_job_does_not_exists(self):
        obs = self.get('/qiita_db/jobs/do-not-exist', headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get(self):
        obs = self.get('/qiita_db/jobs/6d368e16-2242-4cf8-87b4-a5dc40bb890b',
                       headers=self.header)
        self.assertEqual(obs.code, 200)
        cmd = 'Split libraries FASTQ'
        params = {"max_bad_run_length": 3,
                  "min_per_read_length_fraction": 0.75, "sequence_max_n": 0,
                  "rev_comp_barcode": False,
                  "rev_comp_mapping_barcodes": False, "rev_comp": False,
                  "phred_quality_threshold": 3, "barcode_type": "golay_12",
                  "max_barcode_errors": 1.5, "input_data": 1,
                  'phred_offset': 'auto'}
        exp = {'command': cmd, 'parameters': params, 'status': 'success'}
        self.assertEqual(loads(obs.body), exp)

    def test_get_no_header(self):
        obs = self.get('/qiita_db/jobs/6d368e16-2242-4cf8-87b4-a5dc40bb890b')
        self.assertEqual(obs.code, 400)


class HeartbeatHandlerTests(OauthTestingBase):
    def test_post_job_does_not_exists(self):
        obs = self.post('/qiita_db/jobs/do-not-exist/heartbeat/', '',
                        headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_post_job_already_finished(self):
        obs = self.post(
            '/qiita_db/jobs/6d368e16-2242-4cf8-87b4-a5dc40bb890b/heartbeat/',
            '', headers=self.header)
        self.assertEqual(obs.code, 403)
        self.assertEqual(obs.body,
                         "Can't execute heartbeat on job: already completed")

    def test_post(self):
        before = datetime.now()
        obs = self.post(
            '/qiita_db/jobs/bcc7ebcd-39c1-43e4-af2d-822e3589f14d/heartbeat/',
            '', headers=self.header)
        self.assertEqual(obs.code, 200)
        job = qdb.processing_job.ProcessingJob(
            'bcc7ebcd-39c1-43e4-af2d-822e3589f14d')
        self.assertTrue(before < job.heartbeat < datetime.now())

    def test_post_no_header(self):
        obs = self.post(
            '/qiita_db/jobs/bcc7ebcd-39c1-43e4-af2d-822e3589f14d/heartbeat/',
            '')
        self.assertEqual(obs.code, 400)

    def test_post_first_heartbeat(self):
        before = datetime.now()
        job = qdb.processing_job.ProcessingJob(
            '063e553b-327c-4818-ab4a-adfe58e49860')
        self.assertEqual(job.status, 'queued')
        obs = self.post(
            '/qiita_db/jobs/063e553b-327c-4818-ab4a-adfe58e49860/heartbeat/',
            '', headers=self.header)
        self.assertEqual(obs.code, 200)
        self.assertTrue(before < job.heartbeat < datetime.now())
        self.assertEqual(job.status, 'running')


class ActiveStepHandlerTests(OauthTestingBase):
    def test_post_no_header(self):
        obs = self.post(
            '/qiita_db/jobs/063e553b-327c-4818-ab4a-adfe58e49860/step/', '')
        self.assertEqual(obs.code, 400)

    def test_post_job_does_not_exists(self):
        obs = self.post('/qiita_db/jobs/do-not-exist/step/', '',
                        headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_post_non_running_job(self):
        payload = dumps({'step': 'Step 1 of 4: demultiplexing'})
        obs = self.post(
            '/qiita_db/jobs/063e553b-327c-4818-ab4a-adfe58e49860/step/',
            payload, headers=self.header)
        self.assertEqual(obs.code, 403)
        self.assertEqual(obs.body, "Cannot change the step of a job whose "
                                   "status is not 'running'")

    def test_post(self):
        payload = dumps({'step': 'Step 1 of 4: demultiplexing'})
        obs = self.post(
            '/qiita_db/jobs/bcc7ebcd-39c1-43e4-af2d-822e3589f14d/step/',
            payload, headers=self.header)
        self.assertEqual(obs.code, 200)
        job = qdb.processing_job.ProcessingJob(
            'bcc7ebcd-39c1-43e4-af2d-822e3589f14d')
        self.assertEqual(job.step, 'Step 1 of 4: demultiplexing')


class CompleteHandlerTests(OauthTestingBase):
    def setUp(self):
        self._clean_up_files = []
        super(CompleteHandlerTests, self).setUp()

    def tearDown(self):
        super(CompleteHandlerTests, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    def test_post_no_header(self):
        obs = self.post(
            '/qiita_db/jobs/063e553b-327c-4818-ab4a-adfe58e49860/complete/',
            '')
        self.assertEqual(obs.code, 400)

    def test_post_job_does_not_exists(self):
        obs = self.post('/qiita_db/jobs/do-not-exist/complete/', '',
                        headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_post_job_not_running(self):
        payload = dumps({'success': True, 'artifacts': []})
        obs = self.post(
            '/qiita_db/jobs/063e553b-327c-4818-ab4a-adfe58e49860/complete/',
            payload, headers=self.header)
        self.assertEqual(obs.code, 403)
        self.assertEqual(obs.body,
                         "Can't complete job: not in a running state")

    def test_post_job_failure(self):
        pt = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.prep_template.PrepTemplate.create,
            pd.DataFrame({'new_col': {'1.SKD6.640190': 1}}),
            qdb.study.Study(1), '16S')
        job = qdb.processing_job.ProcessingJob.create(
            qdb.user.User('test@foo.bar'),
            qdb.software.Parameters.load(
                qdb.software.Command.get_validator('BIOM'),
                values_dict={'template': pt.id, 'files':
                             dumps({'BIOM': ['file']}),
                             'artifact_type': 'BIOM'}))
        job._set_status('running')

        payload = dumps({'success': False, 'error': 'Job failure'})
        obs = self.post(
            '/qiita_db/jobs/%s/complete/' % job.id,
            payload, headers=self.header)
        self.assertEqual(obs.code, 200)
        wait_for_processing_job(job.id)
        self.assertEqual(job.status, 'error')
        self.assertEqual(job.log,
                         qdb.logger.LogEntry.newest_records(numrecords=1)[0])
        self.assertEqual(job.log.msg, 'Job failure')

    def test_post_job_success(self):
        pt = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.prep_template.PrepTemplate.create,
            pd.DataFrame({'new_col': {'1.SKD6.640190': 1}}),
            qdb.study.Study(1), '16S')
        job = qdb.processing_job.ProcessingJob.create(
            qdb.user.User('test@foo.bar'),
            qdb.software.Parameters.load(
                qdb.software.Command.get_validator('BIOM'),
                values_dict={'template': pt.id, 'files':
                             dumps({'BIOM': ['file']}),
                             'artifact_type': 'BIOM'}))
        job._set_status('running')

        fd, fp = mkstemp(suffix='_table.biom')
        close(fd)
        with open(fp, 'w') as f:
            f.write('\n')

        self._clean_up_files.append(fp)

        exp_artifact_count = qdb.util.get_count('qiita.artifact') + 1
        payload = dumps(
            {'success': True, 'error': '',
             'artifacts': {'OTU table': {'filepaths': [(fp, 'biom')],
                                         'artifact_type': 'BIOM'}}})
        obs = self.post(
            '/qiita_db/jobs/%s/complete/' % job.id,
            payload, headers=self.header)
        wait_for_processing_job(job.id)
        self.assertEqual(obs.code, 200)
        self.assertEqual(job.status, 'success')
        self.assertEqual(qdb.util.get_count('qiita.artifact'),
                         exp_artifact_count)


class ProcessingJobAPItestHandlerTests(OauthTestingBase):
    def test_post_processing_job(self):
        data = {
            'user': 'demo@microbio.me',
            'command': dumps(['QIIME', '1.9.1', 'Pick closed-reference OTUs']),
            'parameters': dumps({"reference": 1,
                                 "sortmerna_e_value": 1,
                                 "sortmerna_max_pos": 10000,
                                 "similarity": 0.97,
                                 "sortmerna_coverage": 0.97,
                                 "threads": 1,
                                 "input_data": 1})
            }

        obs = self.post('/apitest/processing_job/', headers=self.header,
                        data=data)
        self.assertEqual(obs.code, 200)

        obs = loads(obs.body)
        self.assertEqual(obs.keys(), ['job'])
        self.assertIsNotNone(obs['job'])

    def test_post_processing_job_status(self):
        data = {
            'user': 'demo@microbio.me',
            'command': dumps(['QIIME', '1.9.1', 'Pick closed-reference OTUs']),
            'status': 'running',
            'parameters': dumps({"reference": 1,
                                 "sortmerna_e_value": 1,
                                 "sortmerna_max_pos": 10000,
                                 "similarity": 0.97,
                                 "sortmerna_coverage": 0.97,
                                 "threads": 1,
                                 "input_data": 1})
            }

        obs = self.post('/apitest/processing_job/', headers=self.header,
                        data=data)
        self.assertEqual(obs.code, 200)

        obs = loads(obs.body)
        self.assertEqual(obs.keys(), ['job'])
        job_id = obs['job']
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(job_id))
        self.assertEqual(qdb.processing_job.ProcessingJob(job_id).status,
                         'running')

if __name__ == '__main__':
    main()
