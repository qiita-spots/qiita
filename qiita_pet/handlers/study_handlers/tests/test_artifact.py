# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from os.path import exists, join
from os import remove, close
from tempfile import mkstemp
from json import loads
from time import sleep

import pandas as pd
import numpy.testing as npt
from moi import r_client

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.artifact import Artifact
from qiita_db.study import Study
from qiita_db.util import get_mountpoint
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.exceptions import QiitaDBWarning
from qiita_db.processing_job import ProcessingJob


class ArtifactGraphAJAXTests(TestHandlerBase):
    def test_get_ancestors(self):
        response = self.get('/artifact/graph/', {'direction': 'ancestors',
                                                 'artifact_id': 1})
        exp = {'status': 'success',
               'message': '',
               'node_labels': [[1, 'Raw data 1 - FASTQ']],
               'edge_list': []}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

    def test_get_descendants(self):
        response = self.get('/artifact/graph/', {'direction': 'descendants',
                                                 'artifact_id': 1})
        exp = {'status': 'success',
               'message': '',
               'node_labels': [[1, 'Raw data 1 - FASTQ'],
                               [3, 'Demultiplexed 2 - Demultiplexed'],
                               [2, 'Demultiplexed 1 - Demultiplexed'],
                               [4, 'BIOM - BIOM'],
                               [5, 'BIOM - BIOM'],
                               [6, 'BIOM - BIOM']],
               'edge_list': [[1, 3], [1, 2], [2, 4], [2, 5], [2, 6]]}
        self.assertEqual(response.code, 200)
        obs = loads(response.body)
        self.assertEqual(obs['status'], exp['status'])
        self.assertEqual(obs['message'], exp['message'])
        self.assertItemsEqual(obs['node_labels'], exp['node_labels'])
        self.assertItemsEqual(obs['edge_list'], exp['edge_list'])

    def test_get_unknown(self):
        response = self.get('/artifact/graph/', {'direction': 'BAD',
                                                 'artifact_id': 1})
        exp = {'status': 'error',
               'message': 'Unknown directon BAD'}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)


class NewArtifactHandlerTestsReadOnly(TestHandlerBase):
    def test_get(self):
        args = {'study_id': 1, 'prep_template_id': 1}
        response = self.get('/study/new_artifact/', args)
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.body, "")


class NewArtifactHandlerTests(TestHandlerBase):

    def setUp(self):
        super(NewArtifactHandlerTests, self).setUp()
        tmp_dir = join(get_mountpoint('uploads')[0][1], '1')

        # Create prep test file to point at
        fd, prep_fp = mkstemp(dir=tmp_dir, suffix='.txt')
        close(fd)
        with open(prep_fp, 'w') as f:
            f.write("""sample_name\tnew_col\n1.SKD6.640190\tnew_value\n""")
        self.prep = npt.assert_warns(
            QiitaDBWarning, PrepTemplate.create,
            pd.DataFrame({'new_col': {'1.SKD6.640190': 1}}), Study(1), "16S")

        fd, self.fwd_fp = mkstemp(dir=tmp_dir, suffix=".fastq")
        close(fd)
        with open(self.fwd_fp, 'w') as f:
            f.write("@seq\nTACGA\n+ABBBB\n")

        fd, self.barcodes_fp = mkstemp(dir=tmp_dir, suffix=".fastq")
        close(fd)
        with open(self.barcodes_fp, 'w') as f:
            f.write("@seq\nTACGA\n+ABBBB\n")

        self._files_to_remove = [prep_fp, self.fwd_fp, self.barcodes_fp]

    def tearDown(self):
        super(NewArtifactHandlerTests, self).tearDown()

        for fp in self._files_to_remove:
            if exists(fp):
                remove(fp)

        # Replace file if removed as part of function testing
        uploads_path = get_mountpoint('uploads')[0][1]
        fp = join(uploads_path, '1', 'uploaded_file.txt')
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write('')

    def test_post_artifact(self):
        args = {
            'artifact-type': 'FASTQ',
            'name': 'New Artifact Handler test',
            'prep-template-id': self.prep.id,
            'raw_forward_seqs': [self.fwd_fp],
            'raw_barcodes': [self.barcodes_fp],
            'raw_reverse_seqs': [],
            'import-artifact': ''}
        response = self.post('/study/new_artifact/', args)
        self.assertEqual(response.code, 200)

        # make sure new artifact created
        obs = r_client.get('prep_template_%d' % self.prep.id)
        self.assertIsNotNone(obs)
        payload = loads(obs)
        job_id = payload['job_id']
        if payload['is_qiita_job']:
            job = ProcessingJob(job_id)
            while job.status not in ('success', 'error'):
                sleep(0.05)
        else:
            redis_info = loads(r_client.get(job_id))
            while redis_info['status_msg'] == 'Running':
                sleep(0.05)
                redis_info = loads(r_client.get(job_id))


class ArtifactAJAXTests(TestHandlerBase):

    def test_delete_artifact(self):
        response = self.post('/artifact/',
                             {'artifact_id': 2})
        self.assertEqual(response.code, 200)
        # This is needed so the clean up works - this is a distributed system
        # so we need to make sure that all processes are done before we reset
        # the test database
        obs = r_client.get('prep_template_1')
        self.assertIsNotNone(obs)
        payload = loads(obs)
        job_id = payload['job_id']
        if payload['is_qiita_job']:
            job = ProcessingJob(job_id)
            while job.status not in ('success', 'error'):
                sleep(0.05)
        else:
            redis_info = loads(r_client.get(job_id))
            while redis_info['status_msg'] == 'Running':
                sleep(0.05)
                redis_info = loads(r_client.get(job_id))


class ArtifactAdminAJAXTestsReadOnly(TestHandlerBase):
    def test_get_admin(self):
        response = self.get('/admin/artifact/',
                            {'artifact_id': 3})
        self.assertEqual(response.code, 200)

        # checking that proper actions shown
        self.assertIn("Make public</button>", response.body)
        self.assertIn("Revert to sandbox</button>", response.body)
        self.assertIn("Submit to EBI</a>", response.body)
        self.assertIn("Submit to VAMPS</a>", response.body)


class ArtifactAdminAJAXTests(TestHandlerBase):

    def test_post_admin(self):
        response = self.post('/admin/artifact/',
                             {'artifact_id': 3,
                              'visibility': 'sandbox'})
        self.assertEqual(response.code, 200)

        # checking that proper actions shown
        self.assertEqual({"status": "success",
                          "message": "Artifact visibility changed to sandbox"},
                         loads(response.body))

        self.assertEqual(Artifact(3).visibility, 'sandbox')

if __name__ == "__main__":
    main()
