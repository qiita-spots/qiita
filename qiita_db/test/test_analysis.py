from unittest import TestCase, main
from os import remove
from os.path import exists, join
from datetime import datetime
from shutil import move
import warnings

from future.utils import viewitems
from biom import load_table
import pandas as pd
from functools import partial
import numpy.testing as npt

from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


@qiita_test_checker()
class TestAnalysis(TestCase):
    def setUp(self):
        self.analysis = qdb.analysis.Analysis(1)
        self.portal = qiita_config.portal
        _, self.fp = qdb.util.get_mountpoint("analysis")[0]

        self.get_fp = partial(join, self.fp)
        self.biom_fp = self.get_fp("1_analysis_18S.biom")
        self.map_fp = self.get_fp("1_analysis_mapping.txt")
        self._old_portal = qiita_config.portal
        self.table_fp = None

        # fullpaths for testing
        self.duplicated_samples_not_merged = self.get_fp(
            "not_merged_samples.txt")
        self.map_exp_fp = self.get_fp("1_analysis_mapping_exp.txt")

    def tearDown(self):
        qiita_config.portal = self.portal
        with open(self.biom_fp, 'w') as f:
                f.write("")
        with open(self.map_fp, 'w') as f:
                f.write("")

        fp = self.get_fp('testfile.txt')
        if exists(fp):
            remove(fp)

        if self.table_fp:
            mp = qdb.util.get_mountpoint("processed_data")[0][1]
            if exists(self.table_fp):
                move(self.table_fp,
                     join(mp, "2_study_1001_closed_reference_otu_table.biom"))

        qiita_config.portal = self._old_portal

    def test_lock_check(self):
        for status in ["queued", "running", "public", "completed",
                       "error"]:
            new = qdb.analysis.Analysis.create(
                qdb.user.User("admin@foo.bar"), "newAnalysis",
                "A New Analysis")
            new.status = status
            with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
                new._lock_check()

    def test_lock_check_ok(self):
        self.analysis.status = "in_construction"
        self.analysis._lock_check()

    def test_status_setter_checks(self):
        self.analysis.status = "public"
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.analysis.status = "queued"

    def test_get_by_status(self):
        qiita_config.portal = 'QIITA'
        self.assertEqual(
            qdb.analysis.Analysis.get_by_status('public'), set([]))
        qiita_config.portal = 'EMP'
        self.assertEqual(
            qdb.analysis.Analysis.get_by_status('public'), set([]))

        self.analysis.status = "public"
        qiita_config.portal = 'QIITA'
        self.assertEqual(qdb.analysis.Analysis.get_by_status('public'),
                         {qdb.analysis.Analysis(1)})
        qiita_config.portal = 'EMP'
        self.assertEqual(
            qdb.analysis.Analysis.get_by_status('public'), set([]))

    def test_has_access_public(self):
        self.analysis.status = 'public'
        qiita_config.portal = 'QIITA'
        self.assertTrue(
            self.analysis.has_access(qdb.user.User("demo@microbio.me")))
        qiita_config.portal = 'EMP'
        self.assertFalse(
            self.analysis.has_access(qdb.user.User("demo@microbio.me")))

    def test_has_access_shared(self):
        self.assertTrue(
            self.analysis.has_access(qdb.user.User("shared@foo.bar")))

    def test_has_access_private(self):
        self.assertTrue(
            self.analysis.has_access(qdb.user.User("test@foo.bar")))

    def test_has_access_admin(self):
        qiita_config.portal = 'QIITA'
        self.assertTrue(
            self.analysis.has_access(qdb.user.User("admin@foo.bar")))
        qiita_config.portal = 'EMP'
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.analysis.Analysis(1).has_access(qdb.user.User("admin@foo.bar"))

    def test_has_access_no_access(self):
        self.assertFalse(
            self.analysis.has_access(qdb.user.User("demo@microbio.me")))

    def test_create_nonqiita_portal(self):
        new_id = qdb.util.get_count("qiita.analysis") + 1
        qiita_config.portal = "EMP"
        qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis")

        # make sure portal is associated
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.analysis_portal WHERE analysis_id = %s",
            [new_id])
        self.assertEqual(obs, [[new_id, 2], [new_id, 1]])

    def test_delete(self):
        # successful delete
        total_analyses = qdb.util.get_count("qiita.analysis")
        qdb.analysis.Analysis.delete(1)
        self.assertEqual(total_analyses - 1,
                         qdb.util.get_count("qiita.analysis"))

        # no possible to delete
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.analysis.Analysis.delete(total_analyses + 1)

    def test_retrieve_dropped_samples(self):
        # Create and populate second study to do test with
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "emp_person_id": qdb.study.StudyPerson(2),
            "principal_investigator_id": qdb.study.StudyPerson(3),
            "lab_person_id": qdb.study.StudyPerson(1)
        }
        metadata_dict = {
            'SKB8.640193': {'physical_specimen_location': 'location1',
                            'physical_specimen_remaining': True,
                            'dna_extracted': True,
                            'sample_type': 'type1',
                            'required_sample_info_status': 'received',
                            'collection_timestamp':
                            datetime(2014, 5, 29, 12, 24, 51),
                            'host_subject_id': 'NotIdentified',
                            'Description': 'Test Sample 1',
                            'str_column': 'Value for sample 1',
                            'latitude': 42.42,
                            'longitude': 41.41,
                            'taxon_id': 9606,
                            'scientific_name': 'homo sapiens'},
            'SKD8.640184': {'physical_specimen_location': 'location1',
                            'physical_specimen_remaining': True,
                            'dna_extracted': True,
                            'sample_type': 'type1',
                            'required_sample_info_status': 'received',
                            'collection_timestamp':
                            datetime(2014, 5, 29, 12, 24, 51),
                            'host_subject_id': 'NotIdentified',
                            'Description': 'Test Sample 2',
                            'str_column': 'Value for sample 2',
                            'latitude': 4.2,
                            'longitude': 1.1,
                            'taxon_id': 9606,
                            'scientific_name': 'homo sapiens'},
            'SKB7.640196': {'physical_specimen_location': 'location1',
                            'physical_specimen_remaining': True,
                            'dna_extracted': True,
                            'sample_type': 'type1',
                            'required_sample_info_status': 'received',
                            'collection_timestamp':
                            datetime(2014, 5, 29, 12, 24, 51),
                            'host_subject_id': 'NotIdentified',
                            'Description': 'Test Sample 3',
                            'str_column': 'Value for sample 3',
                            'latitude': 4.8,
                            'longitude': 4.41,
                            'taxon_id': 9606,
                            'scientific_name': 'homo sapiens'},
            }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')

        study = qdb.study.Study.create(
            qdb.user.User("test@foo.bar"), "Test study 2", [1], info)

        qdb.metadata_template.sample_template.SampleTemplate.create(
            metadata, study)

        metadata = pd.DataFrame.from_dict(
            {'SKB8.640193': {'barcode': 'AAAAAAAAAAAA'},
             'SKD8.640184': {'barcode': 'AAAAAAAAAAAC'},
             'SKB7.640196': {'barcode': 'AAAAAAAAAAAG'}},
            orient='index')

        warnings.simplefilter('ignore', qdb.exceptions.QiitaDBWarning)
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, study, "16S")

        mp = qdb.util.get_mountpoint("processed_data")[0][1]
        study_fp = join(mp, "2_study_1001_closed_reference_otu_table.biom")
        artifact = qdb.artifact.Artifact.create([(study_fp, 7)], "BIOM",
                                                prep_template=pt)
        self.table_fp = artifact.filepaths[0][1]

        sql = """INSERT INTO qiita.analysis_sample (analysis_id, artifact_id,
                                                    sample_id)
                 VALUES (1, %s, '2.SKB8.640193'),
                        (1, %s, '2.SKD8.640184'),
                        (1, %s, '2.SKB7.640196')"""
        self.conn_handler.execute(sql, [artifact.id, artifact.id, artifact.id])

        samples = {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'],
                   artifact.id: ['2.SKB8.640193', '2.SKD8.640184']}
        self.analysis._build_biom_tables(samples, 10000)
        exp = {4: {'1.SKM4.640180', '1.SKM9.640192'},
               5: {'1.SKM4.640180', '1.SKM9.640192'},
               6: {'1.SKM4.640180', '1.SKM9.640192'},
               artifact.id: {'2.SKB7.640196'}}
        self.assertEqual(self.analysis.dropped_samples, exp)

    def test_empty_analysis(self):
        analysis = qdb.analysis.Analysis(2)
        # These should be empty as the analysis hasn't started
        self.assertEqual(analysis.biom_tables, {})
        self.assertEqual(analysis.dropped_samples, {})

    def test_retrieve_portal(self):
        self.assertEqual(self.analysis._portals, ["QIITA"])

    def test_retrieve_shared_with(self):
        self.assertEqual(self.analysis.shared_with,
                         [qdb.user.User("shared@foo.bar")])

    def test_retrieve_biom_tables_empty(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        self.assertEqual(new.biom_tables, {})

    def test_set_step_twice(self):
        new_id = qdb.util.get_count("qiita.analysis") + 1
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        new.step = 2
        new.step = 4
        sql = "SELECT * FROM qiita.analysis_workflow WHERE analysis_id = %s"
        obs = self.conn_handler.execute_fetchall(sql, [new_id])
        self.assertEqual(obs, [[new_id, 4]])

    def test_retrieve_step_new(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        with self.assertRaises(ValueError):
            new.step

    def test_retrieve_step_locked(self):
        self.analysis.status = "public"
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.analysis.step = 3

    def test_retrieve_jobs_none(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        self.assertEqual(new.jobs, [])

    def test_retrieve_pmid_none(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        self.assertEqual(new.pmid, None)

    def test_set_pmid(self):
        self.analysis.pmid = "11211221212213"
        self.assertEqual(self.analysis.pmid, "11211221212213")

    def test_retrieve_mapping_file_none(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        obs = new.mapping_file
        self.assertEqual(obs, None)

    # def test_get_parent(self):
    #     raise NotImplementedError()

    # def test_get_children(self):
    #     raise NotImplementedError()

    def test_summary_data(self):
        obs = self.analysis.summary_data()
        exp = {'studies': 1,
               'artifacts': 3,
               'samples': 5}
        self.assertEqual(obs, exp)

    def test_remove_samples_both(self):
        self.analysis.remove_samples(artifacts=(qdb.artifact.Artifact(4), ),
                                     samples=('1.SKB8.640193', ))
        exp = {4: ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180'],
               5: ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180'],
               6: ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180']}
        self.assertItemsEqual(self.analysis.samples, exp)

    def test_remove_samples_samples(self):
        self.analysis.remove_samples(samples=('1.SKD8.640184', ))
        exp = {4: ['1.SKB8.640193', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180'],
               5: ['1.SKB8.640193', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180'],
               6: ['1.SKB8.640193', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180']}
        self.assertItemsEqual(self.analysis.samples, exp)

    def test_remove_samples_artifact(self):
        self.analysis.remove_samples(
            artifacts=(qdb.artifact.Artifact(4), qdb.artifact.Artifact(5)))
        exp = {6: {'1.SKB7.640196', '1.SKB8.640193', '1.SKD8.640184',
                   '1.SKM4.640180', '1.SKM9.640192'}}
        self.assertItemsEqual(self.analysis.samples, exp)

    def test_share(self):
        self.analysis.share(qdb.user.User("admin@foo.bar"))
        exp = [qdb.user.User("shared@foo.bar"), qdb.user.User("admin@foo.bar")]
        self.assertEqual(self.analysis.shared_with, exp)

    def test_unshare(self):
        self.analysis.unshare(qdb.user.User("shared@foo.bar"))
        self.assertEqual(self.analysis.shared_with, [])

    def test_build_files(self):
        npt.assert_warns(qdb.exceptions.QiitaDBWarning,
                         self.analysis.build_files)

        # testing that the generated files have the same sample ids
        biom_ids = load_table(
            self.analysis.biom_tables['18S']).ids(axis='sample')
        mf_ids = qdb.metadata_template.util.load_template_to_dataframe(
            self.analysis.mapping_file, index='#SampleID').index

        self.assertItemsEqual(biom_ids, mf_ids)

        # now that the samples have been prefixed
        exp = ['1.SKM9.640192', '1.SKM4.640180', '1.SKD8.640184',
               '1.SKB8.640193', '1.SKB7.640196']
        self.assertItemsEqual(biom_ids, exp)

    def test_build_files_merge_duplicated_sample_ids(self):
        npt.assert_warns(qdb.exceptions.QiitaDBWarning,
                         self.analysis.build_files,
                         merge_duplicated_sample_ids=True)

        # testing that the generated files have the same sample ids
        biom_ids = []
        for _, fp in viewitems(self.analysis.biom_tables):
            biom_ids.extend(load_table(fp).ids(axis='sample'))
        mf_ids = qdb.metadata_template.util.load_template_to_dataframe(
            self.analysis.mapping_file, index='#SampleID').index
        self.assertItemsEqual(biom_ids, mf_ids)

        # now that the samples have been prefixed
        exp = ['4.1.SKM9.640192', '4.1.SKM4.640180', '4.1.SKD8.640184',
               '4.1.SKB8.640193', '4.1.SKB7.640196',
               '5.1.SKM9.640192', '5.1.SKM4.640180', '5.1.SKD8.640184',
               '5.1.SKB8.640193', '5.1.SKB7.640196',
               '6.1.SKM9.640192', '6.1.SKM4.640180', '6.1.SKD8.640184',
               '6.1.SKB8.640193', '6.1.SKB7.640196']
        self.assertItemsEqual(biom_ids, exp)

    def test_build_files_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.analysis.build_files('string')

        with self.assertRaises(TypeError):
            self.analysis.build_files(100.5)

    def test_build_files_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.analysis.build_files(0)

        with self.assertRaises(ValueError):
            self.analysis.build_files(-10)


@qiita_test_checker()
class TestCollection(TestCase):
    def setUp(self):
        self.collection = qdb.analysis.Collection(1)

    def test_create(self):
        qdb.analysis.Collection.create(
            qdb.user.User('test@foo.bar'), 'TestCollection2', 'Some desc')

        obs = self.conn_handler.execute_fetchall(
            'SELECT * FROM qiita.collection WHERE collection_id = 2')
        exp = [[2, 'test@foo.bar', 'TestCollection2', 'Some desc', 1]]
        self.assertEqual(obs, exp)

    def test_create_no_desc(self):
        qdb.analysis.Collection.create(
            qdb.user.User('test@foo.bar'), 'Test Collection2')

        obs = self.conn_handler.execute_fetchall(
            'SELECT * FROM qiita.collection WHERE collection_id = 2')
        exp = [[2, 'test@foo.bar', 'Test Collection2', None, 1]]
        self.assertEqual(obs, exp)

    def test_delete(self):
        qdb.analysis.Collection.delete(1)

        obs = self.conn_handler.execute_fetchall(
            'SELECT * FROM qiita.collection')
        exp = []
        self.assertEqual(obs, exp)

    def test_delete_public(self):
        self.collection.status = 'public'
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            qdb.analysis.Collection.delete(1)

        obs = self.conn_handler.execute_fetchall(
            'SELECT * FROM qiita.collection')
        exp = [[1, 'test@foo.bar', 'TEST_COLLECTION',
                'collection for testing purposes', 2]]
        self.assertEqual(obs, exp)

    def test_set_name(self):
        self.collection.name = "NeW NaMe 123"
        self.assertEqual(self.collection.name, "NeW NaMe 123")

    def test_set_name_public(self):
        self.collection.status = "public"
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.collection.name = "FAILBOAT"

    def test_set_desc(self):
        self.collection.description = "NeW DeSc 123"
        self.assertEqual(self.collection.description, "NeW DeSc 123")

    def test_set_desc_public(self):
        self.collection.status = "public"
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.collection.description = "FAILBOAT"

    def test_retrieve_owner(self):
        obs = self.collection.owner
        exp = qdb.user.User("test@foo.bar")
        self.assertEqual(obs, exp)

    def test_retrieve_analyses(self):
        obs = self.collection.analyses
        exp = [qdb.analysis.Analysis(1)]
        self.assertEqual(obs, exp)

    def test_retrieve_highlights(self):
        obs = self.collection.highlights
        exp = [qdb.job.Job(1)]
        self.assertEqual(obs, exp)

    def test_retrieve_shared_with(self):
        obs = self.collection.shared_with
        exp = [qdb.user.User("shared@foo.bar")]
        self.assertEqual(obs, exp)

    def test_add_analysis(self):
        self.collection.add_analysis(qdb.analysis.Analysis(2))
        obs = self.collection.analyses
        exp = [qdb.analysis.Analysis(1), qdb.analysis.Analysis(2)]
        self.assertEqual(obs, exp)

    def test_remove_analysis(self):
        self.collection.remove_analysis(qdb.analysis.Analysis(1))
        obs = self.collection.analyses
        exp = []
        self.assertEqual(obs, exp)

    def test_highlight_job(self):
        self.collection.highlight_job(qdb.job.Job(2))
        obs = self.collection.highlights
        exp = [qdb.job.Job(1), qdb.job.Job(2)]
        self.assertEqual(obs, exp)

    def test_remove_highlight(self):
        self.collection.remove_highlight(qdb.job.Job(1))
        obs = self.collection.highlights
        exp = []
        self.assertEqual(obs, exp)

    def test_share(self):
        self.collection.share(qdb.user.User("admin@foo.bar"))
        obs = self.collection.shared_with
        exp = [qdb.user.User("shared@foo.bar"), qdb.user.User("admin@foo.bar")]
        self.assertEqual(obs, exp)

    def test_unshare(self):
        self.collection.unshare(qdb.user.User("shared@foo.bar"))
        obs = self.collection.shared_with
        exp = []
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    main()
