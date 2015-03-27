from unittest import main
from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.study import StudyPerson, Study
from qiita_db.data import ProcessedData
from qiita_db.util import get_count, check_count
from qiita_db.user import User
from qiita_pet.handlers.study_handlers.listing_handlers import (
    _get_shared_links_for_study, _build_study_info)


class TestHelpers(TestHandlerBase):
    database = True

    def setUp(self):
        self.exp = [{
            'status': 'public',
            'checkbox': "<input type='checkbox' value='1' />",
            'abstract': 'This is a preliminary study to examine the microbiota'
                        ' associated with the Cannabis plant. Soils samples '
                        'from the bulk soil, soil associated with the roots, '
                        'and the rhizosphere were extracted and the DNA '
                        'sequenced. Roots from three independent plants of '
                        'different strains were examined. These roots were '
                        'obtained November 11, 2011 from plants that had been '
                        'harvested in the summer. Future studies will attempt '
                        'to analyze the soils and rhizospheres from the same '
                        'location at different time points in the plant '
                        'lifecycle.',
            'owner': '<a target="_blank" href="mailto:test@foo.bar">test@foo.'
                     'bar</a>',
            'meta_complete': "<span class='glyphicon glyphicon-ok'></span>",
            'title': '<a href=\'#\' data-toggle=\'modal\' data-target=\''
                     '#study-abstract-modal\' onclick=\'fillAbstract("standard'
                     '-studies-table", 0)\'><span class=\'glyphicon glyphicon'
                     '-file\' aria-hidden=\'true\'></span></a> | <a href=\'/'
                     'study/description/1\' id=\'study0-title\'>Identification'
                     ' of the Microbiomes for Cannabis Soils</a>',
            'num_raw_data': 4, 'id': 1, 'num_samples': 27,
            'shared': 'Not Available',
            'pmid': '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/'
                    'pubmed/123456">123456</a>, <a target="_blank" href="http:'
                    '//www.ncbi.nlm.nih.gov/pubmed/7891011">7891011</a>',
            'pi': '<a target="_blank" href="mailto:PI_dude@foo.bar">PIDude</a>'
        }]
        super(TestHelpers, self).setUp()

    def test_get_shared_links_for_study(self):
        obs = _get_shared_links_for_study(Study(1))
        exp = '<a target="_blank" href="mailto:shared@foo.bar">Shared</a>'
        self.assertEqual(obs, exp)

    def test_build_study_info(self):
        ProcessedData(1).status = 'public'
        obs = _build_study_info('standard', User('test@foo.bar'))
        self.assertEqual(obs, self.exp)

    def test_build_study_info_new_study(self):
        ProcessedData(1).status = 'public'
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
        user = User('test@foo.bar')

        Study.create(user, 'test_study_1', efo=[1], info=info)
        obs = _build_study_info('standard', user)
        self.exp.append({
            'status': 'sandbox',
            'checkbox': "<input type='checkbox' value='2' />",
            'abstract': 'abstract',
            'owner': '<a target="_blank" href="mailto:test@foo.bar">test@foo.'
            'bar</a>',
            'meta_complete': "<span class='glyphicon glyphicon-remove'>"
            "</span>",
            'title': '<a href=\'#\' data-toggle=\'modal\' data-target=\'#study'
            '-abstract-modal\' onclick=\'fillAbstract("standard-studies-table"'
            ', 1)\'><span class=\'glyphicon glyphicon-file\' aria-hidden=\''
            'true\'></span></a> | <a href=\'/study/description/2\' id=\''
            'study1-title\'>test_study_1</a>',
            'num_raw_data': 0, 'id': 2, 'num_samples': '0',
            'shared': "<span id='shared_html_2'></span><br/><a class='btn "
            "btn-primary btn-xs' data-toggle='modal' data-target='#share-study"
            "-modal-view' onclick='modify_sharing(2);'>Modify</a>",
            'pmid': '', 'pi':
            '<a target="_blank" href="mailto:PI_dude@foo.bar">PIDude</a>'})
        self.assertEqual(obs, self.exp)


class TestStudyEditorForm(TestHandlerBase):
    # TODO: add proper test for this once figure out how. Issue 567
    pass


class TestStudyEditorExtendedForm(TestHandlerBase):
    # TODO: add proper test for this once figure out how. Issue 567
    pass


class TestListStudiesHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/list/')
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

    def test_update_sample_template(self):
        # not sending file
        post_args = {
            'sample_template': '',
            'action': 'update_sample_template'
        }
        response = self.post('/study/description/1', post_args)
        self.assertEqual(response.code, 200)

        # sending blank file
        post_args = {
            'sample_template': 'uploaded_file.txt',
            'action': 'update_sample_template'
        }
        response = self.post('/study/description/1', post_args)
        self.assertEqual(response.code, 200)

    def test_create_raw_data(self):
        # testing adding new raw data
        post_args = {
            'filetype': '1',
            'action': 'create_raw_data'
        }
        response = self.post('/study/description/1', post_args)
        self.assertEqual(response.code, 200)

        # testing an error due to previous raw data already added
        post_args = {
            'previous_raw_data': '1',
            'action': 'create_raw_data'
        }
        response = self.post('/study/description/1', post_args)
        self.assertEqual(response.code, 500)

        # testing an error due to previous_raw_data not existing
        post_args = {
            'previous_raw_data': '5',
            'action': 'create_raw_data'
        }
        response = self.post('/study/description/1', post_args)
        self.assertEqual(response.code, 500)


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


