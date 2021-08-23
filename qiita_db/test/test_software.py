# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from copy import deepcopy
from os.path import exists
from os import remove, close
from tempfile import mkstemp
import warnings

import networkx as nx

from qiita_core.util import qiita_test_checker
import qiita_db as qdb

from json import dumps


@qiita_test_checker()
class CommandTests(TestCase):
    def setUp(self):
        self.software = qdb.software.Software(1)
        self.parameters = {
            'req_art': ['artifact:["BIOM"]', None],
            'req_param': ['string', None],
            'opt_int_param': ['integer', '4'],
            'opt_choice_param': ['choice:["opt1", "opt2"]', 'opt1'],
            'opt_mchoice_param': ['mchoice:["opt1", "opt2", "opt3"]',
                                  ['opt1', 'opt2']],
            'opt_bool': ['boolean', 'False']}
        self.outputs = {'out1': 'BIOM'}

    def test_get_commands_by_input_type(self):
        qdb.software.Software.deactivate_all()
        obs = list(qdb.software.Command.get_commands_by_input_type(['FASTQ']))
        self.assertEqual(obs, [])

        cmd = qdb.software.Command(1)
        cmd.activate()
        obs = list(qdb.software.Command.get_commands_by_input_type(['FASTQ']))
        exp = [cmd]
        self.assertCountEqual(obs, exp)

        obs = list(qdb.software.Command.get_commands_by_input_type(
            ['FASTQ', 'per_sample_FASTQ']))
        self.assertCountEqual(obs, exp)

        obs = list(qdb.software.Command.get_commands_by_input_type(
            ['FASTQ', 'SFF']))
        self.assertEqual(obs, exp)

        obs = list(qdb.software.Command.get_commands_by_input_type(
            ['FASTQ', 'SFF'], active_only=False))
        exp = [qdb.software.Command(1), qdb.software.Command(2)]
        self.assertCountEqual(obs, exp)

        new_cmd = qdb.software.Command.create(
            self.software, "Analysis Only Command",
            "This is a command for testing",
            {'req_art': ['artifact:["FASTQ"]', None]},
            analysis_only=True)
        obs = list(qdb.software.Command.get_commands_by_input_type(
            ['FASTQ', 'SFF'], active_only=False))
        exp = [qdb.software.Command(1), qdb.software.Command(2)]
        self.assertCountEqual(obs, exp)

        obs = list(qdb.software.Command.get_commands_by_input_type(
            ['FASTQ', 'SFF'], active_only=False, exclude_analysis=False))
        exp = [qdb.software.Command(1), qdb.software.Command(2), new_cmd]
        self.assertCountEqual(obs, exp)

        obs = list(qdb.software.Command.get_commands_by_input_type(
            ['FASTQ'], active_only=False, exclude_analysis=False,
            prep_type='Metagenomic'))
        exp = [qdb.software.Command(1), new_cmd]
        self.assertCountEqual(obs, exp)

        obs = list(qdb.software.Command.get_commands_by_input_type(
            ['FASTQ'], active_only=False, exclude_analysis=False,
            prep_type='18S'))
        exp = [qdb.software.Command(1)]
        self.assertCountEqual(obs, exp)

    def test_get_html_artifact(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.get_html_generator('BIOM')

        exp = qdb.software.Command(5)
        exp.activate()
        obs = qdb.software.Command.get_html_generator('BIOM')
        self.assertEqual(obs, exp)

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.get_html_generator('Demultiplexed')

        exp = qdb.software.Command(7)
        exp.activate()
        obs = qdb.software.Command.get_html_generator('Demultiplexed')
        self.assertEqual(obs, exp)

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.get_html_generator('Unknown')

    def test_get_validator(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.get_validator('BIOM')

        exp = qdb.software.Command(4)
        exp.activate()
        obs = qdb.software.Command.get_validator('BIOM')
        self.assertEqual(obs, exp)

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.get_validator('Demultiplexed')

        exp = qdb.software.Command(6)
        exp.activate()
        obs = qdb.software.Command.get_validator('Demultiplexed')
        self.assertEqual(obs, exp)

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.get_validator('Unknown')

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

    def test_post_processing_cmd(self):
        # initial test
        self.assertEqual(qdb.software.Command(1).post_processing_cmd, None)

        results = {}
        results['script_env'] = 'source deactivate; source activate qiita'
        results['script_path'] = 'qiita_db/test/support_files/worker.py'
        results['script_params'] = {'a': 'A', 'b': 'B'}

        results = dumps(results)

        # modify table directly, in order to test method
        sql = """UPDATE qiita.software_command
                 SET post_processing_cmd = %s
                 WHERE command_id = 1"""
        qdb.sql_connection.perform_as_transaction(sql, [results])

        results = qdb.software.Command(1).post_processing_cmd

        # test method returns 'ls'
        self.assertEqual(results['script_env'],
                         'source deactivate; source activate qiita')
        self.assertEqual(results['script_path'],
                         'qiita_db/test/support_files/worker.py')
        self.assertEqual(results['script_params'], {'a': 'A', 'b': 'B'})

        # clean up table
        sql = """UPDATE qiita.software_command
                 SET post_processing_cmd = NULL
                 WHERE command_id = 1"""
        qdb.sql_connection.perform_as_transaction(sql)

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
                      'sequence_max_n': ['integer', '0'],
                      'phred_offset': ['choice:["auto", "33", "64"]', 'auto']}
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
        exp_params = {
            'input_data': ('artifact', ['FASTQ', 'per_sample_FASTQ'])}
        obs = qdb.software.Command(1).required_parameters
        self.assertCountEqual(list(obs.keys()), exp_params.keys())
        self.assertEqual(obs['input_data'][0],  exp_params['input_data'][0])
        self.assertCountEqual(obs['input_data'][1],
                              exp_params['input_data'][1])

        exp_params = {
            'input_data': ('artifact', ['SFF', 'FASTA', 'FASTA_Sanger'])}
        obs = qdb.software.Command(2).required_parameters
        self.assertCountEqual(list(obs.keys()), exp_params.keys())
        self.assertEqual(obs['input_data'][0],  exp_params['input_data'][0])
        self.assertCountEqual(obs['input_data'][1],
                              exp_params['input_data'][1])

    def test_optional_parameters(self):
        exp_params = {'barcode_type': ['string', 'golay_12'],
                      'max_bad_run_length': ['integer', '3'],
                      'max_barcode_errors': ['float', '1.5'],
                      'min_per_read_length_fraction': ['float', '0.75'],
                      'phred_quality_threshold': ['integer', '3'],
                      'rev_comp': ['bool', 'False'],
                      'rev_comp_barcode': ['bool', 'False'],
                      'rev_comp_mapping_barcodes': ['bool', 'False'],
                      'sequence_max_n': ['integer', '0'],
                      'phred_offset': ['choice:["auto", "33", "64"]', 'auto']}
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
               qdb.software.DefaultParameters(7),
               qdb.software.DefaultParameters(11),
               qdb.software.DefaultParameters(12)]
        self.assertEqual(obs, exp)

        obs = list(qdb.software.Command(2).default_parameter_sets)
        exp = [qdb.software.DefaultParameters(8),
               qdb.software.DefaultParameters(9)]
        self.assertEqual(obs, exp)

    def test_outputs(self):
        obs = qdb.software.Command(1).outputs
        exp = [['demultiplexed', 'Demultiplexed']]
        self.assertEqual(obs, exp)

        obs = qdb.software.Command(2).outputs
        exp = [['demultiplexed', 'Demultiplexed']]
        self.assertEqual(obs, exp)

        obs = qdb.software.Command(3).outputs
        exp = [['OTU table', 'BIOM']]
        self.assertEqual(obs, exp)

    def test_create_error(self):
        #  no parameters
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command", {},
                self.outputs)

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command", None,
                self.outputs)

        # malformed params
        parameters = deepcopy(self.parameters)
        parameters['req_param'].append('breaking_the_format')
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command",
                parameters, self.outputs)

        # unsupported parameter type
        parameters = deepcopy(self.parameters)
        parameters['opt_int_param'][0] = 'unsupported_type'
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command",
                parameters, self.outputs)

        # bad default choice
        parameters = deepcopy(self.parameters)
        parameters['opt_choice_param'][1] = 'unsupported_choice'
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Command.create(
                self.software, "Test command", "Testing command",
                parameters, self.outputs)

        # duplicate
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.software.Command.create(
                self.software, "Split libraries",
                "This is a command for testing", self.parameters,
                self.outputs)

        # the output type doesn't exist
        with self.assertRaisesRegex(ValueError, "Error creating QIIME, Split "
                                    "libraries - wrong output, This is a "
                                    "command for testing - Unknown "
                                    "artifact_type: BLA!"):
            qdb.software.Command.create(
                self.software, "Split libraries - wrong output",
                "This is a command for testing", self.parameters,
                {'out': 'BLA!'})

    def test_create(self):
        # let's deactivate all current plugins and commands; this is not
        # important to test the creation but it is important to test if a
        # command is active as the new commands should take precedence and
        # should make the old commands active if they have the same name
        qdb.software.Software.deactivate_all()

        # note that here we are adding commands to an existing software
        obs = qdb.software.Command.create(
            self.software, "Test Command", "This is a command for testing",
            self.parameters, self.outputs)
        self.assertEqual(obs.name, "Test Command")
        self.assertEqual(obs.description, "This is a command for testing")
        exp_required = {'req_param': ('string', [None]),
                        'req_art': ('artifact', ['BIOM'])}
        self.assertEqual(obs.required_parameters, exp_required)
        exp_optional = {
            'opt_int_param': ['integer', '4'],
            'opt_choice_param': ['choice:["opt1", "opt2"]', 'opt1'],
            'opt_mchoice_param': ['mchoice:["opt1", "opt2", "opt3"]',
                                  ['opt1', 'opt2']],
            'opt_bool': ['boolean', 'False']}
        self.assertEqual(obs.optional_parameters, exp_optional)
        self.assertFalse(obs.analysis_only)
        self.assertEqual(obs.naming_order, [])
        self.assertEqual(obs.merging_scheme,
                         {'parameters': [], 'outputs': [],
                          'ignore_parent_command': False})

        # here we are creating a new software that we will add new commads to
        obs = qdb.software.Command.create(
            self.software, "Test Command 2", "This is a command for testing",
            self.parameters, analysis_only=True)
        self.assertEqual(obs.name, "Test Command 2")
        self.assertEqual(obs.description, "This is a command for testing")
        self.assertEqual(obs.required_parameters, exp_required)
        self.assertEqual(obs.optional_parameters, exp_optional)
        self.assertTrue(obs.analysis_only)
        self.assertEqual(obs.naming_order, [])
        self.assertEqual(obs.merging_scheme,
                         {'parameters': [], 'outputs': [],
                          'ignore_parent_command': False})

        # Test that the internal parameters in "Validate"
        # are created automatically
        software = qdb.software.Software.create(
            "New Type Software", "1.0.0",
            "This is adding a new software for testing", "env_name",
            "start_plugin", "artifact definition")
        parameters = {
            'template': ('prep_template', None),
            'analysis': ('analysis', None),
            'files': ('string', None),
            'artifact_type': ('string', None)}
        validate = qdb.software.Command.create(
            software, "Validate", "Test creating a validate command",
            parameters)
        self.assertEqual(validate.name, "Validate")
        self.assertEqual(
            validate.description, "Test creating a validate command")
        exp_required = {
            'template': ('prep_template', [None]),
            'analysis': ('analysis', [None]),
            'files': ('string', [None]),
            'artifact_type': ('string', [None])}
        self.assertEqual(validate.required_parameters, exp_required)
        exp_optional = {'name': ['string', 'dflt_name'],
                        'provenance': ['string', None]}
        self.assertEqual(validate.optional_parameters, exp_optional)
        self.assertFalse(validate.analysis_only)
        self.assertEqual(validate.naming_order, [])
        self.assertEqual(validate.merging_scheme,
                         {'parameters': [], 'outputs': [],
                          'ignore_parent_command': False})

        # Test that the naming and merge information is provided
        parameters = {
            'req_art': ['artifact:["BIOM"]', None],
            'opt_int_param': ['integer', '4', 1, True],
            'opt_choice_param': ['choice:["opt1", "opt2"]', 'opt1', 2, True],
            'opt_bool': ['boolean', 'False', None, False]}
        outputs = {'out1': ('BIOM', True)}
        obs = qdb.software.Command.create(
            self.software, "Test Command Merge", "Testing cmd", parameters,
            outputs=outputs)
        self.assertEqual(obs.name, "Test Command Merge")
        self.assertEqual(obs.description, "Testing cmd")
        exp_required = {'req_art': ('artifact', ['BIOM'])}
        self.assertEqual(obs.required_parameters, exp_required)
        exp_optional = {
            'opt_int_param': ['integer', '4'],
            'opt_choice_param': ['choice:["opt1", "opt2"]', 'opt1'],
            'opt_bool': ['boolean', 'False']}
        self.assertEqual(obs.optional_parameters, exp_optional)
        self.assertFalse(obs.analysis_only)
        self.assertEqual(obs.naming_order,
                         ['opt_int_param', 'opt_choice_param'])
        exp = {'parameters': ['opt_choice_param', 'opt_int_param'],
               'outputs': ['out1'],
               'ignore_parent_command': False}
        self.assertEqual(obs.merging_scheme, exp)

        # now that we are done with the regular creation testing we can create
        # a new command with the name of an old deprecated command and make
        # sure that is not deprecated now
        # 1. let's find the previous command and make sure is deprecated
        cmd_name = 'Split libraries FASTQ'
        old_cmd = [cmd for cmd in self.software.commands
                   if cmd.name == cmd_name][0]
        self.assertFalse(old_cmd.active)

        # 2. let's create a new command with the same name and check that now
        #    the old and the new are active. Remember the new command is going
        #    to be created in a new software that has a Validate command which
        #    is an 'artifact definition', so this will allow us to test that
        #    a previous Validate command is not active
        new_cmd = qdb.software.Command.create(
            software, cmd_name, cmd_name, parameters, outputs=outputs)
        self.assertEqual(old_cmd.name, new_cmd.name)
        self.assertTrue(old_cmd.active)
        self.assertTrue(new_cmd.active)
        # find an old Validate command
        old_validate = [c for c in qdb.software.Software.from_name_and_version(
            'BIOM type', '2.1.4 - Qiime2').commands if c.name == 'Validate'][0]
        self.assertEqual(old_validate.name, validate.name)
        self.assertTrue(validate.active)
        self.assertFalse(old_validate.active)

    def test_activate(self):
        qdb.software.Software.deactivate_all()
        tester = qdb.software.Command(1)
        self.assertFalse(tester.active)
        tester.activate()
        self.assertTrue(tester.active)

    def test_processing_jobs(self):
        exp_jids = ['6d368e16-2242-4cf8-87b4-a5dc40bb890b',
                    '4c7115e8-4c8e-424c-bf25-96c292ca1931',
                    'b72369f9-a886-4193-8d3d-f7b504168e75',
                    '46b76f74-e100-47aa-9bf2-c0208bcea52d',
                    '6ad4d590-4fa3-44d3-9a8f-ddbb472b1b5f',
                    '063e553b-327c-4818-ab4a-adfe58e49860',
                    'ac653cb5-76a6-4a45-929e-eb9b2dee6b63']
        exp = [qdb.processing_job.ProcessingJob(j) for j in exp_jids]
        self.assertCountEqual(qdb.software.Command(1).processing_jobs, exp)

        exp_jids = ['bcc7ebcd-39c1-43e4-af2d-822e3589f14d']
        exp = [qdb.processing_job.ProcessingJob(j) for j in exp_jids]
        self.assertCountEqual(qdb.software.Command(2).processing_jobs, exp)

        self.assertCountEqual(qdb.software.Command(4).processing_jobs, [])


