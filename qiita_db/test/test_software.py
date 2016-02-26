# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


@qiita_test_checker()
class CommandTests(TestCase):
    def setUp(self):
        self.software = qdb.software.Software(1)
        self.parameters = {
            'req_param': ['string', None],
            'opt_int_param': ['integer', '4'],
            'opt_choice_param': ['choice:["opt1", "opt2"]', 'opt1']}

    def test_exists(self):
        self.assertFalse(qdb.software.Command.exists(
            self.software, "donotexists"))
        self.assertTrue(qdb.software.Command.exists(
            self.software, "Split libraries"))

    def test_create_error_no_parameters(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command", {})

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command", None)

    def test_create_error_malformed_params(self):
        self.parameters['req_param'].append('breaking_the_format')
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command",
                self.parameters)

    def test_create_error_unsupported_parameter_type(self):
        self.parameters['opt_int_param'][0] = 'unsupported_type'
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command",
                self.parameters)

    def test_create_error_bad_default_choice(self):
        self.parameters['opt_choice_param'][1] = 'unsupported_choice'
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command",
                self.parameters)

    def test_create_error_duplicate(self):
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.software.Command.create(
                self.software, "Split libraries",
                "This is a command for testing", self.parameters)

    def test_software(self):
        self.assertEqual(qdb.software.Command(1).software,
                         qdb.software.Software(1))
        self.assertEqual(qdb.software.Command(2).software,
                         qdb.software.Software(1))

    def test_name(self):
        self.assertEqual(qdb.software.Command(1).name, "Split libraries FASTQ")
        self.assertEqual(qdb.software.Command(2).name, "Split libraries")

    def test_description(self):
        self.assertEqual(
            qdb.software.Command(1).description,
            "Demultiplexes and applies quality control to FASTQ data")
        self.assertEqual(
            qdb.software.Command(2).description,
            "Demultiplexes and applies quality control to FASTA data")

    def test_parameters(self):
        exp_params = {'barcode_type': ['string', 'golay_12'],
                      'input_data': ['artifact', None],
                      'max_bad_run_length': ['integer', '3'],
                      'max_barcode_errors': ['float', '1.5'],
                      'min_per_read_length_fraction': ['float', '0.75'],
                      'phred_quality_threshold': ['integer', '3'],
                      'rev_comp': ['bool', 'False'],
                      'rev_comp_barcode': ['bool', 'False'],
                      'rev_comp_mapping_barcodes': ['bool', 'False'],
                      'sequence_max_n': ['integer', '0']}
        self.assertEqual(qdb.software.Command(1).parameters, exp_params)
        exp_params = {
            'barcode_type': ['string', 'golay_12'],
            'disable_bc_correction': ['bool', 'False'],
            'disable_primers': ['bool', 'False'],
            'input_data': ['artifact', None],
            'max_ambig': ['integer', '6'],
            'max_barcode_errors': ['float', '1.5'],
            'max_homopolymer': ['integer', '6'],
            'max_primer_mismatch': ['integer', '0'],
            'max_seq_len': ['integer', '1000'],
            'min_qual_score': ['integer', '25'],
            'min_seq_len': ['integer', '200'],
            'qual_score_window': ['integer', '0'],
            'reverse_primer_mismatches': ['integer', '0'],
            'reverse_primers':
                ['choice:["disable", "truncate_only", "truncate_remove"]',
                 'disable'],
            'trim_seq_length': ['bool', 'False'],
            'truncate_ambi_bases': ['bool', 'False']}
        self.assertEqual(qdb.software.Command(2).parameters, exp_params)


