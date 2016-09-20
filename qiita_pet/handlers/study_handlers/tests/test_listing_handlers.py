# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import main
from json import loads

from mock import Mock
from moi import r_client

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.qiita_settings import qiita_config
from qiita_db.artifact import Artifact
from qiita_db.study import Study
from qiita_db.user import User
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.study_handlers.listing_handlers import (
    _build_study_info)
from qiita_pet.handlers.base_handlers import BaseHandler


class TestHelpers(TestHandlerBase):
    def setUp(self):
        super(TestHelpers, self).setUp()

        self.proc_data_exp = [{
            'pid': 4,
            'processed_date': '2012-10-02 17:30:00',
            'data_type': '18S',
            'algorithm': 'sortmerna',
            'reference_name': 'Greengenes',
            'reference_version': '13_8',
            'taxonomy_filepath': 'GreenGenes_13_8_97_otu_taxonomy.txt',
            'sequence_filepath': 'GreenGenes_13_8_97_otus.fasta',
            'tree_filepath': 'GreenGenes_13_8_97_otus.tree',
            'similarity': 0.97,
            'sortmerna_max_pos': 10000,
            'sortmerna_e_value': 1,
            'sortmerna_coverage': 0.97,
            'threads': 1,
            'samples': ['1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195',
                        '1.SKB4.640189', '1.SKB5.640181', '1.SKB6.640176',
                        '1.SKB7.640196', '1.SKB8.640193', '1.SKB9.640200',
                        '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
                        '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190',
                        '1.SKD7.640191', '1.SKD8.640184', '1.SKD9.640182',
                        '1.SKM1.640183', '1.SKM2.640199', '1.SKM3.640197',
                        '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
                        '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192']
        }, {
            'pid': 5,
            'processed_date': '2012-10-02 17:30:00',
            'data_type': '18S',
            'algorithm': 'sortmerna',
            'reference_name': 'Greengenes',
            'reference_version': '13_8',
            'taxonomy_filepath': 'GreenGenes_13_8_97_otu_taxonomy.txt',
            'sequence_filepath': 'GreenGenes_13_8_97_otus.fasta',
            'tree_filepath': 'GreenGenes_13_8_97_otus.tree',
            'similarity': 0.97,
            'sortmerna_max_pos': 10000,
            'sortmerna_e_value': 1,
            'sortmerna_coverage': 0.97,
            'threads': 1,
            'samples': ['1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195',
                        '1.SKB4.640189', '1.SKB5.640181', '1.SKB6.640176',
                        '1.SKB7.640196', '1.SKB8.640193', '1.SKB9.640200',
                        '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
                        '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190',
                        '1.SKD7.640191', '1.SKD8.640184', '1.SKD9.640182',
                        '1.SKM1.640183', '1.SKM2.640199', '1.SKM3.640197',
                        '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
                        '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192']
        }, {
            'pid': 6,
            'processed_date': '2012-10-02 17:30:00',
            'data_type': '16S',
            'algorithm': 'sortmerna',
            'reference_name': 'Silva',
            'reference_version': 'test',
            'taxonomy_filepath': 'Silva_97_otu_taxonomy.txt',
            'sequence_filepath': 'Silva_97_otus.fasta',
            'tree_filepath': '',
            'similarity': 0.97,
            'sortmerna_max_pos': 10000,
            'sortmerna_e_value': 1,
            'sortmerna_coverage': 0.97,
            'threads': 1,
            'samples': ['1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195',
                        '1.SKB4.640189', '1.SKB5.640181', '1.SKB6.640176',
                        '1.SKB7.640196', '1.SKB8.640193', '1.SKB9.640200',
                        '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
                        '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190',
                        '1.SKD7.640191', '1.SKD8.640184', '1.SKD9.640182',
                        '1.SKM1.640183', '1.SKM2.640199', '1.SKM3.640197',
                        '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
                        '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192']
        }, {
            'pid': 7,
            'processed_date': '2012-10-02 17:30:00',
            'data_type': '16S',
            'samples': ['1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195',
                        '1.SKB4.640189', '1.SKB5.640181', '1.SKB6.640176',
                        '1.SKB7.640196', '1.SKB8.640193', '1.SKB9.640200',
                        '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
                        '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190',
                        '1.SKD7.640191', '1.SKD8.640184', '1.SKD9.640182',
                        '1.SKM1.640183', '1.SKM2.640199', '1.SKM3.640197',
                        '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
                        '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192']
        }]
        self.single_exp = {
            'study_id': 1,
            'status': 'private',
            'study_abstract':
                'This is a preliminary study to examine the microbiota '
                'associated with the Cannabis plant. Soils samples '
                'from the bulk soil, soil associated with the roots, '
                'and the rhizosphere were extracted and the DNA '
                'sequenced. Roots from three independent plants of '
                'different strains were examined. These roots were '
                'obtained November 11, 2011 from plants that had been '
                'harvested in the summer. Future studies will attempt '
                'to analyze the soils and rhizospheres from the same '
                'location at different time points in the plant '
                'lifecycle.',
            'metadata_complete': True,
            'ebi_study_accession': 'EBI123456-BB',
            'ebi_submission_status': 'submitted',
            'study_title':
                'Identification of the Microbiomes for Cannabis Soils',
            'number_samples_collected': 27,
            'shared': [('shared@foo.bar', 'Shared')],
            'publication_doi': ['10.100/123456', '10.100/7891011'],
            'pmid': ['7891011', '123456'],
            'pi': ('PI_dude@foo.bar', 'PIDude'),
            'proc_data_info': self.proc_data_exp
        }
        self.exp = [self.single_exp]

    def test_build_study_info(self):
        obs = _build_study_info(User('test@foo.bar'), 'user')
        self.assertEqual(obs, self.exp)

    def test_build_study_info_erros(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            _build_study_info(User('test@foo.bar'), 'user', study_proc={})
        with self.assertRaises(IncompetentQiitaDeveloperError):
            _build_study_info(User('test@foo.bar'), 'user', proc_samples={})
        with self.assertRaises(ValueError):
            _build_study_info(User('test@foo.bar'), 'wrong')


class TestBuildStudyWithDBAccess(TestHelpers):
    database = True

    def test_build_study_info_empty_study(self):
        info = {
            'timeseries_type_id': 1,
            'lab_person_id': None,
            'principal_investigator_id': 3,
            'metadata_complete': False,
            'mixs_compliant': True,
            'study_description': 'desc',
            'study_alias': 'alias',
            'study_abstract': 'abstract'}
        Study.create(User('test@foo.bar'), "My study", efo=[1], info=info)
        obs = _build_study_info(User('test@foo.bar'), 'user')

        self.exp.append({
            'metadata_complete': False,
            'ebi_submission_status':
            'not submitted',
            'shared': [],
            'pmid': [],
            'pi': ('PI_dude@foo.bar', 'PIDude'),
            'status': 'private',
            'proc_data_info': [],
            'publication_doi': [],
            'study_abstract': 'abstract',
            'study_id': 2,
            'ebi_study_accession': None,
            'study_title': 'My study',
            'number_samples_collected': 0})
        self.assertItemsEqual(obs, self.exp)


class TestListStudiesHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/list/')
        self.assertEqual(response.code, 200)


class TestStudyApprovalList(TestHandlerBase):
    database = True

    def test_get(self):
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        Artifact(4).visibility = "awaiting_approval"
        response = self.get('/admin/approval/')
        self.assertEqual(response.code, 200)
        self.assertIn("test@foo.bar", response.body)


class TestAutocompleteHandler(TestHandlerBase):
    database = False

    base_url = '/study/sharing/autocomplete/?text=%s'

    def test_get(self):
        # Create the usernames key so we can do autocomplete
        r_client.zadd('qiita-usernames', **{u: 0 for u in User.iter()})
        response = self.get(self.base_url % 't')
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body),
                         {'results': [{"id": "test@foo.bar",
                                       "text": "test@foo.bar"}]})

        response = self.get(self.base_url % 'admi')
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body),
                         {'results': [{"id": "admin@foo.bar",
                                       "text": "admin@foo.bar"}]})

        response = self.get(self.base_url % 'tesq')
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body),
                         {'results': []})

        r_client.delete('qiita-usernames')


