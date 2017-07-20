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

import pandas as pd
import numpy.testing as npt

from qiita_core.testing import wait_for_prep_information_job
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.artifact import Artifact
from qiita_db.study import Study
from qiita_db.util import get_mountpoint
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.exceptions import QiitaDBWarning


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
        self.assertEqual(loads(response.body),
                         {'status': 'success', 'message': ''})

        # make sure new artifact created
        wait_for_prep_information_job(self.prep.id)


class ArtifactGetSamplesTest(TestHandlerBase):
    def test_get(self):
        response = self.get('/artifact/samples/', {'ids[]': [4, 5]})
        self.assertEqual(response.code, 200)
        exp = (
            {"status": "success", "msg": "",
             "data":
                {"4": ["1.SKB2.640194", "1.SKM4.640180", "1.SKB3.640195",
                       "1.SKB6.640176", "1.SKD6.640190", "1.SKM6.640187",
                       "1.SKD9.640182", "1.SKM8.640201", "1.SKM2.640199",
                       "1.SKD2.640178", "1.SKB7.640196", "1.SKD4.640185",
                       "1.SKB8.640193", "1.SKM3.640197", "1.SKD5.640186",
                       "1.SKB1.640202", "1.SKM1.640183", "1.SKD1.640179",
                       "1.SKD3.640198", "1.SKB5.640181", "1.SKB4.640189",
                       "1.SKB9.640200", "1.SKM9.640192", "1.SKD8.640184",
                       "1.SKM5.640177", "1.SKM7.640188", "1.SKD7.640191"],
                 "5": ["1.SKB2.640194", "1.SKM4.640180", "1.SKB3.640195",
                       "1.SKB6.640176", "1.SKD6.640190", "1.SKM6.640187",
                       "1.SKD9.640182", "1.SKM8.640201", "1.SKM2.640199",
                       "1.SKD2.640178", "1.SKB7.640196", "1.SKD4.640185",
                       "1.SKB8.640193", "1.SKM3.640197", "1.SKD5.640186",
                       "1.SKB1.640202", "1.SKM1.640183", "1.SKD1.640179",
                       "1.SKD3.640198", "1.SKB5.640181", "1.SKB4.640189",
                       "1.SKB9.640200", "1.SKM9.640192", "1.SKD8.640184",
                       "1.SKM5.640177", "1.SKM7.640188", "1.SKD7.640191"]}})
        self.assertEqual(loads(response.body), exp)


class ArtifactGetInfoTest(TestHandlerBase):
    def test_get(self):
        response = self.get('/artifact/info/', {'ids[]': [6, 7]})
        self.assertEqual(response.code, 200)
        data = [
            {'files': ['1_study_1001_closed_reference_otu_table_Silva.biom'],
             'target_subfragment': ['V4'], 'algorithm': (
                'Pick closed-reference OTUs, QIIMEv1.9.1 | barcode_type 8, '
                'defaults'), 'artifact_id': 6, 'data_type': '16S',
             'timestamp': '2012-10-02 17:30:00', 'parameters': {
                'reference': 2, 'similarity': 0.97, 'sortmerna_e_value': 1,
                'sortmerna_max_pos': 10000, 'input_data': 2, 'threads': 1,
                'sortmerna_coverage': 0.97}, 'name': 'BIOM'},
            {'files': [], 'target_subfragment': ['V4'], 'algorithm': '',
             'artifact_id': 7, 'data_type': '16S',
             'timestamp': '2012-10-02 17:30:00', 'parameters': {},
             'name': 'BIOM'}]
        exp = {'status': 'success', 'msg': '', 'data': data}
        self.assertEqual(loads(response.body), exp)


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
