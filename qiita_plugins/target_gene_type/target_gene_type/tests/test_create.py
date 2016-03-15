# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

import httpretty
from qiita_client import QiitaClient

from target_gene_type.create import (
    _create_artifact_run_prefix, _create_artifact_per_sample,
    _create_artifact_demultiplexed, create_artifact)


class CreateTests(TestCase):
    @httpretty.activate
    def setUp(self):
        # Register the URIs for the QiitaClient
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')

        self.qclient = QiitaClient('https://test_server.com', 'client_id',
                                   'client_secret')

    @httpretty.activate
    def test_create_artifact_run_prefix(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )

        prep_info = {"1.S1": {"run_prefix": "prefix1"},
                     "1.S2": {"run_prefix": "prefix1"},
                     "1.S3": {"run_prefix": "prefix2"}}
        files = {'raw_forward_seqs': ['/path/to/prefix1.fastq',
                                      '/path/to/prefix2.fastq'],
                 'raw_barcodes': ['/path/to/prefix1_b.fastq',
                                  '/path/to/prefix2_b.fastq']}
        atype = "FASTQ"
        obs = _create_artifact_run_prefix(
            self.qclient, 'job-id', prep_info, files, atype)
        exp = {'success': True,
               'error': "",
               'artifacts': {
                   None: {'artifact_type': "FASTQ",
                          'filepaths': [
                              ('/path/to/prefix1.fastq', 'raw_forward_seqs'),
                              ('/path/to/prefix2.fastq', 'raw_forward_seqs'),
                              ('/path/to/prefix1_b.fastq', 'raw_barcodes'),
                              ('/path/to/prefix2_b.fastq', 'raw_barcodes')]}}}
        self.assertItemsEqual(obs, exp)

    @httpretty.activate
    def test_create_artifact_run_prefix_single_lane(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )

        prep_info = {"1.S1": {"not_a_run_prefix": "prefix1"},
                     "1.S2": {"not_a_run_prefix": "prefix1"},
                     "1.S3": {"not_a_run_prefix": "prefix2"}}
        files = {'raw_forward_seqs': ['/path/to/prefix1.fastq'],
                 'raw_barcodes': ['/path/to/prefix1_b.fastq']}
        atype = "FASTQ"
        obs = _create_artifact_run_prefix(
            self.qclient, 'job-id', prep_info, files, atype)
        exp = {'success': True,
               'error': "",
               'artifacts': {
                   None: {'artifact_type': "FASTQ",
                          'filepaths': [
                              ('/path/to/prefix1.fastq', 'raw_forward_seqs'),
                              ('/path/to/prefix1_b.fastq', 'raw_barcodes')]}}}
        self.assertItemsEqual(obs, exp)

    @httpretty.activate
    def test_create_artifact_run_prefix_error(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )

        # Filepath type not supported
        prep_info = {"1.S1": {"run_prefix": "prefix1"},
                     "1.S2": {"run_prefix": "prefix1"},
                     "1.S3": {"run_prefix": "prefix2"}}
        files = {'Unknown': ['/path/to/file1.fastq']}
        atype = "FASTQ"
        obs = _create_artifact_run_prefix(
            self.qclient, 'job-id', prep_info, files, atype)
        exp = {'success': False,
               'error': "Filepath type(s) Unknown not supported by artifact "
                        "type FASTQ. Supported filepath types: raw_barcodes, "
                        "raw_forward_seqs, raw_reverse_seqs",
               'artifacts': None}
        self.assertEqual(obs, exp)

        # Number of provided files != Num run prefix values
        files = {'raw_forward_seqs': ['/path/to/file1.fastq'],
                 'raw_barcodes': ['/path/to/file1_b.fastq',
                                  '/path/to/file2_b.fastq',
                                  '/path/to/file3_b.fastq']}
        obs = _create_artifact_run_prefix(
            self.qclient, 'job-id', prep_info, files, atype)
        error = ("Error creating artifact. Offending files:\nraw_forward_seqs:"
                 " The number of provided files (1) doesn't match the number "
                 "of run prefix values in the prep info (2): file1.fastq\n"
                 "raw_barcodes: The number of provided files (3) doesn't "
                 "match the number of run prefix values in the prep info (2): "
                 "file1_b.fastq, file2_b.fastq, file3_b.fastq")
        self.assertFalse(obs['success'])
        self.assertIsNone(obs['artifacts'])
        self.assertItemsEqual(obs['error'].split('\n'), error.split('\n'))

        # File doesn't match any run prefix
        files = {'raw_forward_seqs': ['/path/to/file1.fastq',
                                      '/path/to/prefix2.fastq'],
                 'raw_barcodes': ['/path/to/file1_b.fastq',
                                  '/path/to/prefix2_b.fastq']}
        obs = _create_artifact_run_prefix(
            self.qclient, 'job-id', prep_info, files, atype)
        error = ("Error creating artifact. Offending files:\nraw_forward_seqs:"
                 " The provided files do not match the run prefix values in "
                 "the prep information: file1.fastq\n"
                 "raw_barcodes: The provided files do not match the run "
                 "prefix values in the prep information: file1_b.fastq")
        self.assertFalse(obs['success'])
        self.assertIsNone(obs['artifacts'])
        self.assertItemsEqual(obs['error'].split('\n'), error.split('\n'))

        # A required filepath type is missing
        files = {'raw_forward_seqs': ['/path/to/prefix1.fastq',
                                      '/path/to/prefix2.fastq'],
                 'raw_reverse_seqs': ['/path/to/prefix1_rev.fastq',
                                      '/path/to/prefix2_rev.fastq']}
        obs = _create_artifact_run_prefix(
            self.qclient, 'job-id', prep_info, files, atype)
        exp = {'success': False,
               'error': "Missing required filepath type(s): raw_barcodes",
               'artifacts': None}
        self.assertEqual(obs, exp)

        # No run prefix and more than 1 lane
        prep_info = {"1.S1": {"not_a_run_prefix": "prefix1"},
                     "1.S2": {"not_a_run_prefix": "prefix1"},
                     "1.S3": {"not_a_run_prefix": "prefix2"}}
        files = {'raw_forward_seqs': ['/path/to/prefix1.fastq',
                                      '/path/to/prefix2.fastq'],
                 'raw_barcodes': ['/path/to/prefix1_b.fastq',
                                  '/path/to/prefix2_b.fastq']}
        obs = _create_artifact_run_prefix(
            self.qclient, 'job-id', prep_info, files, atype)
        error = ("Error creating artifact. Offending files:\nraw_forward_seqs:"
                 " Only one file per type is allowed. Please provide the "
                 "column 'run_prefix' if you need more than one file per "
                 "type: prefix1.fastq, prefix2.fastq\n"
                 "raw_barcodes: Only one file per type is allowed. Please "
                 "provide the column 'run_prefix' if you need more than one "
                 "file per type: prefix1_b.fastq, prefix2_b.fastq")
        self.assertFalse(obs['success'])
        self.assertIsNone(obs['artifacts'])
        self.assertItemsEqual(obs['error'].split('\n'), error.split('\n'))

    @httpretty.activate
    def test_create_artifact_per_sample_run_prefix(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )

        prep_info = {"1.S1": {"run_prefix": "prefix1"},
                     "1.S2": {"run_prefix": "prefix2"},
                     "1.S3": {"run_prefix": "prefix3"}}
        files = {'raw_forward_seqs': ['/path/to/prefix1_file.fastq',
                                      '/path/to/prefix2_file.fastq',
                                      '/path/to/prefix3_file.fastq']}
        obs = _create_artifact_per_sample(
            self.qclient, 'job-id', prep_info, files)
        exp = {'success': True,
               'error': "",
               'artifacts': {
                   None: {'artifact_type': "per_sample_FASTQ",
                          'filepaths': [
                              [['/path/to/prefix1_file.fastq',
                                '/path/to/prefix2_file.fastq',
                                '/path/to/prefix3_file.fastq'],
                               'raw_forward_seqs']]
                          }}}
        self.assertEqual(obs, exp)

    @httpretty.activate
    def test_create_artifact_per_sample(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )

        prep_info = {"1.S1": {"not_a_run_prefix": "prefix1"},
                     "1.S2": {"not_a_run_prefix": "prefix1"},
                     "1.S3": {"not_a_run_prefix": "prefix2"}}
        files = {'raw_forward_seqs': ['/path/to/S1_file.fastq',
                                      '/path/to/S2_file.fastq',
                                      '/path/to/S3_file.fastq']}
        obs = _create_artifact_per_sample(
            self.qclient, 'job-id', prep_info, files)
        exp = {'success': True,
               'error': "",
               'artifacts': {
                   None: {'artifact_type': "per_sample_FASTQ",
                          'filepaths': [
                              [['/path/to/S1_file.fastq',
                                '/path/to/S2_file.fastq',
                                '/path/to/S3_file.fastq'], 'raw_forward_seqs']]
                          }}}
        self.assertEqual(obs, exp)

    @httpretty.activate
    def test_create_artifact_per_sample_error(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )

        # Filepath type not supported
        prep_info = {"1.S1": {"run_prefix": "prefix1"},
                     "1.S2": {"run_prefix": "prefix2"},
                     "1.S3": {"run_prefix": "prefix3"}}
        files = {'Unknown': ['/path/to/file1.fastq']}
        obs = _create_artifact_per_sample(
            self.qclient, 'job-id', prep_info, files)
        exp = {'success': False,
               'error': "Filepath type(s) Unknown not supported by artifact "
                        "type per_sample_FASTQ. Supported filepath types: "
                        "raw_forward_seqs, raw_reverse_seqs",
               'artifacts': None}
        self.assertEqual(obs, exp)

        # Missing raw_forward_seqs
        files = {'raw_reverse_seqs': ['/path/to/file1.fastq']}
        obs = _create_artifact_per_sample(
            self.qclient, 'job-id', prep_info, files)
        exp = {'success': False,
               'error': "Missing required filepath type: raw_forward_seqs",
               'artifacts': None}
        self.assertEqual(obs, exp)

        # Count mismatch
        files = {'raw_forward_seqs': ['/path/to/file1.fastq'],
                 'raw_reverse_seqs': ['/path/to/file1.fastq',
                                      '/path/to/file1.fastq']}
        obs = _create_artifact_per_sample(
            self.qclient, 'job-id', prep_info, files)
        exp = {'success': False,
               'error': "The number of provided files doesn't match the "
                        "number of samples (3): 1 raw_forward_seqs, "
                        "2 raw_reverse_seqs (optional, 0 is ok)",
               'artifacts': None}
        self.assertEqual(obs, exp)

        # Run prefix mismatch
        files = {'raw_forward_seqs': ['/path/to/prefix1_fwd.fastq',
                                      '/path/to/prefix2_fwd.fastq',
                                      '/path/to/Aprefix3_fwd.fastq']}
        obs = _create_artifact_per_sample(
            self.qclient, 'job-id', prep_info, files)
        exp = {'success': False,
               'error': "The provided files do not match the run prefix values"
                        " in the prep information. Offending files: "
                        "raw_forward_seqs: Aprefix3_fwd.fastq, "
                        "raw_reverse_seqs: ",
               'artifacts': None}
        self.assertEqual(obs, exp)

        # Non-unique run-prefix values
        prep_info = {"1.S1": {"run_prefix": "prefix1"},
                     "1.S2": {"run_prefix": "prefix1"},
                     "1.S3": {"run_prefix": "prefix3"}}
        obs = _create_artifact_per_sample(
            self.qclient, 'job-id', prep_info, files)
        exp = {'success': False,
               'error': "The values for the column 'run_prefix' are not "
                        "unique for each sample. Repeated values: prefix1 (2)",
               'artifacts': None}
        self.assertEqual(obs, exp)

        # Sample id mismatch
        prep_info = {"1.S1": {"not_a_run_prefix": "prefix1"},
                     "1.S2": {"not_a_run_prefix": "prefix1"},
                     "1.S3": {"not_a_run_prefix": "prefix3"}}
        obs = _create_artifact_per_sample(
            self.qclient, 'job-id', prep_info, files)
        exp = {'success': False,
               'error': "The provided files are not prefixed by sample id. "
                        "Please provide the 'run_prefix' column in your prep "
                        "information. Offending files: raw_forward_seqs: "
                        "prefix1_fwd.fastq, prefix2_fwd.fastq, "
                        "Aprefix3_fwd.fastq, raw_reverse_seqs: ",
               'artifacts': None}
        self.assertEqual(obs, exp)

    @httpretty.activate
    def test_create_artifact_demultipelexed_error(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/jobs/job-id/step/",
            body='{"success": true, "error": ""}'
        )

        # Filepath type not supported
        prep_info = {"1.S1": {"run_prefix": "prefix1"},
                     "1.S2": {"run_prefix": "prefix2"},
                     "1.S3": {"run_prefix": "prefix3"}}
        files = {'Unknown': ['/path/to/file1.fastq']}
        obs = _create_artifact_demultiplexed(
            self.qclient, 'job-id', prep_info, files)
        exp = {'success': False,
               'error': "Filepath type(s) Unknown not supported by artifact "
                        "type Demultiplexed. Supported filepath types: "
                        "log, preprocessed_demux, preprocessed_fasta, "
                        "preprocessed_fastq",
               'artifacts': None}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