class TestSearchStudiesAJAX(TestHandlerBase):
    database = False

    json = {
        'iTotalRecords': 1, 'sEcho': 1021, 'iTotalDisplayRecords': 1,
        'aaData': [{
            'status': 'private',
            'checkbox': "<input type='checkbox' value='1' />",
            'title': '<a href=\'#\' data-toggle=\'modal\' data-target=\'#study'
            '-abstract-modal\' onclick=\'fillAbstract("standard-studies-table"'
            ', 0)\'><span class=\'glyphicon glyphicon-file\' aria-hidden=\''
            'true\'></span></a> | <a href=\'/study/description/1\' id=\''
            'study0-title\'>Identification of the Microbiomes for Cannabis '
            'Soils</a>',
            'abstract': 'This is a preliminary study to examine the microbiota'
            ' associated with the Cannabis plant. Soils samples from the bulk'
            ' soil, soil associated with the roots, and the rhizosphere were '
            'extracted and the DNA sequenced. Roots from three independent '
            'plants of different strains were examined. These roots were '
            'obtained November 11, 2011 from plants that had been harvested in'
            ' the summer. Future studies will attempt to analyze the soils and'
            ' rhizospheres from the same location at different time points in '
            'the plant lifecycle.',
            'pi': '<a target="_blank" href="mailto:PI_dude@foo.bar">PIDude'
            '</a>',
            'id': 1,
            'num_samples': 27,
            'owner': '<a target="_blank" href="mailto:test@foo.bar">test@foo.'
            'bar</a>',
            'shared': '<span id=\'shared_html_1\'><a target="_blank" href="'
            'mailto:shared@foo.bar">Shared</a></span><br/><a class=\'btn '
            'btn-primary btn-xs\' data-toggle=\'modal\' data-target=\'#share'
            '-study-modal-view\' onclick=\'modify_sharing(1);\'>Modify</a>',
            'meta_complete': "<span class='glyphicon glyphicon-ok'>"
            "</span>",
            'pmid': '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/'
            'pubmed/123456">123456</a>, <a target="_blank" href="http://www.'
            'ncbi.nlm.nih.gov/pubmed/7891011">7891011</a>',
            'num_raw_data': 4}]}
    empty = {'aaData': [],
             'iTotalDisplayRecords': 0,
             'iTotalRecords': 0,
             'sEcho': 1021}

    def test_get(self):
        response = self.get('/study/search/', {
            'type': 'standard',
            'user': 'test@foo.bar',
            'query': '',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(loads(response.body), self.json)

        response = self.get('/study/search/', {
            'type': 'shared',
            'user': 'test@foo.bar',
            'query': '',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(loads(response.body), self.empty)

        response = self.get('/study/search/', {
            'type': 'standard',
            'user': 'test@foo.bar',
            'query': 'ph > 50',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(loads(response.body), self.empty)

    def test_get_failure(self):
        response = self.get('/study/search/', {
            'type': 'standard',
            'user': 'test@foo.bar',
            'query': 'ph',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 400)
        # make sure responds properly
        self.assertEqual(response.body, 'Malformed search query. '
                         'Please read "search help" and try again.')

        response = self.get('/study/search/', {
            'type': 'standard',
            'user': 'FAKE@foo.bar',
            'query': 'ph',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 403)


class TestMetadataSummaryHandler(TestHandlerBase):
    def test_error_prep_and_sample(self):
        response = self.get('/metadata_summary/', {'sample_template': 1,
                                                   'prep_template': 1,
                                                   'study_id': 1})
        self.assertEqual(response.code, 500)

    def test_error_no_prep_no_sample(self):
        response = self.get('/metadata_summary/', {'study_id': 1})
        self.assertEqual(response.code, 500)

    def test_get_exists_prep(self):
        response = self.get('/metadata_summary/', {'prep_template': 1,
                                                   'study_id': 1})
        self.assertEqual(response.code, 200)

    def test_get_exists_sample(self):
        response = self.get('/metadata_summary/', {'sample_template': 1,
                                                   'study_id': 1})
        self.assertEqual(response.code, 200)

    def test_get_no_exist(self):
        response = self.get('/metadata_summary/', {'sample_template': 237,
                                                   'study_id': 237})
        self.assertEqual(response.code, 500)


class TestEBISubmitHandler(TestHandlerBase):
    # TODO: add proper test for this once figure out how. Issue 567
    pass


if __name__ == "__main__":
    main()
