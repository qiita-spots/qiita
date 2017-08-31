# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from tempfile import mkstemp
from os import close, remove
from os.path import basename, exists, relpath
from json import loads

from tornado.web import HTTPError

from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.testing import wait_for_prep_information_job
from qiita_core.util import qiita_test_checker
from qiita_db.user import User
from qiita_db.artifact import Artifact
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Parameters, Command
from qiita_pet.exceptions import QiitaHTTPError
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.artifact_handlers.base_handlers import (
    check_artifact_access, artifact_summary_get_request,
    artifact_summary_post_request, artifact_patch_request,
    artifact_post_req)


@qiita_test_checker()
class TestBaseHandlersUtils(TestCase):
    def setUp(self):
        self._files_to_remove = []
        self.maxDiff = None

    def tearDown(self):
        for fp in self._files_to_remove:
            if exists(fp):
                remove(fp)

    def test_check_artifact_access(self):
        # "Study" artifact
        a = Artifact(1)
        # The user has access
        u = User('test@foo.bar')
        check_artifact_access(u, a)

        # Admin has access to everything
        admin = User('admin@foo.bar')
        check_artifact_access(admin, a)

        # Demo user doesn't have access
        demo_u = User('demo@microbio.me')
        with self.assertRaises(HTTPError):
            check_artifact_access(demo_u, a)

        # "Analysis" artifact
        a = Artifact(8)
        a.visibility = 'private'
        check_artifact_access(u, a)
        check_artifact_access(admin, a)
        with self.assertRaises(HTTPError):
            check_artifact_access(demo_u, a)
        check_artifact_access(User('shared@foo.bar'), a)
        a.visibility = 'public'
        check_artifact_access(demo_u, a)

    def _assert_summary_equal(self, obs, exp):
        "Utility function for testing the artifact summary get request"
        obs_files = obs.pop('files')
        exp_files = exp.pop('files')
        self.assertItemsEqual(obs_files, exp_files)
        obs_jobs = obs.pop('processing_jobs')
        exp_jobs = obs.pop('processing_jobs')
        self.assertItemsEqual(obs_jobs, exp_jobs)
        self.assertEqual(obs, exp)

    def test_artifact_summary_get_request(self):
        user = User('test@foo.bar')
        # Artifact w/o summary
        obs = artifact_summary_get_request(user, 1)
        exp_p_jobs = [
            ['063e553b-327c-4818-ab4a-adfe58e49860', 'Split libraries FASTQ',
             'queued', None, None],
            ['bcc7ebcd-39c1-43e4-af2d-822e3589f14d', 'Split libraries',
             'running', 'demultiplexing', None]]
        exp_files = [
            (1L, '1_s_G1_L001_sequences.fastq.gz (raw forward seqs)'),
            (2L, '1_s_G1_L001_sequences_barcodes.fastq.gz (raw barcodes)')]
        exp = {'name': 'Raw data 1',
               'artifact_id': 1,
               'artifact_timestamp': '2012-10-01 09:10',
               'visibility': 'private',
               'editable': True,
               'buttons': ('<button onclick="if (confirm(\'Are you sure you '
                           'want to make public artifact id: 1?\')) { '
                           'set_artifact_visibility(\'public\', 1) }" '
                           'class="btn btn-primary btn-sm">Make public'
                           '</button> <button onclick="if (confirm(\'Are you '
                           'sure you want to revert to sandbox artifact id: '
                           '1?\')) { set_artifact_visibility(\'sandbox\', 1) '
                           '}" class="btn btn-primary btn-sm">Revert to '
                           'sandbox</button>'),
               'processing_parameters': {},
               'files': exp_files,
               'summary': None,
               'job': None,
               'processing_jobs': exp_p_jobs,
               'errored_jobs': []}
        self.assertEqual(obs, exp)

        # Artifact with summary being generated
        job = ProcessingJob.create(
            User('test@foo.bar'),
            Parameters.load(Command(7), values_dict={'input_data': 1})
        )
        job._set_status('queued')
        obs = artifact_summary_get_request(user, 1)
        exp = {'name': 'Raw data 1',
               'artifact_id': 1,
               'artifact_timestamp': '2012-10-01 09:10',
               'visibility': 'private',
               'editable': True,
               'buttons': ('<button onclick="if (confirm(\'Are you sure you '
                           'want to make public artifact id: 1?\')) { '
                           'set_artifact_visibility(\'public\', 1) }" '
                           'class="btn btn-primary btn-sm">Make public'
                           '</button> <button onclick="if (confirm(\'Are you '
                           'sure you want to revert to sandbox artifact id: '
                           '1?\')) { set_artifact_visibility(\'sandbox\', 1) '
                           '}" class="btn btn-primary btn-sm">Revert to '
                           'sandbox</button>'),
               'processing_parameters': {},
               'files': exp_files,
               'summary': None,
               'job': [job.id, 'queued', None],
               'processing_jobs': exp_p_jobs,
               'errored_jobs': []}
        self.assertEqual(obs, exp)

        # Artifact with summary
        fd, fp = mkstemp(suffix=".html")
        close(fd)
        with open(fp, 'w') as f:
            f.write('<b>HTML TEST - not important</b>\n')
        a = Artifact(1)
        a.set_html_summary(fp)
        self._files_to_remove.extend([fp, a.html_summary_fp[1]])
        exp_files.append(
            (a.html_summary_fp[0],
             '%s (html summary)' % basename(a.html_summary_fp[1])))
        exp_summary_path = relpath(
            a.html_summary_fp[1], qiita_config.base_data_dir)
        obs = artifact_summary_get_request(user, 1)
        exp = {'name': 'Raw data 1',
               'artifact_id': 1,
               'artifact_timestamp': '2012-10-01 09:10',
               'visibility': 'private',
               'editable': True,
               'buttons': ('<button onclick="if (confirm(\'Are you sure you '
                           'want to make public artifact id: 1?\')) { '
                           'set_artifact_visibility(\'public\', 1) }" '
                           'class="btn btn-primary btn-sm">Make public'
                           '</button> <button onclick="if (confirm(\'Are you '
                           'sure you want to revert to sandbox artifact id: '
                           '1?\')) { set_artifact_visibility(\'sandbox\', 1) '
                           '}" class="btn btn-primary btn-sm">Revert to '
                           'sandbox</button>'),
               'processing_parameters': {},
               'files': exp_files,
               'summary': exp_summary_path,
               'job': None,
               'processing_jobs': exp_p_jobs,
               'errored_jobs': []}
        self.assertEqual(obs, exp)

        # No access
        demo_u = User('demo@microbio.me')
        with self.assertRaises(QiitaHTTPError):
            obs = artifact_summary_get_request(demo_u, 1)

        # A non-owner/share user can't see the files
        a.visibility = 'public'
        obs = artifact_summary_get_request(demo_u, 1)
        exp = {'name': 'Raw data 1',
               'artifact_id': 1,
               'artifact_timestamp': '2012-10-01 09:10',
               'visibility': 'public',
               'editable': False,
               'buttons': '',
               'processing_parameters': {},
               'files': [],
               'summary': exp_summary_path,
               'job': None,
               'processing_jobs': exp_p_jobs,
               'errored_jobs': []}
        self.assertEqual(obs, exp)

        # returnig to private
        a.visibility = 'private'

        # admin gets buttons
        obs = artifact_summary_get_request(User('admin@foo.bar'), 2)
        exp_p_jobs = [
            ['d19f76ee-274e-4c1b-b3a2-a12d73507c55',
             'Pick closed-reference OTUs', 'error', 'generating demux file',
             'Error message']]
        exp_files = [
            (3L, '1_seqs.fna (preprocessed fasta)'),
            (4L, '1_seqs.qual (preprocessed fastq)'),
            (5L, '1_seqs.demux (preprocessed demux)')]
        exp = {'name': 'Demultiplexed 1',
               'artifact_id': 2,
               'artifact_timestamp': '2012-10-01 10:10',
               'visibility': 'private',
               'editable': True,
               'buttons': ('<button onclick="if (confirm(\'Are you sure you '
                           'want to make public artifact id: 2?\')) { '
                           'set_artifact_visibility(\'public\', 2) }" '
                           'class="btn btn-primary btn-sm">Make public'
                           '</button> <button onclick="if (confirm(\'Are you '
                           'sure you want to revert to sandbox artifact id: '
                           '2?\')) { set_artifact_visibility(\'sandbox\', 2) '
                           '}" class="btn btn-primary btn-sm">Revert to '
                           'sandbox</button> <a class="btn btn-primary '
                           'btn-sm" href="/ebi_submission/2"><span '
                           'class="glyphicon glyphicon-export"></span> '
                           'Submit to EBI</a> <a class="btn btn-primary '
                           'btn-sm" href="/vamps/2"><span class="glyphicon '
                           'glyphicon-export"></span> Submit to VAMPS</a>'),
               'processing_parameters': {
                   'max_barcode_errors': 1.5, 'sequence_max_n': 0,
                   'max_bad_run_length': 3, 'phred_offset': u'auto',
                   'rev_comp': False, 'phred_quality_threshold': 3,
                   'input_data': 1, 'rev_comp_barcode': False,
                   'rev_comp_mapping_barcodes': False,
                   'min_per_read_length_fraction': 0.75,
                   'barcode_type': u'golay_12'},
               'files': exp_files,
               'summary': None,
               'job': None,
               'processing_jobs': exp_p_jobs,
               'errored_jobs': []}
        self.assertEqual(obs, exp)

        # analysis artifact
        obs = artifact_summary_get_request(user, 8)
        exp = {'name': 'noname',
               'artifact_id': 8,
               # this value changes on build so copy from obs
               'artifact_timestamp': obs['artifact_timestamp'],
               'visibility': 'sandbox',
               'editable': True,
               'buttons': '',
               'processing_parameters': {},
               'files': [(27, 'biom_table.biom (biom)')],
               'summary': None,
               'job': None,
               'processing_jobs': [],
               'errored_jobs': []}
        self.assertEqual(obs, exp)

    def test_artifact_summary_post_request(self):
        # No access
        with self.assertRaises(QiitaHTTPError):
            artifact_summary_post_request(User('demo@microbio.me'), 1)

        # Returns already existing job
        job = ProcessingJob.create(
            User('test@foo.bar'),
            Parameters.load(Command(7), values_dict={'input_data': 2})
        )
        job._set_status('queued')
        obs = artifact_summary_post_request(User('test@foo.bar'), 2)
        exp = {'job': [job.id, 'queued', None]}
        self.assertEqual(obs, exp)

    def test_artifact_post_request(self):
        # No access
        with self.assertRaises(QiitaHTTPError):
            artifact_post_req(User('demo@microbio.me'), 1)

        artifact_post_req(User('test@foo.bar'), 2)
        # Wait until the job is completed
        wait_for_prep_information_job(1)
        # Check that the delete function has been actually called
        obs = r_client.get(loads(r_client.get('prep_template_1'))['job_id'])
        self.assertIn('Cannot delete artifact 2', obs)

    def test_artifact_patch_request(self):
        a = Artifact(1)
        test_user = User('test@foo.bar')
        self.assertEqual(a.name, 'Raw data 1')

        artifact_patch_request(test_user, 1, 'replace', '/name/',
                               req_value='NEW_NAME')
        self.assertEqual(a.name, 'NEW_NAME')

        # Reset the name
        a.name = 'Raw data 1'

        # No access
        with self.assertRaises(QiitaHTTPError):
            artifact_patch_request(User('demo@microbio.me'), 1, 'replace',
                                   '/name/', req_value='NEW_NAME')

        # Incorrect path parameter
        with self.assertRaises(QiitaHTTPError):
            artifact_patch_request(test_user, 1, 'replace',
                                   '/name/wrong/', req_value='NEW_NAME')

        # Missing value
        with self.assertRaises(QiitaHTTPError):
            artifact_patch_request(test_user, 1, 'replace', '/name/')

        # Wrong attribute
        with self.assertRaises(QiitaHTTPError):
            artifact_patch_request(test_user, 1, 'replace',
                                   '/wrong/', req_value='NEW_NAME')

        # Wrong operation
        with self.assertRaises(QiitaHTTPError):
            artifact_patch_request(test_user, 1, 'add', '/name/',
                                   req_value='NEW_NAME')

        # Changing visibility
        self.assertEqual(a.visibility, 'private')
        artifact_patch_request(test_user, 1, 'replace', '/visibility/',
                               req_value='sandbox')
        self.assertEqual(a.visibility, 'sandbox')

        # Admin can change to private
        artifact_patch_request(User('admin@foo.bar'), 1, 'replace',
                               '/visibility/', req_value='private')
        self.assertEqual(a.visibility, 'private')

        # Test user can't change to private
        with self.assertRaises(QiitaHTTPError):
            artifact_patch_request(test_user, 1, 'replace', '/visibility/',
                                   req_value='private')

        # Unkown req value
        with self.assertRaises(QiitaHTTPError):
            artifact_patch_request(test_user, 1, 'replace', '/visibility/',
                                   req_value='wrong')


