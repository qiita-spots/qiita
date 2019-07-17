# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from json import dumps

from qiita_core.util import qiita_test_checker
from qiita_db.processing_job import ProcessingWorkflow, ProcessingJob
from qiita_db.software import Command, Parameters
from qiita_db.user import User
from qiita_pet.handlers.api_proxy.processing import (
    list_commands_handler_get_req, list_options_handler_get_req,
    workflow_handler_post_req, workflow_handler_patch_req, job_ajax_get_req,
    job_ajax_patch_req)


class TestProcessingAPIReadOnly(TestCase):
    def test_list_commands_handler_get_req(self):
        obs = list_commands_handler_get_req('FASTQ', True)
        exp = {'status': 'success',
               'message': '',
               'commands': [{'id': 1, 'command': 'Split libraries FASTQ',
                             'output': [['demultiplexed', 'Demultiplexed']]}]}
        self.assertEqual(obs, exp)

        obs = list_commands_handler_get_req('Demultiplexed', True)
        exp = {'status': 'success',
               'message': '',
               'commands': [{'id': 3, 'command': 'Pick closed-reference OTUs',
                             'output': [['OTU table', 'BIOM']]}]}
        self.assertEqual(obs, exp)

        obs = list_commands_handler_get_req('BIOM', False)
        exp = {'status': 'success',
               'message': '',
               'commands': [
                    {'command': 'Summarize Taxa', 'id': 9,
                     'output': [['taxa_summary', 'taxa_summary']]},
                    {'command': 'Beta Diversity', 'id': 10,
                     'output': [['distance_matrix', 'beta_div_plots']]},
                    {'command': 'Alpha Rarefaction', 'id': 11,
                     'output': [['rarefaction_curves', 'rarefaction_curves']]},
                    {'command': 'Single Rarefaction', 'id': 12,
                     'output': [['rarefied_table', 'BIOM']]}]}
        # since the order of the commands can change, test them separately
        self.assertCountEqual(obs.pop('commands'), exp.pop('commands'))
        self.assertEqual(obs, exp)

    def test_list_options_handler_get_req(self):
        obs = list_options_handler_get_req(3)
        exp = {'status': 'success',
               'message': '',
               'options': [{'id': 10,
                            'name': 'Defaults',
                            'values': {'reference': 1,
                                       'similarity': 0.97,
                                       'sortmerna_coverage': 0.97,
                                       'sortmerna_e_value': 1,
                                       'sortmerna_max_pos': 10000,
                                       'threads': 1}}],
               'req_options': {'input_data': ('artifact', ['Demultiplexed'])},
               'opt_options': {'reference': ['reference', '1'],
                               'similarity': ['float', '0.97'],
                               'sortmerna_coverage': ['float', '0.97'],
                               'sortmerna_e_value': ['float', '1'],
                               'sortmerna_max_pos': ['integer', '10000'],
                               'threads': ['integer', '1']}}
        # First check that the keys are the same
        self.assertCountEqual(obs, exp)
        self.assertEqual(obs['status'], exp['status'])
        self.assertEqual(obs['message'], exp['message'])
        self.assertEqual(obs['options'], exp['options'])
        self.assertEqual(obs['req_options'], exp['req_options'])
        self.assertEqual(obs['opt_options'], exp['opt_options'])

    def test_job_ajax_get_req(self):
        obs = job_ajax_get_req("063e553b-327c-4818-ab4a-adfe58e49860")
        exp = {'status': 'success',
               'message': '',
               'job_id': "063e553b-327c-4818-ab4a-adfe58e49860",
               'job_status': "queued",
               'job_step': None,
               'job_error': None,
               'job_parameters': {'barcode_type': u'golay_12',
                                  'input_data': 1,
                                  'max_bad_run_length': 3,
                                  'max_barcode_errors': 1.5,
                                  'min_per_read_length_fraction': 0.75,
                                  'phred_quality_threshold': 3,
                                  'rev_comp': False,
                                  'rev_comp_barcode': False,
                                  'rev_comp_mapping_barcodes': False,
                                  'sequence_max_n': 0,
                                  'phred_offset': 'auto'},
               'command': 'Split libraries FASTQ',
               'command_description': 'Demultiplexes and applies quality '
                                      'control to FASTQ data',
               'software': 'QIIME',
               'software_version': '1.9.1'}
        self.assertEqual(obs, exp)


