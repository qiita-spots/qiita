# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from copy import deepcopy

import networkx as nx

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


class CommandTestsReadOnly(TestCase):
    def setUp(self):
        self.software = qdb.software.Software(1)
        self.parameters = {
            'req_param': ['string', None],
            'opt_int_param': ['integer', '4'],
            'opt_choice_param': ['choice:["opt1", "opt2"]', 'opt1']}

    def test_get_commands_by_input_type(self):
        obs = list(qdb.software.Command.get_commands_by_input_type(['FASTQ']))
        exp = [qdb.software.Command(1)]
        self.assertItemsEqual(obs, exp)

        obs = list(qdb.software.Command.get_commands_by_input_type(
            ['FASTQ', 'per_sample_FASTQ']))
        exp = [qdb.software.Command(1)]
        self.assertItemsEqual(obs, exp)

        obs = list(qdb.software.Command.get_commands_by_input_type(
            ['FASTQ', 'SFF']))
        exp = [qdb.software.Command(1), qdb.software.Command(2)]
        self.assertItemsEqual(obs, exp)

    def test_get_html_artifact(self):
        obs = qdb.software.Command.get_html_generator('BIOM')
        exp = qdb.software.Command(5)
        self.assertEqual(obs, exp)

        obs = qdb.software.Command.get_html_generator('Demultiplexed')
        exp = qdb.software.Command(7)
        self.assertEqual(obs, exp)

    def test_get_html_artifact_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.get_html_generator('Unknown')

    def test_exists(self):
        self.assertFalse(qdb.software.Command.exists(
            self.software, "donotexists"))
        self.assertTrue(qdb.software.Command.exists(
            self.software, "Split libraries"))

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

    def test_required_parameters(self):
        exp_params = {'input_data': 'artifact'}
        self.assertEqual(qdb.software.Command(1).required_parameters,
                         exp_params)
        self.assertEqual(qdb.software.Command(2).required_parameters,
                         exp_params)

    def test_optional_parameters(self):
        exp_params = {'barcode_type': ['string', 'golay_12'],
                      'max_bad_run_length': ['integer', '3'],
                      'max_barcode_errors': ['float', '1.5'],
                      'min_per_read_length_fraction': ['float', '0.75'],
                      'phred_quality_threshold': ['integer', '3'],
                      'rev_comp': ['bool', 'False'],
                      'rev_comp_barcode': ['bool', 'False'],
                      'rev_comp_mapping_barcodes': ['bool', 'False'],
                      'sequence_max_n': ['integer', '0']}
        self.assertEqual(qdb.software.Command(1).optional_parameters,
                         exp_params)
        exp_params = exp_params = {
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
            'reverse_primers':
                ['choice:["disable", "truncate_only", "truncate_remove"]',
                 'disable'],
            'trim_seq_length': ['bool', 'False'],
            'truncate_ambi_bases': ['bool', 'False']}
        self.assertEqual(qdb.software.Command(2).optional_parameters,
                         exp_params)

    def test_default_parameter_sets(self):
        obs = list(qdb.software.Command(1).default_parameter_sets)
        exp = [qdb.software.DefaultParameters(1),
               qdb.software.DefaultParameters(2),
               qdb.software.DefaultParameters(3),
               qdb.software.DefaultParameters(4),
               qdb.software.DefaultParameters(5),
               qdb.software.DefaultParameters(6),
               qdb.software.DefaultParameters(7)]
        self.assertEqual(obs, exp)

        obs = list(qdb.software.Command(2).default_parameter_sets)
        exp = [qdb.software.DefaultParameters(8),
               qdb.software.DefaultParameters(9)]
        self.assertEqual(obs, exp)


@qiita_test_checker()
class CommandTests(TestCase):
    def setUp(self):
        self.software = qdb.software.Software(1)
        self.parameters = {
            'req_param': ['string', None],
            'opt_int_param': ['integer', '4'],
            'opt_choice_param': ['choice:["opt1", "opt2"]', 'opt1']}

    def test_create_error(self):
        #  no parameters
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command", {})

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command", None)

        # malformed params
        parameters = deepcopy(self.parameters)
        parameters['req_param'].append('breaking_the_format')
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command",
                parameters)

        # unsupported parameter type
        parameters = deepcopy(self.parameters)
        parameters['opt_int_param'][0] = 'unsupported_type'
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command",
                parameters)

        # bad default choice
        parameters = deepcopy(self.parameters)
        parameters['opt_choice_param'][1] = 'unsupported_choice'
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command",
                parameters)

        # duplicate
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.software.Command.create(
                self.software, "Split libraries",
                "This is a command for testing", self.parameters)

    def test_create(self):
        obs = qdb.software.Command.create(
            self.software, "Test Command", "This is a command for testing",
            self.parameters)
        self.assertEqual(obs.name, "Test Command")
        self.assertEqual(obs.description, "This is a command for testing")
        self.assertEqual(obs.parameters, self.parameters)
        exp_required = {'req_param': 'string'}
        self.assertEqual(obs.required_parameters, exp_required)
        exp_optional = {
            'opt_int_param': ['integer', '4'],
            'opt_choice_param': ['choice:["opt1", "opt2"]', 'opt1']}
        self.assertEqual(obs.optional_parameters, exp_optional)


