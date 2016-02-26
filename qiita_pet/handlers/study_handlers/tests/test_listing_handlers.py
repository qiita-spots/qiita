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

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.study_handlers.listing_handlers import (
    _get_shared_links_for_study, _build_study_info, _build_single_study_info,
    _build_single_proc_data_info)
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.study import Study
from qiita_db.user import User
from qiita_db.artifact import Artifact


class TestHelpers(TestHandlerBase):
    database = True

    def setUp(self):
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
            'study_title':
                'Identification of the Microbiomes for Cannabis Soils',
            'num_raw_data': 1,
            'number_samples_collected': 27,
            'shared':
                '<a target="_blank" href="mailto:shared@foo.bar">Shared</a>',
            'publication_doi':
                '<a target="_blank" href="http://dx.doi.org/10.100/123456">'
                '10.100/123456</a>, <a target="_blank" '
                'href="http://dx.doi.org/10.100/7891011">10.100/7891011</a>',
            'pmid': '<a target="_blank" href="http://www.ncbi.nlm.nih.gov'
                    '/pubmed/7891011">7891011</a>, <a target="_blank" href='
                    '"http://www.ncbi.nlm.nih.gov/pubmed/123456">123456</a>',
            'pi': '<a target="_blank" href="mailto:PI_dude@foo.bar">'
                  'PIDude</a>',
            'proc_data_info': self.proc_data_exp
        }
        self.exp = [self.single_exp]
        super(TestHelpers, self).setUp()

    def test_get_shared_links_for_study(self):
        obs = _get_shared_links_for_study(Study(1))
        exp = '<a target="_blank" href="mailto:shared@foo.bar">Shared</a>'
        self.assertEqual(obs, exp)

    def test_build_single_study_info(self):
        study_proc = {1: {'18S': [4, 5, 6]}}
        proc_samples = {4: self.proc_data_exp[0]['samples'],
                        5: self.proc_data_exp[1]['samples'],
                        6: self.proc_data_exp[2]['samples']}
        study_info = {
            'study_id': 1,
            'email': 'test@foo.bar',
            'principal_investigator_id': 3,
            'publication_doi': ['10.100/123456', '10.100/7891011'],
            'study_title':
                'Identification of the Microbiomes for Cannabis Soils',
            'metadata_complete': True,
            'number_samples_collected': 27,
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
                'lifecycle.'
            }
        obs = _build_single_study_info(Study(1), study_info, study_proc,
                                       proc_samples)
        self.assertItemsEqual(obs, self.single_exp)

    def test_build_single_proc_data_info(self):
        obs = _build_single_proc_data_info(4, '18S',
                                           self.proc_data_exp[0]['samples'])
        self.assertItemsEqual(obs, self.proc_data_exp[0])

    def test_build_study_info_new_study(self):
        info = {
            'timeseries_type_id': 1,
            'lab_person_id': None,
            'principal_investigator_id': 3,
            'metadata_complete': False,
            'mixs_compliant': True,
            'study_description': 'desc',
            'study_alias': 'alias',
            'study_abstract': 'abstract'}
        user = User('test@foo.bar')

        Study.create(user, 'test_study_1', efo=[1], info=info)
        obs = _build_study_info(user)
        self.exp.append({
            'study_id': 2,
            'status': 'sandbox',
            'study_abstract': 'abstract',
            'metadata_complete': False,
            'study_title': 'test_study_1',
            'num_raw_data': 0,
            'number_samples_collected': 0,
            'shared': '',
            'pmid': '',
            'publication_doi': '',
            'pi':
                '<a target="_blank" href="mailto:PI_dude@foo.bar">PIDude</a>',
            'proc_data_info': []})
        self.assertEqual(obs, self.exp)

        with self.assertRaises(IncompetentQiitaDeveloperError):
            obs = _build_study_info(User('test@foo.bar'), study_proc={})
        with self.assertRaises(IncompetentQiitaDeveloperError):
            obs = _build_study_info(User('test@foo.bar'), proc_samples={})


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


class TestShareStudyAjax(TestHandlerBase):
    database = True

    def test_get_deselected(self):
        s = Study(1)
        u = User('shared@foo.bar')
        args = {'deselected': u.id, 'study_id': s.id}
        self.assertEqual(s.shared_with, [u])
        response = self.get('/study/sharing/', args)
        self.assertEqual(response.code, 200)
        exp = {'users': [], 'links': ''}
        self.assertEqual(loads(response.body), exp)
        self.assertEqual(s.shared_with, [])

    def test_get_selected(self):
        s = Study(1)
        u = User('admin@foo.bar')
        args = {'selected': u.id, 'study_id': s.id}
        response = self.get('/study/sharing/', args)
        self.assertEqual(response.code, 200)
        exp = {
            'users': ['shared@foo.bar', u.id],
            'links':
                ('<a target="_blank" href="mailto:shared@foo.bar">Shared</a>, '
                 '<a target="_blank" href="mailto:admin@foo.bar">Admin</a>')}
        self.assertEqual(loads(response.body), exp)
        self.assertEqual(s.shared_with, [User('shared@foo.bar'), u])

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

        args = {'selected': 'test@foo.bar', 'study_id': s.id}
        response = self.get('/study/sharing/', args)
        self.assertEqual(response.code, 403)
        self.assertEqual(s.shared_with, [])


class TestSearchStudiesAJAX(TestHandlerBase):
    database = True

    json = {
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
            'study_title':
                'Identification of the Microbiomes for Cannabis Soils',
            'num_raw_data': 1,
            'number_samples_collected': 27,
            'shared':
                '<a target="_blank" href="mailto:shared@foo.bar">Shared</a>',
            'publication_doi':
                '<a target="_blank" href="http://dx.doi.org/10.100/123456">'
                '10.100/123456</a>, <a target="_blank" '
                'href="http://dx.doi.org/10.100/7891011">10.100/7891011</a>',
            'pmid': '<a target="_blank" href="http://www.ncbi.nlm.nih.gov'
                    '/pubmed/7891011">7891011</a>, <a target="_blank" href='
                    '"http://www.ncbi.nlm.nih.gov/pubmed/123456">123456</a>',
            'pi': '<a target="_blank" href="mailto:PI_dude@foo.bar">'
                  'PIDude</a>',
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
                }]
            }]
        }
    empty = {'aaData': [],
             'iTotalDisplayRecords': 0,
             'iTotalRecords': 0,
             'sEcho': 1021}

    def test_get(self):
        response = self.get('/study/search/', {
            'user': 'test@foo.bar',
            'query': '',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(loads(response.body), self.json)

        response = self.get('/study/search/', {
            'user': 'test@foo.bar',
            'query': 'ph > 50',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 200)
        # make sure responds properly
        self.assertEqual(loads(response.body), self.empty)

    def test_get_failure(self):
        response = self.get('/study/search/', {
            'user': 'test@foo.bar',
            'query': 'ph',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 400)
        # make sure responds properly
        self.assertEqual(response.body, 'Malformed search query. '
                         'Please read "search help" and try again.')

        response = self.get('/study/search/', {
            'user': 'FAKE@foo.bar',
            'query': 'ph',
            'sEcho': '1021'
            })
        self.assertEqual(response.code, 403)

if __name__ == "__main__":
    main()
