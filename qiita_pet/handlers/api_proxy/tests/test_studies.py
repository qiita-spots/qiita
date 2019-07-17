# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from datetime import datetime
from os.path import exists, join, isdir
from os import remove
from shutil import rmtree
from tempfile import mkdtemp

import pandas as pd
import numpy.testing as npt

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
import qiita_db as qdb
from qiita_pet.handlers.api_proxy.studies import (
    data_types_get_req, study_get_req, study_prep_get_req, study_delete_req,
    study_tags_request, study_get_tags_request, study_patch_request,
    study_files_get_req)


@qiita_test_checker()
class TestStudyAPI(TestCase):
    def setUp(self):
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)


class TestStudyAPI1(TestStudyAPI):
    def test_data_types_get_req(self):
        obs = data_types_get_req()
        exp = {
            'status': 'success',
            'message': '',
            'data_types': ['16S', '18S', 'ITS', 'Proteomic', 'Metagenomic',
                           'Metabolomic']}
        self.assertCountEqual(obs, exp)

    def test_study_get_req(self):
        obs = study_get_req(1, 'test@foo.bar')
        exp = {
            'status': 'success',
            'study_info': {
                'mixs_compliant': True, 'metadata_complete': True, 'level': '',
                'reprocess': False, 'owner': 'test@foo.bar', 'message': '',
                'funding': None, 'show_biom_download_button': True,
                'publication_pid': ['123456', '7891011'], 'vamps_id': None,
                'first_contact': datetime(2014, 5, 19, 16, 10),
                'ebi_submission_status': 'submitted',
                'show_raw_download_button': True, 'timeseries_type_id': 1,
                'study_abstract': (
                    'This is a preliminary study to examine the microbiota '
                    'associated with the Cannabis plant. Soils samples from '
                    'the bulk soil, soil associated with the roots, and the '
                    'rhizosphere were extracted and the DNA sequenced. Roots '
                    'from three independent plants of different strains were '
                    'examined. These roots were obtained November 11, 2011 '
                    'from plants that had been harvested in the summer. '
                    'Future studies will attempt to analyze the soils and '
                    'rhizospheres from the same location at different time '
                    'points in the plant lifecycle.'),
                'status': 'private', 'spatial_series': False,
                'specimen_id_column': None, 'public_raw_download': False,
                'study_description': (
                    'Analysis of the Cannabis Plant Microbiome'),
                'shared_with': ['shared@foo.bar'], 'publication_doi': [
                    '10.100/123456', '10.100/7891011'],
                'has_access_to_raw_data': True, 'lab_person': {
                    'affiliation': 'knight lab', 'name': 'LabDude',
                    'email': 'lab_dude@foo.bar'},
                'principal_investigator': {
                    'affiliation': 'Wash U', 'name': 'PIDude',
                    'email': 'PI_dude@foo.bar'},
                'study_alias': 'Cannabis Soils', 'study_id': 1,
                'most_recent_contact': datetime(2014, 5, 19, 16, 11),
                'ebi_study_accession': 'EBI123456-BB', 'num_samples': 27,
                'public_raw_download': False,
                'study_title': (
                    'Identification of the Microbiomes for Cannabis Soils')},
            'message': '',
            'editable': True}
        self.assertEqual(obs, exp)

        # Test with no lab person
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": qdb.study.StudyPerson(3),
            'first_contact': datetime(2015, 5, 19, 16, 10),
            'most_recent_contact': datetime(2015, 5, 19, 16, 11),
        }
        new_study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Some New Study for test", info)

        obs = study_get_req(new_study.id, 'test@foo.bar')
        exp = {'status': 'success', 'study_info': {
            'mixs_compliant': True, 'metadata_complete': True,
            'reprocess': False, 'public_raw_download': False,
            'owner': 'test@foo.bar', 'message': '', 'funding': None,
            'show_biom_download_button': False, 'publication_pid': [],
            'vamps_id': None, 'first_contact': datetime(2015, 5, 19, 16, 10),
            'ebi_submission_status': 'not submitted',
            'show_raw_download_button': False, 'timeseries_type_id': 1,
            'study_abstract': 'ABS', 'status': 'sandbox',
            'spatial_series': None, 'study_description': 'DESC',
            'num_samples': 0, 'shared_with': [], 'publication_doi': [],
            'has_access_to_raw_data': True, 'lab_person': None, 'level': '',
            'principal_investigator': {
                'affiliation': 'Wash U', 'name': 'PIDude',
                'email': 'PI_dude@foo.bar'}, 'study_alias': 'FCM',
            'study_id': new_study.id,
            'most_recent_contact': datetime(2015, 5, 19, 16, 11),
            'ebi_study_accession': None, 'specimen_id_column': None,
            'study_title': 'Some New Study for test'}, 'message': '',
            'editable': True}
        self.assertCountEqual(obs, exp)
        self.assertCountEqual(obs['study_info'], exp['study_info'])

    def test_study_get_req_no_access(self):
        obs = study_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_study_get_req_no_exists(self):
        obs = study_get_req(4000, 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Study does not exist'}
        self.assertEqual(obs, exp)

    def test_study_prep_get_req_failed_EBI(self):
        temp_dir = mkdtemp()
        self._clean_up_files.append(temp_dir)
        user_email = 'test@foo.bar'

        # creating a (A) new study, (B) sample info, (C) prep without EBI
        # values

        # (A)
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "Test EBI",
            "study_description": "Study for testing EBI",
            "study_abstract": "Study for testing EBI",
            "principal_investigator_id": qdb.study.StudyPerson(3),
            "lab_person_id": qdb.study.StudyPerson(1)
        }
        study = qdb.study.Study.create(
            qdb.user.User(user_email), "Test EBI study", info)

        # (B)
        metadata_dict = {
            'Sample1': {'collection_timestamp': datetime(2015, 6, 1, 7, 0, 0),
                        'physical_specimen_location': 'location1',
                        'taxon_id': 9606,
                        'scientific_name': 'homo sapiens',
                        'Description': 'Test Sample 1'},
            'Sample2': {'collection_timestamp': datetime(2015, 6, 2, 7, 0, 0),
                        'physical_specimen_location': 'location1',
                        'taxon_id': 9606,
                        'scientific_name': 'homo sapiens',
                        'Description': 'Test Sample 2'},
            'Sample3': {'collection_timestamp': datetime(2015, 6, 3, 7, 0, 0),
                        'physical_specimen_location': 'location1',
                        'taxon_id': 9606,
                        'scientific_name': 'homo sapiens',
                        'Description': 'Test Sample 3'}
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.sample_template.SampleTemplate.create,
            metadata, study)

        # (C)
        metadata_dict = {
            'Sample1': {'primer': 'GTGCCAGCMGCCGCGGTAA',
                        'barcode': 'CGTAGAGCTCTC',
                        'center_name': 'KnightLab',
                        'platform': 'Illumina',
                        'instrument_model': 'Illumina MiSeq',
                        'library_construction_protocol': 'Protocol ABC',
                        'experiment_design_description': "Random value 1"},
            'Sample2': {'primer': 'GTGCCAGCMGCCGCGGTAA',
                        'barcode': 'CGTAGAGCTCTA',
                        'center_name': 'KnightLab',
                        'platform': 'Illumina',
                        'instrument_model': 'Illumina MiSeq',
                        'library_construction_protocol': 'Protocol ABC',
                        'experiment_design_description': "Random value 2"},
            'Sample3': {'primer': 'GTGCCAGCMGCCGCGGTAA',
                        'barcode': 'CGTAGAGCTCTT',
                        'center_name': 'KnightLab',
                        'platform': 'Illumina',
                        'instrument_model': 'Illumina MiSeq',
                        'library_construction_protocol': 'Protocol ABC',
                        'experiment_design_description': "Random value 3"},
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, study, "16S", 'Metagenomics')

        # making sure that the EBI values are empty
        exp = {('%d.Sample3' % study.id): None,
               ('%d.Sample2' % study.id): None,
               ('%d.Sample1' % study.id): None}
        self.assertEqual(pt.ebi_experiment_accessions, exp)

        # actual test
        obs = study_prep_get_req(study.id, user_email)
        exp = {
            'info': {
                '16S': [
                    {'status': 'sandbox',
                     'name': 'Prep information %d' % pt.id,
                     'start_artifact': None, 'youngest_artifact': None,
                     'ebi_experiment': False, 'id': pt.id,
                     'start_artifact_id': None}]
            },
            'message': '',
            'status': 'success'}
        self.assertEqual(obs, exp)

        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_study_prep_get_req_no_access(self):
        obs = study_prep_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_study_delete_req_no_access(self):
        obs = study_delete_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_study_delete_req_no_exists(self):
        obs = study_delete_req(4, 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Study does not exist'}
        self.assertEqual(obs, exp)

    def test_study_files_get_req(self):
        obs = study_files_get_req('test@foo.bar', 1, 1, 'FASTQ')
        exp = {'status': 'success',
               'message': '',
               'remaining': ['uploaded_file.txt'],
               'file_types': [('raw_barcodes', True, []),
                              ('raw_forward_seqs', True, []),
                              ('raw_reverse_seqs', False, [])],
               'num_prefixes': 1,
               'artifacts': [(1, 'Identification of the Microbiomes for '
                                 'Cannabis Soils (1) - Raw data 1 (1)')]}
        self.assertEqual(obs, exp)

        obs = study_files_get_req('admin@foo.bar', 1, 1, 'FASTQ')
        exp = {'status': 'success',
               'message': '',
               'remaining': ['uploaded_file.txt'],
               'file_types': [('raw_barcodes', True, []),
                              ('raw_forward_seqs', True, []),
                              ('raw_reverse_seqs', False, [])],
               'num_prefixes': 1,
               'artifacts': [(1, 'Identification of the Microbiomes for '
                                 'Cannabis Soils (1) - Raw data 1 (1)')]}
        self.assertEqual(obs, exp)

        # adding a new study for further testing
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": qdb.study.StudyPerson(3),
            "lab_person_id": qdb.study.StudyPerson(1)
        }
        new_study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Some New Study to get files", info)

        # check that you can't call a this function using two unrelated
        # study_id and prep_template_id
        with self.assertRaises(IncompetentQiitaDeveloperError):
            study_files_get_req('test@foo.bar', new_study.id, 1, 'FASTQ')

    def test_study_files_get_req_multiple(self):
        study_id = 1
        # adding a new prep for testing
        PREP = qdb.metadata_template.prep_template.PrepTemplate
        prep_info_dict = {
            'SKB7.640196': {'run_prefix': 'test_1'},
            'SKB8.640193': {'run_prefix': 'test_2'}
        }
        prep_info = pd.DataFrame.from_dict(prep_info_dict,
                                           orient='index', dtype=str)
        pt = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, PREP.create, prep_info,
            qdb.study.Study(study_id), "Metagenomic")

        # getting the upload folder so we can test
        study_upload_dir = join(
            qdb.util.get_mountpoint("uploads")[0][1], str(study_id))

        # adding just foward per sample FASTQ to the upload folder
        filenames = ['test_1.R1.fastq.gz', 'test_2.R1.fastq.gz']
        for f in filenames:
            fpt = join(study_upload_dir, f)
            open(fpt, 'wb', 0).close()
            self._clean_up_files.append(fpt)
        obs = study_files_get_req(
            'shared@foo.bar', 1, pt.id, 'per_sample_FASTQ')
        exp = {
            'status': 'success', 'num_prefixes': 2, 'artifacts': [],
            'remaining': ['uploaded_file.txt'], 'message': '',
            'file_types': [
                ('raw_forward_seqs', True,
                 sorted(['test_2.R1.fastq.gz', 'test_1.R1.fastq.gz'])),
                ('raw_reverse_seqs', False, [])]}
        # making sure they are always in the same order
        oft = obs['file_types'][0]
        obs['file_types'][0] = (oft[0], oft[1], sorted(oft[2]))
        self.assertEqual(obs, exp)

        # let's add reverse
        filenames = ['test_1.R2.fastq.gz', 'test_2.R2.fastq.gz']
        for f in filenames:
            fpt = join(study_upload_dir, f)
            open(fpt, 'wb', 0).close()
            self._clean_up_files.append(fpt)
        obs = study_files_get_req(
            'shared@foo.bar', 1, pt.id, 'per_sample_FASTQ')
        exp = {'status': 'success', 'num_prefixes': 2, 'artifacts': [],
               'remaining': ['uploaded_file.txt'], 'message': '',
               'file_types': [
                   ('raw_forward_seqs', True, sorted(
                       ['test_2.R1.fastq.gz', 'test_1.R1.fastq.gz'])),
                   ('raw_reverse_seqs', False, sorted(
                       ['test_2.R2.fastq.gz', 'test_1.R2.fastq.gz']))]}
        # making sure they are always in the same order
        oft = obs['file_types']
        obs['file_types'][0] = (oft[0][0], oft[0][1], sorted(oft[0][2]))
        obs['file_types'][1] = (oft[1][0], oft[1][1], sorted(oft[1][2]))
        self.assertEqual(obs, exp)

        # let's an extra file that matches
        filenames = ['test_1.R3.fastq.gz']
        for f in filenames:
            fpt = join(study_upload_dir, f)
            open(fpt, 'wb', 0).close()
            self._clean_up_files.append(fpt)
        obs = study_files_get_req(
            'shared@foo.bar', 1, pt.id, 'per_sample_FASTQ')
        exp = {'status': 'success', 'num_prefixes': 2, 'artifacts': [],
               'remaining': ['test_1.R1.fastq.gz', 'test_1.R2.fastq.gz',
                             'test_1.R3.fastq.gz', 'uploaded_file.txt'],
               'message':  "Check these run_prefix:\n'test_1' has 3 matches.",
               'file_types': [('raw_forward_seqs', True,
                               ['test_2.R1.fastq.gz']),
                              ('raw_reverse_seqs', False,
                              ['test_2.R2.fastq.gz'])]}
        self.assertEqual(obs, exp)

        # now if we select FASTQ we have 3 columns so the extra file should go
        # to the 3rd column
        obs = study_files_get_req(
            'shared@foo.bar', 1, pt.id, 'FASTQ')
        exp = {'status': 'success', 'num_prefixes': 2,
               'remaining': ['uploaded_file.txt'],
               'message': '',
               'artifacts': [(1, 'Identification of the Microbiomes for '
                                 'Cannabis Soils (1) - Raw data 1 (1)')],
               'file_types': [
                ('raw_barcodes', True, sorted(
                    ['test_2.R1.fastq.gz', 'test_1.R1.fastq.gz'])),
                ('raw_forward_seqs', True, sorted(
                    ['test_2.R2.fastq.gz', 'test_1.R2.fastq.gz'])),
                ('raw_reverse_seqs', False, ['test_1.R3.fastq.gz'])]}
        # making sure they are always in the same order
        oft = obs['file_types']
        obs['file_types'][0] = (oft[0][0], oft[0][1], sorted(oft[0][2]))
        obs['file_types'][1] = (oft[1][0], oft[1][1], sorted(oft[1][2]))
        self.assertEqual(obs, exp)

        PREP.delete(pt.id)

    def test_study_get_tags_request(self):
        obs = study_get_tags_request('shared@foo.bar', 1)
        exp = {'status': 'success', 'message': '', 'tags': []}
        self.assertEqual(obs, exp)

        # check error
        obs = study_get_tags_request('shared@foo.bar', 2000)
        exp = {'message': 'Study does not exist', 'status': 'error'}
        self.assertEqual(obs, exp)

    def test_study_patch_request_tags(self):
        # adding test for study_tags_request here as it makes sense to check
        # that the tags were added
        obs = study_tags_request()
        exp = {'status': 'success', 'message': '',
               'tags': {'admin': [], 'user': []}}
        self.assertEqual(obs, exp)

        obs = study_patch_request(
            'shared@foo.bar', 1, 'replace', '/tags', ['testA', 'testB'])
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(obs, exp)

        obs = study_tags_request()
        exp = {'status': 'success', 'message': '',
               'tags': {'admin': [], 'user': ['testA', 'testB']}}
        self.assertEqual(obs, exp)

        obs = study_patch_request(
            'shared@foo.bar', 2000, 'replace', '/tags', ['testA', 'testB'])
        exp = {'message': 'Study does not exist', 'status': 'error'}
        self.assertEqual(obs, exp)

    def test_study_patch_request_errors(self):
        # check errors
        obs = study_patch_request(
            'shared@foo.bar', 1, 'no-exists', '/tags', ['testA', 'testB'])
        exp = {'message': ('Operation "no-exists" not supported. Current '
               'supported operations: replace'), 'status': 'error'}
        self.assertEqual(obs, exp)

        obs = study_patch_request(
            'shared@foo.bar', 1, 'replace', '/tags/na', ['testA', 'testB'])
        exp = {'message': 'Incorrect path parameter', 'status': 'error'}
        self.assertEqual(obs, exp)

        obs = study_patch_request(
            'shared@foo.bar', 1, 'replace', '/na')
        exp = {'message': ('Attribute "na" not found. Please, check the '
                           'path parameter'), 'status': 'error'}
        self.assertEqual(obs, exp)

    def test_study_patch_request_specimen_id(self):
        obs = study_patch_request('shared@foo.bar', 1,
                                  'replace', '/specimen_id_column',
                                  'anonymized_name')
        exp = {'status': 'success', 'message': 'Successfully updated '
                                               'specimen id column'}
        self.assertEqual(obs, exp)

        obs = study_patch_request('shared@foo.bar', 1,
                                  'replace', '/specimen_id_column',
                                  'host_subject_id')
        exp = {'status': 'success', 'message': 'Successfully updated '
                                               'specimen id column'}
        self.assertEqual(obs, exp)

        qdb.study.Study(1).specimen_id_column = None

    def test_study_patch_request_specimen_id_errors(self):
        obs = study_patch_request('shared@foo.bar', 1,
                                  'replace', '/specimen_id_column',
                                  'taxon_id')
        exp = {'status': 'error', 'message': 'The category does not contain'
               ' unique values.'}
        self.assertEqual(obs, exp)

        obs = study_patch_request('shared@foo.bar', 1,
                                  'replace', '/specimen_id_column',
                                  'bleep_bloop')
        exp = {'status': 'error', 'message': "Category 'bleep_bloop' is not"
               " present in the sample information."}
        self.assertEqual(obs, exp)

    def test_study_patch_request_toggle_public_raw_download(self):
        study_id = 1
        study = qdb.study.Study(study_id)
        obs = study_patch_request('shared@foo.bar', study_id,
                                  'replace', '/toggle_public_raw_download',
                                  None)
        exp = {'status': 'success', 'message': 'Successfully updated '
                                               'public_raw_download'}
        self.assertEqual(obs, exp)
        self.assertTrue(study.public_raw_download)

        obs = study_patch_request('demo@microbio.me', study_id,
                                  'replace', '/specimen_id_column',
                                  'host_subject_id')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)
        self.assertTrue(study.public_raw_download)

        # returning to default status
        study.public_raw_download = False


