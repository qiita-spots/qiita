from unittest import main
from collections import namedtuple

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.study import StudyPerson, Study
from qiita_db.util import get_count, check_count
from qiita_db.user import User
from qiita_pet.handlers.study_handlers import (
    _get_shared_links_for_study, _build_study_info)


class TestHelpers(TestHandlerBase):
    database = True

    def test_get_shared_links_for_study(self):
        obs = _get_shared_links_for_study(Study(1))
        exp = '<a target="_blank" href="mailto:shared@foo.bar">Shared</a>'
        self.assertEqual(obs, exp)

    def test_build_study_info(self):
        Study(1).status = 'public'
        obs = _build_study_info('public', User('test@foo.bar'))
        StudyTuple = namedtuple('StudyInfo', 'id title meta_complete '
                                'num_samples_collected shared num_raw_data pi '
                                'pmids owner status')
        exp = [
            StudyTuple(
                id=1,
                title='Identification of the Microbiomes for Cannabis Soils',
                meta_complete=True, num_samples_collected=27,
                shared='<a target="_blank" href="mailto:shared@foo.bar">'
                       'Shared</a>',
                num_raw_data=2,
                pi='<a target="_blank" href="mailto:PI_dude@foo.bar">'
                   'PIDude</a>',
                pmids='<a target="_blank" href="http://www.ncbi.nlm.nih.gov/'
                      'pubmed/123456">123456</a>, '
                      '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/'
                      'pubmed/7891011">7891011</a>',
                owner='<a target="_blank" href="mailto:test@foo.bar">'
                      'test@foo.bar</a>',
                status='public')]
        self.assertEqual(obs, exp)

    def test_build_study_info_new_study(self):
        info = {
            'timeseries_type_id': 1,
            'portal_type_id': 1,
            'lab_person_id': None,
            'principal_investigator_id': 3,
            'metadata_complete': False,
            'mixs_compliant': True,
            'study_description': 'desc',
            'study_alias': 'alias',
            'study_abstract': 'abstract'}
        user = User('shared@foo.bar')

        Study.create(user, 'test_study_1', efo=[1], info=info)

        obs = _build_study_info('private', user)

        StudyTuple = namedtuple('StudyInfo', 'id title meta_complete '
                                'num_samples_collected shared num_raw_data pi '
                                'pmids owner status')
        exp = [
            StudyTuple(
                id=2,
                title='test_study_1',
                meta_complete=False, num_samples_collected=None,
                shared='',
                num_raw_data=0,
                pi='<a target="_blank" href="mailto:PI_dude@foo.bar">'
                   'PIDude</a>',
                pmids='',
                owner='<a target="_blank" href="mailto:shared@foo.bar">'
                      'shared@foo.bar</a>',
                status='sandbox')]
        self.assertEqual(obs, exp)


class TestStudyEditorForm(TestHandlerBase):
    # TODO: add proper test for this once figure out how. Issue 567
    pass


class TestStudyEditorExtendedForm(TestHandlerBase):
    # TODO: add proper test for this once figure out how. Issue 567
    pass


class TestPrivateStudiesHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/private/')
        self.assertEqual(response.code, 200)


class TestPublicStudiesHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/public/')
        self.assertEqual(response.code, 200)


class TestStudyDescriptionHandler(TestHandlerBase):
    def test_get_exists(self):
        response = self.get('/study/description/1')
        self.assertEqual(response.code, 200)

    def test_get_no_exists(self):
        response = self.get('/study/description/245')
        self.assertEqual(response.code, 404)

    def test_post(self):
        post_args = {}
        response = self.post('/study/description/1', post_args)
        self.assertEqual(response.code, 200)

    def test_post_no_exists(self):
        post_args = {}
        response = self.post('/study/description/245', post_args)
        self.assertEqual(response.code, 404)


class TestStudyEditHandler(TestHandlerBase):
    database = True

    def test_get(self):
        """Make sure the page loads when no arguments are passed"""
        response = self.get('/study/create/')
        self.assertEqual(response.code, 200)
        self.assertNotEqual(str(response.body), "")

    def test_get_edit(self):
        """Make sure the page loads when we want to edit a study"""
        response = self.get('/study/edit/1')
        self.assertEqual(response.code, 200)
        self.assertNotEqual(str(response.body), "")

    def test_post(self):
        person_count_before = get_count('qiita.study_person')
        study_count_before = get_count('qiita.study')

        post_data = {'new_people_names': ['Adam', 'Ethan'],
                     'new_people_emails': ['a@mail.com', 'e@mail.com'],
                     'new_people_affiliations': ['CU Boulder', 'NYU'],
                     'new_people_addresses': ['Some St., Boulder, CO 80305',
                                              ''],
                     'new_people_phones': ['', ''],
                     'study_title': 'dummy title',
                     'study_alias': 'dummy alias',
                     'pubmed_id': 'dummy pmid',
                     'environmental_packages': ['air'],
                     'timeseries': '1',
                     'study_abstract': "dummy abstract",
                     'study_description': 'dummy description',
                     'principal_investigator': '-2',
                     'lab_person': '1'}

        self.post('/study/create/', post_data)

        # Check that the new person was created
        expected_id = person_count_before + 1
        self.assertTrue(check_count('qiita.study_person', expected_id))

        new_person = StudyPerson(expected_id)
        self.assertTrue(new_person.name == 'Ethan')
        self.assertTrue(new_person.email == 'e@mail.com')
        self.assertTrue(new_person.affiliation == 'NYU')
        self.assertTrue(new_person.address is None)
        self.assertTrue(new_person.phone is None)

        # Check the study was created
        expected_id = study_count_before + 1
        self.assertTrue(check_count('qiita.study', expected_id))

    def test_post_edit(self):
        study_count_before = get_count('qiita.study')
        study = Study(1)
        study_info = study.info

        post_data = {
            'new_people_names': [],
            'new_people_emails': [],
            'new_people_affiliations': [],
            'new_people_addresses': [],
            'new_people_phones': [],
            'study_title': 'dummy title',
            'study_alias': study_info['study_alias'],
            'pubmed_id': ','.join(study.pmids),
            'study_abstract': study_info['study_abstract'],
            'study_description': study_info['study_description'],
            'principal_investigator': study_info['principal_investigator_id'],
            'lab_person': study_info['lab_person_id']}

        self.post('/study/edit/1', post_data)

        # Check that the study was updated
        self.assertTrue(check_count('qiita.study', study_count_before))
        self.assertEqual(study.title, 'dummy title')


class TestCreateStudyAJAX(TestHandlerBase):
    database = True

    def test_get(self):

        response = self.get('/check_study/', {'study_title': 'notreal'})
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(response.body, 'True')

        response = self.get('/check_study/')
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(response.body, 'False')

        response = self.get(
            '/check_study/',
            {'study_title':
             'Identification of the Microbiomes for Cannabis Soils'})
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(response.body, 'False')


class TestMetadataSummaryHandler(TestHandlerBase):
    def test_get_exists(self):
        response = self.get('/metadata_summary/', {'sample_template': 1,
                                                   'prep_template': 1,
                                                   'study_id': 1})
        self.assertEqual(response.code, 200)

    def test_get_no_exist(self):
        response = self.get('/metadata_summary/', {'sample_template': 237,
                                                   'prep_template': 1,
                                                   'study_id': 237})
        self.assertEqual(response.code, 404)


class TestEBISubmitHandler(TestHandlerBase):
    # TODO: add proper test for this once figure out how. Issue 567
    pass


if __name__ == "__main__":
    main()
