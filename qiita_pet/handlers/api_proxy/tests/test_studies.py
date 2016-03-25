# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from datetime import datetime

import pandas as pd
import numpy.testing as npt

from qiita_core.util import qiita_test_checker
import qiita_db as qdb
from qiita_pet.handlers.api_proxy.studies import (
    data_types_get_req, study_get_req, study_prep_get_req, study_delete_req,
    study_files_get_req)


@qiita_test_checker()
class TestStudyAPI(TestCase):
    def test_data_types_get_req(self):
        obs = data_types_get_req()
        exp = {
            'status': 'success',
            'message': '',
            'data_types': ['16S', '18S', 'ITS', 'Proteomic', 'Metagenomic',
                           'Metabolomic']}
        self.assertItemsEqual(obs, exp)

    def test_study_get_req(self):
        obs = study_get_req(1, 'test@foo.bar')
        exp = {
            'status': 'success',
            'message': '',
            'study_info': {
                'mixs_compliant': True,
                'metadata_complete': True,
                'reprocess': False,
                'emp_person_id': 2,
                'number_samples_promised': 27,
                'funding': None,
                'vamps_id': None,
                'first_contact': datetime(2014, 5, 19, 16, 10),
                'timeseries_type_id': 1,
                'study_abstract':
                    'This is a preliminary study to examine the microbiota '
                    'associated with the Cannabis plant. Soils samples from '
                    'the bulk soil, soil associated with the roots, and the '
                    'rhizosphere were extracted and the DNA sequenced. Roots '
                    'from three independent plants of different strains were '
                    'examined. These roots were obtained November 11, 2011 '
                    'from plants that had been harvested in the summer. '
                    'Future studies will attempt to analyze the soils and '
                    'rhizospheres from the same location at different time '
                    'points in the plant lifecycle.',
                'status': 'private',
                'spatial_series': False,
                'study_description': 'Analysis of the Cannabis Plant '
                                     'Microbiome',
                'shared_with': ['shared@foo.bar'],
                'lab_person': {'affiliation': 'knight lab',
                               'name': 'LabDude',
                               'email': 'lab_dude@foo.bar'},
                'principal_investigator': {'affiliation': 'Wash U',
                                           'name': 'PIDude',
                                           'email': 'PI_dude@foo.bar'},
                'study_alias': 'Cannabis Soils',
                'study_id': 1,
                'most_recent_contact': datetime(2014, 5, 19, 16, 11),
                'publications': [['10.100/123456', '123456'],
                                 ['10.100/7891011', '7891011']],
                'num_samples': 27,
                'study_title': 'Identification of the Microbiomes for '
                               'Cannabis Soils',
                'number_samples_collected': 27},
            'editable': True}

        self.assertEqual(obs, exp)

        # Test with no lab person
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": qdb.study.StudyPerson(3),
            'first_contact': datetime(2015, 5, 19, 16, 10),
            'most_recent_contact': datetime(2015, 5, 19, 16, 11),
        }

        new_study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Some New Study", [1],
            info)

        obs = study_get_req(new_study.id, 'test@foo.bar')
        exp = {
            'status': 'success',
            'message': '',
            'study_info': {
                'mixs_compliant': True,
                'metadata_complete': True,
                'reprocess': False,
                'emp_person_id': None,
                'number_samples_promised': 28,
                'funding': None,
                'vamps_id': None,
                'first_contact': datetime(2015, 5, 19, 16, 10),
                'timeseries_type_id': 1,
                'study_abstract': 'ABS',
                'status': 'private',
                'spatial_series': False,
                'study_description': 'DESC',
                'shared_with': [],
                'lab_person': None,
                'principal_investigator': {'affiliation': 'Wash U',
                                           'name': 'PIDude',
                                           'email': 'PI_dude@foo.bar'},
                'study_alias': 'FCM',
                'study_id': new_study.id,
                'most_recent_contact': datetime(2015, 5, 19, 16, 11),
                'publications': [],
                'num_samples': 25,
                'study_title': 'Some New Study',
                'number_samples_collected': 27},
            'editable': True}
        self.assertItemsEqual(obs, exp)

    def test_study_get_req_no_access(self):
        obs = study_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_study_get_req_no_exists(self):
        obs = study_get_req(4, 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Study does not exist'}
        self.assertEqual(obs, exp)

    def test_study_prep_get_req(self):
        obs = study_prep_get_req(1, 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'info': {'18S': [{
                   'id': 1,
                   'status': 'private',
                   'name': 'PREP 1 NAME',
                   'start_artifact_id': 1,
                   'start_artifact': 'FASTQ',
                   'youngest_artifact': 'BIOM - BIOM'}]}}
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
                            'name': 'PREP 1 NAME',
                            'start_artifact_id': 1,
                            'start_artifact': 'FASTQ',
                            'youngest_artifact': 'BIOM - BIOM'}],
                   '16S': [{'id': pt.id,
                            'status': 'sandbox',
                            'name': 'PREP %d NAME' % pt.id,
                            'start_artifact_id': None,
                            'start_artifact': None,
                            'youngest_artifact': None}]}}
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
                            'name': 'PREP 1 NAME',
                            'start_artifact_id': 1,
                            'start_artifact': 'FASTQ',
                            'youngest_artifact': 'BIOM - BIOM'}]}}
        self.assertEqual(obs, exp)

    def test_study_prep_get_req_no_access(self):
        obs = study_prep_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_study_delete_req(self):
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "emp_person_id": qdb.study.StudyPerson(2),
            "principal_investigator_id": qdb.study.StudyPerson(3),
            "lab_person_id": qdb.study.StudyPerson(1)
        }

        new_study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Some New Study", [1],
            info)

        study_delete_req(new_study.id, 'test@foo.bar')

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.study.Study(new_study.id)

    def test_study_delete_req_error(self):
        obs = study_delete_req(1, 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Unable to delete study: Study "Identification of '
                          'the Microbiomes for Cannabis Soils" cannot be '
                          'erased because it has a sample template'}
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
        obs = study_files_get_req(1, 1, 'FASTQ')
        exp = {'status': 'success',
               'message': '',
               'remaining': ['uploaded_file.txt'],
               'file_types': [('raw_barcodes', True, []),
                              ('raw_forward_seqs', True, []),
                              ('raw_reverse_seqs', False, [])],
               'num_prefixes': 1}
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
