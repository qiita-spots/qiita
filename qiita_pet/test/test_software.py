# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from copy import deepcopy
from unittest import main

from mock import Mock

from qiita_db.software import DefaultWorkflow
from qiita_db.sql_connection import TRN, perform_as_transaction
from qiita_db.user import User
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.software import _retrive_workflows
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestSoftware(TestHandlerBase):
    def test_get(self):
        response = self.get("/software/")
        self.assertEqual(response.code, 200)
        body = response.body.decode("ascii")
        self.assertNotEqual(body, "")
        # checking that this software is not displayed
        self.assertNotIn("Target Gene", body)

        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.get("/software/")
        self.assertEqual(response.code, 200)
        body = response.body.decode("ascii")
        self.assertNotEqual(body, "")
        # checking that this software is displayed
        self.assertIn("Target Gene", body)


class TestWorkflowsHandler(TestHandlerBase):
    def test_get(self):
        DefaultWorkflow(2).active = False
        response = self.get("/workflows/")
        self.assertEqual(response.code, 200)
        body = response.body.decode("ascii")
        self.assertNotEqual(body, "")
        # checking that this software is not displayed
        self.assertNotIn("FASTA upstream workflow", body)

        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.get("/workflows/")
        self.assertEqual(response.code, 200)
        body = response.body.decode("ascii")
        self.assertNotEqual(body, "")
        # checking that this software is displayed
        self.assertIn("FASTA upstream workflow", body)
        DefaultWorkflow(2).active = True

    def test_retrive_workflows_standalone(self):
        # let's create a new workflow, add 1 commands, and make parameters not
        # required to make sure the stanalone is "active"
        with TRN:
            # 5 per_sample_FASTQ
            sql = """INSERT INTO qiita.default_workflow
                     (name, artifact_type_id, description, parameters)
                     VALUES ('', 5, '', '{"prep": {}, "sample": {}}')
                     RETURNING default_workflow_id"""
            TRN.add(sql)
            wid = TRN.execute_fetchlast()
            # 11 is per-sample-FASTQ split libraries commands
            sql = """INSERT INTO qiita.default_workflow_node
                     (default_workflow_id, default_parameter_set_id)
                     VALUES (%s, 11)
                     RETURNING default_workflow_node_id"""
            TRN.add(sql, [wid])
            nid = TRN.execute_fetchflatten()
            sql = """UPDATE qiita.command_parameter SET required = false"""
            TRN.add(sql)
            TRN.execute()

        # here we expect 1 input node and 1 edge
        obs = _retrive_workflows(True)[-1]
        exp_value = f"input_params_{nid[0]}_per_sample_FASTQ"
        self.assertEqual(1, len([x for x in obs["nodes"] if x[0] == exp_value]))
        self.assertEqual(1, len([x for x in obs["edges"] if x[0] == exp_value]))

        # now let's insert another command using the same input
        with TRN:
            # 12 is per-sample-FASTQ split libraries commands
            sql = """INSERT INTO qiita.default_workflow_node
                     (default_workflow_id, default_parameter_set_id)
                     VALUES (%s, 12)"""
            TRN.add(sql, [wid])
            TRN.execute()

        # we should still have 1 node but now with 2 edges
        obs = _retrive_workflows(True)[-1]
        self.assertEqual(1, len([x for x in obs["nodes"] if x[0] == exp_value]))
        self.assertEqual(2, len([x for x in obs["edges"] if x[0] == exp_value]))

    def test_retrive_workflows(self):
        # we should see all 3 workflows
        DefaultWorkflow(2).active = False
        exp = deepcopy(WORKFLOWS)
        self.assertCountEqual(_retrive_workflows(False), exp)

        # validating that the params_name is not being used
        self.assertNotIn(
            "Split libraries | Defaults with Golay 12 barcodes",
            [x[2] for x in _retrive_workflows(False)[1]["nodes"]],
        )
        # now it should be there
        with TRN:
            # Hard-coded values; 19 -> barcode_type
            sql = """UPDATE qiita.command_parameter
                     SET name_order = 0
                     WHERE command_parameter_id = 19"""
            TRN.add(sql)
            TRN.execute()
        self.assertIn(
            "Split libraries | Defaults with Golay 12 barcodes",
            [x[2] for x in _retrive_workflows(False)[1]["nodes"]],
        )
        # and gone again
        with TRN:
            sql = """UPDATE qiita.command_parameter
                     SET name_order = NULL
                     WHERE command_parameter_id = 19"""
            TRN.add(sql)
            TRN.execute()
        self.assertNotIn(
            "Split libraries | Defaults with Golay 12 barcodes",
            [x[2] for x in _retrive_workflows(False)[1]["nodes"]],
        )

        # we should not see the middle one
        del exp[1]
        self.assertCountEqual(_retrive_workflows(True), exp)

        # let's create a couple of more complex scenarios so we touch all code
        # by adding multiple paths, that should connect and get separate
        # -- adds a new path that should be kept separate all the way; this is
        #    to emulate what happens with different trimming (different
        #    default parameter) and deblur (same for each of the previous
        #    steps)
        sql = """
            INSERT INTO qiita.default_workflow_node (
                default_workflow_id, default_parameter_set_id)
            VALUES (1, 2), (1, 10);
            INSERT INTO qiita.default_workflow_edge (
                parent_id, child_id)
            VALUES (7, 8);
            INSERT INTO qiita.default_workflow_edge_connections (
                default_workflow_edge_id, parent_output_id, child_input_id)
            VALUES (4, 1, 3)"""
        perform_as_transaction(sql)
        # -- adds a new path that should be kept together and then separate;
        #    this is to simulate what happens with MTX/WGS processing, one
        #    single QC step (together) and 2 separete profilers
        sql = """
            INSERT INTO qiita.default_parameter_set (
                command_id, parameter_set_name, parameter_set)
            VALUES (3, '100%',
                    ('{"reference":1,"sortmerna_e_value":1,'
                     || '"sortmerna_max_pos":'
                     || '10000,"similarity":1.0,"sortmerna_coverage":1.00,'
                     || '"threads":1}')::json);
            INSERT INTO qiita.default_workflow_node (
                default_workflow_id, default_parameter_set_id)
            VALUES (2, 17);
            INSERT INTO qiita.default_workflow_edge (
                parent_id, child_id)
            VALUES (3, 9);
            INSERT INTO qiita.default_workflow_edge_connections (
                default_workflow_edge_id, parent_output_id, child_input_id)
            VALUES (5, 1, 3)"""
        perform_as_transaction(sql)

        # adding new expected values
        exp = deepcopy(WORKFLOWS)
        obs = _retrive_workflows(False)
        exp[0]["nodes"].extend(
            [
                [
                    "params_7",
                    1,
                    "Split libraries FASTQ",
                    "Defaults with reverse complement mapping file barcodes",
                    {
                        "max_bad_run_length": "3",
                        "min_per_read_length_fraction": "0.75",
                        "sequence_max_n": "0",
                        "rev_comp_barcode": "False",
                        "rev_comp_mapping_barcodes": "True",
                        "rev_comp": "False",
                        "phred_quality_threshold": "3",
                        "barcode_type": "golay_12",
                        "max_barcode_errors": "1.5",
                        "phred_offset": "auto",
                    },
                ],
                [
                    "input_params_7_FASTQ | per_sample_FASTQ",
                    1,
                    "FASTQ | per_sample_FASTQ",
                ],
                [
                    "output_params_7_demultiplexed | Demultiplexed",
                    1,
                    "demultiplexed | Demultiplexed",
                ],
                [
                    "params_8",
                    3,
                    "Pick closed-reference OTUs",
                    "Defaults",
                    {
                        "reference": "1",
                        "sortmerna_e_value": "1",
                        "sortmerna_max_pos": "10000",
                        "similarity": "0.97",
                        "sortmerna_coverage": "0.97",
                        "threads": "1",
                    },
                ],
                ["output_params_8_OTU table | BIOM", 3, "OTU table | BIOM"],
            ]
        )
        exp[0]["edges"].extend(
            [
                ["input_params_7_FASTQ | per_sample_FASTQ", "params_7"],
                ["params_7", "output_params_7_demultiplexed | Demultiplexed"],
                ["output_params_7_demultiplexed | Demultiplexed", "params_8"],
                ["params_8", "output_params_8_OTU table | BIOM"],
            ]
        )
        exp[1]["nodes"].extend(
            [
                [
                    "params_9",
                    3,
                    "Pick closed-reference OTUs",
                    "100%",
                    {
                        "reference": "1",
                        "sortmerna_e_value": "1",
                        "sortmerna_max_pos": "10000",
                        "similarity": "1.0",
                        "sortmerna_coverage": "1.0",
                        "threads": "1",
                    },
                ],
                ["output_params_9_OTU table | BIOM", 3, "OTU table | BIOM"],
            ]
        )
        exp[1]["edges"].extend(
            [
                ["output_params_3_demultiplexed | Demultiplexed", "params_9"],
                ["params_9", "output_params_9_OTU table | BIOM"],
            ]
        )
        self.assertCountEqual(obs, exp)


