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

from qiita_core.qiita_settings import r_client
from qiita_core.testing import wait_for_processing_job
from qiita_db.user import User
from qiita_db.study import Study, StudyPerson
from qiita_db.util import get_mountpoint
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.study_handlers.sample_template import (
    _build_sample_summary, _check_study_access,
    sample_template_handler_post_request,
    sample_template_overview_handler_get_request)


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

    def test_check_study_access(self):
        user = User('test@foo.bar')

        # If the user has access, this should not raise anything, so it will
        # keep the execution
        _check_study_access(1, user)

        with self.assertRaisesRegexp(HTTPError, 'Study does not exist'):
            _check_study_access(1000000, user)

        with self.assertRaisesRegexp(HTTPError,
                                     'User does not have access to study'):
            _check_study_access(1, User('demo@microbio.me'))

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
               'job': None}
        self.assertEqual(obs, exp)

        # Test sample template doesn't exist
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
        new_study = Study.create(User('test@foo.bar'), 'Some New Study',
                                 info)
        obs = sample_template_overview_handler_get_request(new_study.id, user)
        exp = {'exists': False,
               'uploaded_files': [],
               'data_types': ['16S', '18S', 'Genomics', 'ITS', 'Metabolomic',
                              'Metagenomic', 'Metatranscriptomics',
                              'Multiomic', 'Proteomic', 'Transcriptomics',
                              'Viromics'],
               'user_can_edit': True,
               'job': None}
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


class TestSampleTemplateAJAX(TestHandlerBase):

    def test_delete_sample_template(self):
        response = self.post('/study/description/sample_template/',
                             {'study_id': 1,
                              'action': 'delete'})
        self.assertEqual(response.code, 200)
        exp = ('{"status": "success", '
               '"message": ""}')
        # checking that the action was sent
        self.assertEqual(response.body, exp)

        # Wait until the job has completed
        obs = r_client.get('sample_template_1')
        wait_for_processing_job(loads(obs)['job_id'])


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