@qiita_test_checker()
class TestProcessingAPI(TestCase):
    def test_workflow_handler_post_req(self):
        params = ('{"max_barcode_errors": 1.5, "barcode_type": "golay_12", '
                  '"max_bad_run_length": 3, "phred_offset": "auto", '
                  '"rev_comp": false, "phred_quality_threshold": 3, '
                  '"input_data": 1, "rev_comp_barcode": false, '
                  '"rev_comp_mapping_barcodes": false, '
                  '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}')
        obs = workflow_handler_post_req("test@foo.bar", 1, params)
        self.assertRegex(
            obs.pop('message'), 'Cannot create job because the parameters are '
            'the same as jobs that are queued, running or already have '
            'succeeded:\n')
        exp = {'status': 'error', 'workflow_id': None, 'job': None}
        self.assertEqual(obs, exp)

    def test_workflow_handler_patch_req(self):
        # Create a new workflow so it is in construction
        exp_command = Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}')
        exp_params = Parameters.load(exp_command, json_str=json_str)
        exp_user = User('test@foo.bar')
        name = "Test processing workflow"

        # tests success
        wf = ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name, force=True)

        graph = wf.graph
        nodes = list(graph.nodes())
        job_id = nodes[0].id
        value = {'dflt_params': 10,
                 'connections': {job_id: {'demultiplexed': 'input_data'}}}
        obs = workflow_handler_patch_req(
            'add', '/%s/' % wf.id, req_value=dumps(value))
        new_jobs = set(wf.graph.nodes()) - set(nodes)
        self.assertEqual(len(new_jobs), 1)
        new_job = new_jobs.pop()
        exp = {'status': 'success',
               'message': '',
               'job': {'id': new_job.id,
                       'inputs': [job_id],
                       'label': 'Pick closed-reference OTUs',
                       'outputs': [['OTU table', 'BIOM']]}}
        self.assertEqual(obs, exp)

        obs = workflow_handler_patch_req(
            'remove', '/%s/%s/' % (wf.id, new_job.id))
        exp = {'status': 'success', 'message': ''}
        jobs = set(wf.graph.nodes()) - set(nodes)
        self.assertEqual(jobs, set())

    def test_workflow_handler_patch_req_error(self):
        # Incorrect path parameter
        obs = workflow_handler_patch_req('add', '/1/extra/')
        exp = {'status': 'error',
               'message': 'Incorrect path parameter'}
        self.assertEqual(obs, exp)

        # Workflow does not exist
        obs = workflow_handler_patch_req('add', '/1000/')
        exp = {'status': 'error',
               'message': 'Workflow 1000 does not exist'}
        self.assertEqual(obs, exp)

        # Operation not supported
        obs = workflow_handler_patch_req('replace', '/1/')
        exp = {'status': 'error',
               'message': 'Operation "replace" not supported. '
                          'Current supported operations: add'}
        self.assertEqual(obs, exp)

        # Incorrect path parameter (op = remove)
        obs = workflow_handler_patch_req('remove', '/1/')
        exp = {'status': 'error',
               'message': 'Incorrect path parameter'}
        self.assertEqual(obs, exp)

    def test_job_ajax_patch_req(self):
        # Create a new job - through a workflow since that is the only way
        # of creating jobs in the interface
        exp_command = Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}')
        exp_params = Parameters.load(exp_command, json_str=json_str)
        exp_user = User('test@foo.bar')
        name = "Test processing workflow"

        # tests success
        wf = ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name, force=True)

        graph = wf.graph
        nodes = list(graph.nodes())
        job_id = nodes[0].id

        # Incorrect path parameter
        obs = job_ajax_patch_req('remove', '/%s/somethingelse' % job_id)
        exp = {'status': 'error',
               'message': 'Incorrect path parameter: missing job id'}
        self.assertEqual(obs, exp)

        obs = job_ajax_patch_req('remove', '/')
        exp = {'status': 'error',
               'message': 'Incorrect path parameter: missing job id'}
        self.assertEqual(obs, exp)

        # Job id is not like a job id
        obs = job_ajax_patch_req('remove', '/notAJobId')
        exp = {'status': 'error',
               'message': 'Incorrect path parameter: '
                          'notAJobId is not a recognized job id'}
        self.assertEqual(obs, exp)

        # Job doesn't exist
        obs = job_ajax_patch_req('remove',
                                 '/6d368e16-2242-4cf8-87b4-a5dc40bc890b')
        exp = {'status': 'error',
               'message': 'Incorrect path parameter: '
                          '6d368e16-2242-4cf8-87b4-a5dc40bc890b is not a '
                          'recognized job id'}
        self.assertEqual(obs, exp)

        # in_construction job
        obs = job_ajax_patch_req('remove', '/%s' % job_id)
        exp = {'status': 'error',
               'message': "Can't delete job %s. It is 'in_construction' "
                          "status. Please use /study/process/workflow/"
                          % job_id}
        self.assertEqual(obs, exp)

        # job status != 'error'
        job = ProcessingJob(job_id)
        job._set_status('queued')
        obs = job_ajax_patch_req('remove', '/%s' % job_id)
        exp = {'status': 'error',
               'message': 'Only jobs in "error" status can be deleted.'}
        self.assertEqual(obs, exp)

        # Operation not supported
        job._set_status('queued')
        obs = job_ajax_patch_req('add', '/%s' % job_id)
        exp = {'status': 'error',
               'message': 'Operation "add" not supported. Current supported '
                          'operations: remove'}
        self.assertEqual(obs, exp)

        # Test success
        job._set_error('Killed for testing')
        obs = job_ajax_patch_req('remove', '/%s' % job_id)
        exp = {'status': 'success',
               'message': ''}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
