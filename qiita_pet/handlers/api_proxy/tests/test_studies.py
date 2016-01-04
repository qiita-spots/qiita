from unittest import TestCase, main
import datetime

from qiita_pet.handlers.api_proxy.studies import (
    data_types_get_req, study_get_req)


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
            'info': {
                'number_samples_collected': 27,
                'mixs_compliant': True,
                'metadata_complete': True,
                'reprocess': False,
                'emp_person_id': 2,
                'number_samples_promised': 27,
                'funding': None,
                'vamps_id': None,
                'first_contact': datetime.datetime(2014, 5, 19, 16, 10),
                'timeseries_type_id': 1,
                'study_abstract':
                    'This is a preliminary study to examine the microbiota '
                    'associated with the Cannabis plant. Soils samples from '
                    'the bulk soil, soil associated with the roots, and the '
                    'rhizosphere were extracted and the DNA sequenced. Roots '
                    'from three independent plants of different strains were '
                    'examined. These roots were obtained November 11, 2011 '
                    'from plants that had been harvested in the summer. Future'
                    ' studies will attempt to analyze the soils and '
                    'rhizospheres from the same location at different time '
                    'points in the plant lifecycle.',
                'status': 'private',
                'spatial_series': False,
                'study_description':
                    'Analysis of the Cannabis Plant Microbiome',
                'shared_with': ['shared@foo.bar'],
                'lab_person': 'LabDude (knight lab)',
                'principal_investigator': 'PIDude (Wash U)',
                'study_alias': 'Cannabis Soils',
                'study_id': 1,
                'most_recent_contact': datetime.datetime(2014, 5, 19, 16, 11),
                'publications': [['10.100/123456', '123456'],
                                 ['10.100/7891011', '7891011']],
                'num_samples': 27,
                'study_title': 'Identification of the Microbiomes for Cannabis'
                               ' Soils'
            }}
        self.assertEqual(obs, exp)

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

if __name__ == '__main__':
    main()