WORKFLOWS = [
    {
        "name": "FASTQ upstream workflow",
        "id": 1,
        "data_types": ["16S", "18S"],
        "description": 'This accepts html <a href="https://qiita.ucsd.edu">Qiita!'
        "</a><br/><br/><b>BYE!</b>",
        "active": True,
        "parameters_sample": {},
        "parameters_prep": {},
        "nodes": [
            [
                "params_1",
                1,
                "Split libraries FASTQ",
                "Defaults",
                {
                    "max_bad_run_length": "3",
                    "min_per_read_length_fraction": "0.75",
                    "sequence_max_n": "0",
                    "rev_comp_barcode": "False",
                    "rev_comp_mapping_barcodes": "False",
                    "rev_comp": "False",
                    "phred_quality_threshold": "3",
                    "barcode_type": "golay_12",
                    "max_barcode_errors": "1.5",
                    "phred_offset": "auto",
                },
            ],
            ["input_params_1_FASTQ", 1, "FASTQ"],
            [
                "output_params_1_demultiplexed | Demultiplexed",
                1,
                "demultiplexed | Demultiplexed",
            ],
            [
                "params_2",
                3,
                "Pick closed-reference OTUs",
                "Defaults",
                {
                    "reference": "1",
                    "sortmerna_e_value": "1",
                    "sortmerna_max_pos": "10000",
                    "similarity": "0.97",
                    "sortmerna_coverage": "0.97",
                    "threads": "1",
                },
            ],
            ["output_params_2_OTU table | BIOM", 3, "OTU table | BIOM"],
        ],
        "edges": [
            ["input_params_1_FASTQ", "params_1"],
            ["params_1", "output_params_1_demultiplexed | Demultiplexed"],
            ["output_params_1_demultiplexed | Demultiplexed", "params_2"],
            ["params_2", "output_params_2_OTU table | BIOM"],
        ],
    },
    {
        "name": "FASTA upstream workflow",
        "id": 2,
        "data_types": ["18S"],
        "description": "This is another description",
        "active": False,
        "parameters_sample": {},
        "parameters_prep": {},
        "nodes": [
            [
                "params_3",
                2,
                "Split libraries",
                "Defaults with Golay 12 barcodes",
                {
                    "min_seq_len": "200",
                    "max_seq_len": "1000",
                    "trim_seq_length": "False",
                    "min_qual_score": "25",
                    "max_ambig": "6",
                    "max_homopolymer": "6",
                    "max_primer_mismatch": "0",
                    "barcode_type": "golay_12",
                    "max_barcode_errors": "1.5",
                    "disable_bc_correction": "False",
                    "qual_score_window": "0",
                    "disable_primers": "False",
                    "reverse_primers": "disable",
                    "reverse_primer_mismatches": "0",
                    "truncate_ambi_bases": "False",
                },
            ],
            [
                "input_params_3_** WARNING, NOT DEFINED **",
                2,
                "** WARNING, NOT DEFINED **",
            ],
            [
                "output_params_3_demultiplexed | Demultiplexed",
                2,
                "demultiplexed | Demultiplexed",
            ],
            [
                "params_4",
                3,
                "Pick closed-reference OTUs",
                "Defaults",
                {
                    "reference": "1",
                    "sortmerna_e_value": "1",
                    "sortmerna_max_pos": "10000",
                    "similarity": "0.97",
                    "sortmerna_coverage": "0.97",
                    "threads": "1",
                },
            ],
            ["output_params_4_OTU table | BIOM", 3, "OTU table | BIOM"],
        ],
        "edges": [
            ["input_params_3_** WARNING, NOT DEFINED **", "params_3"],
            ["params_3", "output_params_3_demultiplexed | Demultiplexed"],
            ["output_params_3_demultiplexed | Demultiplexed", "params_4"],
            ["params_4", "output_params_4_OTU table | BIOM"],
        ],
    },
    {
        "name": "Per sample FASTQ upstream workflow",
        "id": 3,
        "data_types": ["ITS"],
        "description": None,
        "active": True,
        "parameters_sample": {},
        "parameters_prep": {},
        "nodes": [
            [
                "params_5",
                1,
                "Split libraries FASTQ",
                "per sample FASTQ defaults",
                {
                    "max_bad_run_length": "3",
                    "min_per_read_length_fraction": "0.75",
                    "sequence_max_n": "0",
                    "rev_comp_barcode": "False",
                    "rev_comp_mapping_barcodes": "False",
                    "rev_comp": "False",
                    "phred_quality_threshold": "3",
                    "barcode_type": "not-barcoded",
                    "max_barcode_errors": "1.5",
                    "phred_offset": "auto",
                },
            ],
            ["input_params_5_FASTQ", 1, "FASTQ"],
            [
                "output_params_5_demultiplexed | Demultiplexed",
                1,
                "demultiplexed | Demultiplexed",
            ],
            [
                "params_6",
                3,
                "Pick closed-reference OTUs",
                "Defaults",
                {
                    "reference": "1",
                    "sortmerna_e_value": "1",
                    "sortmerna_max_pos": "10000",
                    "similarity": "0.97",
                    "sortmerna_coverage": "0.97",
                    "threads": "1",
                },
            ],
            ["output_params_6_OTU table | BIOM", 3, "OTU table | BIOM"],
        ],
        "edges": [
            ["input_params_5_FASTQ", "params_5"],
            ["params_5", "output_params_5_demultiplexed | Demultiplexed"],
            ["output_params_5_demultiplexed | Demultiplexed", "params_6"],
            ["params_6", "output_params_6_OTU table | BIOM"],
        ],
    },
]


if __name__ == "__main__":
    main()
