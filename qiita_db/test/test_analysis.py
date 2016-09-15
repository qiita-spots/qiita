from unittest import TestCase, main
from tempfile import mkstemp
from os import remove, close
from os.path import exists, join
from shutil import move

from future.utils import viewitems
from biom import load_table
import pandas as pd
from pandas.util.testing import assert_frame_equal
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
        self.biom_fp = self.get_fp("1_analysis_dt-18S_r-1_c-3.biom")
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

    def _create_analyses_with_samples(self):
        """Aux function to create an analysis with samples

        Returns
        -------
        qiita_db.analysis.Analysis

        Notes
        -----
        Replicates the samples contained in Analysis(1) at the moment of
        creation of this function (September 15, 2016)
        """
        new = qdb.analysis.Analysis.create(
            qdb.user.User('demo@microbio.me'), "newAnalysis",
            "A New Analysis")

        new.add_samples({4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                             '1.SKM9.640192', '1.SKM4.640180'],
                         5: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                             '1.SKM9.640192', '1.SKM4.640180'],
                         6: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                             '1.SKM9.640192', '1.SKM4.640180']})
        return new

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
        analysis = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis",
            "A New Analysis")
        analysis.status = "in_construction"
        analysis._lock_check()

    def test_status_setter_checks(self):
        analysis = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis",
            "A New Analysis")
        analysis.status = "public"
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            analysis.status = "queued"

    def test_get_by_status(self):
        qiita_config.portal = 'QIITA'
        self.assertEqual(
            qdb.analysis.Analysis.get_by_status('public'), set([]))
        qiita_config.portal = 'EMP'
        self.assertEqual(
            qdb.analysis.Analysis.get_by_status('public'), set([]))

        qiita_config.portal = 'QIITA'
        analysis = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis",
            "A New Analysis")
        analysis.status = 'public'
        self.assertEqual(qdb.analysis.Analysis.get_by_status('public'),
                         {analysis})
        qiita_config.portal = 'EMP'
        self.assertEqual(
            qdb.analysis.Analysis.get_by_status('public'), set([]))

    def test_has_access_public(self):
        analysis = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis",
            "A New Analysis")
        analysis.status = 'public'
        qiita_config.portal = 'QIITA'
        self.assertTrue(
            analysis.has_access(qdb.user.User("demo@microbio.me")))
        qiita_config.portal = 'EMP'
        self.assertFalse(
            analysis.has_access(qdb.user.User("demo@microbio.me")))

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

    def test_create(self):
        with qdb.sql_connection.TRN:
            sql = "SELECT NOW()"
            qdb.sql_connection.TRN.add(sql)
            time1 = qdb.sql_connection.TRN.execute_fetchlast()

        new_id = qdb.util.get_count("qiita.analysis") + 1
        user = qdb.user.User("admin@foo.bar")
        obs = qdb.analysis.Analysis.create(user, "newAnalysis",
                                           "A New Analysis")

        self.assertEqual(obs.id, new_id)
        self.assertEqual(obs.owner, user)
        self.assertEqual(obs.name, "newAnalysis")
        self.assertEqual(obs._portals, ["QIITA"])
        self.assertTrue(time1 < obs.timestamp)
        self.assertEqual(obs.description, "A New Analysis")
        self.assertEqual(obs.samples, {})
        self.assertEqual(obs.dropped_samples, {})
        self.assertEqual(obs.data_types, [])
        self.assertEqual(obs.shared_with, [])
        self.assertEqual(obs.all_associated_filepath_ids, set())
        self.assertEqual(obs.biom_tables, {})
        self.assertEqual(obs.mapping_file, None)
        self.assertEqual(obs.tgz, None)
        with self.assertRaises(ValueError):
            obs.step
        self.assertEqual(obs.jobs, [])
        self.assertEqual(obs.pmid, None)
        self.assertEqual(obs.status, "in_construction")

    def test_create_nonqiita_portal(self):
        qiita_config.portal = "EMP"
        obs = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis")

        # make sure portal is associated
        self.assertItemsEqual(obs._portals, ["QIITA", "EMP"])

    def test_create_parent(self):
        new_id = qdb.util.get_count("qiita.analysis") + 1
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        self.assertEqual(new.id, new_id)

        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.analysis_chain WHERE child_id = %s"
            qdb.sql_connection.TRN.add(sql, [new_id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
            self.assertEqual(obs, [[1, new_id]])

    def test_create_from_default(self):
        new_id = qdb.util.get_count("qiita.analysis") + 1
        owner = qdb.user.User("test@foo.bar")
        new = qdb.analysis.Analysis.create(
            owner, "newAnalysis", "A New Analysis", from_default=True)
        self.assertEqual(new.id, new_id)
        self.assertEqual(new.step, 3)

        # Make sure samples were transfered properly
        # Magic number 4 -> the id of the artifact where the samples are taken
        # from
        self.assertEqual(owner.default_analysis.samples, {})
        obs = new.samples
        self.assertEqual(obs.keys(), [4])
        exp = ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
               '1.SKM4.640180']
        self.assertItemsEqual(obs[4], exp)

    def test_exists(self):
        qiita_config.portal = 'QIITA'
        self.assertTrue(qdb.analysis.Analysis.exists(1))
        new_id = qdb.util.get_count("qiita.analysis") + 1
        self.assertFalse(qdb.analysis.Analysis.exists(new_id))
        qiita_config.portal = 'EMP'
        self.assertFalse(qdb.analysis.Analysis.exists(1))
        new_id = qdb.util.get_count("qiita.analysis") + 1
        self.assertFalse(qdb.analysis.Analysis.exists(new_id))

    def test_delete(self):
        # successful delete
        new = qdb.analysis.Analysis.create(
            qdb.user.User('demo@microbio.me'), "newAnalysis",
            "A New Analysis")
        self.assertTrue(qdb.analysis.Analysis.exists(new.id))
        qdb.analysis.Analysis.delete(new.id)
        self.assertFalse(qdb.analysis.Analysis.exists(new.id))

        # no possible to delete
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.analysis.Analysis.delete(new.id)

    def test_retrieve_owner(self):
        self.assertEqual(self.analysis.owner, qdb.user.User("test@foo.bar"))

    def test_retrieve_name(self):
        self.assertEqual(self.analysis.name, "SomeAnalysis")

    def test_retrieve_description(self):
        self.assertEqual(self.analysis.description, "A test analysis")

    def test_set_description(self):
        self.analysis.description = "New description"
        self.assertEqual(self.analysis.description, "New description")

    def test_retrieve_samples(self):
        exp = {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                   '1.SKM9.640192', '1.SKM4.640180'],
               5: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                   '1.SKM9.640192', '1.SKM4.640180'],
               6: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                   '1.SKM9.640192', '1.SKM4.640180']}
        self.assertItemsEqual(self.analysis.samples, exp)

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
                            '05/29/14 12:24:51',
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
                            '05/29/14 12:24:51',
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
                            '05/29/14 12:24:51',
                            'host_subject_id': 'NotIdentified',
                            'Description': 'Test Sample 3',
                            'str_column': 'Value for sample 3',
                            'latitude': 4.8,
                            'longitude': 4.41,
                            'taxon_id': 9606,
                            'scientific_name': 'homo sapiens'},
            }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)

        study = qdb.study.Study.create(
            qdb.user.User("test@foo.bar"), "Test study 2", [1], info)

        qdb.metadata_template.sample_template.SampleTemplate.create(
            metadata, study)

        metadata = pd.DataFrame.from_dict(
            {'SKB8.640193': {'barcode': 'AAAAAAAAAAAA'},
             'SKD8.640184': {'barcode': 'AAAAAAAAAAAC'},
             'SKB7.640196': {'barcode': 'AAAAAAAAAAAG'}},
            orient='index', dtype=str)

        pt = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.prep_template.PrepTemplate.create,
            metadata, study, "16S")

        mp = qdb.util.get_mountpoint("processed_data")[0][1]
        study_fp = join(mp, "2_study_1001_closed_reference_otu_table.biom")
        artifact = qdb.artifact.Artifact.create([(study_fp, 7)], "BIOM",
                                                prep_template=pt)
        self.table_fp = artifact.filepaths[0][1]

        new = self._create_analyses_with_samples()

        new.add_samples({artifact.id: ['%s.SKB8.640193' % study.id,
                                       '%s.SKD8.640184' % study.id,
                                       '%s.SKB7.640196' % study.id]})

        grouped_samples = {'18S.1.3': [
            (4, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']),
            (artifact.id, ['%s.SKB8.640193' % study.id,
                           '%s.SKD8.640184' % study.id])]}
        new._build_biom_tables(grouped_samples, 10000)
        exp = {4: {'1.SKM4.640180', '1.SKM9.640192'},
               5: {'1.SKM4.640180', '1.SKM9.640192'},
               6: {'1.SKM4.640180', '1.SKM9.640192'},
               artifact.id: {'%s.SKB7.640196' % study.id}}
        self.assertEqual(new.dropped_samples, exp)

    def test_empty_analysis(self):
        analysis = qdb.analysis.Analysis(2)
        # These should be empty as the analysis hasn't started
        self.assertEqual(analysis.biom_tables, {})
        self.assertEqual(analysis.dropped_samples, {})

    def test_retrieve_portal(self):
        self.assertEqual(self.analysis._portals, ["QIITA"])

    def test_retrieve_data_types(self):
        exp = ['18S', '16S']
        self.assertItemsEqual(self.analysis.data_types, exp)

    def test_retrieve_shared_with(self):
        self.assertEqual(self.analysis.shared_with,
                         [qdb.user.User("shared@foo.bar")])

    def test_retrieve_biom_tables(self):
        exp = {"18S": join(self.fp, "1_analysis_18S.biom")}
        self.assertEqual(self.analysis.biom_tables, exp)

    def test_all_associated_filepaths(self):
        exp = {13, 14, 15, 16}
        self.assertItemsEqual(self.analysis.all_associated_filepath_ids, exp)

    def test_retrieve_biom_tables_empty(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        self.assertEqual(new.biom_tables, {})

    def test_set_step(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis",
            "A New Analysis", qdb.analysis.Analysis(1))
        new.step = 2
        self.assertEqual(new.step, 2)

    def test_set_step_twice(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        new.step = 2
        new.step = 4
        self.assertEqual(new.step, 4)

    def test_retrieve_step(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        new.step = 2
        self.assertEqual(new.step, 2)

    def test_retrieve_step_new(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        with self.assertRaises(ValueError):
            new.step

    def test_retrieve_step_locked(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        new.status = "public"
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            new.step = 3

    def test_retrieve_jobs(self):
        self.assertEqual(self.analysis.jobs,
                         [qdb.job.Job(1), qdb.job.Job(2)])

    def test_retrieve_jobs_none(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        self.assertEqual(new.jobs, [])

    def test_retrieve_pmid(self):
        self.assertEqual(self.analysis.pmid, "121112")

    def test_retrieve_pmid_none(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        self.assertEqual(new.pmid, None)

    def test_set_pmid(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        new.pmid = "11211221212213"
        self.assertEqual(new.pmid, "11211221212213")

    def test_retrieve_mapping_file(self):
        exp = join(self.fp, "1_analysis_mapping.txt")
        obs = self.analysis.mapping_file
        self.assertEqual(obs, exp)
        self.assertTrue(exists(exp))

    def test_retrieve_mapping_file_none(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        obs = new.mapping_file
        self.assertEqual(obs, None)

    def test_retrieve_tgz(self):
        # generating here as the tgz is only generated once the analysis runs
        # to completion (un)successfully
        analysis = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))
        fp = self.get_fp('test.tgz')
        with open(fp, 'w') as f:
            f.write('')
        analysis._add_file(fp, 'tgz')
        self.assertEqual(analysis.tgz, fp)

    def test_retrieve_tgz_none(self):
        self.assertIsNone(self.analysis.tgz)

    def test_generate_tgz(self):
        analysis = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis",
            qdb.analysis.Analysis(1))

        # Raises an error because there are no files attached to it
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            analysis.generate_tgz()

        analysis_mp = qdb.util.get_mountpoint('analysis')[0][1]
        fd, fp = mkstemp(dir=analysis_mp, suffix='.txt')
        close(fd)
        with open(fp, 'w') as f:
            f.write("")
        analysis._add_file(fp, 'plain_text')
        obs_sout, obs_serr, obs_return = analysis.generate_tgz()
        # not testing obs_serr as it will change depending on the system's tar
        # version
        self.assertEqual(obs_sout, "")
        self.assertEqual(obs_return, 0)

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

    def test_add_samples(self):
        new = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis")
        new.add_samples({1: ['1.SKB8.640193', '1.SKD5.640186']})
        obs = new.samples
        self.assertEqual(obs.keys(), [1])
        self.assertItemsEqual(obs[1], ['1.SKB8.640193', '1.SKD5.640186'])

    def test_remove_samples_both(self):
        analysis = self._create_analyses_with_samples()
        analysis.remove_samples(artifacts=(qdb.artifact.Artifact(4), ),
                                samples=('1.SKB8.640193', ))
        exp = {4: ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180'],
               5: ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180', '1.SKB8.640193'],
               6: ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180', '1.SKB8.640193']}
        obs = analysis.samples
        self.assertItemsEqual(obs.keys(), exp.keys())
        for k in obs:
            self.assertItemsEqual(obs[k], exp[k])

    def test_remove_samples_samples(self):
        analysis = self._create_analyses_with_samples()
        analysis.remove_samples(samples=('1.SKD8.640184', ))
        exp = {4: ['1.SKB8.640193', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180'],
               5: ['1.SKB8.640193', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180'],
               6: ['1.SKB8.640193', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180']}
        self.assertItemsEqual(analysis.samples, exp)

    def test_remove_samples_artifact(self):
        analysis = self._create_analyses_with_samples()
        analysis.remove_samples(
            artifacts=(qdb.artifact.Artifact(4), qdb.artifact.Artifact(5)))
        exp = {6: {'1.SKB7.640196', '1.SKB8.640193', '1.SKD8.640184',
                   '1.SKM4.640180', '1.SKM9.640192'}}
        self.assertItemsEqual(analysis.samples, exp)

    def test_share(self):
        analysis = self._create_analyses_with_samples()
        user = qdb.user.User("admin@foo.bar")
        self.assertEqual(analysis.shared_with, [])
        analysis.share(user)
        exp = [user]
        self.assertEqual(analysis.shared_with, exp)

    def test_unshare(self):
        analysis = self._create_analyses_with_samples()
        user = qdb.user.User("admin@foo.bar")
        analysis.share(user)
        exp = [user]
        self.assertEqual(analysis.shared_with, exp)
        analysis.unshare(user)
        self.assertEqual(analysis.shared_with, [])

    def test_build_mapping_file(self):
        analysis = self._create_analyses_with_samples()
        samples = {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']}

        npt.assert_warns(qdb.exceptions.QiitaDBWarning,
                         analysis._build_mapping_file, samples)
        obs = analysis.mapping_file
        exp = self.get_fp("%s_analysis_mapping.txt" % analysis.id)
        self.assertEqual(obs, exp)

        obs = qdb.metadata_template.util.load_template_to_dataframe(
            obs, index='#SampleID')
        exp = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.util.load_template_to_dataframe,
            self.map_exp_fp, index='#SampleID')
        assert_frame_equal(obs, exp)

    def test_build_mapping_file_duplicated_samples_no_merge(self):
        analysis = self._create_analyses_with_samples()
        samples = {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'],
                   3: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']}
        npt.assert_warns(qdb.exceptions.QiitaDBWarning,
                         analysis._build_mapping_file, samples, True)

        obs = qdb.metadata_template.util.load_template_to_dataframe(
            analysis.mapping_file, index='#SampleID')
        exp = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.util.load_template_to_dataframe,
            self.duplicated_samples_not_merged, index='#SampleID')

        # assert_frame_equal assumes same order on the rows, thus sorting
        # frames by index
        obs.sort_index(inplace=True)
        exp.sort_index(inplace=True)
        assert_frame_equal(obs, exp)

    def test_build_mapping_file_duplicated_samples_merge(self):
        analysis = self._create_analyses_with_samples()
        samples = {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'],
                   3: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']}
        npt.assert_warns(qdb.exceptions.QiitaDBWarning,
                         analysis._build_mapping_file, samples)
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            analysis.mapping_file, index='#SampleID')
        exp = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.util.load_template_to_dataframe,
            self.map_exp_fp, index='#SampleID')
        assert_frame_equal(obs, exp)

    def test_build_biom_tables(self):
        analysis = self._create_analyses_with_samples()
        grouped_samples = {'18S.1.3': [(
            4, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'])]}
        analysis._build_biom_tables(grouped_samples, 100)
        obs = analysis.biom_tables
        biom_fp = self.get_fp("%s_analysis_dt-18S_r-1_c-3.biom" % analysis.id)
        self.assertEqual(obs, {'18S': biom_fp})

        table = load_table(biom_fp)
        obs = set(table.ids(axis='sample'))
        exp = {'1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'}
        self.assertEqual(obs, exp)

        obs = table.metadata('1.SKB8.640193')
        exp = {'study':
               'Identification of the Microbiomes for Cannabis Soils',
               'artifact_ids': '4',
               'reference_id': '1',
               'command_id': '3'}
        self.assertEqual(obs, exp)

    def test_build_biom_tables_duplicated_samples_not_merge(self):
        analysis = self._create_analyses_with_samples()
        grouped_samples = {'18S.1.3': [
            (4, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']),
            (5, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'])]}
        analysis._build_biom_tables(grouped_samples, 100, True)
        obs = analysis.biom_tables
        biom_fp = self.get_fp("%s_analysis_dt-18S_r-1_c-3.biom" % analysis.id)
        self.assertEqual(obs, {'18S': biom_fp})

        table = load_table(biom_fp)
        obs = set(table.ids(axis='sample'))
        exp = {'4.1.SKD8.640184', '4.1.SKB7.640196', '4.1.SKB8.640193',
               '5.1.SKB8.640193', '5.1.SKB7.640196', '5.1.SKD8.640184'}
        self.assertItemsEqual(obs, exp)

    def test_build_biom_tables_raise_error_due_to_sample_selection(self):
        grouped_samples = {'18S.1.3': [
            (4, ['sample_name_1', 'sample_name_2', 'sample_name_3'])]}
        with self.assertRaises(RuntimeError):
            self.analysis._build_biom_tables(grouped_samples)

    def test_build_biom_tables_raise_error_due_to_rarefaction_level(self):
        grouped_samples = {'18S.1.3': [
            (4, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']),
            (5, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'])]}
        with self.assertRaises(RuntimeError):
            self.analysis._build_biom_tables(grouped_samples, 100000)

    def test_build_files(self):
        analysis = self._create_analyses_with_samples()
        npt.assert_warns(qdb.exceptions.QiitaDBWarning,
                         analysis.build_files)

        # testing that the generated files have the same sample ids
        biom_ids = load_table(
            analysis.biom_tables['18S']).ids(axis='sample')
        mf_ids = qdb.metadata_template.util.load_template_to_dataframe(
            analysis.mapping_file, index='#SampleID').index

        self.assertItemsEqual(biom_ids, mf_ids)

        # now that the samples have been prefixed
        exp = ['1.SKM9.640192', '1.SKM4.640180', '1.SKD8.640184',
               '1.SKB8.640193', '1.SKB7.640196']
        self.assertItemsEqual(biom_ids, exp)

    def test_build_files_merge_duplicated_sample_ids(self):
        analysis = self._create_analyses_with_samples()
        npt.assert_warns(qdb.exceptions.QiitaDBWarning,
                         analysis.build_files,
                         merge_duplicated_sample_ids=True)

        # testing that the generated files have the same sample ids
        biom_ids = []
        for _, fp in viewitems(analysis.biom_tables):
            biom_ids.extend(load_table(fp).ids(axis='sample'))
        mf_ids = qdb.metadata_template.util.load_template_to_dataframe(
            analysis.mapping_file, index='#SampleID').index
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

    def test_add_file(self):
        analysis = self._create_analyses_with_samples()
        new_id = qdb.util.get_count('qiita.filepath') + 1
        fp = self.get_fp('testfile.txt')
        with open(fp, 'w') as f:
            f.write('testfile!')

        self.assertEqual(analysis.all_associated_filepath_ids, set())
        analysis._add_file('testfile.txt', 'plain_text', '18S')
        self.assertEqual(analysis.all_associated_filepath_ids, {new_id})


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

    def test_retrieve_name(self):
        obs = self.collection.name
        exp = "TEST_COLLECTION"
        self.assertEqual(obs, exp)

    def test_set_name(self):
        self.collection.name = "NeW NaMe 123"
        self.assertEqual(self.collection.name, "NeW NaMe 123")

    def test_set_name_public(self):
        self.collection.status = "public"
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.collection.name = "FAILBOAT"

    def test_retrieve_desc(self):
        obs = self.collection.description
        exp = "collection for testing purposes"
        self.assertEqual(obs, exp)

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