class TestShareStudyAjax(TestHandlerBase):
    database = True

    def test_get_deselected(self):
        s = Study(1)
        u = User('shared@foo.bar')
        args = {'deselected': u.id, 'id': s.id}
        self.assertEqual(s.shared_with, [u])
        response = self.get('/study/sharing/', args)
        self.assertEqual(response.code, 200)
        exp = {'users': [], 'links': ''}
        self.assertEqual(loads(response.body), exp)
        self.assertEqual(s.shared_with, [])

        # Make sure unshared message added to the system
        self.assertEqual('Study \'Identification of the Microbiomes for '
                         'Cannabis Soils\' has been unshared from you.',
                         u.messages()[0][1])
        # Share the study back with the user
        s.share(u)

    def test_get_selected(self):
        s = Study(1)
        u = User('admin@foo.bar')
        args = {'selected': u.id, 'id': s.id}
        response = self.get('/study/sharing/', args)
        self.assertEqual(response.code, 200)
        exp = {
            'users': ['shared@foo.bar', u.id],
            'links':
                ('<a target="_blank" href="mailto:shared@foo.bar">Shared</a>, '
                 '<a target="_blank" href="mailto:admin@foo.bar">Admin</a>')}
        self.assertEqual(loads(response.body), exp)
        self.assertEqual(s.shared_with, [User('shared@foo.bar'), u])

        # Make sure shared message added to the system
        self.assertEqual('Study <a href="/study/description/1">'
                         '\'Identification of the Microbiomes for Cannabis '
                         'Soils\'</a> has been shared with you.',
                         u.messages()[0][1])

    def test_get_no_access(self):
        # Create a new study belonging to the 'shared' user, so 'test' doesn't
        # have access
        info = {
            'timeseries_type_id': 1,
            'lab_person_id': None,
            'principal_investigator_id': 3,
            'metadata_complete': False,
            'mixs_compliant': True,
            'study_description': 'desc',
            'study_alias': 'alias',
            'study_abstract': 'abstract'}
        u = User('shared@foo.bar')
        s = Study.create(u, 'test_study', efo=[1], info=info)
        self.assertEqual(s.shared_with, [])

        args = {'selected': 'test@foo.bar', 'id': s.id}
        response = self.get('/study/sharing/', args)
        self.assertEqual(response.code, 403)
        self.assertEqual(s.shared_with, [])


