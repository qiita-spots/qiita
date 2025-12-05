# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from json import loads
from unittest import main

from qiita_db.processing_job import ProcessingJob, ProcessingWorkflow
from qiita_db.software import Command, Parameters
from qiita_db.user import User
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestListCommandsHandler(TestHandlerBase):
    def test_get(self):
        response = self.get(
            "/study/process/commands/", {"artifact_id": "8", "include_analysis": "true"}
        )
        self.assertEqual(response.code, 200)
        exp = {
            "status": "success",
            "message": "",
            "commands": [
                {
                    "id": 9,
                    "command": "Summarize Taxa",
                    "output": [["taxa_summary", "taxa_summary"]],
                },
                {
                    "id": 10,
                    "command": "Beta Diversity",
                    "output": [["distance_matrix", "beta_div_plots"]],
                },
                {
                    "id": 11,
                    "command": "Alpha Rarefaction",
                    "output": [["rarefaction_curves", "rarefaction_curves"]],
                },
                {
                    "id": 12,
                    "command": "Single Rarefaction",
                    "output": [["rarefied_table", "BIOM"]],
                },
            ],
        }

        response = self.get(
            "/study/process/commands/",
            {"artifact_id": "3", "include_analysis": "false"},
        )
        self.assertEqual(response.code, 200)
        exp = {
            "status": "success",
            "message": "",
            "commands": [
                {
                    "id": 3,
                    "command": "Pick closed-reference OTUs",
                    "output": [["OTU table", "BIOM"]],
                }
            ],
        }
        self.assertEqual(loads(response.body), exp)


class TestListOptionsHandler(TestHandlerBase):
    def test_get(self):
        response = self.get(
            "/study/process/commands/options/", {"command_id": "3", "artifact_id": "8"}
        )
        self.assertEqual(response.code, 200)
        exp = {
            "status": "success",
            "message": "",
            "options": [
                {
                    "id": 10,
                    "name": "Defaults",
                    "values": {
                        "reference": 1,
                        "sortmerna_e_value": 1,
                        "sortmerna_max_pos": 10000,
                        "similarity": 0.97,
                        "sortmerna_coverage": 0.97,
                        "threads": 1,
                    },
                }
            ],
            "req_options": {"input_data": ["artifact", ["Demultiplexed"]]},
            "opt_options": {
                "reference": ["reference", "1"],
                "sortmerna_e_value": ["float", "1"],
                "sortmerna_max_pos": ["integer", "10000"],
                "similarity": ["float", "0.97"],
                "sortmerna_coverage": ["float", "0.97"],
                "threads": ["integer", "1"],
            },
            "extra_artifacts": {},
        }
        self.assertEqual(loads(response.body), exp)

        # test that it works fine with a job_id:artifact_type
        response = self.get(
            "/study/process/commands/options/",
            {"command_id": "3", "artifact_id": "job_id:artifact_type"},
        )
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

        # test that it works fine with no artifact_id
        response = self.get("/study/process/commands/options/", {"command_id": "3"})
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)


class TestJobAJAX(TestHandlerBase):
    def test_get(self):
        response = self.get(
            "/study/process/job/", {"job_id": "063e553b-327c-4818-ab4a-adfe58e49860"}
        )
        self.assertEqual(response.code, 200)
        exp = {
            "status": "success",
            "message": "",
            "job_id": "063e553b-327c-4818-ab4a-adfe58e49860",
            "job_external_id": "Not Available",
            "job_status": "queued",
            "job_step": None,
            "job_error": None,
            "job_parameters": {
                "barcode_type": "golay_12",
                "input_data": 1,
                "max_bad_run_length": 3,
                "max_barcode_errors": 1.5,
                "min_per_read_length_fraction": 0.75,
                "phred_quality_threshold": 3,
                "rev_comp": False,
                "rev_comp_barcode": False,
                "rev_comp_mapping_barcodes": False,
                "sequence_max_n": 0,
                "phred_offset": "auto",
            },
            "command": "Split libraries FASTQ",
            "command_description": "Demultiplexes and applies quality "
            "control to FASTQ data",
            "software": "QIIMEq2",
            "software_version": "1.9.1",
        }
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
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}'
        )
        exp_params = Parameters.load(exp_command, json_str=json_str)
        exp_user = User("test@foo.bar")
        name = "Test processing workflow"

        # tests success
        wf = ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name, force=True
        )

        graph = wf.graph
        nodes = list(graph.nodes())
        job_id = nodes[0].id

        response = self.patch("/study/process/job/", {"op": "remove", "path": job_id})
        self.assertEqual(response.code, 200)
        exp = {
            "status": "error",
            "message": "Can't delete job %s. It is 'in_construction' "
            "status. Please use /study/process/workflow/" % job_id,
        }
        self.assertEqual(loads(response.body), exp)

        # Test success
        ProcessingJob(job_id)._set_error("Killed for testing")
        response = self.patch("/study/process/job/", {"op": "remove", "path": job_id})
        self.assertEqual(response.code, 200)
        exp = {"status": "success", "message": ""}
        self.assertEqual(loads(response.body), exp)


class TestWorkflowHandler(TestHandlerBase):
    def test_post(self):
        # test error
        response = self.post(
            "/study/process/workflow/", {"command_id": "3", "params": "{}"}
        )
        self.assertEqual(response.code, 200)
        exp = {
            "status": "error",
            "workflow_id": None,
            "job": None,
            "message": "The provided JSON string doesn't encode a parameter"
            " set for command 'Pick closed-reference OTUs "
            "(ID: 3)'. Missing required parameter: "
            "input_data",
        }
        self.assertDictEqual(loads(response.body), exp)

        # test success
        response = self.post(
            "/study/process/workflow/",
            {"command_id": "3", "params": '{"input_data": 1}'},
        )
        self.assertEqual(response.code, 200)
        obs = loads(response.body)
        # we are going to copy the workflow_id/job information because we only
        # care about the reply
        exp = {
            "status": "success",
            "workflow_id": obs["workflow_id"],
            "job": obs["job"],
            "message": "",
        }
        self.assertEqual(obs, exp)

        # test with files
        response = self.post(
            "/study/process/workflow/",
            {
                "command_id": "3",
                "params": '{"input_data": 3}',
                "files": '{"template": {"body": b""}}',
                "headers": {"Content-Type": "application/json", "Origin": "localhost"},
            },
        )
        self.assertEqual(response.code, 200)
        obs = loads(response.body)
        # we are going to copy the workflow_id/job information because we only
        # care about the reply
        exp = {
            "status": "success",
            "workflow_id": obs["workflow_id"],
            "job": obs["job"],
            "message": "",
        }
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    main()
