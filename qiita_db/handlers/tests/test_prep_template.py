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
import qiita_db as qdb
from qiita_db.handlers.prep_template import _get_prep_template


class UtilTests(TestCase):
    def test_get_prep_template(self):
        obs = _get_prep_template(1)
        exp = qdb.metadata_template.prep_template.PrepTemplate(1)
        self.assertEqual(obs, exp)

        # It does not exist
        with self.assertRaises(HTTPError):
            _get_prep_template(100)


class PrepTemplateDataHandlerTests(OauthTestingBase):
    def test_get_does_not_exist(self):
        obs = self.get('/qiita_db/prep_template/100/data/',
                       headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get_no_header(self):
        obs = self.get('/qiita_db/prep_template/100/data/')
        self.assertEqual(obs.code, 400)

    def test_get(self):
        obs = self.get('/qiita_db/prep_template/1/data/', headers=self.header)
        self.assertEqual(obs.code, 200)

        obs = loads(obs.body)
        self.assertEqual(obs.keys(), ['data'])

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
        exp = {
            'barcode': 'GTCCGCAAGTTA',
            'center_name': 'ANL',
            'center_project_name': None,
            'emp_status': 'EMP',
            'experiment_center': 'ANL',
            'experiment_design_description':
                'micro biome of soil and rhizosphere of cannabis plants '
                'from CA',
            'experiment_title': 'Cannabis Soil Microbiome',
            'illumina_technology': 'MiSeq',
            'instrument_model': 'Illumina MiSeq',
            'library_construction_protocol':
                'This analysis was done as in Caporaso et al 2011 Genome '
                'research. The PCR primers (F515/R806) were developed against '
                'the V4 region of the 16S rRNA (both bacteria and archaea), '
                'which we determined would yield optimal community clustering '
                'with reads of this length using a procedure similar to that '
                'of ref. 15. [For reference, this primer pair amplifies the '
                'region 533_786 in the Escherichia coli strain 83972 sequence '
                '(greengenes accession no. prokMSA_id:470367).] The reverse '
                'PCR primer is barcoded with a 12-base error-correcting Golay '
                'code to facilitate multiplexing of up to 1,500 samples per '
                'lane, and both PCR primers contain sequencer adapter '
                'regions.',
            'pcr_primers': 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT',
            'platform': 'Illumina',
            'primer': 'GTGCCAGCMGCCGCGGTAA',
            'run_center': 'ANL',
            'run_date': '8/1/12',
            'run_prefix': 's_G1_L001_sequences',
            'samp_size': '.25,g',
            'sample_center': 'ANL',
            'sequencing_meth': 'Sequencing by synthesis',
            'study_center': 'CCME',
            'target_gene': '16S rRNA',
            'target_subfragment': 'V4'}
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