@qiita_test_checker()
class SoftwareTests(TestCase):
    def test_create_with_publications(self):
        exp_publications = [['10.1000/nmeth.f.101', '12345678']]
        obs = qdb.software.Software.create(
            "Published Software", "1.0.0", "Another testing software",
            "env_name", "start_plugin",
            publications=exp_publications)
        self.assertEqual(obs.name, "Published Software")
        self.assertEqual(obs.version, "1.0.0")
        self.assertEqual(obs.description, "Another testing software")
        self.assertEqual(obs.commands, [])
        self.assertEqual(obs.publications, exp_publications)
        self.assertEqual(obs.environment_script, 'env_name')
        self.assertEqual(obs.start_script, 'start_plugin')

    def test_add_publications(self):
        tester = qdb.software.Software(1)
        self.assertEqual(tester.publications,
                         [['10.1038/nmeth.f.303', '20383131']])
        tester.add_publications([['10.1000/nmeth.f.101', '12345678']])
        exp = [['10.1038/nmeth.f.303', '20383131'],
               ['10.1000/nmeth.f.101', '12345678']]
        self.assertItemsEqual(tester.publications, exp)

    def test_environment_script(self):
        tester = qdb.software.Software(1)
        self.assertEqual(tester.environment_script, 'source activate qiita')

    def test_start_script(self):
        tester = qdb.software.Software(1)
        self.assertEqual(tester.start_script, 'start_target_gene')


@qiita_test_checker()
class DefaultParametersTests(TestCase):
    def test_exists(self):
        cmd = qdb.software.Command(1)
        obs = qdb.software.DefaultParameters.exists(
            cmd, max_bad_run_length=3, min_per_read_length_fraction=0.75,
            sequence_max_n=0, rev_comp_barcode=False,
            rev_comp_mapping_barcodes=False, rev_comp=False,
            phred_quality_threshold=3, barcode_type="golay_12",
            max_barcode_errors=1.5)
        self.assertTrue(obs)

        obs = qdb.software.DefaultParameters.exists(
            cmd, max_bad_run_length=3, min_per_read_length_fraction=0.75,
            sequence_max_n=0, rev_comp_barcode=False,
            rev_comp_mapping_barcodes=False, rev_comp=False,
            phred_quality_threshold=3, barcode_type="hamming_8",
            max_barcode_errors=1.5)
        self.assertFalse(obs)

    def test_name(self):
        self.assertEqual(qdb.software.DefaultParameters(1).name, "Defaults")

    def test_values(self):
        exp = {'min_per_read_length_fraction': 0.75,
               'max_barcode_errors': 1.5, 'max_bad_run_length': 3,
               'rev_comp': False, 'phred_quality_threshold': 3,
               'rev_comp_barcode': False, 'sequence_max_n': 0,
               'barcode_type': 'golay_12', 'rev_comp_mapping_barcodes': False}
        self.assertEqual(qdb.software.DefaultParameters(1).values, exp)

    def test_command(self):
        self.assertEqual(
            qdb.software.DefaultParameters(1).command, qdb.software.Command(1))