@qiita_test_checker()
class SoftwareTestsIter(TestCase):
    # different class to assure integrity of database

    def test_iter(self):
        s1 = qdb.software.Software(1)
        s2 = qdb.software.Software(2)
        s3 = qdb.software.Software(3)
        s4 = qdb.software.Software(4)

        qdb.software.Software.deactivate_all()
        obs = list(qdb.software.Software.iter())
        self.assertEqual(obs, [])
        obs = list(qdb.software.Software.iter(False))
        self.assertEqual(obs, [s1, s2, s3, s4])

        s2.activate()
        obs = list(qdb.software.Software.iter())
        self.assertEqual(obs, [s2])
        obs = list(qdb.software.Software.iter(False))
        self.assertEqual(obs, [s1, s2, s3, s4])

        s1.activate()
        s3.activate()
        obs = list(qdb.software.Software.iter())
        self.assertEqual(obs, [s1, s2, s3])
        obs = list(qdb.software.Software.iter(False))
        self.assertEqual(obs, [s1, s2, s3, s4])

        # test command resouce allocations here to be able to delete
        # allocations so we can tests errors.

        # Command 2 is Split libraries and has defined resources
        self.assertEqual(
            qdb.software.Command(2).resource_allocation,
            '-q qiita -l nodes=1:ppn=1 -l mem=60gb -l walltime=25:00:00')

        # Command 9 is Summarize Taxa and has no defined resources so it goes
        # to defaults
        self.assertEqual(
            qdb.software.Command(9).resource_allocation,
            '-q qiita -l nodes=1:ppn=5 -l pmem=8gb -l walltime=168:00:00')

        # delete allocations to test errors
        qdb.sql_connection.perform_as_transaction(
            "DELETE FROM qiita.processing_job_resource_allocation")

        with self.assertRaisesRegex(ValueError, "Could not match 'Split "
                                    "libraries' to a resource allocation!"):
            qdb.software.Command(2).resource_allocation


