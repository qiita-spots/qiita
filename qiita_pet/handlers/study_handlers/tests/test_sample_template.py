# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import main
from json import loads
from os import remove, close
from os.path import exists, join
from tempfile import mkstemp

from tornado.web import HTTPError
from mock import Mock
import pandas as pd

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_core.qiita_settings import r_client
from qiita_core.testing import wait_for_processing_job
from qiita_db.user import User
from qiita_db.study import Study, StudyPerson
from qiita_db.util import get_mountpoint
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.study_handlers.sample_template import (
    _build_sample_summary, sample_template_checks,
    sample_template_handler_post_request,
    sample_template_overview_handler_get_request,
    sample_template_handler_delete_request,
    sample_template_handler_patch_request, sample_template_summary_get_req)


class TestHelpers(TestHandlerBase):
    def setUp(self):
        self._clean_up_files = []

    def tearDown(self):
        # Clear up the redis cache
        r_client.flushdb()
        # Remove any files that need to be remove
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    def _create_study(self, study_title):
        """Creates a new study

        Parameters
        ----------
        study_title: str
            The title of the new study

        Returns
        -------
        qiita_db.study.Study
            The newly created study
        """
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "ALIAS",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }
        return Study.create(User('test@foo.bar'), study_title, info)

    def test_sample_template_checks(self):
        user = User('test@foo.bar')

        # If the user has access, this should not raise anything, so it will
        # keep the execution
        sample_template_checks(1, user)
        sample_template_checks(1, user, check_exists=True)

        # Test study doesn't exist
        with self.assertRaisesRegexp(HTTPError, 'Study does not exist'):
            sample_template_checks(1000000, user)

        # Test user doesn't have access to the study
        with self.assertRaisesRegexp(HTTPError,
                                     'User does not have access to study'):
            sample_template_checks(1, User('demo@microbio.me'))

        # Test sample template doesn't exist
        new_study = self._create_study('Test Sample Template Checks')
        with self.assertRaisesRegexp(HTTPError,
                                     "Study %s doesn't have sample information"
                                     % new_study.id):
            sample_template_checks(new_study.id, user, check_exists=True)

    def test_sample_template_handler_post_request(self):
        # Test user doesn't have access
        with self.assertRaisesRegexp(HTTPError,
                                     'User does not have access to study'):
            sample_template_handler_post_request(
                1, User('demo@microbio.me'), 'ignored')

        # Test study doesn't exist
        user = User('test@foo.bar')
        with self.assertRaisesRegexp(HTTPError, 'Study does not exist'):
            sample_template_handler_post_request(1000000, user, 'ignored')

        # Test file doesn't exist
        with self.assertRaisesRegexp(HTTPError, 'Filepath not found'):
            sample_template_handler_post_request(1, user, 'DoesNotExist.txt')

        # Test looks like mapping file and no data_type provided
        uploads_dir = join(get_mountpoint('uploads')[0][1], '1')
        fd, fp = mkstemp(suffix='.txt', dir=uploads_dir)
        self._clean_up_files.append(fp)
        close(fd)

        with open(fp, 'w') as f:
            f.write('#SampleID\tCol1\nSample1\tVal1')

        with self.assertRaisesRegexp(
                HTTPError, 'Please, choose a data type if uploading a QIIME '
                           'mapping file'):
            sample_template_handler_post_request(1, user, fp)

        # Test success
        obs = sample_template_handler_post_request(
            1, user, 'uploaded_file.txt')
        self.assertEqual(obs.keys(), ['job'])
        job_info = r_client.get('sample_template_1')
        self.assertIsNotNone(job_info)

        # Wait until the job is done
        wait_for_processing_job(loads(job_info)['job_id'])

    def test_sample_template_handler_patch_request(self):
        user = User('test@foo.bar')

        # Test user doesn't have access
        with self.assertRaisesRegexp(HTTPError,
                                     'User does not have access to study'):
            sample_template_handler_patch_request(
                User('demo@microbio.me'), "remove",
                "/1/10/columns/season_environment/")

        # Test study doesn't exist
        with self.assertRaisesRegexp(HTTPError, 'Study does not exist'):
            sample_template_handler_patch_request(
                user, "remove", "/10000/10/columns/season_environment/")

        # Test sample template doesn't exist
        new_study = self._create_study('Patching test')
        with self.assertRaisesRegexp(HTTPError,
                                     "Study %s doesn't have sample information"
                                     % new_study.id):
            sample_template_handler_patch_request(
                user, "remove", "/%s/10/columns/season_environment/"
                                % new_study.id)

        # Test wrong operation value
        with self.assertRaisesRegexp(
                HTTPError, 'Operation add not supported. Current supported '
                           'operations: remove.'):
            sample_template_handler_patch_request(
                user, 'add', '/1/19/columns/season_environment')

        # Test wrong path parameter < 2
        with self.assertRaisesRegexp(HTTPError, 'Incorrect path parameter'):
            sample_template_handler_patch_request(user, 'ignored', '1')

        # TESTS FOR OPERATION: remove
        # Test wrong path parameter
        with self.assertRaisesRegexp(HTTPError, 'Incorrect path parameter'):
            sample_template_handler_patch_request(
                user, 'remove', '1/columns/season_environment/')

        # Add sample information to the new study so we can delete one column
        # without affecting the other tests
        md = pd.DataFrame.from_dict(
            {'Sample1': {'col1': 'val1', 'col2': 'val2'}},
            orient='index', dtype=str)
        st = SampleTemplate.create(md, new_study)

        # Test success
        obs = sample_template_handler_patch_request(
            user, "remove", "/%s/2/columns/col2/"
                            % new_study.id)
        self.assertEqual(obs.keys(), ['job', 'row_id'])
        self.assertEqual(obs['row_id'], '2')
        job_info = r_client.get('sample_template_%s' % new_study.id)
        self.assertIsNotNone(job_info)

        # Wait until the job is done
        wait_for_processing_job(loads(job_info)['job_id'])
        self.assertNotIn('col2', st.categories())

        # TESTS FOR OPERATION: replace
        # Test incorrect path parameter with replace
        with self.assertRaisesRegexp(HTTPError, 'Incorrect path parameter'):
            sample_template_handler_patch_request(user, "replace", "/1/")

        # Test attribute not found
        with self.assertRaisesRegexp(HTTPError, 'Attribute name not found'):
            sample_template_handler_patch_request(user, "replace", "/1/name")

        # Test missing value
        with self.assertRaisesRegexp(HTTPError,
                                     'Value is required when updating sample '
                                     'information'):
            sample_template_handler_patch_request(user, "replace", "/1/data")

        # Test file doesn't exist
        with self.assertRaisesRegexp(HTTPError, 'Filepath not found'):
            sample_template_handler_patch_request(user, "replace", "/1/data",
                                                  req_value='DoesNotExist')

        # Test success
        obs = sample_template_handler_patch_request(
            user, "replace", "/1/data", req_value='uploaded_file.txt')
        self.assertEqual(obs.keys(), ['job', 'row_id'])
        self.assertIsNone(obs['row_id'])
        job_info = r_client.get('sample_template_1')
        self.assertIsNotNone(job_info)

        # Wait until the job is done
        wait_for_processing_job(loads(job_info)['job_id'])

    def test_sample_template_handler_delete_request(self):
        # Test user doesn't have access
        with self.assertRaisesRegexp(HTTPError,
                                     'User does not have access to study'):
            sample_template_handler_delete_request(
                1, User('demo@microbio.me'))

        # Test study doesn't exist
        user = User('test@foo.bar')
        with self.assertRaisesRegexp(HTTPError, 'Study does not exist'):
            sample_template_handler_delete_request(1000000, user)

        # Test sample information doesn't exist
        new_study = self._create_study('Study for deleting test')
        with self.assertRaisesRegexp(HTTPError, "Study %s doesn't have sample "
                                                "information" % new_study.id):
            sample_template_handler_delete_request(new_study.id, user)

        # Test success
        user = User('test@foo.bar')
        obs = sample_template_handler_delete_request(1, user)
        self.assertEqual(obs.keys(), ['job'])
        job_info = r_client.get('sample_template_1')
        self.assertIsNotNone(job_info)

        # Wait until the job is done
        wait_for_processing_job(loads(job_info)['job_id'])

    def test_sample_template_overview_handler_get_request(self):
        # Test user doesn't have access
        with self.assertRaisesRegexp(HTTPError,
                                     'User does not have access to study'):
            sample_template_overview_handler_get_request(
                1, User('demo@microbio.me'))

        # Test study doesn't exist
        user = User('test@foo.bar')
        with self.assertRaisesRegexp(HTTPError, 'Study does not exist'):
            sample_template_overview_handler_get_request(1000000, user)

        # Test sample template exist
        obs = sample_template_overview_handler_get_request(1, user)
        exp = {'exists': True,
               'uploaded_files': ['uploaded_file.txt'],
               'data_types': [],
               'user_can_edit': True,
               'job': None,
               'download_id': 22,
               'old_files': ['1_19700101-000000.txt'],
               'num_samples': 27,
               'num_columns': 30}
        self.assertEqual(obs, exp)

        # Test sample template doesn't exist
        new_study = self._create_study('Some New Study')
        obs = sample_template_overview_handler_get_request(new_study.id, user)
        exp = {'exists': False,
               'uploaded_files': [],
               'data_types': ['16S', '18S', 'Genomics', 'ITS', 'Metabolomic',
                              'Metagenomic', 'Metatranscriptomics',
                              'Multiomic', 'Proteomic', 'Transcriptomics',
                              'Viromics'],
               'user_can_edit': True,
               'job': None,
               'download_id': None,
               'old_files': [],
               'num_samples': 0,
               'num_columns': 0}
        self.assertEqual(obs, exp)

    def test_sample_template_summary_get_req(self):
        # Test user doesn't have access
        with self.assertRaisesRegexp(HTTPError,
                                     'User does not have access to study'):
            sample_template_summary_get_req(1, User('demo@microbio.me'))

        # Test study doesn't exist
        user = User('test@foo.bar')
        with self.assertRaisesRegexp(HTTPError, 'Study does not exist'):
            sample_template_summary_get_req(1000000, user)

        # Test sample template doesn't exist
        new_study = self._create_study('New Study - Summary')
        with self.assertRaisesRegexp(HTTPError, "Study %s doesn't have sample "
                                                "information" % new_study.id):
            sample_template_summary_get_req(new_study.id, user)

        # Test succes
        obs = sample_template_summary_get_req(1, user)
        exp = {
            'physical_specimen_location': [('ANL', 27)],
            'texture': [('63.1 sand, 17.7 silt, 19.2 clay', 9),
                        ('64.6 sand, 17.6 silt, 17.8 clay', 9),
                        ('66 sand, 16.3 silt, 17.7 clay', 9)],
            'common_name': [('rhizosphere metagenome', 9),
                            ('root metagenome', 9),
                            ('soil metagenome', 9)],
            'water_content_soil': [('0.101', 9), ('0.164', 9),
                                   ('0.178', 9)],
            'env_feature': [('ENVO:plant-associated habitat', 27)],
            'assigned_from_geo': [('n', 27)],
            'altitude': [('0', 27)],
            'tot_org_carb': [('3.31', 9), ('4.32', 9), ('5', 9)],
            'env_biome': [('ENVO:Temperate grasslands, savannas, and '
                           'shrubland biome', 27)],
            'sample_type': [('ENVO:soil', 27)],
            'scientific_name': [('1118232', 27)],
            'host_taxid': [('3483', 27)],
            'latitude': [('0.291867635913', 1), ('3.21190859967', 1),
                         ('4.59216095574', 1), ('10.6655599093', 1),
                         ('12.6245524972', 1), ('12.7065957714', 1),
                         ('13.089194595', 1), ('23.1218032799', 1),
                         ('29.1499460692', 1), ('35.2374368957', 1),
                         ('38.2627021402', 1), ('40.8623799474', 1),
                         ('43.9614715197', 1), ('44.9725384282', 1),
                         ('53.5050692395', 1), ('57.571893782', 1),
                         ('60.1102854322', 1), ('68.51099627', 1),
                         ('68.0991287718', 1), ('74.0894932572', 1),
                         ('78.3634273709', 1), ('82.8302905615', 1),
                         ('84.0030227585', 1), ('85.4121476399', 1),
                         ('95.2060749748', 1), ('Not applicable', 2)],
            'ph': [('6.8', 9), ('6.82', 10), ('6.94', 8)],
            'description_duplicate': [
                ('Bucu Rhizo', 3), ('Bucu Roots', 3), ('Bucu bulk', 3),
                ('Burmese Rhizo', 3), ('Burmese bulk', 3),
                ('Burmese root', 3), ('Diesel Rhizo', 3),
                ('Diesel Root', 3), ('Diesel bulk', 3)],
            'elevation': [('114', 27)],
            'description': [('Cannabis Soil Microbiome', 27)],
            'collection_timestamp': [('2011-11-11 13:00:00', 27)],
            'physical_specimen_remaining': [('true', 27)],
            'dna_extracted': [('true', 27)],
            'taxon_id': [('410658', 9), ('939928', 9), ('1118232', 9)],
            'samp_salinity': [('7.1', 9), ('7.15', 9), ('7.44', 9)],
            'host_subject_id': [
                ('1001:B1', 1), ('1001:B2', 1), ('1001:B3', 1),
                ('1001:B4', 1), ('1001:B5', 1), ('1001:B6', 1),
                ('1001:B7', 1), ('1001:B8', 1), ('1001:B9', 1),
                ('1001:D1', 1), ('1001:D2', 1), ('1001:D3', 1),
                ('1001:D4', 1), ('1001:D5', 1), ('1001:D6', 1),
                ('1001:D7', 1), ('1001:D8', 1), ('1001:D9', 1),
                ('1001:M1', 1), ('1001:M2', 1), ('1001:M3', 1),
                ('1001:M4', 1), ('1001:M5', 1), ('1001:M6', 1),
                ('1001:M7', 1), ('1001:M8', 1), ('1001:M9', 1)],
            'temp': [('15', 27)],
            'country': [('GAZ:United States of America', 27)],
            'longitude': [
                ('2.35063674718', 1), ('3.48274264219', 1),
                ('6.66444220187', 1), ('15.6526750776', 1),
                ('26.8138925876', 1), ('27.3592668624', 1),
                ('31.2003474585', 1), ('31.6056761814', 1),
                ('32.5563076447', 1), ('34.8360987059', 1),
                ('42.838497795', 1), ('63.5115213108', 1),
                ('65.3283470202', 1), ('66.1920014699', 1),
                ('66.8954849864', 1), ('68.5041623253', 1),
                ('68.5945325743', 1), ('70.784770579', 1),
                ('74.423907894', 1), ('74.7123248382', 1),
                ('82.1270418227', 1), ('82.8516734159', 1),
                ('84.9722975792', 1), ('86.3615778099', 1),
                ('92.5274472082', 1), ('96.0693176066', 1),
                ('Not applicable', 1)],
            'tot_nitro': [('1.3', 9), ('1.41', 9), ('1.51', 9)],
            'depth': [('0.15', 27)],
            'qiita_study_id': [('1', 27)],
            'anonymized_name': [
                ('SKB1', 1), ('SKB2', 1), ('SKB3', 1), ('SKB4', 1),
                ('SKB5', 1), ('SKB6', 1), ('SKB7', 1), ('SKB8', 1),
                ('SKB9', 1), ('SKD1', 1), ('SKD2', 1), ('SKD3', 1),
                ('SKD4', 1), ('SKD5', 1), ('SKD6', 1), ('SKD7', 1),
                ('SKD8', 1), ('SKD9', 1), ('SKM1', 1), ('SKM2', 1),
                ('SKM3', 1), ('SKM4', 1), ('SKM5', 1), ('SKM6', 1),
                ('SKM7', 1), ('SKM8', 1), ('SKM9', 1)],
            'season_environment': [('winter', 27)]}

        self.assertEqual(obs, exp)

    def test_build_sample_summary(self):
        cols, table = _build_sample_summary(1, 'test@foo.bar')
        # Make sure header filled properly
        cols_exp = [{'field': 'sample', 'width': 240, 'sortable': False,
                     'id': 'sample', 'name': 'Sample'},
                    {'field': 'prep1', 'width': 240, 'sortable': False,
                     'id': 'prep1', 'name': 'Prep information 1 - 1'},
                    {'field': 'prep2', 'width': 240, 'sortable': False,
                     'id': 'prep2', 'name': 'Prep information 2 - 2'}]
        self.assertEqual(cols, cols_exp)
        table_exp = [{'sample': '1.SKB2.640194', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKM4.640180', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKB3.640195', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKB6.640176', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKD6.640190', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKM6.640187', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKD9.640182', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKM8.640201', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKM2.640199', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKD2.640178', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKB7.640196', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKD4.640185', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKB8.640193', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKM3.640197', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKD5.640186', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKB1.640202', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKM1.640183', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKD1.640179', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKD3.640198', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKB5.640181', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKB4.640189', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKB9.640200', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKM9.640192', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKD8.640184', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKM5.640177', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKM7.640188', 'prep2': 'X', 'prep1': 'X'},
                     {'sample': '1.SKD7.640191', 'prep2': 'X', 'prep1': 'X'}]
        self.assertEqual(table, table_exp)


class TestSampleTemplateHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/description/sample_template/',
                            {'study_id': 1})
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.body, "")

        # Study doesn't exist
        response = self.get('/study/description/sample_template/',
                            {'study_id': 10000})
        self.assertEqual(response.code, 404)

        # User doesn't have access
        BaseHandler.get_current_user = Mock(
            return_value=User('demo@microbio.me'))
        response = self.get('/study/description/sample_template/',
                            {'study_id': 1})
        self.assertEqual(response.code, 403)

    def test_post(self):
        response = self.post('/study/description/sample_template/',
                             {'study_id': 1,
                              'filepath': 'uploaded_file.txt',
                              'data_type': ''})
        self.assertEqual(response.code, 200)
        self.assertIsNotNone(response.body)
        obs = loads(response.body)
        self.assertEqual(obs.keys(), ['job'])
        # Wait until the job is done
        wait_for_processing_job(obs['job'])

    def test_patch(self):
        response = self.patch('/study/description/sample_template/',
                              {'op': 'replace',
                               'path': '/1/data',
                               'value': 'uploaded_file.txt'})
        self.assertEqual(response.code, 200)
        self.assertIsNotNone(response.body)
        obs = loads(response.body)
        self.assertEqual(obs.keys(), ['job', 'row_id'])
        # Wait until the job is done
        wait_for_processing_job(obs['job'])

    def test_delete(self):
        response = self.delete('/study/description/sample_template/',
                               {'study_id': 1})
        self.assertEqual(response.code, 200)
        self.assertIsNotNone(response.body)
        obs = loads(response.body)
        self.assertEqual(obs.keys(), ['job'])
        # Wait until the job is done
        wait_for_processing_job(obs['job'])


class TestSampleTemplateOverviewHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/description/sample_template/overview/',
                            {'study_id': 1})
        self.assertEqual(response.code, 200)
        self.assertIsNotNone(response.body)
        obs = loads(response.body)
        exp = {'exists': True,
               'uploaded_files': ['uploaded_file.txt'],
               'data_types': [],
               'user_can_edit': True,
               'job': None,
               'download_id': 22,
               'old_files': ['1_19700101-000000.txt'],
               'num_samples': 27,
               'num_columns': 30}
        self.assertEqual(obs, exp)


class TestSampleTemplateSummaryHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/description/sample_template/summary/',
                            {'study_id': 1})
        self.assertEqual(response.code, 200)
        self.assertIsNotNone(response.body)
        obs = loads(response.body)
        exp = {
            'physical_specimen_location': [['ANL', 27]],
            'texture': [['63.1 sand, 17.7 silt, 19.2 clay', 9],
                        ['64.6 sand, 17.6 silt, 17.8 clay', 9],
                        ['66 sand, 16.3 silt, 17.7 clay', 9]],
            'common_name': [['rhizosphere metagenome', 9],
                            ['root metagenome', 9],
                            ['soil metagenome', 9]],
            'water_content_soil': [['0.101', 9], ['0.164', 9],
                                   ['0.178', 9]],
            'env_feature': [['ENVO:plant-associated habitat', 27]],
            'assigned_from_geo': [['n', 27]],
            'altitude': [['0', 27]],
            'tot_org_carb': [['3.31', 9], ['4.32', 9], ['5', 9]],
            'env_biome': [['ENVO:Temperate grasslands, savannas, and '
                           'shrubland biome', 27]],
            'sample_type': [['ENVO:soil', 27]],
            'scientific_name': [['1118232', 27]],
            'host_taxid': [['3483', 27]],
            'latitude': [['0.291867635913', 1], ['3.21190859967', 1],
                         ['4.59216095574', 1], ['10.6655599093', 1],
                         ['12.6245524972', 1], ['12.7065957714', 1],
                         ['13.089194595', 1], ['23.1218032799', 1],
                         ['29.1499460692', 1], ['35.2374368957', 1],
                         ['38.2627021402', 1], ['40.8623799474', 1],
                         ['43.9614715197', 1], ['44.9725384282', 1],
                         ['53.5050692395', 1], ['57.571893782', 1],
                         ['60.1102854322', 1], ['68.51099627', 1],
                         ['68.0991287718', 1], ['74.0894932572', 1],
                         ['78.3634273709', 1], ['82.8302905615', 1],
                         ['84.0030227585', 1], ['85.4121476399', 1],
                         ['95.2060749748', 1], ['Not applicable', 2]],
            'ph': [['6.8', 9], ['6.82', 10], ['6.94', 8]],
            'description_duplicate': [
                ['Bucu Rhizo', 3], ['Bucu Roots', 3], ['Bucu bulk', 3],
                ['Burmese Rhizo', 3], ['Burmese bulk', 3],
                ['Burmese root', 3], ['Diesel Rhizo', 3],
                ['Diesel Root', 3], ['Diesel bulk', 3]],
            'elevation': [['114', 27]],
            'description': [['Cannabis Soil Microbiome', 27]],
            'collection_timestamp': [['2011-11-11 13:00:00', 27]],
            'physical_specimen_remaining': [['true', 27]],
            'dna_extracted': [['true', 27]],
            'taxon_id': [['410658', 9], ['939928', 9], ['1118232', 9]],
            'samp_salinity': [['7.1', 9], ['7.15', 9], ['7.44', 9]],
            'host_subject_id': [
                ['1001:B1', 1], ['1001:B2', 1], ['1001:B3', 1],
                ['1001:B4', 1], ['1001:B5', 1], ['1001:B6', 1],
                ['1001:B7', 1], ['1001:B8', 1], ['1001:B9', 1],
                ['1001:D1', 1], ['1001:D2', 1], ['1001:D3', 1],
                ['1001:D4', 1], ['1001:D5', 1], ['1001:D6', 1],
                ['1001:D7', 1], ['1001:D8', 1], ['1001:D9', 1],
                ['1001:M1', 1], ['1001:M2', 1], ['1001:M3', 1],
                ['1001:M4', 1], ['1001:M5', 1], ['1001:M6', 1],
                ['1001:M7', 1], ['1001:M8', 1], ['1001:M9', 1]],
            'temp': [['15', 27]],
            'country': [['GAZ:United States of America', 27]],
            'longitude': [
                ['2.35063674718', 1], ['3.48274264219', 1],
                ['6.66444220187', 1], ['15.6526750776', 1],
                ['26.8138925876', 1], ['27.3592668624', 1],
                ['31.2003474585', 1], ['31.6056761814', 1],
                ['32.5563076447', 1], ['34.8360987059', 1],
                ['42.838497795', 1], ['63.5115213108', 1],
                ['65.3283470202', 1], ['66.1920014699', 1],
                ['66.8954849864', 1], ['68.5041623253', 1],
                ['68.5945325743', 1], ['70.784770579', 1],
                ['74.423907894', 1], ['74.7123248382', 1],
                ['82.1270418227', 1], ['82.8516734159', 1],
                ['84.9722975792', 1], ['86.3615778099', 1],
                ['92.5274472082', 1], ['96.0693176066', 1],
                ['Not applicable', 1]],
            'tot_nitro': [['1.3', 9], ['1.41', 9], ['1.51', 9]],
            'depth': [['0.15', 27]],
            'qiita_study_id': [['1', 27]],
            'anonymized_name': [
                ['SKB1', 1], ['SKB2', 1], ['SKB3', 1], ['SKB4', 1],
                ['SKB5', 1], ['SKB6', 1], ['SKB7', 1], ['SKB8', 1],
                ['SKB9', 1], ['SKD1', 1], ['SKD2', 1], ['SKD3', 1],
                ['SKD4', 1], ['SKD5', 1], ['SKD6', 1], ['SKD7', 1],
                ['SKD8', 1], ['SKD9', 1], ['SKM1', 1], ['SKM2', 1],
                ['SKM3', 1], ['SKM4', 1], ['SKM5', 1], ['SKM6', 1],
                ['SKM7', 1], ['SKM8', 1], ['SKM9', 1]],
            'season_environment': [['winter', 27]]}
        self.assertEqual(obs, exp)


