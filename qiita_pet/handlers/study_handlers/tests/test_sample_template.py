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
from qiita_db.exceptions import QiitaDBColumnError
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.study_handlers.sample_template import (
    _build_sample_summary, sample_template_checks,
    sample_template_handler_post_request,
    sample_template_overview_handler_get_request,
    sample_template_handler_delete_request,
    sample_template_handler_patch_request, sample_template_columns_get_req)


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
                "/1/columns/season_environment/")

        # Test study doesn't exist
        with self.assertRaisesRegexp(HTTPError, 'Study does not exist'):
            sample_template_handler_patch_request(
                user, "remove", "/10000/columns/season_environment/")

        # Test sample template doesn't exist
        new_study = self._create_study('Patching test')
        with self.assertRaisesRegexp(HTTPError,
                                     "Study %s doesn't have sample information"
                                     % new_study.id):
            sample_template_handler_patch_request(
                user, "remove", "/%s/columns/season_environment/"
                                % new_study.id)

        # Test wrong operation value
        with self.assertRaisesRegexp(
                HTTPError, 'Operation add not supported. Current supported '
                           'operations: remove.'):
            sample_template_handler_patch_request(
                user, 'add', '/1/columns/season_environment')

        # Test wrong path parameter < 2
        with self.assertRaisesRegexp(HTTPError, 'Incorrect path parameter'):
            sample_template_handler_patch_request(user, 'ignored', '1')

        # TESTS FOR OPERATION: remove
        # Test wrong path parameter
        with self.assertRaisesRegexp(HTTPError, 'Incorrect path parameter'):
            sample_template_handler_patch_request(
                user, 'remove', '/1/season_environment/')

        # Add sample information to the new study so we can delete one column
        # without affecting the other tests
        md = pd.DataFrame.from_dict(
            {'Sample1': {'col1': 'val1', 'col2': 'val2'}},
            orient='index', dtype=str)
        st = SampleTemplate.create(md, new_study)

        # Test success
        obs = sample_template_handler_patch_request(
            user, "remove", "/%s/columns/col2/"
                            % new_study.id)
        self.assertEqual(obs.keys(), ['job'])
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
        self.assertEqual(obs.keys(), ['job'])
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

    def test_sample_template_columns_get_req(self):
        # Test user doesn't have access
        with self.assertRaisesRegexp(HTTPError,
                                     'User does not have access to study'):
            sample_template_columns_get_req(1, None, User('demo@microbio.me'))

        # Test study doesn't exist
        user = User('test@foo.bar')
        with self.assertRaisesRegexp(HTTPError, 'Study does not exist'):
            sample_template_columns_get_req(1000000, None, user)

        # Test sample template doesn't exist
        new_study = self._create_study('New Study - Summary')
        with self.assertRaisesRegexp(HTTPError, "Study %s doesn't have sample "
                                                "information" % new_study.id):
            sample_template_columns_get_req(new_study.id, None, user)

        # Test that if the column doesn't exist it raises an error
        with self.assertRaisesRegexp(QiitaDBColumnError, 'should-fail'):
            sample_template_columns_get_req(1, 'should-fail', user)

        # Test success

        obs = sample_template_columns_get_req(1, None, user)
        exp = [
            'season_environment', 'assigned_from_geo', 'texture', 'taxon_id',
            'depth', 'host_taxid', 'common_name', 'water_content_soil',
            'elevation', 'temp', 'tot_nitro', 'samp_salinity', 'altitude',
            'env_biome', 'country', 'ph', 'anonymized_name', 'tot_org_carb',
            'description_duplicate', 'env_feature',
            'physical_specimen_location', 'physical_specimen_remaining',
            'dna_extracted', 'sample_type', 'collection_timestamp',
            'host_subject_id', 'description', 'latitude', 'longitude',
            'scientific_name']
        self.assertEqual(obs, exp)

        obs = sample_template_columns_get_req(1, 'season_environment', user)
        exp = ['winter', 'winter', 'winter', 'winter', 'winter', 'winter',
               'winter', 'winter', 'winter', 'winter', 'winter', 'winter',
               'winter', 'winter', 'winter', 'winter', 'winter', 'winter',
               'winter', 'winter', 'winter', 'winter', 'winter', 'winter',
               'winter', 'winter', 'winter']
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
        self.assertEqual(obs.keys(), ['job'])
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


class TestSampleTemplateColumnsHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/description/sample_template/columns/',
                            {'study_id': 1})
        self.assertEqual(response.code, 200)
        self.assertIsNotNone(response.body)
        obs = loads(response.body)
        exp = {'values': [
            'season_environment', 'assigned_from_geo', 'texture', 'taxon_id',
            'depth', 'host_taxid', 'common_name', 'water_content_soil',
            'elevation', 'temp', 'tot_nitro', 'samp_salinity', 'altitude',
            'env_biome', 'country', 'ph', 'anonymized_name', 'tot_org_carb',
            'description_duplicate', 'env_feature',
            'physical_specimen_location', 'physical_specimen_remaining',
            'dna_extracted', 'sample_type', 'collection_timestamp',
            'host_subject_id', 'description', 'latitude', 'longitude',
            'scientific_name']}
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
