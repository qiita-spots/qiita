# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from os.path import join, exists
from os import remove
from datetime import datetime

import pandas as pd
import numpy.testing as npt

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import qiita_test_checker
from qiita_db.artifact import Artifact
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.study import Study
from qiita_db.util import get_count, get_mountpoint
from qiita_db.exceptions import QiitaDBUnknownIDError, QiitaDBWarning
from qiita_pet.handlers.api_proxy.artifact import (
    artifact_get_req, artifact_status_put_req, artifact_graph_get_req,
    artifact_delete_req, artifact_types_get_req, artifact_post_req)


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
                   (1, join(qiita_config.base_data_dir, 'raw_data',
                    '1_s_G1_L001_sequences.fastq.gz'), 'raw_forward_seqs'),
                   (2,  join(qiita_config.base_data_dir, 'raw_data',
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
                               (5, 'BIOM - BIOM')],
               'edge_list': [(1, 3), (1, 2), (2, 5), (2, 4)]}
        self.assertItemsEqual(obs, exp)

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
                         ['Demultiplexed', 'Demultiplexed and QC sequeneces'],
                         ['FASTA', None],
                         ['FASTA_Sanger', None],
                         ['FASTQ', None],
                         ['SFF', None],
                         ['per_sample_FASTQ', None]]}

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

    def tearDown(self):
        if exists(self.update_fp):
            remove(self.update_fp)

        # Replace file if removed as part of function testing
        uploads_path = get_mountpoint('uploads')[0][1]
        fp = join(uploads_path, '1', 'uploaded_file.txt')
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write('')

    def test_artifact_delete_req(self):
        obs = artifact_delete_req(3, 'test@foo.bar')
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(obs, exp)

        with self.assertRaises(QiitaDBUnknownIDError):
            Artifact(3)

    def test_artifact_delete_req_error(self):
        obs = artifact_delete_req(1, 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Cannot delete artifact 1: it has children: 2, 3'}
        self.assertEqual(obs, exp)

    def test_artifact_delete_req_no_access(self):
        obs = artifact_delete_req(3, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_artifact_post_req(self):
        # Create new prep template to attach artifact to
        new_prep_id = get_count('qiita.prep_template') + 1
        npt.assert_warns(
            QiitaDBWarning, PrepTemplate.create,
            pd.DataFrame({'new_col': {'1.SKD6.640190': 1}}), Study(1), '16S')

        new_artifact_id = get_count('qiita.artifact') + 1
        obs = artifact_post_req(
            'test@foo.bar', {'raw_forward_seqs': ['uploaded_file.txt'],
                             'raw_reverse_seqs': []},
            'per_sample_FASTQ', 'New Test Artifact', new_prep_id)
        exp = {'status': 'success',
               'message': '',
               'artifact': new_artifact_id}
        self.assertEqual(obs, exp)
        # Instantiate the artifact to make sure it was made
        Artifact(new_artifact_id)

    def test_artifact_post_req_bad_file(self):
        # Create new prep template to attach artifact to
        new_prep_id = get_count('qiita.prep_template') + 1
        npt.assert_warns(
            QiitaDBWarning, PrepTemplate.create,
            pd.DataFrame({'new_col': {'1.SKD6.640190': 1}}), Study(1), '16S')

        obs = artifact_post_req(
            'test@foo.bar', {'raw_forward_seqs': ['NOEXIST']},
            'per_sample_FASTQ', 'New Test Artifact', new_prep_id)
        exp = {'status': 'error',
               'message': 'File does not exist: NOEXIST'}
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
