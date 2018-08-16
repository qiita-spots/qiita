# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from json import loads

from qiita_db.handlers.tests.oauthbase import OauthTestingBase


class SampleInfoDBHandlerTests(OauthTestingBase):
    def test_get_does_not_exist(self):
        obs = self.get('/qiita_db/sample_information/100/data/',
                       headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get_no_header(self):
        obs = self.get('/qiita_db/sample_information/100/data/')
        self.assertEqual(obs.code, 400)

    def test_get(self):
        obs = self.get('/qiita_db/sample_information/1/data/',
                       headers=self.header)
        self.assertEqual(obs.code, 200)

        obs = loads(obs.body)
        self.assertEqual(obs.keys(), ['data'])

        # for simplicity we will only test that the keys are the same
        # and that one of the key's info is correct
        obs = obs['data']
        exp = ['1.SKB2.640194', '1.SKM4.640180', '1.SKB3.640195',
               '1.SKB6.640176', '1.SKD6.640190', '1.SKM6.640187',
               '1.SKD9.640182', '1.SKM8.640201', '1.SKM2.640199',
               '1.SKD2.640178', '1.SKB7.640196', '1.SKD4.640185',
               '1.SKB8.640193', '1.SKM3.640197', '1.SKD5.640186',
               '1.SKB1.640202', '1.SKM1.640183', '1.SKD1.640179',
               '1.SKD3.640198', '1.SKB5.640181', '1.SKB4.640189',
               '1.SKB9.640200', '1.SKM9.640192', '1.SKD8.640184',
               '1.SKM5.640177', '1.SKM7.640188', '1.SKD7.640191']
        self.assertItemsEqual(obs.keys(), exp)

        obs = obs['1.SKB1.640202']
        exp = {'qiita_study_id': '1', 'physical_specimen_location': 'ANL',
               'tot_org_carb': '5', 'common_name': 'soil metagenome',
               'water_content_soil': '0.164',
               'env_feature': 'ENVO:plant-associated habitat',
               'assigned_from_geo': 'n', 'altitude': '0',
               'env_biome': ('ENVO:Temperate grasslands, savannas, and '
                             'shrubland biome'),
               'texture': '64.6 sand, 17.6 silt, 17.8 clay',
               'scientific_name': '1118232',
               'description_duplicate': 'Burmese bulk',
               'latitude': '4.59216095574', 'ph': '6.94', 'host_taxid': '3483',
               'elevation': '114', 'description': 'Cannabis Soil Microbiome',
               'collection_timestamp': '2011-11-11 13:00:00',
               'physical_specimen_remaining': 'true', 'dna_extracted': 'true',
               'taxon_id': '410658', 'samp_salinity': '7.15',
               'host_subject_id': '1001:M2', 'sample_type': 'ENVO:soil',
               'season_environment': 'winter', 'temp': '15',
               'country': 'GAZ:United States of America',
               'longitude': '63.5115213108', 'tot_nitro': '1.41',
               'depth': '0.15', 'anonymized_name': 'SKB1'}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