class SoftwareTestsReadOnly(TestCase):
    def test_name(self):
        self.assertEqual(qdb.software.Software(1).name, "QIIME")

    def test_version(self):
        self.assertEqual(qdb.software.Software(1).version, "1.9.1")

    def test_description(self):
        exp = ("Quantitative Insights Into Microbial Ecology (QIIME) is an "
               "open-source bioinformatics pipeline for performing microbiome "
               "analysis from raw DNA sequencing data")
        self.assertEqual(qdb.software.Software(1).description, exp)

    def test_commands(self):
        exp = [qdb.software.Command(1), qdb.software.Command(2),
               qdb.software.Command(3)]
        self.assertEqual(qdb.software.Software(1).commands, exp)

    def test_publications(self):
        self.assertEqual(qdb.software.Software(1).publications,
                         [['10.1038/nmeth.f.303', '20383131']])

    def test_environment_script(self):
        tester = qdb.software.Software(1)
        self.assertEqual(tester.environment_script, 'source activate qiita')

    def test_start_script(self):
        tester = qdb.software.Software(1)
        self.assertEqual(tester.start_script, 'start_target_gene')

    def test_default_workflows(self):
        obs = list(qdb.software.Software(1).default_workflows)
        exp = [qdb.software.DefaultWorkflow(1),
               qdb.software.DefaultWorkflow(2),
               qdb.software.DefaultWorkflow(3)]
        self.assertEqual(obs, exp)

    def test_type(self):
        self.assertEqual(qdb.software.Software(1).type,
                         "artifact transformation")


@qiita_test_checker()
class SoftwareTests(TestCase):
    def test_create(self):
        obs = qdb.software.Software.create(
            "New Software", "0.1.0",
            "This is adding a new software for testing", "env_name",
            "start_plugin", "artifact transformation")
        self.assertEqual(obs.name, "New Software")
        self.assertEqual(obs.version, "0.1.0")
        self.assertEqual(obs.description,
                         "This is adding a new software for testing")
        self.assertEqual(obs.commands, [])
        self.assertEqual(obs.publications, [])
        self.assertEqual(obs.environment_script, 'env_name')
        self.assertEqual(obs.start_script, 'start_plugin')
        self.assertEqual(obs.type, 'artifact transformation')

        # create with publications
        exp_publications = [['10.1000/nmeth.f.101', '12345678']]
        obs = qdb.software.Software.create(
            "Published Software", "1.0.0", "Another testing software",
            "env_name", "start_plugin", "artifact transformation",
            publications=exp_publications)
        self.assertEqual(obs.name, "Published Software")
        self.assertEqual(obs.version, "1.0.0")
        self.assertEqual(obs.description, "Another testing software")
        self.assertEqual(obs.commands, [])
        self.assertEqual(obs.publications, exp_publications)
        self.assertEqual(obs.environment_script, 'env_name')
        self.assertEqual(obs.start_script, 'start_plugin')
        self.assertEqual(obs.type, 'artifact transformation')

    def test_add_publications(self):
        tester = qdb.software.Software(1)
        self.assertEqual(tester.publications,
                         [['10.1038/nmeth.f.303', '20383131']])
        tester.add_publications([['10.1000/nmeth.f.101', '12345678']])
        exp = [['10.1038/nmeth.f.303', '20383131'],
               ['10.1000/nmeth.f.101', '12345678']]
        self.assertItemsEqual(tester.publications, exp)


