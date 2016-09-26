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
from qiita_db.handlers.plugin import _get_plugin, _get_command
import qiita_db as qdb


class UtilTests(TestCase):
    def test_get_plugin(self):
        obs = _get_plugin("QIIME", "1.9.1")
        exp = qdb.software.Software(1)
        self.assertEqual(obs, exp)

        # It does not exist
        with self.assertRaises(HTTPError):
            _get_plugin("QiIME", "1.9.1")

    def test_get_command(self):
        obs = _get_command('QIIME', '1.9.1', 'Split libraries FASTQ')
        exp = qdb.software.Command(1)
        self.assertEqual(obs, exp)

        # It does not exist
        with self.assertRaises(HTTPError):
            _get_command('QIIME', '1.9.1', 'UNKNOWN')


class PluginHandlerTests(OauthTestingBase):
    def test_get_plugin_does_not_exist(self):
        obs = self.get('/qiita_db/plugins/QIIME/1.9.0/', headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get_no_header(self):
        obs = self.get('/qiita_db/plugins/QIIME/1.9.0/')
        self.assertEqual(obs.code, 400)

    def test_get(self):
        obs = self.get('/qiita_db/plugins/QIIME/1.9.1/', headers=self.header)
        self.assertEqual(obs.code, 200)
        exp = {
            'name': 'QIIME',
            'version': '1.9.1',
            'description': 'Quantitative Insights Into Microbial Ecology '
                           '(QIIME) is an open-source bioinformatics pipeline '
                           'for performing microbiome analysis from raw DNA '
                           'sequencing data',
            'commands': ['Split libraries FASTQ', 'Split libraries',
                         'Pick closed-reference OTUs'],
            'publications': [{'DOI': '10.1038/nmeth.f.303',
                              'PubMed': '20383131'}],
            'default_workflows': ['FASTQ upstream workflow',
                                  'FASTA upstream workflow',
                                  'Per sample FASTQ upstream workflow'],
            'type': 'artifact transformation',
            'active': False}
        self.assertEqual(loads(obs.body), exp)


class CommandListHandlerTests(OauthTestingBase):
    def test_post(self):
        data = {
            'name': 'New Command',
            'description': 'Command added for testing',
            'required_parameters': {'in_data': ['artifact', ['FASTA']]},
            'optional_parameters': {'param1': ['string', ''],
                                    'param2': ['float', '1.5'],
                                    'param3': ['bool', 'True']},
            'default_parameter_sets': {
                'dflt1': {'param1': 'test', 'param2': '2.4', 'param3': 'False'}
            }}
        obs = self.post('/qiita_db/plugins/QIIME/1.9.1/commands/', data=data,
                        headers=self.header)
        self.assertEqual(obs.code, 200)
        obs = _get_command('QIIME', '1.9.1', 'New Command')
        self.assertEqual(obs.name, 'New Command')


class CommandHandlerTests(OauthTestingBase):
    def test_get_command_does_not_exist(self):
        obs = self.get('/qiita_db/plugins/QIIME/1.9.1/commands/UNKNOWN/',
                       headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get_no_header(self):
        obs = self.get(
            '/qiita_db/plugins/QIIME/1.9.1/commands/Split%20libraries/')
        self.assertEqual(obs.code, 400)

    def test_get(self):
        obs = self.get(
            '/qiita_db/plugins/QIIME/1.9.1/commands/Split%20libraries/',
            headers=self.header)
        self.assertEqual(obs.code, 200)
        exp = {'name': 'Split libraries',
               'description': 'Demultiplexes and applies quality control to '
                              'FASTA data',
               'required_parameters': {
                    'input_data': ['artifact', ['FASTA', 'FASTA_Sanger',
                                                'SFF']]},
               'optional_parameters': {
                    'barcode_type': ['string', 'golay_12'],
                    'disable_bc_correction': ['bool', 'False'],
                    'disable_primers': ['bool', 'False'],
                    'max_ambig': ['integer', '6'],
                    'max_barcode_errors': ['float', '1.5'],
                    'max_homopolymer': ['integer', '6'],
                    'max_primer_mismatch': ['integer', '0'],
                    'max_seq_len': ['integer', '1000'],
                    'min_qual_score': ['integer', '25'],
                    'min_seq_len': ['integer', '200'],
                    'qual_score_window': ['integer', '0'],
                    'reverse_primer_mismatches': ['integer', '0'],
                    'reverse_primers': ['choice:["disable", "truncate_only", '
                                        '"truncate_remove"]', 'disable'],
                    'trim_seq_length': ['bool', 'False'],
                    'truncate_ambi_bases': ['bool', 'False']},
               'default_parameter_sets': {
                    'Defaults with Golay 12 barcodes': {
                        'reverse_primers': 'disable',
                        'reverse_primer_mismatches': 0,
                        'disable_bc_correction': False,
                        'max_barcode_errors': 1.5,
                        'disable_primers': False,
                        'min_seq_len': 200,
                        'truncate_ambi_bases': False,
                        'max_ambig': 6,
                        'min_qual_score': 25,
                        'trim_seq_length': False,
                        'max_seq_len': 1000,
                        'max_primer_mismatch': 0,
                        'max_homopolymer': 6,
                        'qual_score_window': 0,
                        'barcode_type': 'golay_12'},
                    'Defaults with Hamming 8 barcodes': {
                        'reverse_primers': 'disable',
                        'reverse_primer_mismatches': 0,
                        'disable_bc_correction': False,
                        'max_barcode_errors': 1.5,
                        'disable_primers': False,
                        'min_seq_len': 200,
                        'truncate_ambi_bases': False,
                        'max_ambig': 6,
                        'min_qual_score': 25,
                        'trim_seq_length': False,
                        'max_seq_len': 1000,
                        'max_primer_mismatch': 0,
                        'max_homopolymer': 6,
                        'qual_score_window': 0,
                        'barcode_type': 'hamming_8'}}}
        self.assertEqual(loads(obs.body), exp)


if __name__ == '__main__':
    main()
