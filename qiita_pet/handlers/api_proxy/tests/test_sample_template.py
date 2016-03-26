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

from qiita_core.util import qiita_test_checker
import qiita_db as qdb
from qiita_pet.handlers.api_proxy.sample_template import (
    sample_template_summary_get_req, sample_template_post_req,
    sample_template_put_req, sample_template_delete_req,
    sample_template_filepaths_get_req, sample_template_get_req,
    _check_sample_template_exists, sample_template_samples_get_req,
    sample_template_category_get_req, sample_template_meta_cats_get_req)


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
            qdb.user.User('test@foo.bar'), "Some New Study", [1],
            info)

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
            'water_content_soil': 0.164,
            'env_feature': 'ENVO:plant-associated habitat',
            'assigned_from_geo': 'n',
            'altitude': 0.0,
            'tot_org_carb': 5.0,
            'env_biome': 'ENVO:Temperate grasslands, savannas, and shrubland '
                         'biome',
            'sample_type': 'ENVO:soil',
            'scientific_name': '1118232',
            'host_taxid': '3483',
            'latitude': 35.2374368957,
            'ph': 6.94,
            'description_duplicate': 'Burmese bulk',
            'elevation': 114.0,
            'description': 'Cannabis Soil Microbiome',
            'physical_specimen_remaining': True,
            'dna_extracted': True,
            'taxon_id': '410658',
            'samp_salinity': 7.15,
            'host_subject_id': '1001:B4',
            'season_environment': 'winter',
            'temp': 15.0,
            'country': 'GAZ:United States of America',
            'longitude': 68.5041623253,
            'tot_nitro': 1.41,
            'depth': 0.15,
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

    def test_sample_template_summary_get_req(self):
        obs = sample_template_summary_get_req(1, 'test@foo.bar')
        exp = {'summary': {
            'physical_specimen_location': [('ANL', 27)],
            'texture': [('63.1 sand, 17.7 silt, 19.2 clay', 9),
                        ('64.6 sand, 17.6 silt, 17.8 clay', 9),
                        ('66 sand, 16.3 silt, 17.7 clay', 9)],
            'common_name': [('rhizosphere metagenome', 9),
                            ('root metagenome', 9), ('soil metagenome', 9)],
            'water_content_soil': [('0.101', 9), ('0.164', 9), ('0.178', 9)],
            'env_feature': [('ENVO:plant-associated habitat', 27)],
            'assigned_from_geo': [('n', 27)], 'altitude': [('0.0', 27)],
            'tot_org_carb': [('3.31', 9), ('4.32', 9), ('5.0', 9)],
            'env_biome': [('ENVO:Temperate grasslands, savannas, and shrubland'
                           ' biome', 27)],
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
                         ('60.1102854322', 1), ('68.0991287718', 1),
                         ('68.51099627', 1), ('74.0894932572', 1),
                         ('78.3634273709', 1), ('82.8302905615', 1),
                         ('84.0030227585', 1), ('85.4121476399', 1),
                         ('95.2060749748', 1)],
            'ph': [('6.8', 9), ('6.82', 10), ('6.94', 8)],
            'description_duplicate': [('Bucu Rhizo', 3), ('Bucu Roots', 3),
                                      ('Bucu bulk', 3), ('Burmese Rhizo', 3),
                                      ('Burmese bulk', 3), ('Burmese root', 3),
                                      ('Diesel Rhizo', 3), ('Diesel Root', 3),
                                      ('Diesel bulk', 3)],
            'elevation': [('114.0', 27)],
            'description': [('Cannabis Soil Microbiome', 27)],
            'collection_timestamp': [('2011-11-11 13:00:00', 27)],
            'physical_specimen_remaining': [('True', 27)],
            'dna_extracted': [('True', 27)],
            'taxon_id': [('410658', 9), ('939928', 9), ('1118232', 9)],
            'samp_salinity': [('7.1', 9), ('7.15', 9), ('7.44', 9)],
            'host_subject_id': [('1001:B1', 1), ('1001:B2', 1), ('1001:B3', 1),
                                ('1001:B4', 1), ('1001:B5', 1), ('1001:B6', 1),
                                ('1001:B7', 1), ('1001:B8', 1), ('1001:B9', 1),
                                ('1001:D1', 1), ('1001:D2', 1), ('1001:D3', 1),
                                ('1001:D4', 1), ('1001:D5', 1), ('1001:D6', 1),
                                ('1001:D7', 1), ('1001:D8', 1), ('1001:D9', 1),
                                ('1001:M1', 1), ('1001:M2', 1), ('1001:M3', 1),
                                ('1001:M4', 1), ('1001:M5', 1), ('1001:M6', 1),
                                ('1001:M7', 1), ('1001:M8', 1), ('1001:M9', 1)
                                ],
            'season_environment': [('winter', 27)],
            'temp': [('15.0', 27)],
            'country': [('GAZ:United States of America', 27)],
            'longitude': [('2.35063674718', 1), ('3.48274264219', 1),
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
                          ('92.5274472082', 1), ('96.0693176066', 1)],
            'tot_nitro': [('1.3', 9), ('1.41', 9), ('1.51', 9)],
            'depth': [('0.15', 27)],
            'anonymized_name': [('SKB1', 1), ('SKB2', 1), ('SKB3', 1),
                                ('SKB4', 1), ('SKB5', 1), ('SKB6', 1),
                                ('SKB7', 1), ('SKB8', 1), ('SKB9', 1),
                                ('SKD1', 1), ('SKD2', 1), ('SKD3', 1),
                                ('SKD4', 1), ('SKD5', 1), ('SKD6', 1),
                                ('SKD7', 1), ('SKD8', 1), ('SKD9', 1),
                                ('SKM1', 1), ('SKM2', 1), ('SKM3', 1),
                                ('SKM4', 1), ('SKM5', 1), ('SKM6', 1),
                                ('SKM7', 1), ('SKM8', 1), ('SKM9', 1)]},
               'num_samples': 27,
               'num_columns': 30,
               'editable': True,
               'status': 'success',
               'message': ''}
        self.assertEqual(obs, exp)

    def test_sample_template_summary_get_req_no_access(self):
        obs = sample_template_summary_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_sample_template_summary_get_req_no_template(self):
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
               'values': {'1.SKB2.640194': 35.2374368957,
                          '1.SKM4.640180': None,
                          '1.SKB3.640195': 95.2060749748,
                          '1.SKB6.640176': 78.3634273709,
                          '1.SKD6.640190': 29.1499460692,
                          '1.SKM6.640187': 0.291867635913,
                          '1.SKD9.640182': 23.1218032799,
                          '1.SKM8.640201': 3.21190859967,
                          '1.SKM2.640199': 82.8302905615,
                          '1.SKD2.640178': 53.5050692395,
                          '1.SKB7.640196': 13.089194595,
                          '1.SKD4.640185': 40.8623799474,
                          '1.SKB8.640193': 74.0894932572,
                          '1.SKM3.640197': None,
                          '1.SKD5.640186': 85.4121476399,
                          '1.SKB1.640202': 4.59216095574,
                          '1.SKM1.640183': 38.2627021402,
                          '1.SKD1.640179': 68.0991287718,
                          '1.SKD3.640198': 84.0030227585,
                          '1.SKB5.640181': 10.6655599093,
                          '1.SKB4.640189': 43.9614715197,
                          '1.SKB9.640200': 12.6245524972,
                          '1.SKM9.640192': 12.7065957714,
                          '1.SKD8.640184': 57.571893782,
                          '1.SKM5.640177': 44.9725384282,
                          '1.SKM7.640188': 60.1102854322,
                          '1.SKD7.640191': 68.51099627}}
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

    def test_sample_template_post_req(self):
        obs = sample_template_post_req(1, 'test@foo.bar', '16S',
                                       'uploaded_file.txt')
        exp = {'status': 'error',
               'message': 'Empty file passed!',
               'file': 'uploaded_file.txt'}
        self.assertEqual(obs, exp)

    def test_sample_template_post_req_no_access(self):
        obs = sample_template_post_req(1, 'demo@microbio.me', '16S',
                                       'filepath')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_sample_template_put_req(self):
        obs = sample_template_put_req(1, 'test@foo.bar',
                                      'uploaded_file.txt')
        exp = {'status': 'error',
               'message': 'Empty file passed!',
               'file': 'uploaded_file.txt'}
        self.assertEqual(obs, exp)

    def test_sample_template_put_req_no_access(self):
        obs = sample_template_put_req(1, 'demo@microbio.me', 'filepath')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_sample_template_put_req_no_template(self):
        obs = sample_template_put_req(self.new_study.id, 'test@foo.bar',
                                      'uploaded_file.txt')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Sample template %d does not '
                               'exist' % self.new_study.id})

    def test_sample_template_delete_req(self):
        obs = sample_template_delete_req(1, 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Sample template can not be erased because there are'
                          ' prep templates associated.'}
        self.assertEqual(obs, exp)

    def test_sample_template_delete_req_no_access(self):
        obs = sample_template_delete_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_sample_template_delete_req_no_template(self):
        obs = sample_template_delete_req(self.new_study.id, 'test@foo.bar')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Sample template %d does not '
                               'exist' % self.new_study.id})

    def test_sample_template_filepaths_get_req(self):
        templates_dir = qdb.util.get_mountpoint('templates')[0][1]
        obs = sample_template_filepaths_get_req(1, 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'filepaths': [(17, join(templates_dir,
                              '1_19700101-000000.txt'))]}
        self.assertEqual(obs, exp)

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
