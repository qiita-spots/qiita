# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

import pandas as pd
from os import close, remove
from os.path import join, dirname, abspath
from tempfile import mkstemp

from qiita_core.util import qiita_test_checker
from qiita_db.software import Software, Parameters
from qiita_db.processing_job import ProcessingJob
from qiita_db.user import User
from qiita_db.study import Study
from qiita_db.artifact import Artifact
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_ware.private_plugin import (
    private_task, create_sample_template, delete_artifact)


@qiita_test_checker()
class TestPrivatePlugin(TestCase):
    def setUp(self):
        fd, self.fp = mkstemp(suffix=".txt")
        close(fd)
        with open(self.fp, 'w') as f:
            f.write("sample_name\tnew_col\n"
                    "1.SKD6.640190\tnew_vale")

        self._clean_up_files = [self.fp]

    def _create_job(self, cmd, values_dict):
        user = User('test@foo.bar')
        qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
        cmd = qiita_plugin.get_command('copy_artifact')
        params = Parameters.load(cmd, values_dict=values_dict)
        job = ProcessingJob.create(user, params)
        job._set_status('queued')
        return job

    def test_copy_artifact(self):
        # Failure test
        job = self._create_job('copy_artifact',
                               {'artifact': 1, 'prep_template': 1})

        private_task(job.id)
        self.assertEqual(job.status, 'error')
        self.assertIn("Prep template 1 already has an artifact associated",
                      job.log.msg)

        # Success test
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'instrument_model': 'Illumina MiSeq',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}}
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        prep = PrepTemplate.create(metadata, Study(1), "16S")
        job = self._create_job('copy_artifact', {'artifact': 1,
                                                 'prep_template': prep.id})
        private_task(job.id)
        self.assertEqual(job.status, 'success')

    def test_delete_artifact(self):
        obs = delete_artifact(1)
        exp = {'status': 'danger',
               'message': 'Cannot delete artifact 1: it has children: 2, 3'}
        self.assertEqual(obs, exp)

        obs = delete_artifact(3)
        exp = {'status': 'success',
               'message': ''}
        self.assertEqual(obs, exp)

        with self.assertRaises(QiitaDBUnknownIDError):
            Artifact(3)

    def test_create_sample_template(self):
        obs = create_sample_template(self.fp, Study(1), False)
        exp = {'status': 'danger',
               'message': "The 'SampleTemplate' object with attributes "
                          "(id: 1) already exists."}
        self.assertEqual(obs, exp)

    def test_create_sample_template_nonutf8(self):
        fp = join(dirname(abspath(__file__)), 'test_data',
                  'sample_info_utf8_error.txt')
        obs = create_sample_template(fp, Study(1), False)
        exp = {'status': 'danger',
               'message': 'There are invalid (non UTF-8) characters in your '
                          'information file. The offending fields and their '
                          'location (row, column) are listed below, invalid '
                          'characters are represented using &#128062;: '
                          '"&#128062;collection_timestamp" = (0, 13)'}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
