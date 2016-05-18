# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main, TestCase
from json import loads
from functools import partial
from os.path import join, exists
from os import close, remove
from tempfile import mkstemp

from tornado.web import HTTPError

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
import qiita_db as qdb
from qiita_db.handlers.artifact import _get_artifact


class UtilTests(TestCase):
    def test_get_artifact(self):
        obs = _get_artifact(1)
        exp = qdb.artifact.Artifact(1)
        self.assertEqual(obs, exp)

        # It does not exist
        with self.assertRaises(HTTPError):
            _get_artifact(100)


class ArtifactHandlerTests(OauthTestingBase):
    def test_get_artifact_does_not_exist(self):
        obs = self.get('/qiita_db/artifacts/100/', headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get_no_header(self):
        obs = self.get('/qiita_db/artifacts/100/')
        self.assertEqual(obs.code, 400)

    def test_get_artifact(self):
        obs = self.get('/qiita_db/artifacts/1/', headers=self.header)
        self.assertEqual(obs.code, 200)
        db_test_raw_dir = qdb.util.get_mountpoint('raw_data')[0][1]
        path_builder = partial(join, db_test_raw_dir)
        exp_fps = {
            "raw_forward_seqs":
                [path_builder('1_s_G1_L001_sequences.fastq.gz')],
            "raw_barcodes":
                [path_builder('1_s_G1_L001_sequences_barcodes.fastq.gz')]}
        exp = {
            'name': 'Raw data 1',
            'timestamp': '2012-10-01 09:30:27',
            'visibility': 'private',
            'type': 'FASTQ',
            'data_type': '18S',
            'can_be_submitted_to_ebi': False,
            'ebi_run_accessions': None,
            'can_be_submitted_to_vamps': False,
            'is_submitted_to_vamps': None,
            'prep_information': [1],
            'study': 1,
            'processing_parameters': None,
            'files': exp_fps}
        self.assertEqual(loads(obs.body), exp)


class ArtifactHandlerTestsReadWrite(OauthTestingBase):
    database = True

    def setUp(self):
        super(ArtifactHandlerTestsReadWrite, self).setUp()

        fd, self.html_fp = mkstemp(suffix=".html")
        close(fd)
        self._clean_up_files = [self.html_fp]

    def tearDown(self):
        super(ArtifactHandlerTestsReadWrite, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    def test_patch(self):
        arguments = {'op': 'add', 'path': '/html_summary/',
                     'value': self.html_fp}
        self.assertIsNone(qdb.artifact.Artifact(1).html_summary_fp)
        obs = self.patch('/qiita_db/artifacts/1/',
                         headers=self.header,
                         data=arguments)
        self.assertEqual(obs.code, 200)
        self.assertIsNotNone(qdb.artifact.Artifact(1).html_summary_fp)

        # Wrong operation
        arguments = {'op': 'wrong', 'path': '/html_summary/',
                     'value': self.html_fp}
        obs = self.patch('/qiita_db/artifacts/1/',
                         headers=self.header,
                         data=arguments)
        self.assertEqual(obs.code, 400)
        self.assertEqual(obs.body, 'Operation "wrong" not supported. Current '
                                   'supported operations: add')

        # Wrong path parameter
        arguments = {'op': 'add', 'path': '/wrong/',
                     'value': self.html_fp}
        obs = self.patch('/qiita_db/artifacts/1/',
                         headers=self.header,
                         data=arguments)
        self.assertEqual(obs.code, 400)
        self.assertEqual(obs.body, 'Incorrect path parameter value')

        # Wrong value parameter
        arguments = {'op': 'add', 'path': '/html_summary/',
                     'value': self.html_fp}
        obs = self.patch('/qiita_db/artifacts/1/',
                         headers=self.header,
                         data=arguments)
        self.assertEqual(obs.code, 500)
        self.assertIn('No such file or directory', obs.body)


if __name__ == '__main__':
    main()
