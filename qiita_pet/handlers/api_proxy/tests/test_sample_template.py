from unittest import TestCase, main
from os.path import join

from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.api_proxy.sample_template import (
    sample_template_get_req, sample_template_post_req,
    sample_template_put_req, sample_template_delete_req,
    sample_template_filepaths_get_req)


class TestSampleAPI(TestCase):
    def test_sample_template_get_req(self):
        obs = sample_template_get_req(1, 'test@foo.bar')
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
               'num_samples': 27}
        self.assertEqual(obs, exp)

    def test_sample_template_get_req_no_access(self):
        obs = sample_template_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

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

    def test_sample_template_filepaths_get_req(self):
        obs = sample_template_filepaths_get_req(1, 'test@foo.bar')

        exp = {'status': 'success',
               'message': '',
               'filepaths': [(14, join(qiita_config.base_url,
                             'download/templates/1_19700101-000000.txt'))]}
        self.assertEqual(obs, exp)

    def test_sample_template_filepaths_get_req_no_access(self):
        obs = sample_template_filepaths_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