class DefaultParametersTestsReadOnly(TestCase):
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
class DefaultParametersTests(TestCase):
    def test_create(self):
        cmd = qdb.software.Command(1)
        obs = qdb.software.DefaultParameters.create(
            "test_create", cmd, max_bad_run_length=3,
            min_per_read_length_fraction=0.75, sequence_max_n=0,
            rev_comp_barcode=False, rev_comp_mapping_barcodes=False,
            rev_comp=False, phred_quality_threshold=3,
            barcode_type="hamming_8", max_barcode_errors=1.5)
        self.assertEqual(obs.name, "test_create")

        exp = {'max_bad_run_length': 3, 'min_per_read_length_fraction': 0.75,
               'sequence_max_n': 0, 'rev_comp_barcode': False,
               'rev_comp_mapping_barcodes': False, 'rev_comp': False,
               'phred_quality_threshold': 3, 'barcode_type': "hamming_8",
               'max_barcode_errors': 1.5}
        self.assertEqual(obs.values, exp)
        self.assertEqual(obs.command, cmd)


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

    def test_load_json(self):
        json_str = ('{"barcode_type": "golay_12", "input_data": 1, '
                    '"max_bad_run_length": 3, "max_barcode_errors": 1.5, '
                    '"min_per_read_length_fraction": 0.75, '
                    '"phred_quality_threshold": 3, "rev_comp": false, '
                    '"rev_comp_barcode": false, '
                    '"rev_comp_mapping_barcodes": false, "sequence_max_n": 0}')
        cmd = qdb.software.Command(1)
        obs = qdb.software.Parameters.load(cmd, json_str=json_str)
        exp_values = {
            "barcode_type": "golay_12", "input_data": 1,
            "max_bad_run_length": 3, "max_barcode_errors": 1.5,
            "min_per_read_length_fraction": 0.75,
            "phred_quality_threshold": 3, "rev_comp": False,
            "rev_comp_barcode": False, "rev_comp_mapping_barcodes": False,
            "sequence_max_n": 0}
        self.assertEqual(obs.values, exp_values)

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

    def test_command(self):
        obs = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1}).command
        self.assertEqual(obs, qdb.software.Command(1))

    def test_values(self):
        obs = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1}).values
        exp = {'min_per_read_length_fraction': 0.75,
               'max_barcode_errors': 1.5, 'max_bad_run_length': 3,
               'rev_comp': False, 'phred_quality_threshold': 3,
               'rev_comp_barcode': False, 'sequence_max_n': 0,
               'barcode_type': 'golay_12', 'rev_comp_mapping_barcodes': False,
               'input_data': 1}
        self.assertEqual(obs, exp)

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


class DefaultWorkflowNodeTests(TestCase):
    def test_command(self):
        obs = qdb.software.DefaultWorkflowNode(1)
        self.assertEqual(obs.command, qdb.software.Command(1))

        obs = qdb.software.DefaultWorkflowNode(2)
        self.assertEqual(obs.command, qdb.software.Command(3))

    def test_parameters(self):
        obs = qdb.software.DefaultWorkflowNode(1)
        self.assertEqual(obs.parameters, qdb.software.DefaultParameters(1))

        obs = qdb.software.DefaultWorkflowNode(2)
        self.assertEqual(obs.parameters, qdb.software.DefaultParameters(10))


class DefaultWorkflowEdgeTests(TestCase):
    def test_connections(self):
        tester = qdb.software.DefaultWorkflowEdge(1)
        obs = tester.connections
        self.assertEqual(obs, [['demultiplexed', 'input_data']])


class DefaultWorkflowTests(TestCase):
    def test_name(self):
        self.assertEqual(qdb.software.DefaultWorkflow(1).name,
                         "FASTQ upstream workflow")
        self.assertEqual(qdb.software.DefaultWorkflow(2).name,
                         "FASTA upstream workflow")
        self.assertEqual(qdb.software.DefaultWorkflow(3).name,
                         "Per sample FASTQ upstream workflow")

    def test_graph(self):
        obs = qdb.software.DefaultWorkflow(1).graph
        self.assertTrue(isinstance(obs, nx.DiGraph))
        exp = [qdb.software.DefaultWorkflowNode(1),
               qdb.software.DefaultWorkflowNode(2)]
        self.assertItemsEqual(obs.nodes(), exp)
        exp = [(qdb.software.DefaultWorkflowNode(1),
                qdb.software.DefaultWorkflowNode(2),
                {'connections': qdb.software.DefaultWorkflowEdge(1)})]
        self.assertItemsEqual(obs.edges(data=True), exp)

        obs = qdb.software.DefaultWorkflow(2).graph
        self.assertTrue(isinstance(obs, nx.DiGraph))
        exp = [qdb.software.DefaultWorkflowNode(3),
               qdb.software.DefaultWorkflowNode(4)]
        self.assertItemsEqual(obs.nodes(), exp)
        exp = [(qdb.software.DefaultWorkflowNode(3),
                qdb.software.DefaultWorkflowNode(4),
                {'connections': qdb.software.DefaultWorkflowEdge(2)})]
        self.assertItemsEqual(obs.edges(data=True), exp)


if __name__ == '__main__':
    main()