@qiita_test_checker()
class SoftwareTests(TestCase):
    def setUp(self):
        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            if exists(f):
                remove(f)

    def test_from_name_and_version(self):
        obs = qdb.software.Software.from_name_and_version('QIIME', '1.9.1')
        exp = qdb.software.Software(1)
        self.assertEqual(obs, exp)

        obs = qdb.software.Software.from_name_and_version(
            'BIOM type', '2.1.4 - Qiime2')
        exp = qdb.software.Software(2)
        self.assertEqual(obs, exp)

        # Wrong name
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.software.Software.from_name_and_version('QiIME', '1.9.1')
        # Wrong version
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.software.Software.from_name_and_version('QIIME', '1.9.0')

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
        obs = qdb.software.Software(1).commands
        self.assertEqual(len(obs), 7)
        for e in exp:
            self.assertIn(e, obs)

    def test_get_command(self):
        s = qdb.software.Software(1)
        obs = s.get_command('Split libraries FASTQ')
        self.assertEqual(obs, qdb.software.Command(1))

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            s.get_command('UNKNOWN')

    def test_publications(self):
        self.assertEqual(qdb.software.Software(1).publications,
                         [['10.1038/nmeth.f.303', '20383131']])

    def test_environment_script(self):
        tester = qdb.software.Software(1)
        self.assertEqual(tester.environment_script, 'source activate qiita')

    def test_start_script(self):
        tester = qdb.software.Software(2)
        self.assertEqual(tester.start_script, 'start_biom')

    def test_default_workflows(self):
        obs = list(qdb.software.DefaultWorkflow.iter(True))
        exp = [qdb.software.DefaultWorkflow(1),
               qdb.software.DefaultWorkflow(2),
               qdb.software.DefaultWorkflow(3)]
        self.assertEqual(obs, exp)
        obs = list(qdb.software.DefaultWorkflow.iter(False))
        self.assertEqual(obs, exp)

        qdb.software.DefaultWorkflow(1).active = False
        obs = list(qdb.software.DefaultWorkflow.iter(False))
        self.assertEqual(obs, exp)

        obs = list(qdb.software.DefaultWorkflow.iter(True))
        exp = [qdb.software.DefaultWorkflow(2),
               qdb.software.DefaultWorkflow(3)]
        self.assertEqual(obs, exp)

        obs = qdb.software.DefaultWorkflow(1).data_type
        exp = ['16S', '18S']
        self.assertEqual(obs, exp)
        obs = qdb.software.DefaultWorkflow(2).data_type
        exp = ['18S']
        self.assertEqual(obs, exp)

        dw = qdb.software.DefaultWorkflow(1)
        exp = ('This accepts html <a href="https://qiita.ucsd.edu">Qiita!</a>'
               '<br/><br/><b>BYE!</b>')
        self.assertEqual(dw.description, exp)
        exp = 'bla!'
        dw.description = exp
        self.assertEqual(dw.description, exp)

    def test_type(self):
        self.assertEqual(qdb.software.Software(1).type,
                         "artifact transformation")

    def test_active(self):
        self.assertTrue(qdb.software.Software(1).active)

    def test_client_id(self):
        self.assertEqual(
            qdb.software.Software(1).client_id,
            'yKDgajoKn5xlOA8tpo48Rq8mWJkH9z4LBCx2SvqWYLIryaan2u')

    def test_client_secret(self):
        self.assertEqual(
            qdb.software.Software(1).client_secret,
            '9xhU5rvzq8dHCEI5sSN95jesUULrZi6pT6Wuc71fDbFbsrnWarcSq56TJLN4kP4hH'
            )

    def test_deactivate_all(self):
        obs = qdb.software.Software(1)
        self.assertTrue(obs.active)
        qdb.software.Software.deactivate_all()
        self.assertFalse(obs.active)

    def test_from_file(self):
        exp = qdb.software.Software(1)
        client_id = 'yKDgajoKn5xlOA8tpo48Rq8mWJkH9z4LBCx2SvqWYLIryaan2u'
        client_secret = ('9xhU5rvzq8dHCEI5sSN95jesUULrZi6pT6Wuc71fDbFbsrnWarc'
                         'Sq56TJLN4kP4hH')
        # Activate existing plugin
        fd, fp = mkstemp(suffix='.conf')
        close(fd)
        self._clean_up_files.append(fp)
        with open(fp, 'w') as f:
            f.write(CONF_TEMPLATE %
                    ('QIIME', '1.9.1',
                     'Quantitative Insights Into Microbial Ecology (QIIME) '
                     'is an open-source bioinformatics pipeline for '
                     'performing microbiome analysis from raw DNA '
                     'sequencing data', 'source activate qiita',
                     'start_target_gene', 'artifact transformation',
                     '[["10.1038/nmeth.f.303", "20383131"]]', client_id,
                     client_secret))
        obs = qdb.software.Software.from_file(fp)
        self.assertEqual(obs, exp)

        # Activate an existing plugin with a warning
        fd, fp = mkstemp(suffix='.conf')
        close(fd)
        self._clean_up_files.append(fp)
        with open(fp, 'w') as f:
            f.write(CONF_TEMPLATE %
                    ('QIIME', '1.9.1', 'Different description',
                     'source activate qiime', 'start_qiime',
                     'artifact transformation',
                     '[["10.1038/nmeth.f.303", "20383131"]]', client_id,
                     client_secret))
        with warnings.catch_warnings(record=True) as warns:
            obs = qdb.software.Software.from_file(fp)
            obs_warns = [str(w.message) for w in warns]
            exp_warns = ['Plugin "QIIME" version "1.9.1" config file does not '
                         'match with stored information. Check the config file'
                         ' or run "qiita plugin update" to update the plugin '
                         'information. Offending values: description, '
                         'environment_script, start_script']
            self.assertCountEqual(obs_warns, exp_warns)

        self.assertEqual(obs, exp)
        self.assertEqual(
            obs.description,
            'Quantitative Insights Into Microbial Ecology (QIIME) is an '
            'open-source bioinformatics pipeline for performing microbiome '
            'analysis from raw DNA sequencing data')
        self.assertEqual(obs.environment_script, 'source activate qiita')
        self.assertEqual(obs.start_script, 'start_target_gene')

        # Update an existing plugin
        obs = qdb.software.Software.from_file(fp, update=True)
        self.assertEqual(obs, exp)
        self.assertEqual(obs.description, 'Different description')
        self.assertEqual(obs.environment_script, 'source activate qiime')
        self.assertEqual(obs.start_script, 'start_qiime')

        # Create a new plugin
        fd, fp = mkstemp(suffix='.conf')
        close(fd)
        self._clean_up_files.append(fp)
        with open(fp, 'w') as f:
            f.write(CONF_TEMPLATE %
                    ('NewPlugin', '0.0.1', 'Some description',
                     'source activate newplug', 'start_new_plugin',
                     'artifact definition', '', client_id,
                     client_secret))
        obs = qdb.software.Software.from_file(fp)
        self.assertNotEqual(obs, exp)
        self.assertEqual(obs.name, 'NewPlugin')

        # Update publications
        fd, fp = mkstemp(suffix='.conf')
        close(fd)
        self._clean_up_files.append(fp)
        exp = obs
        with open(fp, 'w') as f:
            f.write(CONF_TEMPLATE %
                    ('NewPlugin', '0.0.1', 'Some description',
                     'source activate newplug', 'start_new_plugin',
                     'artifact definition', '[["10.1039/nmeth.f.303", null]]',
                     client_id, client_secret))
        obs = qdb.software.Software.from_file(fp, update=True)
        self.assertEqual(obs, exp)
        self.assertEqual(obs.publications, [["10.1039/nmeth.f.303", None]])

        # Correctly ignores if there are no publications
        fd, fp = mkstemp(suffix='.conf')
        close(fd)
        self._clean_up_files.append(fp)
        with open(fp, 'w') as f:
            f.write(CONF_TEMPLATE %
                    ('Target Gene type', '0.1.0',
                     'Target gene artifact types plugin', 'source '
                     '~/virtualenv/python2.7/bin/activate; export '
                     'PATH=$HOME/miniconda3/bin/:$PATH; source activate qiita',
                     'start_target_gene_types', 'artifact definition', '',
                     '4MOBzUBHBtUmwhaC258H7PS0rBBLyGQrVxGPgc9g305bvVhf6h',
                     'rFb7jwAb3UmSUN57Bjlsi4DTl2owLwRpwCc0SggRNEVb2Ebae2p5Umnq'
                     '20rNMhmqN'))
        with warnings.catch_warnings(record=True) as warns:
            obs = qdb.software.Software.from_file(fp)
            obs_warns = [str(w.message) for w in warns]
            exp_warns = []
            self.assertCountEqual(obs_warns, exp_warns)

        self.assertEqual(obs, qdb.software.Software(3))
        self.assertEqual(obs.publications, [])

        # Raise an error if changing plugin type
        fd, fp = mkstemp(suffix='.conf')
        close(fd)
        self._clean_up_files.append(fp)
        with open(fp, 'w') as f:
            f.write(CONF_TEMPLATE %
                    ("NewPlugin", "0.0.1", "Some description",
                     "source activate newplug", "start_new_plugin",
                     "artifact transformation", "", client_id,
                     client_secret))
        QE = qdb.exceptions
        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            qdb.software.Software.from_file(fp)

        # Raise an error if client_id or client_secret are different
        fd, fp = mkstemp(suffix='.conf')
        close(fd)
        self._clean_up_files.append(fp)
        with open(fp, 'w') as f:
            f.write(CONF_TEMPLATE %
                    ('Target Gene type', '0.1.0',
                     'Target gene artifact types plugin',
                     'source activate qiita', 'start_target_gene_types',
                     'artifact definition', '', 'client_id', 'client_secret'))

        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            qdb.software.Software.from_file(fp)

        # But allow to update if update = True
        obs = qdb.software.Software.from_file(fp, update=True)
        self.assertEqual(obs, qdb.software.Software(3))
        self.assertEqual(obs.client_id, 'client_id')
        self.assertEqual(obs.client_secret, 'client_secret')

    def test_exists(self):
        self.assertTrue(qdb.software.Software.exists("QIIME", "1.9.1"))
        self.assertFalse(qdb.software.Software.exists("NewPlugin", "1.9.1"))
        self.assertFalse(qdb.software.Software.exists("QIIME", "2.0.0"))

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
        self.assertIsNotNone(obs.client_id)
        self.assertIsNotNone(obs.client_secret)
        self.assertFalse(obs.active)

        # create with publications
        exp_publications = [['10.1000/nmeth.f.101', '12345678'],
                            ['10.1001/nmeth.f.101', '23456789']]
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
        self.assertIsNotNone(obs.client_id)
        self.assertIsNotNone(obs.client_secret)
        self.assertFalse(obs.active)

        # Create with client_id, client_secret
        obs = qdb.software.Software.create(
            "Another Software", "0.1.0",
            "This is adding another software for testing", "env_a_name",
            "start_plugin_script", "artifact transformation",
            client_id='SomeNewClientId', client_secret='SomeNewClientSecret')
        self.assertEqual(obs.name, "Another Software")
        self.assertEqual(obs.version, "0.1.0")
        self.assertEqual(obs.description,
                         "This is adding another software for testing")
        self.assertEqual(obs.commands, [])
        self.assertEqual(obs.publications, [])
        self.assertEqual(obs.environment_script, 'env_a_name')
        self.assertEqual(obs.start_script, 'start_plugin_script')
        self.assertEqual(obs.type, 'artifact transformation')
        self.assertEqual(obs.client_id, 'SomeNewClientId')
        self.assertEqual(obs.client_secret, 'SomeNewClientSecret')
        self.assertFalse(obs.active)

    def test_add_publications(self):
        obs = qdb.software.Software.create(
            "New Software", "0.1.0",
            "This is adding a new software for testing", "env_name",
            "start_plugin", "artifact transformation")
        self.assertEqual(obs.publications, [])
        obs.add_publications([['10.1000/nmeth.f.101', '12345678']])
        exp = [['10.1000/nmeth.f.101', '12345678']]
        self.assertCountEqual(obs.publications, exp)

        # Add a publication that already exists
        obs.add_publications([['10.1000/nmeth.f.101', '12345678']])
        self.assertCountEqual(obs.publications, exp)

    def test_activate(self):
        qdb.software.Software.deactivate_all()
        obs = qdb.software.Software(1)
        self.assertFalse(obs.active)
        obs.activate()
        self.assertTrue(obs.active)

    def test_deprecated(self):
        tester = qdb.software.Software(1)
        self.assertFalse(tester.deprecated)

        tester.deprecated = True
        self.assertTrue(tester.deprecated)

        tester.deprecated = False
        self.assertFalse(tester.deprecated)

        with self.assertRaises(ValueError):
            tester.deprecated = 'error!'