class TestSearchStudiesAJAX(TestHandlerBase):
    database = True

    def setUp(self):
        super(TestSearchStudiesAJAX, self).setUp()
        self.json = {
            'iTotalRecords': 1, 'sEcho': 1021, 'iTotalDisplayRecords': 1,
            'aaData': [{
                'study_id': 1,
                'status': 'private',
                'study_abstract':
                    'This is a preliminary study to examine the microbiota '
                    'associated with the Cannabis plant. Soils samples '
                    'from the bulk soil, soil associated with the roots, '
                    'and the rhizosphere were extracted and the DNA '
                    'sequenced. Roots from three independent plants of '
                    'different strains were examined. These roots were '
                    'obtained November 11, 2011 from plants that had been '
                    'harvested in the summer. Future studies will attempt '
                    'to analyze the soils and rhizospheres from the same '
                    'location at different time points in the plant '
                    'lifecycle.',
                'metadata_complete': True,
                'ebi_study_accession': 'EBI123456-BB',
                'ebi_submission_status': 'submitted',
                'ebi_info': ('<a href="http://www.ebi.ac.uk/ena/data/view/'
                             'EBI123456-BB" target="_blank">EBI123456-BB</a> '
                             '(submitted)'),
                'study_title':
                    'Identification of the Microbiomes for Cannabis Soils',
                'number_samples_collected': 27,
                'shared': ('<a target="_blank" href="mailto:shared@foo.bar">'
                           'Shared</a>'),
                'publication_doi': (
                    '<a target="_blank" href="http://dx.doi.org/10.100/123456"'
                    '>10.100/123456</a>, <a target="_blank" '
                    'href="http://dx.doi.org/10.100/7891011">'
                    '10.100/7891011</a>'),
                'pmid': ('<a target="_blank" '
                         'href="http://www.ncbi.nlm.nih.gov/pubmed/7891011">'
                         '7891011</a>, <a target="_blank" '
                         'href="http://www.ncbi.nlm.nih.gov/pubmed/123456">'
                         '123456</a>'),
                'pi': ('<a target="_blank" href="mailto:PI_dude@foo.bar">'
                       'PIDude</a>'),
                'proc_data_info': [{
                    'pid': 4,
                    'processed_date': '2012-10-02 17:30:00',
                    'data_type': '18S',
                    'algorithm': 'sortmerna',
                    'reference_name': 'Greengenes',
                    'reference_version': '13_8',
                    'taxonomy_filepath': 'GreenGenes_13_8_97_otu_taxonomy.txt',
                    'sequence_filepath': 'GreenGenes_13_8_97_otus.fasta',
                    'tree_filepath': 'GreenGenes_13_8_97_otus.tree',
                    'similarity': 0.97,
                    'sortmerna_max_pos': 10000,
                    'sortmerna_e_value': 1,
                    'sortmerna_coverage': 0.97,
                    'threads': 1,
                    'samples': ['1.SKB1.640202', '1.SKB2.640194',
                                '1.SKB3.640195', '1.SKB4.640189',
                                '1.SKB5.640181', '1.SKB6.640176',
                                '1.SKB7.640196', '1.SKB8.640193',
                                '1.SKB9.640200', '1.SKD1.640179',
                                '1.SKD2.640178', '1.SKD3.640198',
                                '1.SKD4.640185', '1.SKD5.640186',
                                '1.SKD6.640190', '1.SKD7.640191',
                                '1.SKD8.640184', '1.SKD9.640182',
                                '1.SKM1.640183', '1.SKM2.640199',
                                '1.SKM3.640197', '1.SKM4.640180',
                                '1.SKM5.640177', '1.SKM6.640187',
                                '1.SKM7.640188', '1.SKM8.640201',
                                '1.SKM9.640192']
                    }, {
                    'pid': 5,
                    'processed_date': '2012-10-02 17:30:00',
                    'data_type': '18S',
                    'algorithm': 'sortmerna',
                    'reference_name': 'Greengenes',
                    'reference_version': '13_8',
                    'taxonomy_filepath': 'GreenGenes_13_8_97_otu_taxonomy.txt',
                    'sequence_filepath': 'GreenGenes_13_8_97_otus.fasta',
                    'tree_filepath': 'GreenGenes_13_8_97_otus.tree',
                    'similarity': 0.97,
                    'sortmerna_max_pos': 10000,
                    'sortmerna_e_value': 1,
                    'sortmerna_coverage': 0.97,
                    'threads': 1,
                    'samples': ['1.SKB1.640202', '1.SKB2.640194',
                                '1.SKB3.640195', '1.SKB4.640189',
                                '1.SKB5.640181', '1.SKB6.640176',
                                '1.SKB7.640196', '1.SKB8.640193',
                                '1.SKB9.640200', '1.SKD1.640179',
                                '1.SKD2.640178', '1.SKD3.640198',
                                '1.SKD4.640185', '1.SKD5.640186',
                                '1.SKD6.640190', '1.SKD7.640191',
                                '1.SKD8.640184', '1.SKD9.640182',
                                '1.SKM1.640183', '1.SKM2.640199',
                                '1.SKM3.640197', '1.SKM4.640180',
                                '1.SKM5.640177', '1.SKM6.640187',
                                '1.SKM7.640188', '1.SKM8.640201',
                                '1.SKM9.640192']
                    }, {
                    'pid': 6,
                    'processed_date': '2012-10-02 17:30:00',
                    'data_type': '16S',
                    'algorithm': 'sortmerna',
                    'reference_name': 'Silva',
                    'reference_version': 'test',
                    'taxonomy_filepath': 'Silva_97_otu_taxonomy.txt',
                    'sequence_filepath': 'Silva_97_otus.fasta',
                    'tree_filepath': '',
                    'similarity': 0.97,
                    'sortmerna_max_pos': 10000,
                    'sortmerna_e_value': 1,
                    'sortmerna_coverage': 0.97,
                    'threads': 1,
                    'samples': ['1.SKB1.640202', '1.SKB2.640194',
                                '1.SKB3.640195', '1.SKB4.640189',
                                '1.SKB5.640181', '1.SKB6.640176',
                                '1.SKB7.640196', '1.SKB8.640193',
                                '1.SKB9.640200', '1.SKD1.640179',
                                '1.SKD2.640178', '1.SKD3.640198',
                                '1.SKD4.640185', '1.SKD5.640186',
                                '1.SKD6.640190', '1.SKD7.640191',
                                '1.SKD8.640184', '1.SKD9.640182',
                                '1.SKM1.640183', '1.SKM2.640199',
                                '1.SKM3.640197', '1.SKM4.640180',
                                '1.SKM5.640177', '1.SKM6.640187',
                                '1.SKM7.640188', '1.SKM8.640201',
                                '1.SKM9.640192']
                    }, {
                    'pid': 7,
                    'processed_date': '2012-10-02 17:30:00',
                    'data_type': '16S',
                    'samples': ['1.SKB1.640202', '1.SKB2.640194',
                                '1.SKB3.640195', '1.SKB4.640189',
                                '1.SKB5.640181', '1.SKB6.640176',
                                '1.SKB7.640196', '1.SKB8.640193',
                                '1.SKB9.640200', '1.SKD1.640179',
                                '1.SKD2.640178', '1.SKD3.640198',
                                '1.SKD4.640185', '1.SKD5.640186',
                                '1.SKD6.640190', '1.SKD7.640191',
                                '1.SKD8.640184', '1.SKD9.640182',
                                '1.SKM1.640183', '1.SKM2.640199',
                                '1.SKM3.640197', '1.SKM4.640180',
                                '1.SKM5.640177', '1.SKM6.640187',
                                '1.SKM7.640188', '1.SKM8.640201',
                                '1.SKM9.640192']
                    }]
                }]
            }
        self.empty = {'aaData': [],
                      'iTotalDisplayRecords': 0,
                      'iTotalRecords': 0,
                      'sEcho': 1021}
        self.portal = qiita_config.portal

    def tearDown(self):
        super(TestSearchStudiesAJAX, self).tearDown()
        qiita_config.portal = self.portal

    def test_get(self):
        response = self.get('/study/search/', {
            'user': 'test@foo.bar',
            'search_type': 'user',
            'query': '',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(loads(response.body), self.json)

        response = self.get('/study/search/', {
            'user': 'test@foo.bar',
            'search_type': 'user',
            'query': 'ph > 50',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(loads(response.body), self.empty)

    def test_get_failure_malformed_query(self):
        response = self.get('/study/search/', {
            'user': 'test@foo.bar',
            'search_type': 'user',
            'query': 'ph',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 400)
        # make sure responds properly
        self.assertEqual(response.body, 'Malformed search query. '
                         'Please read "search help" and try again.')

        response = self.get('/study/search/', {
            'user': 'FAKE@foo.bar',
            'search_type': 'user',
            'query': 'ph',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 403)

    def test_get_failure_no_valid_search_type(self):
        response = self.get('/study/search/', {
            'user': 'test@foo.bar',
            'search_type': 'wrong',
            'query': 'ph',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 400)

    def test_get_emp_portal(self):
        qiita_config.portal = "EMP"
        response = self.get('/study/search/', {
            'user': 'test@foo.bar',
            'search_type': 'user',
            'query': '',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), self.empty)

if __name__ == "__main__":
    main()