class TestBaseHandlers(TestHandlerBase):
    def setUp(self):
        super(TestBaseHandlers, self).setUp()
        self._files_to_remove = []

    def tearDown(self):
        super(TestBaseHandlers, self).tearDown()
        for fp in self._files_to_remove:
            if exists(fp):
                remove(fp)

    def test_get_artifact_summary_ajax_handler(self):
        response = self.get('/artifact/1/summary/')
        self.assertEqual(response.code, 200)

    def test_post_artifact_ajax_handler(self):
        response = self.post('/artifact/2/', {})
        self.assertEqual(response.code, 200)
        wait_for_prep_information_job(1)

    def test_patch_artifact_ajax_handler(self):
        a = Artifact(1)
        self.assertEqual(a.name, 'Raw data 1')
        arguments = {'op': 'replace', 'path': '/name/', 'value': 'NEW_NAME'}
        response = self.patch('/artifact/1/', data=arguments)
        self.assertEqual(response.code, 200)
        self.assertEqual(a.name, 'NEW_NAME')
        a.name = 'Raw data 1'

    def test_get_artifact_summary_handler(self):
        a = Artifact(1)
        # Add a summary to the artifact
        fd, fp = mkstemp(suffix=".html")
        close(fd)
        with open(fp, 'w') as f:
            f.write('<b>HTML TEST - not important</b>\n')
        a = Artifact(1)
        a.set_html_summary(fp)
        self._files_to_remove.extend([fp, a.html_summary_fp[1]])

        summary = relpath(a.html_summary_fp[1], qiita_config.base_data_dir)
        response = self.get('/artifact/html_summary/%s' % summary)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, '<b>HTML TEST - not important</b>\n')


if __name__ == '__main__':
    main()
