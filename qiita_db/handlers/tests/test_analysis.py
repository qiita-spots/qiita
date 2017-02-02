# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main, TestCase
from json import loads

from tornado.web import HTTPError

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
from qiita_db.handlers.analysis import _get_analysis
import qiita_db as qdb


class UtilTests(TestCase):
    def test_get_analysis(self):
        obs = _get_analysis(1)
        exp = qdb.analysis.Analysis(1)
        self.assertEqual(obs, exp)

        # It doesn't exist
        with self.assertRaises(HTTPError):
            _get_analysis(100)


class APIAnalysisMetadataHandlerTests(OauthTestingBase):
    def test_get_does_not_exist(self):
        obs = self.get('/qiita_db/analysis/100/metadata/', headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get_no_header(self):
        obs = self.get('/qiita_db/analysis/1/metadata/')
        self.assertEqual(obs.code, 400)

    def test_get(self):
        obs = self.get('/qiita_db/analysis/1/metadata/', headers=self.header)
        self.assertEqual(obs.code, 200)

        obs = loads(obs.body)
        exp = ['1.SKM4.640180', '1.SKB8.640193', '1.SKD8.640184',
               '1.SKM9.640192', '1.SKB7.640196']
        self.assertItemsEqual(obs, exp)

        exp = {'platform': 'Illumina', 'longitude': '95.5088566087',
               'experiment_center': 'ANL', 'center_name': 'ANL',
               'run_center': 'ANL', 'run_prefix': 's_G1_L001_sequences',
               'sample_type': 'ENVO:soil',
               'common_name': 'rhizosphere metagenome', 'samp_size': '.25,g',
               'has_extracted_data': 'True', 'water_content_soil': '0.101',
               'target_gene': '16S rRNA',
               'env_feature': 'ENVO:plant-associated habitat',
               'sequencing_meth': 'Sequencing by synthesis',
               'Description': 'Cannabis Soil Microbiome', 'run_date': '8/1/12',
               'qiita_owner': 'Dude', 'altitude': '0.0',
               'BarcodeSequence': 'TCGACCAAACAC',
               'env_biome': 'ENVO:Temperate grasslands, savannas, and '
                            'shrubland biome',
               'texture': '63.1 sand, 17.7 silt, 19.2 clay',
               'pcr_primers': 'FWD:GTGCCAGCMGCCGCGGTAA; '
                              'REV:GGACTACHVGGGTWTCTAAT',
               'experiment_title': 'Cannabis Soil Microbiome',
               'library_construction_protocol':
                   'This analysis was done as in Caporaso et al 2011 Genome '
                   'research. The PCR primers (F515/R806) were developed '
                   'against the V4 region of the 16S rRNA (both bacteria and '
                   'archaea), which we determined would yield optimal '
                   'community clustering with reads of this length using a '
                   'procedure similar to that of ref. 15. [For reference, '
                   'this primer pair amplifies the region 533_786 in the '
                   'Escherichia coli strain 83972 sequence (greengenes '
                   'accession no. prokMSA_id:470367).] The reverse PCR primer '
                   'is barcoded with a 12-base error-correcting Golay code to '
                   'facilitate multiplexing of up to 1,500 samples per lane, '
                   'and both PCR primers contain sequencer adapter regions.',
               'experiment_design_description':
                   'micro biome of soil and rhizosphere of cannabis plants '
                   'from CA',
               'study_center': 'CCME', 'physical_location': 'ANL',
               'qiita_prep_id': '1', 'taxon_id': '939928',
               'has_physical_specimen': 'True', 'ph': '6.82',
               'description_duplicate': 'Bucu Rhizo',
               'qiita_study_alias': 'Cannabis Soils', 'sample_center': 'ANL',
               'elevation': '114.0', 'illumina_technology': 'MiSeq',
               'assigned_from_geo': 'n',
               'collection_timestamp': '2011-11-11 13:00:00',
               'latitude': '31.7167821863',
               'LinkerPrimerSequence': 'GTGCCAGCMGCCGCGGTAA',
               'qiita_principal_investigator': 'PIDude', 'host_taxid': '3483',
               'samp_salinity': '7.44', 'host_subject_id': '1001:D2',
               'target_subfragment': 'V4', 'season_environment': 'winter',
               'temp': '15.0', 'emp_status': 'EMP',
               'country': 'GAZ:United States of America',
               'instrument_model': 'Illumina MiSeq',
               'qiita_study_title': 'Identification of the Microbiomes for '
                                    'Cannabis Soils',
               'tot_nitro': '1.3', 'depth': '0.15',
               'anonymized_name': 'SKM4', 'tot_org_carb': '3.31'}
        self.assertEqual(obs['1.SKM4.640180'], exp)


if __name__ == '__main__':
    main()
