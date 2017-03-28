# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from StringIO import StringIO
import os

import pandas as pd

from tornado.escape import json_decode
from moi import r_client

from qiita_db.metadata_template.util import load_template_to_dataframe
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.util import get_mountpoint


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
                             '&data_type=16S',
                             data=prep_table.T.to_dict(),
                             headers=self.headers, asjson=True)
        self.assertEqual(response.code, 404)

    def test_post_non_matching_identifiers(self):
        prep = StringIO(EXP_PREP_TEMPLATE.format(100))
        prep_table = load_template_to_dataframe(prep)

        response = self.post('/api/v1/study/1/preparation?'
                             'data_type=16S',
                             data=prep_table.T.to_dict(),
                             headers=self.headers, asjson=True)
        self.assertEqual(response.code, 406)
        exp = {'message': 'Samples found in prep template but not sample '
                          'template: 1.100.SKB7.640196, 1.100.SKD8.640184, '
                          '1.100.SKB8.640193'}
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
        exp_prep = PrepTemplate(exp['id']).to_dataframe()

        prep_table.index.name = 'sample_id'

        # sort columns to be comparable
        prep_table = prep_table[sorted(prep_table.columns.tolist())]
        exp_prep = exp_prep[sorted(exp_prep.columns.tolist())]
        exp_prep.drop('qiita_prep_id', axis=1, inplace=True)

        pd.util.testing.assert_frame_equal(prep_table, exp_prep)


class StudyPrepArtifactCreatorTests(TestHandlerBase):
    def setUp(self):
        self.client_token = 'SOMEAUTHTESTINGTOKENHERE2122'
        r_client.hset(self.client_token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.client_token, 'client_id', 'test123123123')
        r_client.hset(self.client_token, 'grant_type', 'client')
        r_client.expire(self.client_token, 5)

        self.headers = {'Authorization': 'Bearer ' + self.client_token}
        super(StudyPrepArtifactCreatorTests, self).setUp()

    def test_post_non_existant_study(self):
        uri = '/api/v1/study/0/preparation/0/artifact'
        body = {'artifact_type': 'foo', 'filepaths': [['foo.txt', 1],
                                                      ['bar.txt', 1]],
                'artifact_name': 'a name is a name'}

        response = self.post(uri, data=body, headers=self.headers, asjson=True)
        exp = {'message': 'Study not found'}
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)

    def test_post_non_existant_prep(self):
        uri = '/api/v1/study/1/preparation/1337/artifact'
        body = {'artifact_type': 'foo', 'filepaths': [['foo.txt', 1],
                                                      ['bar.txt', 1]],
                'artifact_name': 'a name is a name'}

        response = self.post(uri, data=body, headers=self.headers, asjson=True)
        exp = {'message': 'Preparation not found'}
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)

    def test_post_unknown_artifact_type(self):
        uri = '/api/v1/study/1/preparation/1/artifact'
        body = {'artifact_type': 'foo', 'filepaths': [['foo.txt', 1],
                                                      ['bar.txt', 1]],
                'artifact_name': 'a name is a name'}

        response = self.post(uri, data=body, headers=self.headers, asjson=True)
        exp = {'message': '"foo" is not a recognized artifact_type'}
        self.assertEqual(response.code, 406)
        obs = json_decode(response.body)

    def test_post_unknown_filepath_type_id(self):
        uri = '/api/v1/study/1/preparation/1/artifact'
        body = {'artifact_type': 'foo', 'filepaths': [['foo.txt', 123123],
                                                      ['bar.txt', 1]],
                'artifact_name': 'a name is a name'}

        response = self.post(uri, data=body, headers=self.headers, asjson=True)
        exp = {'message': '123123 is not a recognized file path type id'}
        self.assertEqual(response.code, 406)
        obs = json_decode(response.body)

    def test_post_files_notfound(self):
        uri = '/api/v1/study/1/preparation/1/artifact'
        body = {'artifact_type': 'foo', 'filepaths': [['foo.txt', 1],
                                                      ['bar.txt', 1]],
                'artifact_name': 'a name is a name'}

        response = self.post(uri, data=body, headers=self.headers, asjson=True)
        exp = {'message': 'foo.txt, bar.txt not found in uploads'}
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)

    # 1 -> fwd or rev sequences in fastq
    # 3 -> barcodes
    def test_post_valid(self):
        dontcare, uploads_dir = get_mountpoint('uploads')[0]
        foo_fp = os.path.join(uploads_dir, '1', 'foo.txt')
        bar_fp = os.path.join(uploads_dir, '1', 'bar.txt')
        with open(foo_fp, 'w') as fp:
            fp.write("@x\nATGC\n+\nHHHH\n")
        with open(bar_fp, 'w') as fp:
            fp.write("@x\nATGC\n+\nHHHH\n")

        uri = '/api/v1/study/1/preparation/1/artifact'
        body = {'artifact_type': 'FASTQ', 'filepaths': [['foo.txt', 1],
                                                        ['bar.txt', 3]],
                'artifact_name': 'a name is a name'}

        response = self.post(uri, data=body, headers=self.headers, asjson=True)
        self.assertEqual(response.code, 200)


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
