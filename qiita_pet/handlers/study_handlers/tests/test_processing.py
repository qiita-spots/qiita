# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import main
from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.software import Command, Parameters
from qiita_db.user import User
from qiita_db.processing_job import ProcessingWorkflow, ProcessingJob


class TestListCommandsHandler(TestHandlerBase):
    # TODO: Missing tests
    pass


class TestListOptionsHandler(TestHandlerBase):
    # TODO: Missing tests
    pass


class TestJobAJAX(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/process/job/',
                            {'job_id': '063e553b-327c-4818-ab4a-adfe58e49860'})
        self.assertEqual(response.code, 200)
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
        self.assertEqual(loads(response.body), exp)

    def test_patch(self):
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
        nodes = graph.nodes()
        job_id = nodes[0].id

        response = self.patch('/study/process/job/',
                              {'op': 'remove', 'path': job_id})
        self.assertEqual(response.code, 200)
        exp = {'status': 'error',
               'message': "Can't delete job %s. It is 'in_construction' "
                          "status. Please use /study/process/workflow/"
                          % job_id}
        self.assertEqual(loads(response.body), exp)

        # Test success
        ProcessingJob(job_id)._set_error('Killed for testing')
        response = self.patch('/study/process/job/',
                              {'op': 'remove', 'path': job_id})
        self.assertEqual(response.code, 200)
        exp = {'status': 'success',
               'message': ''}
        self.assertEqual(loads(response.body), exp)


if __name__ == "__main__":
    main()
