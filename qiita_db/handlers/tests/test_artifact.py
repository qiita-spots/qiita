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
from json import dumps

from tornado.web import HTTPError
import pandas as pd

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
    def setUp(self):
        super(ArtifactHandlerTests, self).setUp()

        fd, self.html_fp = mkstemp(suffix=".html")
        close(fd)
        self._clean_up_files = [self.html_fp]

    def tearDown(self):
        super(ArtifactHandlerTests, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

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
            'analysis': None,
            'processing_parameters': None,
            'files': exp_fps}
        self.assertEqual(loads(obs.body), exp)

        obs = self.get('/qiita_db/artifacts/9/', headers=self.header)
        self.assertEqual(obs.code, 200)
        db_test_raw_dir = qdb.util.get_mountpoint('analysis')[0][1]
        path_builder = partial(join, db_test_raw_dir)
        exp_fps = {"biom": [path_builder('1_analysis_18S.biom')]}
        exp = {
            'name': 'noname',
            'visibility': 'sandbox',
            'type': 'BIOM',
            'data_type': '18S',
            'can_be_submitted_to_ebi': False,
            'ebi_run_accessions': None,
            'can_be_submitted_to_vamps': False,
            'is_submitted_to_vamps': None,
            'prep_information': [],
            'study': None,
            'analysis': 1,
            'processing_parameters': {'biom_table': 8, 'depth': 9000,
                                      'subsample_multinomial': False},
            'files': exp_fps}
        obs = loads(obs.body)
        # The timestamp is genreated at patch time, so we can't check for it
        del obs['timestamp']
        self.assertEqual(obs, exp)

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


class ArtifactAPItestHandlerTests(OauthTestingBase):
    def setUp(self):
        super(ArtifactAPItestHandlerTests, self).setUp()

        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'instrument_model': 'Illumina MiSeq',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}}
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        self.prep_template = \
            qdb.metadata_template.prep_template.PrepTemplate.create(
                metadata, qdb.study.Study(1), "16S")

        self._clean_up_files = []

    def tearDown(self):
        super(ArtifactAPItestHandlerTests, self).tearDown()

        for f in self._clean_up_files:
            if exists(f):
                remove(f)

    def test_post(self):
        fd, fp1 = mkstemp(suffix='_seqs.fastq')
        close(fd)
        self._clean_up_files.append(fp1)
        with open(fp1, 'w') as f:
            f.write("@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 1:N:0:\n"
                    "NACGTAGGGTGCAAGCGTTGTCCGGAATNA\n"
                    "+\n"
                    "#1=DDFFFHHHHHJJJJJJJJJJJJGII#0\n")

        fd, fp2 = mkstemp(suffix='_barcodes.fastq')
        close(fd)
        self._clean_up_files.append(fp2)
        with open(fp2, 'w') as f:
            f.write("@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 2:N:0:\n"
                    "NNNCNNNNNNNNN\n"
                    "+\n"
                    "#############\n")

        data = {'filepaths': dumps([(fp1, 'raw_forward_seqs'),
                                    (fp2, 'raw_barcodes')]),
                'type': "FASTQ",
                'name': "New test artifact",
                'prep': self.prep_template.id}
        obs = self.post('/apitest/artifact/', headers=self.header, data=data)
        self.assertEqual(obs.code, 200)
        obs = loads(obs.body)
        self.assertEqual(obs.keys(), ['artifact'])

        a = qdb.artifact.Artifact(obs['artifact'])
        self._clean_up_files.extend([fp for _, fp, _ in a.filepaths])
        self.assertEqual(a.name, "New test artifact")

    def test_post_error(self):
        data = {'filepaths': dumps([('Do not exist', 'raw_forward_seqs')]),
                'type': "FASTQ",
                'name': "New test artifact",
                'prep': 1}
        obs = self.post('/apitest/artifact/', headers=self.header, data=data)
        self.assertEqual(obs.code, 500)
        self.assertIn("Prep template 1 already has an artifact associated",
                      obs.body)


class ArtifactTypeHandlerTests(OauthTestingBase):
    def test_post_no_header(self):
        obs = self.post('/qiita_db/artifacts/types/', data={})
        self.assertEqual(obs.code, 400)

    def test_post(self):
        data = {'type_name': 'new_type',
                'description': 'some_description',
                'can_be_submitted_to_ebi': False,
                'can_be_submitted_to_vamps': False,
                'filepath_types': dumps([("log", False),
                                         ("raw_forward_seqs", True)])}
        obs = self.post('/qiita_db/artifacts/types/', headers=self.header,
                        data=data)
        self.assertEqual(obs.code, 200)
        self.assertIn(['new_type', 'some_description'],
                      qdb.artifact.Artifact.types())

        obs = self.post('/qiita_db/artifacts/types/', headers=self.header,
                        data=data)
        self.assertEqual(obs.code, 200)


if __name__ == '__main__':
    main()