class TestSampleAJAXReadOnly(TestHandlerBase):
    def test_get(self):
        res = self.get("/study/description/sample_summary/", {'study_id': 1})
        self.assertEqual(res.code, 200)
        # Make sure metadata read properly
        line = '<option value="altitude">altitude</option>'
        self.assertIn(line, res.body)


class TestSampleAJAX(TestHandlerBase):

    def test_post(self):
        res = self.post("/study/description/sample_summary/", {
            'study_id': 1, 'meta_col': 'latitude'})
        self.assertEqual(res.code, 200)
        exp = {"status": "success",
               "message": "",
               "values": {'1.SKB2.640194': '35.2374368957',
                          '1.SKM4.640180': "Not applicable",
                          '1.SKB3.640195': '95.2060749748',
                          '1.SKB6.640176': '78.3634273709',
                          '1.SKD6.640190': '29.1499460692',
                          '1.SKM6.640187': '0.291867635913',
                          '1.SKD9.640182': '23.1218032799',
                          '1.SKM8.640201': '3.21190859967',
                          '1.SKM2.640199': '82.8302905615',
                          '1.SKD2.640178': '53.5050692395',
                          '1.SKB7.640196': '13.089194595',
                          '1.SKD4.640185': '40.8623799474',
                          '1.SKB8.640193': '74.0894932572',
                          '1.SKM3.640197': "Not applicable",
                          '1.SKD5.640186': '85.4121476399',
                          '1.SKB1.640202': '4.59216095574',
                          '1.SKM1.640183': '38.2627021402',
                          '1.SKD1.640179': '68.0991287718',
                          '1.SKD3.640198': '84.0030227585',
                          '1.SKB5.640181': '10.6655599093',
                          '1.SKB4.640189': '43.9614715197',
                          '1.SKB9.640200': '12.6245524972',
                          '1.SKM9.640192': '12.7065957714',
                          '1.SKD8.640184': '57.571893782',
                          '1.SKM5.640177': '44.9725384282',
                          '1.SKM7.640188': '60.1102854322',
                          '1.SKD7.640191': '68.51099627'}}
        self.assertEqual(loads(res.body), exp)

    def test_post_error(self):
        res = self.post("/study/description/sample_summary/", {
            'study_id': 1, 'meta_col': 'NOEXIST'})
        self.assertEqual(res.code, 200)
        exp = {"status": "error",
               "message": "Category NOEXIST does not exist in sample template"}
        self.assertEqual(loads(res.body), exp)


if __name__ == "__main__":
    main()
