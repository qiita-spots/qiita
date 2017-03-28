# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from StringIO import StringIO

import pandas as pd

from tornado.escape import json_decode
from moi import r_client

from qiita_db.metadata_template.util import load_template_to_dataframe
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_pet.test.tornado_test_base import TestHandlerBase


class StudyPrepCreatorTests(TestHandlerBase):
    def setUp(self):
        self.client_token = 'SOMEAUTHTESTINGTOKENHERE2122'
        r_client.hset(self.client_token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.client_token, 'client_id', 'test123123123')
        r_client.hset(self.client_token, 'grant_type', 'client')
        r_client.expire(self.client_token, 5)

        self.headers = {'Authorization': 'Bearer ' + self.client_token}
        super(StudyPrepCreatorTests, self).setUp()

    def test_post_non_existant_study(self):
        # study id that does not exist
        prep = StringIO(EXP_PREP_TEMPLATE.format(0))
        prep_table = load_template_to_dataframe(prep)

        response = self.post('/api/v1/study/0/preparation?'
                             '&investigation_type=WhoCares',
                             data=prep_table.T.to_dict(),
                             headers=self.headers, asjson=True)
        self.assertEqual(response.code, 404)

    def test_post_non_matching_identifiers(self):
        prep = StringIO(EXP_PREP_TEMPLATE.format(100))
        prep_table = load_template_to_dataframe(prep)

        response = self.post('/api/v1/study/1/preparation?'
                             'data_type=16S'
                             '&investigation_type=WhoCares',
                             data=prep_table.T.to_dict(),
                             headers=self.headers, asjson=True)
        self.assertEqual(response.code, 406)
        exp = {'message': 'Samples found in prep template but not in sample '
                          'template'}
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_post_valid_study(self):
        prep = StringIO(EXP_PREP_TEMPLATE.format(1))
        prep_table = load_template_to_dataframe(prep)

        response = self.post('/api/v1/study/1/preparation?data_type=16S',
                             data=prep_table.T.to_dict(),
                             headers=self.headers, asjson=True)
        self.assertEqual(response.code, 200)
        exp = json_decode(response.body)
        p = PrepTemplate(exp['id']).to_dataframe()

        prep_table.index.name = 'sample_id'
        pd.util.testing.assert_frame_equal(prep_table, p)

    
EXP_PREP_TEMPLATE = (
    'sample_name\tbarcode\tcenter_name\tcenter_project_name\t'
    'ebi_submission_accession\temp_status\texperiment_design_description\t'
    'instrument_model\tlibrary_construction_protocol\tplatform\tprimer\t'
    'bar\trun_prefix\tstr_column\n'
    '{0}.SKB7.640196\tCCTCTGAGAGCT\tANL\tTest Project\t\tEMP\tBBBB\t'
    'Illumina MiSeq\tAAAA\tILLUMINA\tGTGCCAGCMGCCGCGGTAA\tfoo\t'
    's_G1_L002_sequences\tValue for sample 3\n'
    '{0}.SKB8.640193\tGTCCGCAAGTTA\tANL\tTest Project\t\tEMP\tBBBB\t'
    'Illumina MiSeq\tAAAA\tILLUMINA\tGTGCCAGCMGCCGCGGTAA\tfoo\t'
    's_G1_L001_sequences\tValue for sample 1\n'
    '{0}.SKD8.640184\tCGTAGAGCTCTC\tANL\tTest Project\t\tEMP\tBBBB\t'
    'Illumina MiSeq\tAAAA\tILLUMINA\tGTGCCAGCMGCCGCGGTAA\tfoo\t'
    's_G1_L001_sequences\tValue for sample 2\n')


if __name__ == '__main__':
    main()
