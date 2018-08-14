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

from qiita_core.qiita_settings import qiita_config, r_client
from qiita_db.artifact import Artifact
from qiita_db.study import Study
from qiita_db.user import User
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.base_handlers import BaseHandler

GPARAMS = {'similarity': 0.97, 'reference_name': 'Greengenes',
           'sortmerna_e_value': 1, 'sortmerna_max_pos': 10000, 'threads': 1,
           'sortmerna_coverage': 0.97, 'reference_version': u'13_8'}


class TestListStudiesHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/list/')
        self.assertEqual(response.code, 200)


class TestStudyApprovalList(TestHandlerBase):

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
        s = Study.create(u, 'test_study', info=info)
        self.assertEqual(s.shared_with, [])

        args = {'selected': 'test@foo.bar', 'id': s.id}
        response = self.get('/study/sharing/', args)
        self.assertEqual(response.code, 403)
        self.assertEqual(s.shared_with, [])


class TestListStudiesAJAX(TestHandlerBase):

    def setUp(self):
        super(TestListStudiesAJAX, self).setUp()
        self.json = {
            'iTotalRecords': 1,
            'aaData': [{
                'status': 'private',
                'ebi_info': ('<a href="http://www.ebi.ac.uk/ena/data/view/'
                             'EBI123456-BB" target="_blank">EBI123456-BB</a>'
                             ' (submitted)'),
                'study_title': ('Identification of the Microbiomes for '
                                'Cannabis Soils'),
                'metadata_complete': True,
                'ebi_submission_status': 'submitted',
                'study_id': 1,
                'study_alias': 'Cannabis Soils',
                'owner': 'Dude',
                'ebi_study_accession': 'EBI123456-BB',
                'shared': ('<a target="_blank" href="mailto:shared@foo.bar">'
                           'Shared</a>'),
                'pubs': (
                    '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/'
                    'pubmed/123456">123456</a>, <a target="_blank" '
                    'href="http://www.ncbi.nlm.nih.gov/pubmed/7891011">'
                    '7891011</a>, <a target="_blank" href="http://dx.doi.org'
                    '/10.100/123456">10.100/123456</a>, <a target="_blank" '
                    'href="http://dx.doi.org/10.100/7891011">'
                    '10.100/7891011</a>'),
                'pi': ('<a target="_blank" href="mailto:PI_dude@foo.bar">'
                       'PIDude</a>'),
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
                'artifact_biom_ids': [4, 5, 6, 7],
                'number_samples_collected': 27,
                'study_tags': None}],
            'sEcho': 1021,
            'iTotalDisplayRecords': 1}
        self.empty = {'aaData': [],
                      'iTotalDisplayRecords': 0,
                      'iTotalRecords': 0,
                      'sEcho': 1021}
        self.portal = qiita_config.portal

    def tearDown(self):
        super(TestListStudiesAJAX, self).tearDown()
        qiita_config.portal = self.portal


if __name__ == "__main__":
    main()
