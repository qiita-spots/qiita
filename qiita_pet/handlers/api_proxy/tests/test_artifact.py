# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from datetime import datetime
from os.path import join

from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import qiita_config
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_pet.handlers.api_proxy.artifact import (
    artifact_get_req, artifact_status_put_req, artifact_graph_get_req,
    artifact_delete_req)


@qiita_test_checker()
class TestArtifactAPI(TestCase):
    def tearDown(self):
        Artifact(1).visibility = 'private'

    def test_artifact_get_req(self):
        obs = artifact_get_req(1, 'test@foo.bar')
        exp = {'is_submitted_to_vamps': False,
               'data_type': '18S',
               'can_be_submitted_to_vamps': False,
               'can_be_submitted_to_ebi': False,
               'timestamp': datetime(2012, 10, 1, 9, 30, 27),
               'prep_templates': [1],
               'visibility': 'private',
               'study': 1,
               'processing_parameters': None,
               'ebi_run_accessions': None,
               'parents': [],
               'filepaths': [
                   (1, join(qiita_config.base_data_dir,
                            'raw_data/1_s_G1_L001_sequences.fastq.gz'),
                    'raw_forward_seqs'),
                   (2, join(qiita_config.base_data_dir,
                            'raw_data/1_s_G1_L001_sequences_barcodes.'
                            'fastq.gz'),
                    'raw_barcodes')],
               'artifact_type': 'FASTQ'}
        self.assertEqual(obs, exp)

    def test_artifact_get_req_no_access(self):
        obs = artifact_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_artifact_delete_req(self):
        obs = artifact_delete_req(3, 'test@foo.bar')
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(obs, exp)

        with self.assertRaises(QiitaDBUnknownIDError):
            Artifact(3)

    def test_artifact_delete_req_no_access(self):
        obs = artifact_delete_req(3, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
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
                               (4, 'BIOM - BIOM')],
               'edge_list': [(1, 3), (1, 2), (2, 4)]}
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_no_access(self):
        obs = artifact_graph_get_req(1, 'ancestors', 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_bad_direction(self):
        obs = artifact_graph_get_req(1, 'WRONG', 'test@foo.bar')
        exp = {'status': 'error', 'message': 'Unknown directon WRONG'}
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    main()
