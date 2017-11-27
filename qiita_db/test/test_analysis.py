from unittest import TestCase, main
from os import remove
from os.path import exists, join, basename
from shutil import move

from biom import load_table
from pandas.util.testing import assert_frame_equal
from functools import partial
import numpy.testing as npt

from qiita_core.util import qiita_test_checker
from qiita_core.testing import wait_for_processing_job
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
        self._old_portal = qiita_config.portal
        self.table_fp = None

        # fullpaths for testing
        self.duplicated_samples_not_merged = self.get_fp(
            "not_merged_samples.txt")
        self.map_exp_fp = self.get_fp("1_analysis_mapping_exp.txt")

        from glob import glob
        conf_files = glob(join(qiita_config.plugin_dir, "BIOM*.conf"))
        for i, fp in enumerate(conf_files):
            qdb.software.Software.from_file(fp, update=True)

    def tearDown(self):
        self.analysis.artifacts[0].visibility = 'private'

        qiita_config.portal = self.portal
        with open(self.biom_fp, 'w') as f:
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

    def _wait_for_jobs(self, analysis):
        for j in analysis.jobs:
            wait_for_processing_job(j.id)
            if j.status == 'error':
                print j.log.msg

    def _create_analyses_with_samples(self, user='demo@microbio.me',
                                      merge=False):
        """Aux function to create an analysis with samples

        Parameters
        ----------
        user : qiita_db.user.User, optional
            The user email to attach the analysis. Default: demo@microbio.me
        merge : bool, optional
            Merge duplicated ids or not

        Returns
        -------
        qiita_db.analysis.Analysis

        Notes
        -----
        Replicates the samples contained in Analysis(1) at the moment of
        creation of this function (September 15, 2016)
        """
        user = qdb.user.User(user)
        dflt_analysis = user.default_analysis
        dflt_analysis.add_samples(
            {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                 '1.SKM9.640192', '1.SKM4.640180']})
        new = qdb.analysis.Analysis.create(
            user, "newAnalysis", "A New Analysis", from_default=True,
            merge_duplicated_sample_ids=merge)

        self._wait_for_jobs(new)
        return new

    def test_lock_samples(self):
        dflt = qdb.user.User('demo@microbio.me').default_analysis
        # The default analysis can have samples added/removed
        dflt._lock_samples()

        QE = qdb.exceptions
        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            qdb.analysis.Analysis(1)._lock_samples()

    def test_get_by_status(self):
        qiita_config.portal = 'QIITA'
        self.assertEqual(
            qdb.analysis.Analysis.get_by_status('public'), set([]))
        qiita_config.portal = 'EMP'
        self.assertEqual(
            qdb.analysis.Analysis.get_by_status('public'), set([]))

        qiita_config.portal = 'QIITA'
        self.analysis.artifacts[0].visibility = 'public'

        self.assertEqual(qdb.analysis.Analysis.get_by_status('public'),
                         {self.analysis})
        qiita_config.portal = 'EMP'
        self.assertEqual(
            qdb.analysis.Analysis.get_by_status('public'), set([]))

    def test_can_be_publicized(self):
        analysis = qdb.analysis.Analysis(1)
        self.assertFalse(analysis.can_be_publicized)
        a4 = qdb.artifact.Artifact(4)

        a4.visibility = 'public'
        self.assertTrue(analysis.can_be_publicized)

        a4.visibility = 'private'
        self.assertFalse(analysis.can_be_publicized)

    def test_add_artifact(self):
        obs = self._create_analyses_with_samples()
        exp = qdb.artifact.Artifact(4)
        obs.add_artifact(exp)
        self.assertIn(exp, obs.artifacts)

    def test_has_access_public(self):
        analysis = self._create_analyses_with_samples("admin@foo.bar")
        analysis.artifacts[0].visibility = 'public'

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

    def test_can_edit(self):
        a = qdb.analysis.Analysis(1)
        self.assertTrue(a.can_edit(qdb.user.User('test@foo.bar')))
        self.assertTrue(a.can_edit(qdb.user.User('shared@foo.bar')))
        self.assertTrue(a.can_edit(qdb.user.User('admin@foo.bar')))
        self.assertFalse(a.can_edit(qdb.user.User('demo@microbio.me')))

    def test_create_nonqiita_portal(self):
        qiita_config.portal = "EMP"
        obs = qdb.analysis.Analysis.create(
            qdb.user.User("admin@foo.bar"), "newAnalysis", "A New Analysis")

        # make sure portal is associated
        self.assertItemsEqual(obs._portals, ["QIITA", "EMP"])

    def test_create_from_default(self):
        with qdb.sql_connection.TRN:
            sql = "SELECT NOW()"
            qdb.sql_connection.TRN.add(sql)
            time1 = qdb.sql_connection.TRN.execute_fetchlast()

        owner = qdb.user.User("test@foo.bar")
        obs = qdb.analysis.Analysis.create(
            owner, "newAnalysis", "A New Analysis", from_default=True)

        self.assertEqual(obs.owner, owner)
        self.assertEqual(obs.name, "newAnalysis")
        self.assertEqual(obs._portals, ["QIITA"])
        self.assertLess(time1, obs.timestamp)
        self.assertEqual(obs.description, "A New Analysis")
        self.assertItemsEqual(obs.samples, [4])
        self.assertItemsEqual(
            obs.samples[4], ['1.SKD8.640184', '1.SKB7.640196',
                             '1.SKM9.640192', '1.SKM4.640180'])
        self.assertEqual(obs.data_types, ['18S'])
        self.assertEqual(obs.shared_with, [])
        self.assertEqual(obs.mapping_file, None)
        self.assertEqual(obs.tgz, None)
        self.assertNotEqual(obs.jobs, [])
        self.assertEqual(obs.pmid, None)

    def test_exists(self):
        qiita_config.portal = 'QIITA'
        self.assertTrue(qdb.analysis.Analysis.exists(1))
        self.assertFalse(qdb.analysis.Analysis.exists(1000))
        qiita_config.portal = 'EMP'
        self.assertFalse(qdb.analysis.Analysis.exists(1))
        self.assertFalse(qdb.analysis.Analysis.exists(1000))

    def test_delete(self):
        # successful delete
        new = qdb.analysis.Analysis.create(
            qdb.user.User('demo@microbio.me'), "newAnalysis",
            "A New Analysis")
        self.assertTrue(qdb.analysis.Analysis.exists(new.id))
        qdb.analysis.Analysis.delete(new.id)
        self.assertFalse(qdb.analysis.Analysis.exists(new.id))

        # no possible to delete
        QE = qdb.exceptions
        with self.assertRaises(QE.QiitaDBUnknownIDError):
            qdb.analysis.Analysis.delete(new.id)

        # Analysis with artifacts
        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            qdb.analysis.Analysis.delete(1)

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

    def test_retrieve_portal(self):
        self.assertEqual(self.analysis._portals, ["QIITA"])

    def test_retrieve_data_types(self):
        exp = ['18S', '16S']
        self.assertItemsEqual(self.analysis.data_types, exp)

    def test_retrieve_shared_with(self):
        self.assertEqual(self.analysis.shared_with,
                         [qdb.user.User("shared@foo.bar")])

    def test_retrieve_jobs(self):
        self.assertEqual(self.analysis.jobs, [])

    def test_retrieve_pmid(self):
        self.assertEqual(self.analysis.pmid, "121112")

    def test_set_pmid(self):
        new = self._create_analyses_with_samples("admin@foo.bar")
        self.assertIsNone(new.pmid)
        new.pmid = "11211221212213"
        self.assertEqual(new.pmid, "11211221212213")

    def test_retrieve_mapping_file(self):
        exp = join(self.fp, "1_analysis_mapping.txt")
        obs = self.analysis.mapping_file
        self.assertIsNotNone(obs)
        self.assertEqual(
            qdb.util.get_filepath_information(obs)['fullpath'], exp)
        self.assertTrue(exists(exp))

    def test_retrieve_tgz(self):
        # generating here as the tgz is only generated once the analysis runs
        # to completion (un)successfully
        analysis = self._create_analyses_with_samples("admin@foo.bar")
        fp = self.get_fp('test.tgz')
        with open(fp, 'w') as f:
            f.write('')
        analysis._add_file(fp, 'tgz')
        self.assertEqual(analysis.tgz, fp)

    def test_retrieve_tgz_none(self):
        self.assertIsNone(self.analysis.tgz)

    def test_summary_data(self):
        obs = self.analysis.summary_data()
        exp = {'studies': 1,
               'artifacts': 3,
               'samples': 5}
        self.assertEqual(obs, exp)

    def test_add_remove_samples(self):
        analysis = qdb.user.User('shared@foo.bar').default_analysis
        exp = {4: ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180', '1.SKB8.640193'],
               5: ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180', '1.SKB8.640193'],
               6: ['1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180', '1.SKB8.640193']}
        analysis.add_samples(exp)
        obs = analysis.samples
        self.assertItemsEqual(obs.keys(), exp.keys())
        for k in obs:
            self.assertItemsEqual(obs[k], exp[k])

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

        analysis.remove_samples(samples=('1.SKD8.640184', ))
        exp = {4: ['1.SKB7.640196', '1.SKM9.640192', '1.SKM4.640180'],
               5: ['1.SKB8.640193', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180'],
               6: ['1.SKB8.640193', '1.SKB7.640196', '1.SKM9.640192',
                   '1.SKM4.640180']}
        self.assertItemsEqual(analysis.samples, exp)

        analysis.remove_samples(
            artifacts=(qdb.artifact.Artifact(4), qdb.artifact.Artifact(5)))
        exp = {6: {'1.SKB7.640196', '1.SKB8.640193',
                   '1.SKM4.640180', '1.SKM9.640192'}}
        self.assertItemsEqual(analysis.samples, exp)

    def test_share_unshare(self):
        analysis = self._create_analyses_with_samples()
        user = qdb.user.User("admin@foo.bar")
        self.assertEqual(analysis.shared_with, [])
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
        obs = qdb.util.get_filepath_information(
            analysis.mapping_file)['fullpath']

        exp = self.get_fp("%s_analysis_mapping.txt" % analysis.id)
        self.assertEqual(obs, exp)

        obs = qdb.metadata_template.util.load_template_to_dataframe(
            obs, index='#SampleID')
        exp = qdb.metadata_template.util.load_template_to_dataframe(
            self.map_exp_fp, index='#SampleID')
        assert_frame_equal(obs, exp)

    def test_build_mapping_file_duplicated_samples_no_merge(self):
        analysis = self._create_analyses_with_samples()
        samples = {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'],
                   3: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']}
        npt.assert_warns(qdb.exceptions.QiitaDBWarning,
                         analysis._build_mapping_file, samples, True)

        mapping_fp = qdb.util.get_filepath_information(
            analysis.mapping_file)['fullpath']
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            mapping_fp, index='#SampleID')
        exp = qdb.metadata_template.util.load_template_to_dataframe(
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
        mapping_fp = qdb.util.get_filepath_information(
            analysis.mapping_file)['fullpath']
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            mapping_fp, index='#SampleID')
        exp = qdb.metadata_template.util.load_template_to_dataframe(
            self.map_exp_fp, index='#SampleID')
        assert_frame_equal(obs, exp)

    def test_build_biom_tables(self):
        analysis = self._create_analyses_with_samples()
        grouped_samples = {
            '18S || algorithm': [
                (4, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'])]}
        obs_bioms = analysis._build_biom_tables(grouped_samples)
        biom_fp = self.get_fp(
            "%s_analysis_18S_algorithm.biom" % analysis.id)
        obs = [(a, basename(b)) for a, b in obs_bioms]
        self.assertEqual(obs, [('18S', basename(biom_fp))])

        table = load_table(obs_bioms[0][1])
        obs = set(table.ids(axis='sample'))
        exp = {'1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'}
        self.assertEqual(obs, exp)

    def test_build_biom_tables_with_references(self):
        analysis = self._create_analyses_with_samples()
        analysis_id = analysis.id
        grouped_samples = {
            ('18S || Pick closed-reference OTUs (reference: 1) | '
             'Split libraries FASTQ'): [
                (4, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']),
                (5, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'])],
            ('18S || Pick closed-reference OTUs (reference: 1) | '
             'Trim (lenght: 150)'): [
                (4, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']),
                (5, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'])],
            ('16S || Pick closed-reference OTUs (reference: 2) | '
             'Trim (lenght: 100)'): [
                (4, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']),
                (5, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'])]}
        obs_bioms = analysis._build_biom_tables(grouped_samples)
        obs = [(a, basename(b)) for a, b in obs_bioms]
        exp = [
            ('16S', '%s_analysis_16S_PickclosedreferenceOTUsreference2'
             'Trimlenght100.biom' % analysis_id),
            ('18S', '%s_analysis_18S_PickclosedreferenceOTUsreference1'
             'SplitlibrariesFASTQ.biom' % analysis_id),
            ('18S', '%s_analysis_18S_PickclosedreferenceOTUsreference1'
             'Trimlenght150.biom' % analysis_id)]
        self.assertEqual(obs, exp)

        exp = {'1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'}
        for dt, fp in obs_bioms:
            table = load_table(fp)
            obs = set(table.ids(axis='sample'))
            self.assertEqual(obs, exp)

    def test_build_biom_tables_duplicated_samples_not_merge(self):
        analysis = self._create_analyses_with_samples()
        grouped_samples = {
            '18S || algorithm': [
                (4, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']),
                (5, ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'])]}
        obs_bioms = analysis._build_biom_tables(grouped_samples, True)
        obs = [(a, basename(b)) for a, b in obs_bioms]
        biom_fp = (
            "%s_analysis_18S_algorithm.biom" % analysis.id)
        self.assertEqual(obs, [('18S', biom_fp)])

        table = load_table(obs_bioms[0][1])
        obs = set(table.ids(axis='sample'))
        exp = {'4.1.SKD8.640184', '4.1.SKB7.640196', '4.1.SKB8.640193',
               '5.1.SKB8.640193', '5.1.SKB7.640196', '5.1.SKD8.640184'}
        self.assertItemsEqual(obs, exp)

    def test_build_biom_tables_raise_error_due_to_sample_selection(self):
        grouped_samples = {
            '18S || algorithm': [
                (4, ['sample_name_1', 'sample_name_2', 'sample_name_3'])]}
        with self.assertRaises(RuntimeError):
            self.analysis._build_biom_tables(grouped_samples)

    def test_build_files(self):
        analysis = self._create_analyses_with_samples()
        biom_tables = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, analysis.build_files, False)

        # testing that the generated files have the same sample ids
        biom_fp = biom_tables[0][1]
        biom_ids = load_table(biom_fp).ids(axis='sample')
        mapping_fp = qdb.util.get_filepath_information(
            analysis.mapping_file)['fullpath']
        mf_ids = qdb.metadata_template.util.load_template_to_dataframe(
            mapping_fp, index='#SampleID').index

        self.assertItemsEqual(biom_ids, mf_ids)

        # now that the samples have been prefixed
        exp = ['1.SKM9.640192', '1.SKM4.640180', '1.SKD8.640184',
               '1.SKB8.640193', '1.SKB7.640196']
        self.assertItemsEqual(biom_ids, exp)

    def test_build_files_merge_duplicated_sample_ids(self):
        user = qdb.user.User("demo@microbio.me")
        dflt_analysis = user.default_analysis
        dflt_analysis.add_samples(
            {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                 '1.SKM9.640192', '1.SKM4.640180'],
             5: ['1.SKB8.640193', '1.SKB7.640196', '1.SKM9.640192',
                 '1.SKM4.640180', '1.SKD8.640184'],
             6: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                 '1.SKM9.640192', '1.SKM4.640180']})
        new = qdb.analysis.Analysis.create(
            user, "newAnalysis", "A New Analysis", from_default=True,
            merge_duplicated_sample_ids=True)

        self._wait_for_jobs(new)

        biom_tables = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, new.build_files, True)

        # testing that the generated files have the same sample ids
        biom_ids = []
        for _, fp in biom_tables:
            biom_ids.extend(load_table(fp).ids(axis='sample'))

        mapping_fp = qdb.util.get_filepath_information(
            new.mapping_file)['fullpath']
        mf_ids = qdb.metadata_template.util.load_template_to_dataframe(
            mapping_fp, index='#SampleID').index

        self.assertItemsEqual(biom_ids, mf_ids)

        # now that the samples have been prefixed
        exp = ['4.1.SKM9.640192', '4.1.SKM4.640180', '4.1.SKD8.640184',
               '4.1.SKB8.640193', '4.1.SKB7.640196',
               '5.1.SKM9.640192', '5.1.SKM4.640180', '5.1.SKD8.640184',
               '5.1.SKB8.640193', '5.1.SKB7.640196',
               '6.1.SKM9.640192', '6.1.SKM4.640180', '6.1.SKD8.640184',
               '6.1.SKB8.640193', '6.1.SKB7.640196']
        self.assertItemsEqual(biom_ids, exp)

    def test_add_file(self):
        # Tested indirectly through build_files
        pass


if __name__ == "__main__":
    main()