@qiita_test_checker()
class ParametersTests(TestCase):
    def test_init_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.software.Parameters({'a': 1}, None)

    def test_eq(self):
        # Test difference due to type
        a = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1})
        b = qdb.software.DefaultParameters(1)
        self.assertFalse(a == b)
        # Test difference due to command
        b = qdb.software.Parameters.from_default_params(
            qdb.software.Command(2).default_parameter_sets.next(),
            {'input_data': 1})
        self.assertFalse(a == b)
        # Test difference due to values
        b = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 2})
        self.assertFalse(a == b)
        # Test equality
        b = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1})
        self.assertTrue(a == b)

    def test_load_dictionary(self):
        exp_values = {
            "barcode_type": "golay_12", "input_data": 1,
            "max_bad_run_length": 3, "max_barcode_errors": 1.5,
            "min_per_read_length_fraction": 0.75,
            "phred_quality_threshold": 3, "rev_comp": False,
            "rev_comp_barcode": False, "rev_comp_mapping_barcodes": False,
            "sequence_max_n": 0}
        cmd = qdb.software.Command(1)
        obs = qdb.software.Parameters.load(cmd, values_dict=exp_values)
        self.assertEqual(obs.values, exp_values)

    def test_load_error_missing_required(self):
        json_str = ('{"barcode_type": "golay_12",'
                    '"max_bad_run_length": 3, "max_barcode_errors": 1.5, '
                    '"min_per_read_length_fraction": 0.75, '
                    '"phred_quality_threshold": 3, "rev_comp": false, '
                    '"rev_comp_barcode": false, '
                    '"rev_comp_mapping_barcodes": false, "sequence_max_n": 0}')
        cmd = qdb.software.Command(1)
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Parameters.load(cmd, json_str=json_str)

    def test_load_error_missing_optional(self):
        json_str = ('{"barcode_type": "golay_12", "input_data": 1, '
                    '"max_bad_run_length": 3, "max_barcode_errors": 1.5, '
                    '"min_per_read_length_fraction": 0.75, '
                    '"rev_comp": false, '
                    '"rev_comp_barcode": false, '
                    '"rev_comp_mapping_barcodes": false, "sequence_max_n": 0}')
        cmd = qdb.software.Command(1)
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Parameters.load(cmd, json_str=json_str)

    def test_load_error_extra_parameters(self):
        json_str = ('{"barcode_type": "golay_12", "input_data": 1, '
                    '"max_bad_run_length": 3, "max_barcode_errors": 1.5, '
                    '"min_per_read_length_fraction": 0.75, '
                    '"phred_quality_threshold": 3, "rev_comp": false, '
                    '"rev_comp_barcode": false, '
                    '"rev_comp_mapping_barcodes": false, "sequence_max_n": 0,'
                    '"extra_param": 1}')
        cmd = qdb.software.Command(1)
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Parameters.load(cmd, json_str=json_str)

    def test_from_default_parameters(self):
        obs = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1})
        self.assertEqual(obs._command, qdb.software.Command(1))
        exp = {'min_per_read_length_fraction': 0.75,
               'max_barcode_errors': 1.5, 'max_bad_run_length': 3,
               'rev_comp': False, 'phred_quality_threshold': 3,
               'rev_comp_barcode': False, 'sequence_max_n': 0,
               'barcode_type': 'golay_12', 'rev_comp_mapping_barcodes': False,
               'input_data': 1}
        self.assertEqual(obs._values, exp)

        obs = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1},
            opt_params={'max_bad_run_length': 5})
        self.assertEqual(obs._command, qdb.software.Command(1))
        exp = {'min_per_read_length_fraction': 0.75,
               'max_barcode_errors': 1.5, 'max_bad_run_length': 5,
               'rev_comp': False, 'phred_quality_threshold': 3,
               'rev_comp_barcode': False, 'sequence_max_n': 0,
               'barcode_type': 'golay_12', 'rev_comp_mapping_barcodes': False,
               'input_data': 1}
        self.assertEqual(obs._values, exp)

    def test_from_default_params_error_missing_reqd(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Parameters.from_default_params(
                qdb.software.DefaultParameters(1), {})

    def test_from_default_params_error_extra_reqd(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Parameters.from_default_params(
                qdb.software.DefaultParameters(1),
                {'input_data': 1, 'another_one': 2})

    def test_from_default_params_error_extra_opts(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Parameters.from_default_params(
                qdb.software.DefaultParameters(1), {'input_data': 1},
                opt_params={'Unknown': 'foo'})

    def test_dumps(self):
        obs = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1}).dump()
        exp = ('{"barcode_type": "golay_12", "input_data": 1, '
               '"max_bad_run_length": 3, "max_barcode_errors": 1.5, '
               '"min_per_read_length_fraction": 0.75, '
               '"phred_quality_threshold": 3, "rev_comp": false, '
               '"rev_comp_barcode": false, '
               '"rev_comp_mapping_barcodes": false, "sequence_max_n": 0}')
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