class TestStudyAPI2(TestStudyAPI):
    # This test expects a clean DB so creating it's own class
    def test_study_prep_get_req(self):
        obs = study_prep_get_req(1, 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'info': {
                   '18S': [{
                       'id': 1,
                       'status': 'private',
                       'name': 'Prep information 1',
                       'start_artifact_id': 1,
                       'start_artifact': 'FASTQ',
                       'youngest_artifact': 'BIOM - BIOM',
                       'ebi_experiment': 27}, {
                       'id': 2,
                       'status': 'private',
                       'name': 'Prep information 2',
                       'start_artifact': 'BIOM',
                       'youngest_artifact': 'BIOM - BIOM',
                       'ebi_experiment': 27,
                       'start_artifact_id': 7}]}}
        self.assertEqual(obs, exp)

        # Add a new prep template
        pt = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.prep_template.PrepTemplate.create,
            pd.DataFrame({'new_col': {'1.SKD6.640190': 1}}),
            qdb.study.Study(1), '16S')
        obs = study_prep_get_req(1, 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'info': {
                   '18S': [{'id': 1,
                            'status': 'private',
                            'name': 'Prep information 1',
                            'start_artifact_id': 1,
                            'start_artifact': 'FASTQ',
                            'youngest_artifact': 'BIOM - BIOM',
                            'ebi_experiment': 27},
                           {'id': 2,
                            'status': 'private',
                            'name': 'Prep information 2',
                            'start_artifact_id': 7,
                            'start_artifact': 'BIOM',
                            'youngest_artifact': 'BIOM - BIOM',
                            'ebi_experiment': 27}],
                   '16S': [{'id': pt.id,
                            'status': 'sandbox',
                            'name': 'Prep information %d' % pt.id,
                            'start_artifact_id': None,
                            'start_artifact': None,
                            'youngest_artifact': None,
                            'ebi_experiment': 0}]}}
        self.assertEqual(obs, exp)

        obs = study_prep_get_req(1, 'admin@foo.bar')
        self.assertEqual(obs, exp)

        qdb.artifact.Artifact(1).visibility = 'public'
        obs = study_prep_get_req(1, 'demo@microbio.me')
        exp = {'status': 'success',
               'message': '',
               'info': {
                   '18S': [{'id': 1,
                            'status': 'public',
                            'name': 'Prep information 1',
                            'start_artifact_id': 1,
                            'start_artifact': 'FASTQ',
                            'youngest_artifact': 'BIOM - BIOM',
                            'ebi_experiment': 27}]}}
        self.assertEqual(obs, exp)
        # Reset visibility of the artifacts
        for i in range(4, 0, -1):
            qdb.artifact.Artifact(i).visibility = "private"

        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)


if __name__ == '__main__':
    main()
