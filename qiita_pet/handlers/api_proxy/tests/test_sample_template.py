# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from os import remove, mkdir
from os.path import join, exists
from json import dumps

from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import r_client
import qiita_db as qdb
from qiita_pet.handlers.api_proxy.sample_template import (
    sample_template_filepaths_get_req, sample_template_get_req,
    _check_sample_template_exists, sample_template_samples_get_req,
    sample_template_category_get_req, sample_template_meta_cats_get_req,
    get_sample_template_processing_status,
    SAMPLE_TEMPLATE_KEY_FORMAT)


@qiita_test_checker()
class TestSampleAPI(TestCase):
    def setUp(self):
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

        self.new_study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Some New Study", info)

        base_dir = join(qdb.util.get_mountpoint('uploads')[0][1],
                        str(self.new_study.id))
        if not exists(base_dir):
            mkdir(base_dir)
        self.new_study_fp = join(base_dir, 'uploaded_file.txt')
        if not exists(self.new_study_fp):
            with open(self.new_study_fp, 'w') as f:
                f.write('')

    def tearDown(self):
        base_dir = qdb.util.get_mountpoint('uploads')[0][1]
        fp = join(base_dir, '1', 'uploaded_file.txt')
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write('')

        if exists(self.new_study_fp):
            remove(self.new_study_fp)

        r_client.flushdb()

        qdb.study.Study.delete(self.new_study.id)

    def test_check_sample_template_exists(self):
        obs = _check_sample_template_exists(1)
        self.assertEqual(obs, {'status': 'success', 'message': ''})

    def test_check_sample_template_exists_no_template(self):
        obs = _check_sample_template_exists(self.new_study.id)
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Sample template %d does not '
                               'exist' % self.new_study.id})

    def test_sample_template_get_req(self):
        obs = sample_template_get_req(1, 'test@foo.bar')
        self.assertEqual(obs.keys(), ['status', 'message', 'template'])
        self.assertEqual(obs['status'], 'success')
        self.assertEqual(obs['message'], '')
        self.assertEqual(len(obs['template']), 27)
        self.assertEqual(str(
            obs['template']['1.SKB2.640194']['collection_timestamp']),
            '2011-11-11 13:00:00')
        del obs['template']['1.SKB2.640194']['collection_timestamp']
        self.assertEqual(obs['template']['1.SKB2.640194'], {
            'physical_specimen_location': 'ANL',
            'texture': '64.6 sand, 17.6 silt, 17.8 clay',
            'common_name': 'soil metagenome',
            'water_content_soil': '0.164',
            'env_feature': 'ENVO:plant-associated habitat',
            'assigned_from_geo': 'n',
            'altitude': '0',
            'tot_org_carb': '5',
            'env_biome': 'ENVO:Temperate grasslands, savannas, and shrubland '
                         'biome',
            'sample_type': 'ENVO:soil',
            'scientific_name': '1118232',
            'host_taxid': '3483',
            'latitude': '35.2374368957',
            'ph': '6.94',
            'description_duplicate': 'Burmese bulk',
            'elevation': '114',
            'description': 'Cannabis Soil Microbiome',
            'physical_specimen_remaining': 'true',
            'dna_extracted': 'true',
            'taxon_id': '410658',
            'samp_salinity': '7.15',
            'host_subject_id': '1001:B4',
            'season_environment': 'winter',
            'temp': '15',
            'qiita_study_id': '1',
            'country': 'GAZ:United States of America',
            'longitude': '68.5041623253',
            'tot_nitro': '1.41',
            'depth': '0.15',
            'anonymized_name': 'SKB2'})

    def test_sample_template_get_req_no_access(self):
        obs = sample_template_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_sample_template_get_req_no_template(self):
        obs = sample_template_get_req(self.new_study.id, 'test@foo.bar')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Sample template %d does not '
                               'exist' % self.new_study.id})

    def test_get_sample_template_processing_status(self):
        key = SAMPLE_TEMPLATE_KEY_FORMAT % 1

        obs_proc, obs_at, obs_am = get_sample_template_processing_status(1)
        self.assertFalse(obs_proc)
        self.assertEqual(obs_at, "")
        self.assertEqual(obs_am, "")

        # With job id and processing
        qiita_plugin = qdb.software.Software.from_name_and_version('Qiita',
                                                                   'alpha')
        cmd = qiita_plugin.get_command('update_sample_template')
        params = qdb.software.Parameters.load(
            cmd, values_dict={'study': 1, 'template_fp': 'ignored'})
        job = qdb.processing_job.ProcessingJob.create(
            qdb.user.User('test@foo.bar'), params, True)
        job._set_status('running')
        r_client.set(key, dumps({'job_id': job.id}))
        obs_proc, obs_at, obs_am = get_sample_template_processing_status(1)
        self.assertTrue(obs_proc)
        self.assertEqual(obs_at, "info")
        self.assertEqual(
            obs_am, "This sample template is currently being processed")

        # With job id and success
        job._set_status('success')
        r_client.set(key, dumps({'job_id': job.id, 'alert_type': 'warning',
                                 'alert_msg': 'Some\nwarning'}))
        obs_proc, obs_at, obs_am = get_sample_template_processing_status(1)
        self.assertFalse(obs_proc)
        self.assertEqual(obs_at, "warning")
        self.assertEqual(obs_am, "Some</br>warning")

        # With job and not success
        job = qdb.processing_job.ProcessingJob.create(
            qdb.user.User('test@foo.bar'), params, True)
        job._set_status('running')
        job._set_error('Some\nerror')
        r_client.set(key, dumps({'job_id': job.id}))
        obs_proc, obs_at, obs_am = get_sample_template_processing_status(1)
        self.assertFalse(obs_proc)
        self.assertEqual(obs_at, "danger")
        self.assertEqual(obs_am, "Some</br>error")

    def test_sample_template_columns_get_req_no_template(self):
        # Test sample template not existing
        obs = sample_template_get_req(self.new_study.id, 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Sample template %d does not exist' %
                          self.new_study.id}
        self.assertEqual(obs, exp)

    def test_sample_template_samples_get_req(self):
        obs = sample_template_samples_get_req(1, 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'samples': ['1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195',
                           '1.SKB4.640189', '1.SKB5.640181', '1.SKB6.640176',
                           '1.SKB7.640196', '1.SKB8.640193', '1.SKB9.640200',
                           '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
                           '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190',
                           '1.SKD7.640191', '1.SKD8.640184', '1.SKD9.640182',
                           '1.SKM1.640183', '1.SKM2.640199', '1.SKM3.640197',
                           '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
                           '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192']}
        self.assertEqual(obs, exp)

    def test_sample_template_samples_get_req_no_access(self):
        obs = sample_template_samples_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_sample_template_sample_get_req_no_template(self):
        obs = sample_template_samples_get_req(self.new_study.id,
                                              'test@foo.bar')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Sample template %d does not '
                               'exist' % self.new_study.id})

    def test_sample_template_category_get_req(self):
        obs = sample_template_category_get_req('latitude', 1, 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'values': {'1.SKB2.640194': '35.2374368957',
                          '1.SKM4.640180': 'Not applicable',
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
                          '1.SKM3.640197': 'Not applicable',
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

        self.assertEqual(obs, exp)

    def test_sample_template_category_get_req_no_access(self):
        obs = sample_template_category_get_req('latitude', 1,
                                               'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_sample_template_category_get_req_no_template(self):
        obs = sample_template_category_get_req('latitiude', self.new_study.id,
                                               'test@foo.bar')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Sample template %d does not '
                               'exist' % self.new_study.id})

    def test_sample_template_filepaths_get_req(self):
        obs = sample_template_filepaths_get_req(1, 'test@foo.bar')
        # have to check each key individually as the filepaths will change
        self.assertEqual(obs['status'], 'success')
        self.assertEqual(obs['message'], '')
        # [0] the fp_id is the first element, that should change
        fp_ids = [fp[0] for fp in obs['filepaths']]
        self.assertItemsEqual(fp_ids, [17, 22])

    def test_sample_template_filepaths_get_req_no_access(self):
        obs = sample_template_filepaths_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_sample_template_filepaths_get_req_no_template(self):
        obs = sample_template_filepaths_get_req(self.new_study.id,
                                                'test@foo.bar')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Sample template %d does not '
                               'exist' % self.new_study.id})

    def test_sample_template_meta_cats_get_req(self):
        obs = sample_template_meta_cats_get_req(1, 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'categories': [
                   'altitude', 'anonymized_name', 'assigned_from_geo',
                   'collection_timestamp', 'common_name', 'country', 'depth',
                   'description', 'description_duplicate', 'dna_extracted',
                   'elevation', 'env_biome', 'env_feature', 'host_subject_id',
                   'host_taxid', 'latitude', 'longitude', 'ph',
                   'physical_specimen_location', 'physical_specimen_remaining',
                   'samp_salinity', 'sample_type', 'scientific_name',
                   'season_environment', 'taxon_id', 'temp', 'texture',
                   'tot_nitro', 'tot_org_carb', 'water_content_soil']}
        self.assertEqual(obs, exp)

    def test_sample_template_meta_cats_get_req_no_access(self):
        obs = sample_template_meta_cats_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_sample_template_meta_cats_get_req_no_template(self):
        obs = sample_template_meta_cats_get_req(self.new_study.id,
                                                'test@foo.bar')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Sample template %d does not '
                               'exist' % self.new_study.id})


if __name__ == '__main__':
    main()
