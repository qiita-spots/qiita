# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
import numpy.testing as npt
from tarfile import open as topen
from os import remove
from os.path import exists, join

import pandas as pd

from moi import r_client
from qiita_core.qiita_settings import qiita_config
from qiita_core.util import qiita_test_checker

import qiita_db as qdb


@qiita_test_checker()
class MetaUtilTests(TestCase):
    def setUp(self):
        self.old_portal = qiita_config.portal
        self.files_to_remove = []

    def tearDown(self):
        qiita_config.portal = self.old_portal
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)

    def _set_artifact_private(self):
        self.conn_handler.execute(
            "UPDATE qiita.artifact SET visibility_id=3")

    def _set_artifact_public(self):
        self.conn_handler.execute(
            "UPDATE qiita.artifact SET visibility_id=2")

    def test_validate_filepath_access_by_user(self):
        self._set_artifact_private()

        # shared has access to all study files and analysis files
        user = qdb.user.User('shared@foo.bar')
        for i in [1, 2, 3, 4, 5, 9, 12, 15, 16, 17, 18, 19, 20, 21]:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(
                user, i))

        # Now shared should not have access to the study files
        qdb.study.Study(1).unshare(user)
        for i in [1, 2, 3, 4, 5, 9, 12, 17, 18, 19, 20, 21]:
            self.assertFalse(qdb.meta_util.validate_filepath_access_by_user(
                user, i))

        for i in [15, 16]:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(
                user, i))

        # Now shared should not have access to any files
        qdb.analysis.Analysis(1).unshare(user)
        for i in [1, 2, 3, 4, 5, 9, 12, 15, 16, 17, 18, 19, 20, 21]:
            self.assertFalse(qdb.meta_util.validate_filepath_access_by_user(
                user, i))

        # Now shared has access to public study files
        self._set_artifact_public()
        for i in [1, 2, 3, 4, 5, 9, 12, 17, 18, 19, 20, 21]:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(
                user, i))

        # Test that it doesn't break: if the SampleTemplate hasn't been added
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 4,
            "number_samples_promised": 4,
            "study_alias": "TestStudy",
            "study_description": "Description of a test study",
            "study_abstract": "No abstract right now...",
            "emp_person_id": 1,
            "principal_investigator_id": 1,
            "lab_person_id": 1
        }
        study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Test study", [1], info)
        for i in [1, 2, 3, 4, 5, 9, 12, 17, 18, 19, 20, 21]:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(
                user, i))

        # test in case there is a prep template that failed
        self.conn_handler.execute(
            "INSERT INTO qiita.prep_template (data_type_id) VALUES (2)")
        for i in [1, 2, 3, 4, 5, 9, 12, 17, 18, 19, 20, 21]:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(
                user, i))

        # admin should have access to everything
        admin = qdb.user.User('admin@foo.bar')
        fids = self.conn_handler.execute_fetchall(
            "SELECT filepath_id FROM qiita.filepath")
        for i in fids:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(
                admin, i[0]))

        # testing access to a prep info file without artifacts
        # returning artifacts to private
        self._set_artifact_private()
        PT = qdb.metadata_template.prep_template.PrepTemplate
        md_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'instrument_model': 'Illumina MiSeq',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}
            }
        md = pd.DataFrame.from_dict(md_dict, orient='index', dtype=str)
        # creating prep info on Study(1), which is our default Study
        pt = npt.assert_warns(qdb.exceptions.QiitaDBWarning, PT.create, md,
                              qdb.study.Study(1), "18S")
        for idx, _ in pt.get_filepaths():
            self.assertFalse(qdb.meta_util.validate_filepath_access_by_user(
                user, idx))

        # returning to original sharing
        PT.delete(pt.id)
        qdb.study.Study(1).share(user)
        qdb.analysis.Analysis(1).share(user)
        qdb.study.Study.delete(study.id)

    def test_get_lat_longs(self):
        exp = [
            [74.0894932572, 65.3283470202],
            [57.571893782, 32.5563076447],
            [13.089194595, 92.5274472082],
            [12.7065957714, 84.9722975792],
            [44.9725384282, 66.1920014699],
            [10.6655599093, 70.784770579],
            [29.1499460692, 82.1270418227],
            [35.2374368957, 68.5041623253],
            [53.5050692395, 31.6056761814],
            [60.1102854322, 74.7123248382],
            [4.59216095574, 63.5115213108],
            [68.0991287718, 34.8360987059],
            [84.0030227585, 66.8954849864],
            [3.21190859967, 26.8138925876],
            [82.8302905615, 86.3615778099],
            [12.6245524972, 96.0693176066],
            [85.4121476399, 15.6526750776],
            [23.1218032799, 42.838497795],
            [43.9614715197, 82.8516734159],
            [68.51099627, 2.35063674718],
            [0.291867635913, 68.5945325743],
            [40.8623799474, 6.66444220187],
            [95.2060749748, 27.3592668624],
            [78.3634273709, 74.423907894],
            [38.2627021402, 3.48274264219]]

        obs = qdb.meta_util.get_lat_longs()
        self.assertItemsEqual(obs, exp)

    def test_get_lat_longs_EMP_portal(self):
        info = {
            'timeseries_type_id': 1,
            'lab_person_id': None,
            'principal_investigator_id': 3,
            'metadata_complete': False,
            'mixs_compliant': True,
            'study_description': 'desc',
            'study_alias': 'alias',
            'study_abstract': 'abstract'}

        study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), 'test_study_1', efo=[1], info=info)
        qdb.portal.Portal('EMP').add_studies([study.id])

        md = {
            'my.sample': {
                'physical_specimen_location': 'location1',
                'physical_specimen_remaining': True,
                'dna_extracted': True,
                'sample_type': 'type1',
                'collection_timestamp': '2014-05-29 12:24:51',
                'host_subject_id': 'NotIdentified',
                'Description': 'Test Sample 4',
                'str_column': 'Value for sample 4',
                'int_column': 4,
                'latitude': 42.42,
                'longitude': 41.41,
                'taxon_id': 9606,
                'scientific_name': 'homo sapiens'}
        }

        md_ext = pd.DataFrame.from_dict(md, orient='index', dtype=str)
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            md_ext, study)

        qiita_config.portal = 'EMP'

        obs = qdb.meta_util.get_lat_longs()
        exp = [[42.42, 41.41]]

        self.assertItemsEqual(obs, exp)
        qdb.metadata_template.sample_template.SampleTemplate.delete(st.id)
        qdb.study.Study.delete(study.id)

    def test_update_redis_stats(self):
        qdb.meta_util.update_redis_stats()

        portal = qiita_config.portal
        vals = [
            ('number_studies', {'sandbox': '0', 'public': '0',
                                'private': '1'}, r_client.hgetall),
            ('number_of_samples', {'sandbox': '0', 'public': '0',
                                   'private': '27'}, r_client.hgetall),
            ('num_users', '4', r_client.get),
            ('lat_longs', EXP_LAT_LONG, r_client.get),
            ('num_studies_ebi', '1', r_client.get),
            ('num_samples_ebi', '27', r_client.get),
            ('number_samples_ebi_prep', '54', r_client.get)
            # not testing img/time for simplicity
            # ('img', r_client.get),
            # ('time', r_client.get)
            ]
        for k, exp, f in vals:
            redis_key = '%s:stats:%s' % (portal, k)
            self.assertEqual(f(redis_key), exp)

    def test_generate_biom_and_metadata_release(self):
        level = 'private'
        qdb.meta_util.generate_biom_and_metadata_release(level)
        portal = qiita_config.portal
        working_dir = qiita_config.working_dir

        vals = [
            ('filepath', r_client.get),
            ('md5sum', r_client.get),
            ('time', r_client.get)]
        # we are storing the [0] filepath, [1] md5sum and [2] time but we are
        # only going to check the filepath contents so ignoring the others
        tgz = vals[0][1]('%s:release:%s:%s' % (portal, level, vals[0][0]))
        tgz = join(working_dir, tgz)

        self.files_to_remove.extend([tgz])

        tmp = topen(tgz, "r:gz")
        tgz_obs = [ti.name for ti in tmp]
        tmp.close()
        # files names might change due to updates and patches so just check
        # that the prefix exists.
        fn = 'processed_data/1_study_1001_closed_reference_otu_table.biom'
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # yes, this file is there twice
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # let's check the next biom
        fn = ('processed_data/1_study_1001_closed_reference_otu_table_Silva.'
              'biom')
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # now let's check prep info files based on their suffix, just take
        # the first one and check/rm the occurances of that file
        fn_prep = [f for f in tgz_obs
                   if f.startswith('templates/1_prep_1_')][0]
        # 3 times
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        fn_sample = [f for f in tgz_obs if f.startswith('templates/1_')][0]
        # 3 times
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        # now we should only have the text file
        txt = tgz_obs.pop()
        # now it should be empty
        self.assertEqual(tgz_obs, [])

        tmp = topen(tgz, "r:gz")
        fhd = tmp.extractfile(txt)
        txt_obs = fhd.readlines()
        tmp.close()
        txt_exp = [
            'biom_fp\tsample_fp\tprep_fp\tqiita_artifact_id\tcommand\n',
            'processed_data/1_study_1001_closed_reference_otu_table.biom\t'
            '%s\t%s\t4\tPick closed-reference OTUs, Split libraries FASTQ\n'
            % (fn_sample, fn_prep),
            'processed_data/1_study_1001_closed_reference_otu_table.biom\t'
            '%s\t%s\t5\tPick closed-reference OTUs, Split libraries FASTQ\n'
            % (fn_sample, fn_prep),
            'processed_data/1_study_1001_closed_reference_otu_table_Silva.bio'
            'm\t%s\t%s\t6\tPick closed-reference OTUs, Split libraries FASTQ\n'
            % (fn_sample, fn_prep)]
        self.assertEqual(txt_obs, txt_exp)

        # whatever the configuration was, we will change to settings so we can
        # test the other option when dealing with the end '/'
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(
                "SELECT base_data_dir FROM settings")
            obdr = qdb.sql_connection.TRN.execute_fetchlast()
            if obdr[-1] == '/':
                bdr = obdr[:-1]
            else:
                bdr = obdr + '/'

            qdb.sql_connection.TRN.add(
                "UPDATE settings SET base_data_dir = '%s'" % bdr)
            bdr = qdb.sql_connection.TRN.execute()

        qdb.meta_util.generate_biom_and_metadata_release(level)
        # we are storing the [0] filepath, [1] md5sum and [2] time but we are
        # only going to check the filepath contents so ignoring the others
        tgz = vals[0][1]('%s:release:%s:%s' % (portal, level, vals[0][0]))
        tgz = join(working_dir, tgz)

        tmp = topen(tgz, "r:gz")
        tgz_obs = [ti.name for ti in tmp]
        tmp.close()
        # files names might change due to updates and patches so just check
        # that the prefix exists.
        fn = 'processed_data/1_study_1001_closed_reference_otu_table.biom'
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # yes, this file is there twice
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # let's check the next biom
        fn = ('processed_data/1_study_1001_closed_reference_otu_table_Silva.'
              'biom')
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # now let's check prep info files based on their suffix, just take
        # the first one and check/rm the occurances of that file
        fn_prep = [f for f in tgz_obs
                   if f.startswith('templates/1_prep_1_')][0]
        # 3 times
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        fn_sample = [f for f in tgz_obs if f.startswith('templates/1_')][0]
        # 3 times
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        # now we should only have the text file
        txt = tgz_obs.pop()
        # now it should be empty
        self.assertEqual(tgz_obs, [])

        tmp = topen(tgz, "r:gz")
        fhd = tmp.extractfile(txt)
        txt_obs = fhd.readlines()
        tmp.close()
        txt_exp = [
            'biom_fp\tsample_fp\tprep_fp\tqiita_artifact_id\tcommand\n',
            'processed_data/1_study_1001_closed_reference_otu_table.biom\t'
            '%s\t%s\t4\tPick closed-reference OTUs, Split libraries FASTQ\n'
            % (fn_sample, fn_prep),
            'processed_data/1_study_1001_closed_reference_otu_table.biom\t'
            '%s\t%s\t5\tPick closed-reference OTUs, Split libraries FASTQ\n'
            % (fn_sample, fn_prep),
            'processed_data/1_study_1001_closed_reference_otu_table_Silva.bio'
            'm\t%s\t%s\t6\tPick closed-reference OTUs, Split libraries FASTQ\n'
            % (fn_sample, fn_prep)]
        self.assertEqual(txt_obs, txt_exp)

        # returning configuration
        with qdb.sql_connection.TRN:
                    qdb.sql_connection.TRN.add(
                        "UPDATE settings SET base_data_dir = '%s'" % obdr)
                    bdr = qdb.sql_connection.TRN.execute()


EXP_LAT_LONG = (
    '[[60.1102854322, 74.7123248382], [23.1218032799, 42.838497795],'
    ' [3.21190859967, 26.8138925876], [74.0894932572, 65.3283470202],'
    ' [53.5050692395, 31.6056761814], [12.6245524972, 96.0693176066],'
    ' [43.9614715197, 82.8516734159], [10.6655599093, 70.784770579],'
    ' [78.3634273709, 74.423907894], [82.8302905615, 86.3615778099],'
    ' [44.9725384282, 66.1920014699], [4.59216095574, 63.5115213108],'
    ' [57.571893782, 32.5563076447], [40.8623799474, 6.66444220187],'
    ' [95.2060749748, 27.3592668624], [38.2627021402, 3.48274264219],'
    ' [13.089194595, 92.5274472082], [84.0030227585, 66.8954849864],'
    ' [68.51099627, 2.35063674718], [29.1499460692, 82.1270418227],'
    ' [35.2374368957, 68.5041623253], [12.7065957714, 84.9722975792],'
    ' [0.291867635913, 68.5945325743], [85.4121476399, 15.6526750776],'
    ' [68.0991287718, 34.8360987059]]')


if __name__ == '__main__':
    main()
