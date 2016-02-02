# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from os.path import join, exists
import datetime

import pandas as pd

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import qiita_test_checker
from qiita_db.artifact import Artifact
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.study import Study
from qiita_db.util import get_count, get_mountpoint
from qiita_pet.handlers.api_proxy.artifact import (
    artifact_graph_get_req, artifact_types_get_req, artifact_post_req,
    artifact_get_req)


@qiita_test_checker()
class TestArtifactAPI(TestCase):
    def tearDown(self):
        uploads_path = get_mountpoint('uploads')[0][1]
        fp = join(uploads_path, 'uploaded_file.txt')
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write('')

        # Create prep test file to point at
        self.update_fp = join(uploads_path, 'update.txt')
        with open(self.update_fp, 'w') as f:
            f.write("""sample_name\tnew_col\n1.SKD6.640190\tnew_value\n""")

    def test_artifact_get_req(self):
        obs = artifact_get_req('test@foo.bar', 1)
        exp = {'id': 1,
               'type': 'FASTQ',
               'study': 1,
               'data_type': '18S',
               'timestamp': datetime.datetime(2012, 10, 1, 9, 30, 27),
               'visibility': 'private',
               'can_submit_vamps': False,
               'can_submit_ebi': False,
               'processing_parameters': None,
               'ebi_run_accessions': None,
               'is_submitted_vamps': None,
               'parents': [],
               'filepaths': [
                   (1, join(qiita_config.base_data_dir, 'raw_data',
                    '1_s_G1_L001_sequences.fastq.gz'), 'raw_forward_seqs'),
                   (2,  join(qiita_config.base_data_dir, 'raw_data',
                    '1_s_G1_L001_sequences_barcodes.fastq.gz'),
                    'raw_barcodes')]
               }
        self.assertEqual(obs, exp)

    def test_artifact_post_req(self):
        # Create new prep template to attach artifact to
        new_prep_id = get_count('qiita.prep_template') + 1
        PrepTemplate.create(pd.DataFrame(
            {'new_col': {'1.SKD6.640190': 1}}), Study(1), '16S')

        new_artifact_id = get_count('qiita.artifact') + 1
        obs = artifact_post_req(
            'test@foo.bar', {'raw_forward_seqs': ['uploaded_file.txt']},
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
        PrepTemplate.create(pd.DataFrame(
            {'new_col': {'1.SKD6.640190': 1}}), Study(1), '16S')

        obs = artifact_post_req(
            'test@foo.bar', {'raw_forward_seqs': ['NOEXIST']},
            'per_sample_FASTQ', 'New Test Artifact', new_prep_id)
        exp = {'status': 'error',
               'message': 'File does not exist: NOEXIST'}
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
               'edge_list': [(1, 3), (1, 2), (2, 4)],
               'node_labels': [(1, 'Raw data 1 - FASTQ'),
                               (3, 'Demultiplexed 2 - Demultiplexed'),
                               (2, 'Demultiplexed 1 - Demultiplexed'),
                               (4, 'BIOM - BIOM')]}
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_bad(self):
        obs = artifact_graph_get_req(1, 'UNKNOWN', 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Unknown directon UNKNOWN'}
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_no_access(self):
        obs = artifact_graph_get_req(1, 'descendants', 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
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
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    main()
