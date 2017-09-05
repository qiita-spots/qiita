# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os.path import join, dirname, abspath, exists
from os import close, remove
from tempfile import mkstemp

import pandas as pd
import numpy.testing as npt


from qiita_core.util import qiita_test_checker
from qiita_db.software import Software, Parameters
from qiita_db.processing_job import ProcessingJob
from qiita_db.user import User
from qiita_db.study import Study, StudyPerson
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.exceptions import QiitaDBWarning
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_ware.private_plugin import private_task


@qiita_test_checker()
class TestPrivatePlugin(TestCase):
    def setUp(self):
        fd, self.fp = mkstemp(suffix=".txt")
        close(fd)
        with open(self.fp, 'w') as f:
            f.write("sample_name\tnew_col\n"
                    "1.SKD6.640190\tnew_vale")

        self._clean_up_files = [self.fp]

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    def _create_job(self, cmd_name, values_dict):
        user = User('test@foo.bar')
        qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
        cmd = qiita_plugin.get_command(cmd_name)
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
        job = self._create_job('delete_artifact', {'artifact': 1})
        private_task(job.id)
        self.assertEqual(job.status, 'error')
        self.assertIn(
            'Cannot delete artifact 1: it has children: 2, 3', job.log.msg)

        job = self._create_job('delete_artifact', {'artifact': 3})
        private_task(job.id)
        self.assertEqual(job.status, 'success')
        with self.assertRaises(QiitaDBUnknownIDError):
            Artifact(3)

    def test_create_sample_template(self):
        job = self._create_job('create_sample_template', {
            'fp': self.fp, 'study_id': 1, 'is_mapping_file': False,
            'data_type': None})
        private_task(job.id)
        self.assertEqual(job.status, 'error')
        self.assertIn("The 'SampleTemplate' object with attributes (id: 1) "
                      "already exists.", job.log.msg)

    def test_create_sample_template_nonutf8(self):
        fp = join(dirname(abspath(__file__)), 'test_data',
                  'sample_info_utf8_error.txt')
        job = self._create_job('create_sample_template', {
            'fp': fp, 'study_id': 1, 'is_mapping_file': False,
            'data_type': None})
        private_task(job.id)
        self.assertEqual(job.status, 'error')
        self.assertIn(
            'There are invalid (non UTF-8) characters in your information '
            'file. The offending fields and their location (row, column) are '
            'listed below, invalid characters are represented using '
            '&#128062;: "&#128062;collection_timestamp" = (0, 13)',
            job.log.msg)

    def test_update_sample_template(self):
        fd, fp = mkstemp(suffix=".txt")
        close(fd)
        with open(fp, 'w') as f:
            f.write("sample_name\tnew_col\n1.SKD6.640190\tnew_value")
        self._clean_up_files.append(fp)

        job = self._create_job('update_sample_template',
                               {'study': 1, 'template_fp': fp})
        private_task(job.id)
        self.assertEqual(job.status, 'success')
        self.assertEqual(SampleTemplate(1)['1.SKD6.640190']['new_col'],
                         'new_value')

        # TODO: Check that redis has been updated with:
        "Sample names were already prefixed with the study "
        "id.\nThe following columns have been added to the "
        "existing template: new_col\nThere are no "
        "differences between the data stored in the DB and "
        "the new data provided"

    def test_delete_sample_template(self):
        # Error case
        job = self._create_job('delete_sample_template', {'study': 1})
        private_task(job.id)
        self.assertEqual(job.status, 'error')
        self.assertIn("Sample template cannot be erased because there are "
                      "prep templates associated", job.log.msg)

        # Success case
        info = {"timeseries_type_id": '1',
                "metadata_complete": 'true',
                "mixs_compliant": 'true',
                "number_samples_collected": 25,
                "number_samples_promised": 28,
                "study_alias": "TDST",
                "study_description": "Test delete sample template",
                "study_abstract": "Test delete sample template",
                "principal_investigator_id": StudyPerson(1)}
        study = Study.create(User('test@foo.bar'),
                             "Delete Sample Template test", info)
        metadata = pd.DataFrame.from_dict(
            {'Sample1': {'physical_specimen_location': 'location1',
                         'physical_specimen_remaining': 'true',
                         'dna_extracted': 'true',
                         'sample_type': 'type1',
                         'collection_timestamp': '2014-05-29 12:24:15',
                         'host_subject_id': 'NotIdentified',
                         'Description': 'Test Sample 1',
                         'latitude': '42.42',
                         'longitude': '41.41',
                         'taxon_id': '9606',
                         'scientific_name': 'homo sapiens'}},
            orient='index', dtype=str)
        SampleTemplate.create(metadata, study)

        job = self._create_job('delete_sample_template', {'study': study.id})
        private_task(job.id)
        self.assertEqual(job.status, 'success')
        self.assertFalse(SampleTemplate.exists(study.id))

    def test_update_prep_template(self):
        fd, fp = mkstemp(suffix=".txt")
        close(fd)
        with open(fp, 'w') as f:
            f.write("sample_name\tnew_col\n1.SKD6.640190\tnew_value")
        job = self._create_job('update_prep_template', {'prep_template': 1,
                                                        'template_fp': fp})
        private_task(job.id)
        self.assertEqual(job.status, 'success')
        self.assertEqual(PrepTemplate(1)['1.SKD6.640190']['new_col'],
                         'new_value')

        # TODO: Check that redis has been updated with:
        'Sample names were already prefixed with the study '
        'id.\nThe following columns have been added to the '
        'existing template: new_col\nThere are no '
        'differences between the data stored in the DB and '
        'the new data provided'

    def test_delete_sample_or_column(self):
        st = SampleTemplate(1)

        # Delete a sample template column
        job = self._create_job('delete_sample_or_column',
                               {'obj_class': 'SampleTemplate', 'obj_id': 1,
                                'sample_or_col': 'columns',
                                'name': 'season_environment'})
        private_task(job.id)
        self.assertEqual(job.status, 'success')
        self.assertNotIn('season_environment', st.categories())

        # Delete a sample template sample - need to add one
        # sample that we will remove
        npt.assert_warns(
            QiitaDBWarning, st.extend,
            pd.DataFrame.from_dict({'Sample1': {'taxon_id': '9606'}},
                                   orient='index', dtype=str))
        self.assertIn('1.Sample1', st.keys())
        job = self._create_job('delete_sample_or_column',
                               {'obj_class': 'SampleTemplate', 'obj_id': 1,
                                'sample_or_col': 'samples',
                                'name': '1.Sample1'})
        private_task(job.id)
        self.assertEqual(job.status, 'success')
        self.assertNotIn('1.Sample1', st.keys())

        # Delete a prep template column
        pt = PrepTemplate(1)
        job = self._create_job('delete_sample_or_column',
                               {'obj_class': 'PrepTemplate', 'obj_id': 1,
                                'sample_or_col': 'columns',
                                'name': 'target_subfragment'})
        private_task(job.id)
        self.assertEqual(job.status, 'success')
        self.assertNotIn('target_subfragment', pt.categories())

        # Delete a prep template sample
        metadata = pd.DataFrame.from_dict(
            {'1.SKB8.640193': {'barcode': 'GTCCGCAAGTTA',
                               'primer': 'GTGCCAGCMGCCGCGGTAA'},
             '1.SKD8.640184': {'barcode': 'CGTAGAGCTCTC',
                               'primer': 'GTGCCAGCMGCCGCGGTAA'}},
            orient='index', dtype=str)
        pt = npt.assert_warns(QiitaDBWarning, PrepTemplate.create, metadata,
                              Study(1), "16S")
        job = self._create_job('delete_sample_or_column',
                               {'obj_class': 'PrepTemplate', 'obj_id': pt.id,
                                'sample_or_col': 'samples',
                                'name': '1.SKD8.640184'})
        private_task(job.id)
        self.assertNotIn('1.SKD8.640184', pt.keys())

        # Test exceptions
        job = self._create_job('delete_sample_or_column',
                               {'obj_class': 'UnknownClass', 'obj_id': 1,
                                'sample_or_col': 'columns', 'name': 'column'})
        private_task(job.id)
        self.assertEqual(job.status, 'error')
        self.assertIn('Unknown value "UnknownClass". Choose between '
                      '"SampleTemplate" and "PrepTemplate"', job.log.msg)

        job = self._create_job('delete_sample_or_column',
                               {'obj_class': 'SampleTemplate', 'obj_id': 1,
                                'sample_or_col': 'unknown', 'name': 'column'})
        private_task(job.id)
        self.assertEqual(job.status, 'error')
        self.assertIn('Unknown value "unknown". Choose between "samples" '
                      'and "columns"', job.log.msg)


if __name__ == '__main__':
    main()
