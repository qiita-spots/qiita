# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from tempfile import mkstemp, mkdtemp
from os import close, remove
from os.path import exists, isdir, join, basename
from shutil import rmtree

import numpy as np
from biom import Table, load_table
from biom.util import biom_open
from qiita_client import QiitaClient
import httpretty

from biom_type_plugin.create import create_artifact


class CreateTests(TestCase):
    @httpretty.activate
    def setUp(self):
        # Registewr the URIs for the QiitaClient
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')

        self.qclient = QiitaClient('https://test_server.com', 'client_id',
                                   'client_secret')
        # Create a biom table
        fd, self.biom_fp = mkstemp(suffix=".biom")
        close(fd)
        data = np.asarray([[0, 0, 1], [1, 3, 42]])
        table = Table(data, ['O1', 'O2'], ['1.S1', '1.S2', '1.S3'])
        with biom_open(self.biom_fp, 'w') as f:
            table.to_hdf5(f, "Test")
        self.out_dir = mkdtemp()
        self.parameters = {'template': 1,
                           'files': '{"BIOM": ["%s"]}' % self.biom_fp,
                           'artifact_type': 'BIOM'}

        self._clean_up_files = [self.biom_fp, self.out_dir]

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    @httpretty.activate
    def test_create_artifact_error(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )
        httpretty.register_uri(
            httpretty.GET,
            "https://test_server.com/qiita_db/prep_template/1/data",
            body='{"data": "", "success": false, "error": "Some error"}')

        with self.assertRaises(ValueError):
            create_artifact(self.qclient, 'job-id', self.parameters,
                            self.out_dir)

    def test_create_artifact_unknown_type(self):
        self.parameters['artifact_type'] = 'UNKNOWN'
        obs = create_artifact(self.qclient, 'job-id', self.parameters,
                              self.out_dir)
        exp = {'success': False,
               'error': 'Unknown artifact type UNKNOWN. Supported types: BIOM',
               'artifacts': None}
        self.assertEqual(obs, exp)

    @httpretty.activate
    def test_create_artifact_no_changes(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )
        httpretty.register_uri(
            httpretty.GET,
            "https://test_server.com/qiita_db/prep_template/1/data",
            body='{"data": {"1.S1": {"run_prefix": "S1"}, "1.S2": '
                 '{"run_prefix": "S2"}, "1.S3": {"run_prefix": "S3"}}, '
                 '"success": true, "error": ""}')

        obs = create_artifact(self.qclient, 'job-id', self.parameters,
                              self.out_dir)
        exp = {'success': True,
               'error': '',
               'artifacts': {None: {'artifact_type': 'BIOM',
                                    'filepaths': [self.biom_fp, 'biom']}}}
        self.assertEqual(obs, exp)

    @httpretty.activate
    def test_create_artifact_unknown_samples(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )
        httpretty.register_uri(
            httpretty.GET,
            "https://test_server.com/qiita_db/prep_template/1/data",
            body='{"data": {"1.S11": {"orig_name": "S1"}, "1.S22": '
                 '{"orig_name": "S2"}, "1.S33": {"orig_name": "S3"}}, '
                 '"success": true, "error": ""}')
        obs = create_artifact(self.qclient, 'job-id', self.parameters,
                              self.out_dir)
        exp = {'success': False,
               'error': 'The sample ids in the BIOM table do not match the '
                        'ones in the prep information. Please, provide the '
                        'column "run_prefix" in the prep information to map '
                        'the existing sample ids to the prep information '
                        'sample ids.',
               'artifacts': None}
        self.assertEqual(obs, exp)

    @httpretty.activate
    def test_create_artifact_run_prefix(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )
        httpretty.register_uri(
            httpretty.GET,
            "https://test_server.com/qiita_db/prep_template/1/data",
            body='{"data": {"1.S11": {"run_prefix": "1.S1"}, "1.S22": '
                 '{"run_prefix": "1.S2"}, "1.S33": {"run_prefix": "1.S3"}}, '
                 '"success": true, "error": ""}')

        obs = create_artifact(self.qclient, 'job-id', self.parameters,
                              self.out_dir)
        exp_biom_fp = join(self.out_dir, basename(self.biom_fp))
        self._clean_up_files.append(exp_biom_fp)
        exp = {'success': True,
               'error': '',
               'artifacts': {None: {'artifact_type': 'BIOM',
                                    'filepaths': [exp_biom_fp, 'biom']}}}
        self.assertEqual(obs, exp)
        obs_t = load_table(exp_biom_fp)
        self.assertItemsEqual(obs_t.ids(), ["1.S11", "1.S22", "1.S33"])

    @httpretty.activate
    def test_create_artifact_prefix(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )
        httpretty.register_uri(
            httpretty.GET,
            "https://test_server.com/qiita_db/prep_template/1/data",
            body='{"data": {"1.S1": {"orig_name": "S1"}, "1.S2": '
                 '{"orig_name": "S2"}, "1.S3": {"orig_name": "S3"}}, '
                 '"success": true, "error": ""}')

        fd, biom_fp = mkstemp(suffix=".biom")
        close(fd)
        data = np.asarray([[0, 0, 1], [1, 3, 42]])
        table = Table(data, ['O1', 'O2'], ['S1', 'S2', 'S3'])
        with biom_open(biom_fp, 'w') as f:
            table.to_hdf5(f, "Test")

        self._clean_up_files.append(biom_fp)

        self.parameters['files'] = '{"BIOM": ["%s"]}' % biom_fp

        obs = create_artifact(self.qclient, 'job-id', self.parameters,
                              self.out_dir)
        exp_biom_fp = join(self.out_dir, basename(biom_fp))
        self._clean_up_files.append(exp_biom_fp)
        exp = {'success': True,
               'error': '',
               'artifacts': {None: {'artifact_type': 'BIOM',
                                    'filepaths': [exp_biom_fp, 'biom']}}}
        self.assertEqual(obs, exp)
        obs_t = load_table(exp_biom_fp)
        self.assertItemsEqual(obs_t.ids(), ["1.S1", "1.S2", "1.S3"])

if __name__ == '__main__':
    main()