@qiita_test_checker()
class DefaultParametersTests(TestCase):
    def test_exists(self):
        cmd = qdb.software.Command(1)
        obs = qdb.software.DefaultParameters.exists(
            cmd, max_bad_run_length=3, min_per_read_length_fraction=0.75,
            sequence_max_n=0, rev_comp_barcode=False,
            rev_comp_mapping_barcodes=False, rev_comp=False,
            phred_quality_threshold=3, barcode_type="golay_12",
            max_barcode_errors=1.5, phred_offset='auto')
        self.assertTrue(obs)

        obs = qdb.software.DefaultParameters.exists(
            cmd, max_bad_run_length=3, min_per_read_length_fraction=0.65,
            sequence_max_n=0, rev_comp_barcode=False,
            rev_comp_mapping_barcodes=False, rev_comp=False,
            phred_quality_threshold=3, barcode_type="hamming_8",
            max_barcode_errors=1.5, phred_offset='auto')
        self.assertFalse(obs)

    def test_name(self):
        self.assertEqual(qdb.software.DefaultParameters(1).name, "Defaults")

    def test_values(self):
        exp = {'min_per_read_length_fraction': 0.75,
               'max_barcode_errors': 1.5, 'max_bad_run_length': 3,
               'rev_comp': False, 'phred_quality_threshold': 3,
               'rev_comp_barcode': False, 'sequence_max_n': 0,
               'barcode_type': 'golay_12', 'rev_comp_mapping_barcodes': False,
               'phred_offset': 'auto'}
        self.assertEqual(qdb.software.DefaultParameters(1).values, exp)

    def test_command(self):
        self.assertEqual(
            qdb.software.DefaultParameters(1).command, qdb.software.Command(1))

    def test_create(self):
        cmd = qdb.software.Command(1)
        obs = qdb.software.DefaultParameters.create(
            "test_create", cmd, max_bad_run_length=3,
            min_per_read_length_fraction=0.75, sequence_max_n=0,
            rev_comp_barcode=False, rev_comp_mapping_barcodes=False,
            rev_comp=False, phred_quality_threshold=3,
            barcode_type="hamming_8", max_barcode_errors=1.5,
            phred_offset='auto')
        self.assertEqual(obs.name, "test_create")

        exp = {'max_bad_run_length': 3, 'min_per_read_length_fraction': 0.75,
               'sequence_max_n': 0, 'rev_comp_barcode': False,
               'rev_comp_mapping_barcodes': False, 'rev_comp': False,
               'phred_quality_threshold': 3, 'barcode_type': "hamming_8",
               'max_barcode_errors': 1.5, 'phred_offset': 'auto'}
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
            next(qdb.software.Command(2).default_parameter_sets),
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
                    '"rev_comp_barcode": false, "phred_offset": "auto", '
                    '"rev_comp_mapping_barcodes": false, "sequence_max_n": 0}')
        cmd = qdb.software.Command(1)
        obs = qdb.software.Parameters.load(cmd, json_str=json_str)
        exp_values = {
            "barcode_type": "golay_12", "input_data": 1,
            "max_bad_run_length": 3, "max_barcode_errors": 1.5,
            "min_per_read_length_fraction": 0.75,
            "phred_quality_threshold": 3, "rev_comp": False,
            "rev_comp_barcode": False, "rev_comp_mapping_barcodes": False,
            "sequence_max_n": 0, "phred_offset": "auto"}
        self.assertEqual(obs.values, exp_values)

    def test_load_dictionary(self):
        exp_values = {
            "barcode_type": "golay_12", "input_data": 1,
            "max_bad_run_length": 3, "max_barcode_errors": 1.5,
            "min_per_read_length_fraction": 0.75,
            "phred_quality_threshold": 3, "rev_comp": False,
            "rev_comp_barcode": False, "rev_comp_mapping_barcodes": False,
            "sequence_max_n": 0, "phred_offset": "auto"}
        cmd = qdb.software.Command(1)
        obs = qdb.software.Parameters.load(cmd, values_dict=exp_values)
        self.assertEqual(obs.values, exp_values)

    def test_load_error_missing_required(self):
        json_str = ('{"barcode_type": "golay_12",'
                    '"max_bad_run_length": 3, "max_barcode_errors": 1.5, '
                    '"min_per_read_length_fraction": 0.75, '
                    '"phred_quality_threshold": 3, "rev_comp": false, '
                    '"rev_comp_barcode": false, "phred_offset": "auto", '
                    '"rev_comp_mapping_barcodes": false, "sequence_max_n": 0}')
        cmd = qdb.software.Command(1)
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.software.Parameters.load(cmd, json_str=json_str)

    def test_load_loads_defaults(self):
        values = {
            "barcode_type": "golay_12", "input_data": 1,
            "phred_quality_threshold": 3, "rev_comp": False,
            "rev_comp_barcode": False, "rev_comp_mapping_barcodes": False,
            "sequence_max_n": 0, "phred_offset": "auto"}
        cmd = qdb.software.Command(1)
        obs = qdb.software.Parameters.load(cmd, values_dict=values)
        values.update({
            "max_bad_run_length": '3', "max_barcode_errors": '1.5',
            "min_per_read_length_fraction": '0.75'})
        self.assertEqual(obs.values, values)

    def test_load_error_extra_parameters(self):
        json_str = ('{"barcode_type": "golay_12", "input_data": 1, '
                    '"max_bad_run_length": 3, "max_barcode_errors": 1.5, '
                    '"min_per_read_length_fraction": 0.75, '
                    '"phred_quality_threshold": 3, "rev_comp": false, '
                    '"rev_comp_barcode": false, "phred_offset": "auto",'
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
               'input_data': 1, 'phred_offset': 'auto'}
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
               'input_data': 1, 'phred_offset': 'auto'}
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
               'phred_offset': 'auto', 'input_data': 1}
        self.assertEqual(obs, exp)

    def test_dumps(self):
        obs = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1}).dump()
        exp = ('{"barcode_type": "golay_12", "input_data": 1, '
               '"max_bad_run_length": 3, "max_barcode_errors": 1.5, '
               '"min_per_read_length_fraction": 0.75, "phred_offset": "auto", '
               '"phred_quality_threshold": 3, "rev_comp": false, '
               '"rev_comp_barcode": false, '
               '"rev_comp_mapping_barcodes": false, "sequence_max_n": 0}')
        self.assertEqual(obs, exp)


