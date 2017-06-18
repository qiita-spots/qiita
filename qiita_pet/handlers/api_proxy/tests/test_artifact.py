# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from os.path import join, exists, basename
from os import remove, close
from datetime import datetime
from tempfile import mkstemp

import pandas as pd
import numpy.testing as npt
from moi import r_client

from qiita_core.util import qiita_test_checker
from qiita_core.testing import wait_for_prep_information_job
from qiita_db.artifact import Artifact
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.study import Study
from qiita_db.util import get_mountpoint, get_db_files_base_dir
from qiita_db.processing_job import ProcessingJob
from qiita_db.user import User
from qiita_db.software import Command, Parameters, DefaultParameters
from qiita_db.exceptions import QiitaDBWarning
from qiita_pet.handlers.api_proxy.artifact import (
    artifact_get_req, artifact_status_put_req, artifact_graph_get_req,
    artifact_delete_req, artifact_types_get_req, artifact_post_req,
    artifact_summary_get_request, artifact_summary_post_request,
    artifact_patch_request, artifact_get_prep_req, artifact_get_biom_info)


class TestArtifactAPIReadOnly(TestCase):
    def test_artifact_get_req_no_access(self):
        obs = artifact_get_req('demo@microbio.me', 1)
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_artifact_get_req(self):
        obs = artifact_get_req('test@foo.bar', 1)
        exp = {'id': 1,
               'type': 'FASTQ',
               'study': 1,
               'data_type': '18S',
               'timestamp': datetime(2012, 10, 1, 9, 30, 27),
               'visibility': 'private',
               'can_submit_vamps': False,
               'can_submit_ebi': False,
               'processing_parameters': None,
               'ebi_run_accessions': None,
               'is_submitted_vamps': False,
               'parents': [],
               'filepaths': [
                   (1, join(get_mountpoint('raw_data')[0][1],
                    '1_s_G1_L001_sequences.fastq.gz'), 'raw_forward_seqs'),
                   (2,  join(get_mountpoint('raw_data')[0][1],
                    '1_s_G1_L001_sequences_barcodes.fastq.gz'),
                    'raw_barcodes')]
               }
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_ancestors(self):
        obs = artifact_graph_get_req(1, 'ancestors', 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'edge_list': [],
               'node_labels': [(1, 'Raw data 1 - FASTQ')]}
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_descendants(self):
        obs = artifact_graph_get_req(1, 'descendants', 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'node_labels': [(1, 'Raw data 1 - FASTQ'),
                               (3, 'Demultiplexed 2 - Demultiplexed'),
                               (2, 'Demultiplexed 1 - Demultiplexed'),
                               (4, 'BIOM - BIOM'),
                               (5, 'BIOM - BIOM'),
                               (6, 'BIOM - BIOM')],
               'edge_list': [(1, 3), (1, 2), (2, 5), (2, 4), (2, 6)]}
        self.assertEqual(obs['message'], exp['message'])
        self.assertEqual(obs['status'], exp['status'])
        self.assertItemsEqual(obs['node_labels'], exp['node_labels'])
        self.assertItemsEqual(obs['edge_list'], exp['edge_list'])

    def test_artifact_graph_get_req_no_access(self):
        obs = artifact_graph_get_req(1, 'ancestors', 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_bad_direction(self):
        obs = artifact_graph_get_req(1, 'WRONG', 'test@foo.bar')
        exp = {'status': 'error', 'message': 'Unknown directon WRONG'}
        self.assertEqual(obs, exp)

    def test_artifact_types_get_req(self):
        obs = artifact_types_get_req()
        exp = {'message': '',
               'status': 'success',
               'types': [['BIOM', 'BIOM table'],
                         ['Demultiplexed', 'Demultiplexed and QC sequences'],
                         ['FASTA', None],
                         ['FASTA_Sanger', None],
                         ['FASTQ', None],
                         ['SFF', None],
                         ['per_sample_FASTQ', None],
                         ['distance_matrix', 'Distance matrix holding pairwise'
                                             ' distance between samples'],
                         ['rarefaction_curves', 'Rarefaction curves'],
                         ['taxa_summary', 'Taxa summary plots']]}

        self.assertEqual(obs['message'], exp['message'])
        self.assertEqual(obs['status'], exp['status'])
        self.assertItemsEqual(obs['types'], exp['types'])


@qiita_test_checker()
class TestArtifactAPI(TestCase):
    def setUp(self):
        uploads_path = get_mountpoint('uploads')[0][1]
        # Create prep test file to point at
        self.update_fp = join(uploads_path, '1', 'update.txt')
        with open(self.update_fp, 'w') as f:
            f.write("""sample_name\tnew_col\n1.SKD6.640190\tnew_value\n""")

        self._files_to_remove = [self.update_fp]
        self._files_to_remove = []

        # creating temporal files and artifact
        # NOTE: we don't need to remove the artifact created cause it's
        # used to test the delete functionality
        fd, fp = mkstemp(suffix='_seqs.fna')
        close(fd)
        with open(fp, 'w') as f:
            f.write(">1.sid_r4_0 M02034:17:000000000-A5U18:1:1101:15370:1394 "
                    "1:N:0:1 orig_bc=CATGAGCT new_bc=CATGAGCT bc_diffs=0\n"
                    "GTGTGCCAGCAGCCGCGGTAATACGTAGGG\n")
        # 4 Demultiplexed
        filepaths_processed = [(fp, 4)]
        # 1 for default parameters and input data
        exp_params = Parameters.from_default_params(DefaultParameters(1),
                                                    {'input_data': 1})
        self.artifact = Artifact.create(filepaths_processed, "Demultiplexed",
                                        parents=[Artifact(1)],
                                        processing_parameters=exp_params)

    def tearDown(self):
        for fp in self._files_to_remove:
            if exists(fp):
                remove(fp)

        # Replace file if removed as part of function testing
        uploads_path = get_mountpoint('uploads')[0][1]
        fp = join(uploads_path, '1', 'uploaded_file.txt')
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write('')

        r_client.flushdb()

    def test_artifact_summary_get_request(self):
        # Artifact w/o summary
        obs = artifact_summary_get_request('test@foo.bar', 1)
        exp_p_jobs = [
            ['063e553b-327c-4818-ab4a-adfe58e49860', 'Split libraries FASTQ',
             'queued', None, None],
            ['bcc7ebcd-39c1-43e4-af2d-822e3589f14d', 'Split libraries',
             'running', 'demultiplexing', None]]
        exp_files = [
            (1L, '1_s_G1_L001_sequences.fastq.gz (raw forward seqs)'),
            (2L, '1_s_G1_L001_sequences_barcodes.fastq.gz (raw barcodes)')]
        exp = {'status': 'success',
               'message': '',
               'name': 'Raw data 1',
               'processing_parameters': {},
               'summary': None,
               'job': None,
               'processing_jobs': exp_p_jobs,
               'errored_jobs': [],
               'visibility': 'private',
               'buttons': ('<button onclick="if (confirm(\'Are you sure you '
                           'want to make public artifact id: 1?\')) { '
                           'set_artifact_visibility(\'public\', 1) }" '
                           'class="btn btn-primary btn-sm">Make public'
                           '</button> <button onclick="if (confirm(\'Are you '
                           'sure you want to revert to sandbox artifact id: '
                           '1?\')) { set_artifact_visibility(\'sandbox\', 1) '
                           '}" class="btn btn-primary btn-sm">Revert to '
                           'sandbox</button>'),
               'files': exp_files,
               'editable': True,
               'prep_id': 1,
               'study_id': 1}
        self.assertEqual(obs, exp)

        # Artifact with summary being generated
        job = ProcessingJob.create(
            User('test@foo.bar'),
            Parameters.load(Command(7), values_dict={'input_data': 1})
        )
        job._set_status('queued')
        obs = artifact_summary_get_request('test@foo.bar', 1)
        exp = {'status': 'success',
               'message': '',
               'name': 'Raw data 1',
               'processing_parameters': {},
               'summary': None,
               'job': [job.id, 'queued', None],
               'processing_jobs': exp_p_jobs,
               'errored_jobs': [],
               'visibility': 'private',
               'buttons': ('<button onclick="if (confirm(\'Are you sure you '
                           'want to make public artifact id: 1?\')) { '
                           'set_artifact_visibility(\'public\', 1) }" '
                           'class="btn btn-primary btn-sm">Make public'
                           '</button> <button onclick="if (confirm(\'Are you '
                           'sure you want to revert to sandbox artifact id: '
                           '1?\')) { set_artifact_visibility(\'sandbox\', 1) '
                           '}" class="btn btn-primary btn-sm">Revert to '
                           'sandbox</button>'),
               'files': exp_files,
               'editable': True,
               'prep_id': 1,
               'study_id': 1}
        self.assertEqual(obs, exp)

        # Artifact with summary
        fd, fp = mkstemp(suffix=".html")
        close(fd)
        with open(fp, 'w') as f:
            f.write('<b>HTML TEST - not important</b>\n')
        a = Artifact(1)
        a.html_summary_fp = fp
        self._files_to_remove.extend([fp, a.html_summary_fp[1]])
        exp_files.append(
            (a.html_summary_fp[0],
             '%s (html summary)' % basename(a.html_summary_fp[1])))
        obs = artifact_summary_get_request('test@foo.bar', 1)
        exp = {'status': 'success',
               'message': '',
               'name': 'Raw data 1',
               'processing_parameters': {},
               'summary': '<b>HTML TEST - not important</b>\n',
               'job': None,
               'processing_jobs': exp_p_jobs,
               'errored_jobs': [],
               'visibility': 'private',
               'buttons': ('<button onclick="if (confirm(\'Are you sure you '
                           'want to make public artifact id: 1?\')) { '
                           'set_artifact_visibility(\'public\', 1) }" '
                           'class="btn btn-primary btn-sm">Make public'
                           '</button> <button onclick="if (confirm(\'Are you '
                           'sure you want to revert to sandbox artifact id: '
                           '1?\')) { set_artifact_visibility(\'sandbox\', 1) '
                           '}" class="btn btn-primary btn-sm">Revert to '
                           'sandbox</button>'),
               'files': exp_files,
               'editable': True,
               'prep_id': 1,
               'study_id': 1}
        self.assertEqual(obs, exp)

        # No access
        obs = artifact_summary_get_request('demo@microbio.me', 1)
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

        # A non-owner/share user can't see the files
        a.visibility = 'public'
        obs = artifact_summary_get_request('demo@microbio.me', 1)
        exp = {'status': 'success',
               'message': '',
               'name': 'Raw data 1',
               'processing_parameters': {},
               'summary': '<b>HTML TEST - not important</b>\n',
               'job': None,
               'processing_jobs': exp_p_jobs,
               'errored_jobs': [],
               'visibility': 'public',
               'buttons': '',
               'files': [],
               'editable': False,
               'prep_id': 1,
               'study_id': 1}
        self.assertEqual(obs, exp)

        # returnig to private
        a.visibility = 'sandbox'

        # admin gets buttons
        obs = artifact_summary_get_request('admin@foo.bar', 2)
        exp_p_jobs = [
            ['d19f76ee-274e-4c1b-b3a2-a12d73507c55',
             'Pick closed-reference OTUs', 'error', 'generating demux file',
             'Error message']]
        exp_files = [
            (3L, '1_seqs.fna (preprocessed fasta)'),
            (4L, '1_seqs.qual (preprocessed fastq)'),
            (5L, '1_seqs.demux (preprocessed demux)')]
        exp = {'status': 'success',
               'files': exp_files,
               'errored_jobs': [],
               'editable': True,
               'visibility': 'sandbox',
               'job': None,
               'message': '',
               'name': 'Demultiplexed 1',
               'processing_jobs': exp_p_jobs,
               'processing_parameters': {
                   'max_barcode_errors': 1.5, 'sequence_max_n': 0,
                   'max_bad_run_length': 3, 'phred_offset': u'auto',
                   'rev_comp': False, 'phred_quality_threshold': 3,
                   'input_data': 1, 'rev_comp_barcode': False,
                   'rev_comp_mapping_barcodes': False,
                   'min_per_read_length_fraction': 0.75,
                   'barcode_type': u'golay_12'},
               'summary': None,
               'buttons': (
                   '<button onclick="if (confirm(\'Are you sure you want to '
                   'request approval for artifact id: 2?\')) { '
                   'set_artifact_visibility(\'awaiting_approval\', 2) }" '
                   'class="btn btn-primary btn-sm">Request approval</button> '
                   '<a class="btn btn-primary btn-sm" href="/vamps/2"><span '
                   'class="glyphicon glyphicon-export"></span> Submit to '
                   'VAMPS</a>'),
               'study_id': 1,
               'prep_id': 1}
        self.assertEqual(obs, exp)

    def test_artifact_summary_post_request(self):
        # No access
        obs = artifact_summary_post_request('demo@microbio.me', 1)
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

        # Returns already existing job
        job = ProcessingJob.create(
            User('test@foo.bar'),
            Parameters.load(Command(7), values_dict={'input_data': 2})
        )
        job._set_status('queued')
        obs = artifact_summary_post_request('test@foo.bar', 2)
        exp = {'status': 'success',
               'message': '',
               'job': [job.id, 'queued', None]}
        self.assertEqual(obs, exp)

    def test_artifact_patch_request(self):
        obs = artifact_patch_request('test@foo.bar', 'replace',
                                     '/%d/name/' % self.artifact.id,
                                     req_value='NEW_NAME')
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(obs, exp)

        self.assertEqual(Artifact(self.artifact.id).name, 'NEW_NAME')

    def test_artifact_patch_request_errors(self):
        # No access to the study
        obs = artifact_patch_request('demo@microbio.me', 'replace',
                                     '/1/name/', req_value='NEW_NAME')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)
        # Incorrect path parameter
        obs = artifact_patch_request('test@foo.bar', 'replace',
                                     '/1/name/oops/', req_value='NEW_NAME')
        exp = {'status': 'error',
               'message': 'Incorrect path parameter'}
        self.assertEqual(obs, exp)
        # Missing value
        obs = artifact_patch_request('test@foo.bar', 'replace', '/1/name/')
        exp = {'status': 'error',
               'message': 'A value is required'}
        self.assertEqual(obs, exp)
        # Wrong attribute
        obs = artifact_patch_request('test@foo.bar', 'replace', '/1/oops/',
                                     req_value='NEW_NAME')
        exp = {'status': 'error',
               'message': 'Attribute "oops" not found. Please, check the '
                          'path parameter'}
        self.assertEqual(obs, exp)
        # Wrong operation
        obs = artifact_patch_request('test@foo.bar', 'add', '/1/name/',
                                     req_value='NEW_NAME')
        exp = {'status': 'error',
               'message': 'Operation "add" not supported. Current supported '
                          'operations: replace'}
        self.assertEqual(obs, exp)

    def test_artifact_delete_req(self):
        obs = artifact_delete_req(self.artifact.id, 'test@foo.bar')
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(obs, exp)

        # This is needed so the clean up works - this is a distributed system
        # so we need to make sure that all processes are done before we reset
        # the test database
        wait_for_prep_information_job(1)

    def test_artifact_delete_req_no_access(self):
        obs = artifact_delete_req(self.artifact.id, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_artifact_get_prep_req(self):
        obs = artifact_get_prep_req('test@foo.bar', [4])
        exp = {'status': 'success', 'msg': '', 'data': {
            4: ['1.SKB2.640194', '1.SKM4.640180', '1.SKB3.640195',
                '1.SKB6.640176', '1.SKD6.640190', '1.SKM6.640187',
                '1.SKD9.640182', '1.SKM8.640201', '1.SKM2.640199',
                '1.SKD2.640178', '1.SKB7.640196', '1.SKD4.640185',
                '1.SKB8.640193', '1.SKM3.640197', '1.SKD5.640186',
                '1.SKB1.640202', '1.SKM1.640183', '1.SKD1.640179',
                '1.SKD3.640198', '1.SKB5.640181', '1.SKB4.640189',
                '1.SKB9.640200', '1.SKM9.640192', '1.SKD8.640184',
                '1.SKM5.640177', '1.SKM7.640188', '1.SKD7.640191']}}
        self.assertEqual(obs, exp)

        obs = artifact_get_prep_req('demo@microbio.me', [4])
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_artifact_get_biom_info(self):
        bdir = get_db_files_base_dir()

        obs = artifact_get_biom_info('test@foo.bar', [5, 6])
        exp = {'status': 'success', 'msg': '', 'data': {
            5: {'files': [(9, join(bdir, ('processed_data/1_study_1001_closed'
                                          '_reference_otu_table.biom')))],
                'target_subfragment': ['V4'], 'parameters': {
                    'reference': 1, 'similarity': 0.97, 'sortmerna_e_value': 1,
                    'sortmerna_max_pos': 10000, 'input_data': 2, 'threads': 1,
                    'sortmerna_coverage': 0.97},
                'algorithm': ('Pick closed-reference OTUs | Split libraries '
                              'FASTQ (Defaults with reverse complement '
                              'mapping file barcodes)'),
                'timestamp': '2012-10-02 17:30:00',
                'data_type': '18S', 'name': 'BIOM'},
            6: {'files': [(12, join(bdir, (
                    'processed_data/1_study_1001_closed_reference_otu_'
                    'table_Silva.biom')))],
                'target_subfragment': ['V4'], 'parameters': {
                    'reference': 2, 'similarity': 0.97, 'sortmerna_e_value': 1,
                    'sortmerna_max_pos': 10000, 'input_data': 2, 'threads': 1,
                    'sortmerna_coverage': 0.97}, 'algorithm': (
                        'Pick closed-reference OTUs | Split libraries FASTQ '
                        '(Defaults with reverse complement mapping file '
                        'barcodes)'),
                'timestamp': '2012-10-02 17:30:00',
                'data_type': '16S', 'name': 'BIOM'}}}
        self.assertEqual(obs, exp)

        obs = artifact_get_biom_info('demo@microbio.me', [4])
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

        obs = artifact_get_biom_info('test@foo.bar', [7])
        exp = {'status': 'success', 'msg': '', 'data': {7: ''}}
        self.assertEqual(obs, exp)

    def test_artifact_post_req(self):
        # Create new prep template to attach artifact to
        pt = npt.assert_warns(
            QiitaDBWarning, PrepTemplate.create,
            pd.DataFrame({'new_col': {'1.SKD6.640190': 1}}), Study(1), '16S')
        self._files_to_remove.extend([fp for _, fp in pt.get_filepaths()])

        filepaths = {'raw_forward_seqs': 'uploaded_file.txt',
                     'raw_barcodes': 'update.txt'}
        obs = artifact_post_req(
            'test@foo.bar', filepaths, 'FASTQ', 'New Test Artifact', pt.id)
        exp = {'status': 'success',
               'message': ''}
        self.assertEqual(obs, exp)
        wait_for_prep_information_job(pt.id)

        # Test importing an artifact
        # Create new prep template to attach artifact to
        pt = npt.assert_warns(
            QiitaDBWarning, PrepTemplate.create,
            pd.DataFrame({'new_col': {'1.SKD6.640190': 1}}), Study(1), '16S')
        self._files_to_remove.extend([fp for _, fp in pt.get_filepaths()])

        obs = artifact_post_req(
            'test@foo.bar', {}, 'Demultiplexed', 'New Test Artifact 2',
            pt.id, 3)
        exp = {'status': 'success',
               'message': ''}
        self.assertEqual(obs, exp)

        wait_for_prep_information_job(pt.id)
        # Instantiate the artifact to make sure it was made and
        # to clean the environment
        a = Artifact(pt.artifact.id)
        self._files_to_remove.extend([fp for _, fp, _ in a.filepaths])

    def test_artifact_post_req_error(self):
        # Create a new prep template to attach the artifact to
        pt = npt.assert_warns(
            QiitaDBWarning, PrepTemplate.create,
            pd.DataFrame({'new_col': {'1.SKD6.640190': 1}}), Study(1), '16S')
        self._files_to_remove.extend([fp for _, fp in pt.get_filepaths()])

        user_id = 'test@foo.bar'
        filepaths = {'raw_barcodes': 'uploaded_file.txt',
                     'raw_forward_seqs': 'update.txt'}
        artifact_type = "FASTQ"
        name = "TestArtifact"

        # The user doesn't have access to the study
        obs = artifact_post_req("demo@microbio.me", filepaths, artifact_type,
                                name, pt.id)
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

        # A file does not exist
        missing_fps = {'raw_barcodes': 'NOTEXISTS'}
        obs = artifact_post_req(user_id, missing_fps, artifact_type,
                                name, pt.id)
        exp = {'status': 'error',
               'message': 'File does not exist: NOTEXISTS'}
        self.assertEqual(obs, exp)

        # Cleaned filepaths is empty
        empty_fps = {'raw_barcodes': '', 'raw_forward_seqs': ''}
        obs = artifact_post_req(user_id, empty_fps, artifact_type, name, pt.id)
        exp = {'status': 'error',
               'message': "Can't create artifact, no files provided."}
        self.assertEqual(obs, exp)

    def test_artifact_status_put_req(self):
        obs = artifact_status_put_req(1, 'test@foo.bar', 'sandbox')
        exp = {'status': 'success',
               'message': 'Artifact visibility changed to sandbox'}
        self.assertEqual(obs, exp)

    def test_artifact_status_put_req_private(self):
        obs = artifact_status_put_req(1, 'admin@foo.bar', 'private')
        exp = {'status': 'success',
               'message': 'Artifact visibility changed to private'}
        self.assertEqual(obs, exp)

    def test_artifact_status_put_req_private_bad_permissions(self):
        obs = artifact_status_put_req(1, 'test@foo.bar', 'private')
        exp = {'status': 'error',
               'message': 'User does not have permissions to approve change'}
        self.assertEqual(obs, exp)

    def test_artifact_status_put_req_no_access(self):
        obs = artifact_status_put_req(1, 'demo@microbio.me', 'sandbox')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_artifact_status_put_req_unknown_status(self):
        obs = artifact_status_put_req(1, 'test@foo.bar', 'BADSTAT')
        exp = {'status': 'error',
               'message': 'Unknown visiblity value: BADSTAT'}
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    main()