class DefaultWorkflowNodeTests(TestCase):
    def test_default_parameter(self):
        obs = qdb.software.DefaultWorkflowNode(1)
        self.assertEqual(
            obs.default_parameter, qdb.software.DefaultParameters(1))

        obs = qdb.software.DefaultWorkflowNode(2)
        self.assertEqual(
            obs.default_parameter, qdb.software.DefaultParameters(10))


class DefaultWorkflowEdgeTests(TestCase):
    def test_connections(self):
        tester = qdb.software.DefaultWorkflowEdge(1)
        obs = tester.connections
        self.assertEqual(
            obs, [['demultiplexed', 'input_data', 'Demultiplexed']])


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
        self.assertCountEqual(obs.nodes(), exp)
        exp = [(qdb.software.DefaultWorkflowNode(1),
                qdb.software.DefaultWorkflowNode(2),
                {'connections': qdb.software.DefaultWorkflowEdge(1)})]
        self.assertCountEqual(obs.edges(data=True), exp)

        obs = qdb.software.DefaultWorkflow(2).graph
        self.assertTrue(isinstance(obs, nx.DiGraph))
        exp = [qdb.software.DefaultWorkflowNode(3),
               qdb.software.DefaultWorkflowNode(4)]
        self.assertCountEqual(obs.nodes(), exp)
        exp = [(qdb.software.DefaultWorkflowNode(3),
                qdb.software.DefaultWorkflowNode(4),
                {'connections': qdb.software.DefaultWorkflowEdge(2)})]
        self.assertCountEqual(obs.edges(data=True), exp)


CONF_TEMPLATE = """[main]
NAME = %s
VERSION = %s
DESCRIPTION = %s
ENVIRONMENT_SCRIPT = %s
START_SCRIPT = %s
PLUGIN_TYPE = %s
PUBLICATIONS = %s

[oauth2]
CLIENT_ID = %s
CLIENT_SECRET = %s
"""


if __name__ == '__main__':
    main()
