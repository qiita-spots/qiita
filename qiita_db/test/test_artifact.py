# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from datetime import datetime
from functools import partial
from json import dumps
from os import close, remove
from os.path import abspath, basename, dirname, exists, join
from shutil import copyfile
from tempfile import mkdtemp, mkstemp
from unittest import TestCase, main

import networkx as nx
import pandas as pd
from biom import example_table as et
from biom.util import biom_open

import qiita_db as qdb
from qiita_core.testing import wait_for_processing_job
from qiita_core.util import qiita_test_checker


class ArtifactTestsReadOnly(TestCase):
    def test_iter(self):
        obs = list(qdb.artifact.Artifact.iter_by_visibility("public"))
        self.assertEqual(obs, [])

        obs = list(qdb.artifact.Artifact.iter_by_visibility("private"))
        exp = [
            qdb.artifact.Artifact(1),
            qdb.artifact.Artifact(2),
            qdb.artifact.Artifact(3),
            qdb.artifact.Artifact(4),
            qdb.artifact.Artifact(5),
            qdb.artifact.Artifact(6),
            qdb.artifact.Artifact(7),
        ]
        self.assertEqual(obs, exp)

        exp.extend([qdb.artifact.Artifact(8), qdb.artifact.Artifact(9)])
        self.assertEqual(list(qdb.artifact.Artifact.iter()), exp)

    def test_create_type(self):
        obs = qdb.artifact.Artifact.types()
        exp = [
            ["BIOM", "BIOM table", False, False, True],
            ["Demultiplexed", "Demultiplexed and QC sequences", True, True, False],
            ["FASTA", None, False, False, False],
            ["FASTA_Sanger", None, False, False, False],
            ["FASTQ", None, False, False, True],
            ["SFF", None, False, False, False],
            ["per_sample_FASTQ", None, True, False, True],
            ["beta_div_plots", "Qiime 1 beta diversity results", False, False, False],
            ["rarefaction_curves", "Rarefaction curves", False, False, False],
            ["taxa_summary", "Taxa summary plots", False, False, False],
        ]
        self.assertCountEqual(obs, exp)

        qdb.artifact.Artifact.create_type(
            "NewType",
            "NewTypeDesc",
            False,
            False,
            False,
            [("log", False), ("raw_forward_seqs", True)],
        )

        obs = qdb.artifact.Artifact.types()
        exp = [
            ["BIOM", "BIOM table", False, False, True],
            ["Demultiplexed", "Demultiplexed and QC sequences", True, True, False],
            ["FASTA", None, False, False, False],
            ["FASTA_Sanger", None, False, False, False],
            ["FASTQ", None, False, False, True],
            ["SFF", None, False, False, False],
            ["per_sample_FASTQ", None, True, False, True],
            ["beta_div_plots", "Qiime 1 beta diversity results", False, False, False],
            ["rarefaction_curves", "Rarefaction curves", False, False, False],
            ["taxa_summary", "Taxa summary plots", False, False, False],
            ["NewType", "NewTypeDesc", False, False, False],
        ]
        self.assertCountEqual(obs, exp)
        self.assertTrue(exists(qdb.util.get_mountpoint("NewType")[0][1]))

        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.artifact.Artifact.create_type(
                "NewType",
                "NewTypeDesc",
                False,
                False,
                False,
                [("log", False), ("raw_forward_seqs", True)],
            )

    def test_name(self):
        self.assertEqual(qdb.artifact.Artifact(1).name, "Raw data 1")
        self.assertEqual(qdb.artifact.Artifact(2).name, "Demultiplexed 1")
        self.assertEqual(qdb.artifact.Artifact(3).name, "Demultiplexed 2")
        self.assertEqual(qdb.artifact.Artifact(4).name, "BIOM")

    def test_timestamp(self):
        self.assertEqual(
            qdb.artifact.Artifact(1).timestamp, datetime(2012, 10, 1, 9, 30, 27)
        )
        self.assertEqual(
            qdb.artifact.Artifact(2).timestamp, datetime(2012, 10, 1, 10, 30, 27)
        )
        self.assertEqual(
            qdb.artifact.Artifact(3).timestamp, datetime(2012, 10, 1, 11, 30, 27)
        )
        self.assertEqual(
            qdb.artifact.Artifact(4).timestamp, datetime(2012, 10, 2, 17, 30, 00)
        )

    def test_processing_parameters(self):
        self.assertIsNone(qdb.artifact.Artifact(1).processing_parameters)
        obs = qdb.artifact.Artifact(2).processing_parameters
        exp = qdb.software.Parameters.load(
            qdb.software.Command(1),
            values_dict={
                "max_barcode_errors": "1.5",
                "sequence_max_n": "0",
                "max_bad_run_length": "3",
                "rev_comp": "False",
                "phred_quality_threshold": "3",
                "input_data": "1",
                "rev_comp_barcode": "False",
                "rev_comp_mapping_barcodes": "False",
                "min_per_read_length_fraction": "0.75",
                "barcode_type": "golay_12",
                "phred_offset": "auto",
            },
        )
        self.assertEqual(obs, exp)
        obs = qdb.artifact.Artifact(3).processing_parameters
        exp = qdb.software.Parameters.load(
            qdb.software.Command(1),
            values_dict={
                "max_barcode_errors": "1.5",
                "sequence_max_n": "0",
                "max_bad_run_length": "3",
                "rev_comp": "False",
                "phred_quality_threshold": "3",
                "input_data": "1",
                "rev_comp_barcode": "False",
                "rev_comp_mapping_barcodes": "True",
                "min_per_read_length_fraction": "0.75",
                "barcode_type": "golay_12",
                "phred_offset": "auto",
            },
        )
        self.assertEqual(obs, exp)

    def test_visibility(self):
        self.assertEqual(qdb.artifact.Artifact(1).visibility, "private")

    def test_artifact_type(self):
        self.assertEqual(qdb.artifact.Artifact(1).artifact_type, "FASTQ")
        self.assertEqual(qdb.artifact.Artifact(2).artifact_type, "Demultiplexed")
        self.assertEqual(qdb.artifact.Artifact(3).artifact_type, "Demultiplexed")
        self.assertEqual(qdb.artifact.Artifact(4).artifact_type, "BIOM")

    def test_data_type(self):
        self.assertEqual(qdb.artifact.Artifact(1).data_type, "18S")
        self.assertEqual(qdb.artifact.Artifact(2).data_type, "18S")
        self.assertEqual(qdb.artifact.Artifact(3).data_type, "18S")
        self.assertEqual(qdb.artifact.Artifact(4).data_type, "18S")

    def test_can_be_submitted_to_ebi(self):
        self.assertFalse(qdb.artifact.Artifact(1).can_be_submitted_to_ebi)
        self.assertTrue(qdb.artifact.Artifact(2).can_be_submitted_to_ebi)
        self.assertTrue(qdb.artifact.Artifact(3).can_be_submitted_to_ebi)
        self.assertFalse(qdb.artifact.Artifact(4).can_be_submitted_to_ebi)

    def test_is_submitted_to_ebi(self):
        self.assertTrue(qdb.artifact.Artifact(2).is_submitted_to_ebi)
        self.assertFalse(qdb.artifact.Artifact(3).is_submitted_to_ebi)

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.artifact.Artifact(1).is_submitted_to_ebi
        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.artifact.Artifact(4).is_submitted_to_ebi

    def test_ebi_run_accessions(self):
        exp = {
            "1.SKB1.640202": "ERR0000001",
            "1.SKB2.640194": "ERR0000002",
            "1.SKB3.640195": "ERR0000003",
            "1.SKB4.640189": "ERR0000004",
            "1.SKB5.640181": "ERR0000005",
            "1.SKB6.640176": "ERR0000006",
            "1.SKB7.640196": "ERR0000007",
            "1.SKB8.640193": "ERR0000008",
            "1.SKB9.640200": "ERR0000009",
            "1.SKD1.640179": "ERR0000010",
            "1.SKD2.640178": "ERR0000011",
            "1.SKD3.640198": "ERR0000012",
            "1.SKD4.640185": "ERR0000013",
            "1.SKD5.640186": "ERR0000014",
            "1.SKD6.640190": "ERR0000015",
            "1.SKD7.640191": "ERR0000016",
            "1.SKD8.640184": "ERR0000017",
            "1.SKD9.640182": "ERR0000018",
            "1.SKM1.640183": "ERR0000019",
            "1.SKM2.640199": "ERR0000020",
            "1.SKM3.640197": "ERR0000021",
            "1.SKM4.640180": "ERR0000022",
            "1.SKM5.640177": "ERR0000023",
            "1.SKM6.640187": "ERR0000024",
            "1.SKM7.640188": "ERR0000025",
            "1.SKM8.640201": "ERR0000026",
            "1.SKM9.640192": "ERR0000027",
        }
        self.assertEqual(qdb.artifact.Artifact(2).ebi_run_accessions, exp)
        self.assertEqual(qdb.artifact.Artifact(3).ebi_run_accessions, dict())

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.artifact.Artifact(1).ebi_run_accessions

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.artifact.Artifact(4).ebi_run_accessions

    def test_can_be_submitted_to_vamps(self):
        self.assertFalse(qdb.artifact.Artifact(1).can_be_submitted_to_vamps)
        self.assertTrue(qdb.artifact.Artifact(2).can_be_submitted_to_vamps)
        self.assertTrue(qdb.artifact.Artifact(3).can_be_submitted_to_vamps)
        self.assertFalse(qdb.artifact.Artifact(4).can_be_submitted_to_vamps)

    def test_is_submitted_to_vamps(self):
        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.assertFalse(qdb.artifact.Artifact(1).is_submitted_to_vamps)
        self.assertFalse(qdb.artifact.Artifact(2).is_submitted_to_vamps)
        self.assertFalse(qdb.artifact.Artifact(3).is_submitted_to_vamps)
        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.assertFalse(qdb.artifact.Artifact(4).is_submitted_to_vamps)

    def test_filepaths(self):
        db_test_raw_dir = qdb.util.get_mountpoint("raw_data")[0][1]
        path_builder = partial(join, db_test_raw_dir)
        exp_fps = [
            {
                "fp_id": 1,
                "fp": path_builder("1_s_G1_L001_sequences.fastq.gz"),
                "fp_type": "raw_forward_seqs",
                "checksum": "2125826711",
                "fp_size": 58,
            },
            {
                "fp_id": 2,
                "fp": path_builder("1_s_G1_L001_sequences_barcodes.fastq.gz"),
                "fp_type": "raw_barcodes",
                "checksum": "2125826711",
                "fp_size": 58,
            },
        ]
        self.assertEqual(qdb.artifact.Artifact(1).filepaths, exp_fps)

    def test_parents(self):
        self.assertEqual(qdb.artifact.Artifact(1).parents, [])

        exp_parents = [qdb.artifact.Artifact(1)]
        self.assertEqual(qdb.artifact.Artifact(2).parents, exp_parents)
        self.assertEqual(qdb.artifact.Artifact(3).parents, exp_parents)

        exp_parents = [qdb.artifact.Artifact(2)]
        self.assertEqual(qdb.artifact.Artifact(4).parents, exp_parents)

    def test_create_lineage_graph_from_edge_list_empty(self):
        tester = qdb.artifact.Artifact(1)
        obs = tester._create_lineage_graph_from_edge_list([])
        self.assertTrue(isinstance(obs, nx.DiGraph))
        self.assertCountEqual(obs.nodes(), [tester])
        self.assertCountEqual(obs.edges(), [])

    def test_create_lineage_graph_from_edge_list(self):
        tester = qdb.artifact.Artifact(1)
        obs = tester._create_lineage_graph_from_edge_list(
            [(1, 2), (2, 4), (1, 3), (3, 4)]
        )
        self.assertTrue(isinstance(obs, nx.DiGraph))
        exp = [
            qdb.artifact.Artifact(1),
            qdb.artifact.Artifact(2),
            qdb.artifact.Artifact(3),
            qdb.artifact.Artifact(4),
        ]
        self.assertCountEqual(obs.nodes(), exp)
        exp = [
            (qdb.artifact.Artifact(1), qdb.artifact.Artifact(2)),
            (qdb.artifact.Artifact(2), qdb.artifact.Artifact(4)),
            (qdb.artifact.Artifact(1), qdb.artifact.Artifact(3)),
            (qdb.artifact.Artifact(3), qdb.artifact.Artifact(4)),
        ]
        self.assertCountEqual(obs.edges(), exp)

    def test_ancestors(self):
        obs = qdb.artifact.Artifact(1).ancestors
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        self.assertCountEqual(obs_nodes, [qdb.artifact.Artifact(1)])
        obs_edges = obs.edges()
        self.assertCountEqual(obs_edges, [])

        obs = qdb.artifact.Artifact(2).ancestors
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [qdb.artifact.Artifact(1), qdb.artifact.Artifact(2)]
        self.assertCountEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [(qdb.artifact.Artifact(1), qdb.artifact.Artifact(2))]
        self.assertCountEqual(obs_edges, exp_edges)

        obs = qdb.artifact.Artifact(3).ancestors
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [qdb.artifact.Artifact(1), qdb.artifact.Artifact(3)]
        self.assertCountEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [(qdb.artifact.Artifact(1), qdb.artifact.Artifact(3))]
        self.assertCountEqual(obs_edges, exp_edges)

        obs = qdb.artifact.Artifact(4).ancestors
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [
            qdb.artifact.Artifact(1),
            qdb.artifact.Artifact(2),
            qdb.artifact.Artifact(4),
        ]
        self.assertCountEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [
            (qdb.artifact.Artifact(1), qdb.artifact.Artifact(2)),
            (qdb.artifact.Artifact(2), qdb.artifact.Artifact(4)),
        ]
        self.assertCountEqual(obs_edges, exp_edges)

    def test_descendants(self):
        obs = qdb.artifact.Artifact(1).descendants
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [
            qdb.artifact.Artifact(1),
            qdb.artifact.Artifact(2),
            qdb.artifact.Artifact(3),
            qdb.artifact.Artifact(4),
            qdb.artifact.Artifact(5),
            qdb.artifact.Artifact(6),
        ]
        self.assertCountEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [
            (qdb.artifact.Artifact(1), qdb.artifact.Artifact(2)),
            (qdb.artifact.Artifact(1), qdb.artifact.Artifact(3)),
            (qdb.artifact.Artifact(2), qdb.artifact.Artifact(4)),
            (qdb.artifact.Artifact(2), qdb.artifact.Artifact(5)),
            (qdb.artifact.Artifact(2), qdb.artifact.Artifact(6)),
        ]
        self.assertCountEqual(obs_edges, exp_edges)

        obs = qdb.artifact.Artifact(2).descendants
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [
            qdb.artifact.Artifact(2),
            qdb.artifact.Artifact(4),
            qdb.artifact.Artifact(5),
            qdb.artifact.Artifact(6),
        ]
        self.assertCountEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [
            (qdb.artifact.Artifact(2), qdb.artifact.Artifact(4)),
            (qdb.artifact.Artifact(2), qdb.artifact.Artifact(5)),
            (qdb.artifact.Artifact(2), qdb.artifact.Artifact(6)),
        ]
        self.assertCountEqual(obs_edges, exp_edges)

        obs = qdb.artifact.Artifact(3).descendants
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        self.assertCountEqual(obs_nodes, [qdb.artifact.Artifact(3)])
        obs_edges = obs.edges()
        self.assertCountEqual(obs_edges, [])

        obs = qdb.artifact.Artifact(4).descendants
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        self.assertCountEqual(obs_nodes, [qdb.artifact.Artifact(4)])
        obs_edges = obs.edges()
        self.assertCountEqual(obs_edges, [])

    def test_descendants_with_jobs(self):
        A = qdb.artifact.Artifact
        obs = A(1).descendants_with_jobs
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()

        # Add an HTML summary job in one artifact in a non-success statuts, to
        # make sure that it doesn't get returned in the graph
        html_job = qdb.processing_job.ProcessingJob.create(
            qdb.user.User("test@foo.bar"),
            qdb.software.Parameters.load(
                qdb.software.Command.get_html_generator(A(6).artifact_type),
                values_dict={"input_data": 6},
            ),
        )
        html_job._set_status("running")
        # as jobs are created at random we will only check that the artifacts
        # are there and that the number of jobs matches
        exp_nodes = [
            ("artifact", A(1)),
            ("artifact", A(2)),
            ("artifact", A(3)),
            ("artifact", A(4)),
            ("artifact", A(5)),
            ("artifact", A(6)),
        ]
        for e in exp_nodes:
            self.assertIn(e, obs_nodes)
        self.assertEqual(5, len([e for dt, e in obs_nodes if dt == "job"]))
        obs_edges = obs.edges()
        # as jobs are created at random we will only check the number of pairs
        # matches and they are instances of what we expect
        self.assertEqual(10, len(obs_edges))
        self.assertEqual(
            2, len([x for x, y in obs_edges if x[1] == A(1) and y[0] == "job"])
        )
        self.assertEqual(
            3, len([x for x, y in obs_edges if x[1] == A(2) and y[0] == "job"])
        )
        self.assertEqual(
            1, len([y for x, y in obs_edges if y[1] == A(2) and x[0] == "job"])
        )
        self.assertEqual(
            1, len([y for x, y in obs_edges if y[1] == A(3) and x[0] == "job"])
        )
        self.assertEqual(
            1, len([y for x, y in obs_edges if y[1] == A(4) and x[0] == "job"])
        )
        self.assertEqual(
            1, len([y for x, y in obs_edges if y[1] == A(5) and x[0] == "job"])
        )
        self.assertEqual(
            1, len([y for x, y in obs_edges if y[1] == A(6) and x[0] == "job"])
        )

        obs = A(3).descendants
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        self.assertCountEqual(obs_nodes, [A(3)])
        obs_edges = obs.edges()
        self.assertCountEqual(obs_edges, [])

        # Create a workflow starting in the artifact 1, so we can test that
        # "in construction" jobs also show up correctly
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "8", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0, '
            '"phred_offset": "auto"}'
        )
        params = qdb.software.Parameters.load(
            qdb.software.Command(1), json_str=json_str
        )
        wf = qdb.processing_job.ProcessingWorkflow.from_scratch(
            qdb.user.User("test@foo.bar"), params, name="Test WF"
        )
        parent = list(wf.graph.nodes())[0]
        wf.add(
            qdb.software.DefaultParameters(10),
            connections={parent: {"demultiplexed": "input_data"}},
        )
        obs = A(1).descendants_with_jobs
        obs_edges = obs.edges()
        # We have 4 more edges than before. From artifact 1 to parent job,
        # from parent job to output, from output to child job, and from child
        # job to child output
        self.assertEqual(len(obs_edges), 14)
        # We will check that the edges related with the "type" nodes (i.e.
        # the outputs of the jobs in construction) are present
        self.assertEqual(1, len([y for x, y in obs_edges if x[0] == "type"]))
        self.assertEqual(2, len([y for x, y in obs_edges if y[0] == "type"]))

    def test_children(self):
        exp = [qdb.artifact.Artifact(2), qdb.artifact.Artifact(3)]
        self.assertEqual(qdb.artifact.Artifact(1).children, exp)
        exp = [
            qdb.artifact.Artifact(4),
            qdb.artifact.Artifact(5),
            qdb.artifact.Artifact(6),
        ]
        self.assertEqual(qdb.artifact.Artifact(2).children, exp)
        self.assertEqual(qdb.artifact.Artifact(3).children, [])
        self.assertEqual(qdb.artifact.Artifact(4).children, [])

    def test_youngest_artifact(self):
        exp = qdb.artifact.Artifact(6)
        self.assertEqual(qdb.artifact.Artifact(1).youngest_artifact, exp)
        self.assertEqual(qdb.artifact.Artifact(2).youngest_artifact, exp)
        self.assertEqual(
            qdb.artifact.Artifact(3).youngest_artifact, qdb.artifact.Artifact(3)
        )
        self.assertEqual(qdb.artifact.Artifact(6).youngest_artifact, exp)

    def test_prep_templates(self):
        self.assertEqual(
            qdb.artifact.Artifact(1).prep_templates,
            [qdb.metadata_template.prep_template.PrepTemplate(1)],
        )
        self.assertEqual(
            qdb.artifact.Artifact(2).prep_templates,
            [qdb.metadata_template.prep_template.PrepTemplate(1)],
        )
        self.assertEqual(
            qdb.artifact.Artifact(3).prep_templates,
            [qdb.metadata_template.prep_template.PrepTemplate(1)],
        )
        self.assertEqual(
            qdb.artifact.Artifact(4).prep_templates,
            [qdb.metadata_template.prep_template.PrepTemplate(1)],
        )

    def test_study(self):
        self.assertEqual(qdb.artifact.Artifact(1).study, qdb.study.Study(1))
        self.assertIsNone(qdb.artifact.Artifact(9).study)

    def test_analysis(self):
        self.assertEqual(qdb.artifact.Artifact(9).analysis, qdb.analysis.Analysis(1))
        self.assertIsNone(qdb.artifact.Artifact(1).analysis)

    def test_merging_scheme(self):
        self.assertEqual(qdb.artifact.Artifact(1).merging_scheme, ("", ""))
        self.assertEqual(
            qdb.artifact.Artifact(2).merging_scheme,
            ("Split libraries FASTQ | N/A", "N/A"),
        )
        self.assertEqual(
            qdb.artifact.Artifact(3).merging_scheme,
            ("Split libraries FASTQ | N/A", "N/A"),
        )
        self.assertEqual(
            qdb.artifact.Artifact(4).merging_scheme,
            ("Pick closed-reference OTUs | Split libraries FASTQ", "QIIMEq2 v1.9.1"),
        )
        self.assertEqual(
            qdb.artifact.Artifact(5).merging_scheme,
            ("Pick closed-reference OTUs | Split libraries FASTQ", "QIIMEq2 v1.9.1"),
        )

    def test_jobs(self):
        # Returning all jobs
        obs = qdb.artifact.Artifact(1).jobs(show_hidden=True)
        exp = [
            qdb.processing_job.ProcessingJob("6d368e16-2242-4cf8-87b4-a5dc40bb890b"),
            qdb.processing_job.ProcessingJob("4c7115e8-4c8e-424c-bf25-96c292ca1931"),
            qdb.processing_job.ProcessingJob("063e553b-327c-4818-ab4a-adfe58e49860"),
            qdb.processing_job.ProcessingJob("bcc7ebcd-39c1-43e4-af2d-822e3589f14d"),
            qdb.processing_job.ProcessingJob("b72369f9-a886-4193-8d3d-f7b504168e75"),
        ]

        # there are some extra jobs randomly generated, not testing those
        for e in exp:
            self.assertIn(e, obs)

        # Returning only jobs visible by the user
        obs = qdb.artifact.Artifact(1).jobs()
        exp = [
            qdb.processing_job.ProcessingJob("6d368e16-2242-4cf8-87b4-a5dc40bb890b"),
            qdb.processing_job.ProcessingJob("4c7115e8-4c8e-424c-bf25-96c292ca1931"),
            qdb.processing_job.ProcessingJob("b72369f9-a886-4193-8d3d-f7b504168e75"),
        ]

        for e in exp:
            self.assertIn(e, obs)

    def test_jobs_cmd(self):
        cmd = qdb.software.Command(1)
        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd, show_hidden=True)
        exp = [
            qdb.processing_job.ProcessingJob("6d368e16-2242-4cf8-87b4-a5dc40bb890b"),
            qdb.processing_job.ProcessingJob("4c7115e8-4c8e-424c-bf25-96c292ca1931"),
            qdb.processing_job.ProcessingJob("063e553b-327c-4818-ab4a-adfe58e49860"),
            qdb.processing_job.ProcessingJob("b72369f9-a886-4193-8d3d-f7b504168e75"),
        ]
        # there are some extra jobs randomly generated, not testing those
        for e in exp:
            self.assertIn(e, obs)

        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd)
        exp = [
            qdb.processing_job.ProcessingJob("6d368e16-2242-4cf8-87b4-a5dc40bb890b"),
            qdb.processing_job.ProcessingJob("4c7115e8-4c8e-424c-bf25-96c292ca1931"),
            qdb.processing_job.ProcessingJob("b72369f9-a886-4193-8d3d-f7b504168e75"),
        ]

        cmd = qdb.software.Command(2)
        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd, show_hidden=True)
        exp = [qdb.processing_job.ProcessingJob("bcc7ebcd-39c1-43e4-af2d-822e3589f14d")]
        self.assertEqual(obs, exp)

        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd)
        self.assertEqual(obs, [])

    def test_jobs_status(self):
        obs = qdb.artifact.Artifact(1).jobs(status="success")
        exp = [
            qdb.processing_job.ProcessingJob("6d368e16-2242-4cf8-87b4-a5dc40bb890b"),
            qdb.processing_job.ProcessingJob("4c7115e8-4c8e-424c-bf25-96c292ca1931"),
            qdb.processing_job.ProcessingJob("b72369f9-a886-4193-8d3d-f7b504168e75"),
        ]
        # there are some extra jobs randomly generated, not testing those
        for e in exp:
            self.assertIn(e, obs)

        obs = qdb.artifact.Artifact(1).jobs(status="running", show_hidden=True)
        exp = [qdb.processing_job.ProcessingJob("bcc7ebcd-39c1-43e4-af2d-822e3589f14d")]
        self.assertEqual(obs, exp)

        obs = qdb.artifact.Artifact(1).jobs(status="running")
        self.assertEqual(obs, [])

        obs = qdb.artifact.Artifact(1).jobs(status="queued", show_hidden=True)
        exp = [qdb.processing_job.ProcessingJob("063e553b-327c-4818-ab4a-adfe58e49860")]
        self.assertEqual(obs, exp)

        obs = qdb.artifact.Artifact(1).jobs(status="queued")
        self.assertEqual(obs, [])

    def test_jobs_cmd_and_status(self):
        cmd = qdb.software.Command(1)
        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd, status="success")
        exp = [
            qdb.processing_job.ProcessingJob("6d368e16-2242-4cf8-87b4-a5dc40bb890b"),
            qdb.processing_job.ProcessingJob("4c7115e8-4c8e-424c-bf25-96c292ca1931"),
            qdb.processing_job.ProcessingJob("b72369f9-a886-4193-8d3d-f7b504168e75"),
        ]
        # there are some extra jobs randomly generated, not testing those
        for e in exp:
            self.assertIn(e, obs)

        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd, status="queued", show_hidden=True)
        exp = [qdb.processing_job.ProcessingJob("063e553b-327c-4818-ab4a-adfe58e49860")]
        self.assertEqual(obs, exp)

        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd, status="queued")
        self.assertEqual(obs, [])

        cmd = qdb.software.Command(2)
        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd, status="queued")
        exp = []
        self.assertEqual(obs, exp)

    def test_get_commands(self):
        # we will check only ids for simplicity
        # checking processing artifacts
        obs = [c.id for c in qdb.artifact.Artifact(1).get_commands]
        self.assertEqual(obs, [1])
        obs = [c.id for c in qdb.artifact.Artifact(2).get_commands]
        self.assertEqual(obs, [3])
        # this is a biom in processing, so no commands should be available
        obs = [c.id for c in qdb.artifact.Artifact(6).get_commands]
        self.assertEqual(obs, [])

        # checking analysis object - this is a biom in analysis, several
        # commands should be available
        obs = [c.id for c in qdb.artifact.Artifact(8).get_commands]
        self.assertEqual(obs, [9, 10, 11, 12])


@qiita_test_checker()
class ArtifactTests(TestCase):
    def setUp(self):
        # Generate some files for a root artifact
        fd, self.fp1 = mkstemp(suffix="_seqs.fastq")
        close(fd)
        with open(self.fp1, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 1:N:0:\n"
                "NACGTAGGGTGCAAGCGTTGTCCGGAATNA\n"
                "+\n"
                "#1=DDFFFHHHHHJJJJJJJJJJJJGII#0\n"
            )

        fd, self.fp2 = mkstemp(suffix="_barcodes.fastq")
        close(fd)
        with open(self.fp2, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 2:N:0:\n"
                "NNNCNNNNNNNNN\n"
                "+\n"
                "#############\n"
            )
        self.filepaths_root = [(self.fp1, 1), (self.fp2, 3)]

        # Generate some files for a processed artifact
        fd, self.fp3 = mkstemp(suffix="_seqs.fna")
        close(fd)
        with open(self.fp3, "w") as f:
            f.write(
                ">1.sid_r4_0 M02034:17:000000000-A5U18:1:1101:15370:1394 "
                "1:N:0:1 orig_bc=CATGAGCT new_bc=CATGAGCT bc_diffs=0\n"
                "GTGTGCCAGCAGCCGCGGTAATACGTAGGG\n"
            )
        self.filepaths_processed = [(self.fp3, 4)]

        # Generate some file for a BIOM
        fd, self.fp4 = mkstemp(suffix="_table.biom")
        with biom_open(self.fp4, "w") as f:
            et.to_hdf5(f, "test")
        self.filepaths_biom = [(self.fp4, 7)]

        # Create a new prep template
        metadata_dict = {
            "SKB8.640193": {
                "center_name": "ANL",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "GTCCGCAAGTTA",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "target_subfragment": "V4",
                "target_gene": "16S rRNA",
                "experiment_design_description": "BBBB",
            }
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient="index", dtype=str)
        self.prep_template = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, qdb.study.Study(1), "16S"
        )
        self.prep_template_2 = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, qdb.study.Study(1), "16S"
        )

        self._clean_up_files = [self.fp1, self.fp2, self.fp3, self.fp4]

        # per_sample_FASTQ Metagenomic example

        self.prep_template_per_sample_fastq = (
            qdb.metadata_template.prep_template.PrepTemplate.create(
                metadata, qdb.study.Study(1), "Metagenomic"
            )
        )
        fd, self.fwd = mkstemp(prefix="SKB8.640193", suffix="_R1.fastq")
        close(fd)
        with open(self.fwd, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 1:N:0:\n"
                "NACGTAGGGTGCAAGCGTTGTCCGGAATNA\n"
                "+\n"
                "#1=DDFFFHHHHHJJJJJJJJJJJJGII#0\n"
            )
        fd, self.rev = mkstemp(prefix="SKB8.640193", suffix="_R2.fastq")
        close(fd)
        with open(self.rev, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 1:N:0:\n"
                "NACGTAGGGTGCAAGCGTTGTCCGGAATNA\n"
                "+\n"
                "#1=DDFFFHHHHHJJJJJJJJJJJJGII#0\n"
            )

        self._clean_up_files.extend([self.fwd, self.rev])

        self.user = qdb.user.User("test@foo.bar")

    def tearDown(self):
        for f in self._clean_up_files:
            if exists(f):
                remove(f)

    def test_copy(self):
        src = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )
        before = datetime.now()
        obs = qdb.artifact.Artifact.copy(src, self.prep_template_2)

        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertIsNone(obs.processing_parameters)
        self.assertEqual(obs.visibility, "sandbox")
        self.assertEqual(obs.artifact_type, src.artifact_type)
        self.assertEqual(obs.data_type, self.prep_template.data_type())
        self.assertEqual(obs.can_be_submitted_to_ebi, src.can_be_submitted_to_ebi)
        self.assertEqual(obs.can_be_submitted_to_vamps, src.can_be_submitted_to_vamps)

        db_dir = qdb.util.get_mountpoint(src.artifact_type)[0][1]
        path_builder = partial(join, db_dir, str(obs.id))
        exp_fps = []
        for x in src.filepaths:
            new_fp = path_builder(basename(x["fp"]))
            exp_fps.append((new_fp, x["fp_type"]))
            self._clean_up_files.append(new_fp)

        self.assertEqual([(x["fp"], x["fp_type"]) for x in obs.filepaths], exp_fps)
        self.assertEqual(obs.parents, [])
        self.assertEqual(obs.prep_templates, [self.prep_template_2])

        self.assertEqual(obs.study, qdb.study.Study(1))

    def test_create_error(self):
        # no filepaths
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create([], "FASTQ", prep_template=self.prep_template)

        # prep template and parents
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root,
                "FASTQ",
                prep_template=self.prep_template,
                parents=[qdb.artifact.Artifact(1)],
            )

        # analysis and prep_template
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root,
                "BIOM",
                prep_template=self.prep_template,
                analysis=qdb.analysis.Analysis(1),
            )

        # Analysis and parents
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root,
                "BIOM",
                parents=[qdb.artifact.Artifact(1)],
                analysis=qdb.analysis.Analysis(1),
            )

        # no prep template no parents no analysis
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(self.filepaths_root, "FASTQ")

        # parents no processing parameters
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root, "FASTQ", parents=[qdb.artifact.Artifact(1)]
            )

        # analysis no data type
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root, "BIOM", analysis=qdb.analysis.Analysis(1)
            )

        # prep template and processing parameters
        parameters = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": 1}
        )
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root,
                "FASTQ",
                prep_template=self.prep_template,
                processing_parameters=parameters,
            )

        # prep template and data type
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root,
                "FASTQ",
                prep_template=self.prep_template,
                data_type="Multiomic",
            )

        # different data types
        new = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )
        parameters = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": 1}
        )
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_processed,
                "Demultiplexed",
                parents=[qdb.artifact.Artifact(1), new],
                processing_parameters=parameters,
            )

    def test_create_root(self):
        before = datetime.now()
        obs = qdb.artifact.Artifact.create(
            self.filepaths_root,
            "FASTQ",
            prep_template=self.prep_template,
            name="Test artifact",
        )
        self.assertEqual(obs.name, "Test artifact")
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertIsNone(obs.processing_parameters)
        self.assertEqual(obs.visibility, "sandbox")
        self.assertEqual(obs.artifact_type, "FASTQ")
        self.assertEqual(obs.data_type, self.prep_template.data_type())
        self.assertFalse(obs.can_be_submitted_to_ebi)
        self.assertFalse(obs.can_be_submitted_to_vamps)

        db_fastq_dir = qdb.util.get_mountpoint("FASTQ")[0][1]
        path_builder = partial(join, db_fastq_dir, str(obs.id))
        exp_fps = [
            (path_builder(basename(self.fp1)), "raw_forward_seqs"),
            (path_builder(basename(self.fp2)), "raw_barcodes"),
        ]
        self.assertEqual([(x["fp"], x["fp_type"]) for x in obs.filepaths], exp_fps)
        self.assertEqual(obs.parents, [])
        self.assertEqual(obs.prep_templates, [self.prep_template])

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.ebi_run_accessions

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.is_submitted_to_vamps

        self.assertEqual(obs.study, qdb.study.Study(1))
        self.assertIsNone(obs.analysis)

    def test_create_root_analysis(self):
        before = datetime.now()
        obs = qdb.artifact.Artifact.create(
            self.filepaths_biom,
            "BIOM",
            name="Test artifact analysis",
            analysis=qdb.analysis.Analysis(1),
            data_type="16S",
        )
        self.assertEqual(obs.name, "Test artifact analysis")
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertIsNone(obs.processing_parameters)
        self.assertEqual(obs.visibility, "sandbox")
        self.assertEqual(obs.artifact_type, "BIOM")
        self.assertEqual(obs.data_type, "16S")
        self.assertFalse(obs.can_be_submitted_to_ebi)
        self.assertFalse(obs.can_be_submitted_to_vamps)

        db_fastq_dir = qdb.util.get_mountpoint("BIOM")[0][1]
        path_builder = partial(join, db_fastq_dir, str(obs.id))
        exp_fps = [(path_builder(basename(self.fp4)), "biom")]
        self.assertEqual([(x["fp"], x["fp_type"]) for x in obs.filepaths], exp_fps)
        self.assertEqual(obs.parents, [])
        self.assertEqual(obs.prep_templates, [])

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.ebi_run_accessions

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.is_submitted_to_vamps

        self.assertIsNone(obs.study)
        self.assertEqual(obs.analysis, qdb.analysis.Analysis(1))

        # testing that it can be deleted
        qdb.artifact.Artifact.delete(obs.id)

    def test_create_processed(self):
        # make a copy of files for the can_be_submitted_to_ebi tests
        lcopy = self.fp3 + ".fna"
        self._clean_up_files.append(lcopy)
        copyfile(self.fp3, lcopy)

        exp_params = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": 1}
        )
        before = datetime.now()
        obs = qdb.artifact.Artifact.create(
            self.filepaths_processed,
            "Demultiplexed",
            parents=[qdb.artifact.Artifact(1)],
            processing_parameters=exp_params,
        )
        self.assertEqual(obs.name, "noname")
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertEqual(obs.processing_parameters, exp_params)
        self.assertEqual(obs.visibility, "private")
        self.assertEqual(obs.artifact_type, "Demultiplexed")
        self.assertEqual(obs.data_type, qdb.artifact.Artifact(1).data_type)
        self.assertTrue(obs.can_be_submitted_to_ebi)
        self.assertTrue(obs.can_be_submitted_to_vamps)
        self.assertFalse(obs.is_submitted_to_vamps)

        db_demultiplexed_dir = qdb.util.get_mountpoint("Demultiplexed")[0][1]
        path_builder = partial(join, db_demultiplexed_dir, str(obs.id))
        exp_fps = [(path_builder(basename(self.fp3)), "preprocessed_fasta")]
        self.assertEqual([(x["fp"], x["fp_type"]) for x in obs.filepaths], exp_fps)
        self.assertEqual(obs.parents, [qdb.artifact.Artifact(1)])
        self.assertEqual(
            obs.prep_templates, [qdb.metadata_template.prep_template.PrepTemplate(1)]
        )
        self.assertEqual(obs.ebi_run_accessions, dict())
        self.assertEqual(obs.study, qdb.study.Study(1))
        self.assertFalse(exists(self.filepaths_processed[0][0]))
        self.assertIsNone(obs.analysis)

        # let's create another demultiplexed on top of the previous one to
        # test can_be_submitted_to_ebi
        exp_params = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": obs.id}
        )
        new = qdb.artifact.Artifact.create(
            [(lcopy, 4)],
            "Demultiplexed",
            parents=[obs],
            processing_parameters=exp_params,
        )
        self.assertFalse(new.can_be_submitted_to_ebi)

    def test_create_copy_files(self):
        exp_params = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": 1}
        )
        before = datetime.now()
        obs = qdb.artifact.Artifact.create(
            self.filepaths_processed,
            "Demultiplexed",
            parents=[qdb.artifact.Artifact(1)],
            processing_parameters=exp_params,
            move_files=False,
        )
        self.assertEqual(obs.name, "noname")
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertEqual(obs.processing_parameters, exp_params)
        self.assertEqual(obs.visibility, "private")
        self.assertEqual(obs.artifact_type, "Demultiplexed")
        self.assertEqual(obs.data_type, qdb.artifact.Artifact(1).data_type)
        self.assertTrue(obs.can_be_submitted_to_ebi)
        self.assertTrue(obs.can_be_submitted_to_vamps)
        self.assertFalse(obs.is_submitted_to_vamps)

        db_demultiplexed_dir = qdb.util.get_mountpoint("Demultiplexed")[0][1]
        path_builder = partial(join, db_demultiplexed_dir, str(obs.id))
        exp_fps = [(path_builder(basename(self.fp3)), "preprocessed_fasta")]
        self.assertEqual([(x["fp"], x["fp_type"]) for x in obs.filepaths], exp_fps)
        self.assertEqual(obs.parents, [qdb.artifact.Artifact(1)])
        self.assertEqual(
            obs.prep_templates, [qdb.metadata_template.prep_template.PrepTemplate(1)]
        )
        self.assertEqual(obs.ebi_run_accessions, dict())
        self.assertEqual(obs.study, qdb.study.Study(1))
        self.assertTrue(exists(self.filepaths_processed[0][0]))
        self.assertIsNone(obs.analysis)

    def test_create_biom(self):
        before = datetime.now()
        cmd = qdb.software.Command(3)
        exp_params = qdb.software.Parameters.from_default_params(
            next(cmd.default_parameter_sets), {"input_data": 1}
        )
        obs = qdb.artifact.Artifact.create(
            self.filepaths_biom,
            "BIOM",
            parents=[qdb.artifact.Artifact(2)],
            processing_parameters=exp_params,
        )
        self.assertEqual(obs.name, "noname")
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertEqual(obs.processing_parameters, exp_params)
        self.assertEqual(obs.visibility, "private")
        self.assertEqual(obs.artifact_type, "BIOM")
        self.assertEqual(obs.data_type, qdb.artifact.Artifact(2).data_type)
        self.assertFalse(obs.can_be_submitted_to_ebi)
        self.assertFalse(obs.can_be_submitted_to_vamps)
        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.ebi_run_accessions

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.is_submitted_to_vamps

        db_biom_dir = qdb.util.get_mountpoint("BIOM")[0][1]
        path_builder = partial(join, db_biom_dir, str(obs.id))
        exp_fps = [(path_builder(basename(self.fp4)), "biom")]
        self.assertEqual([(x["fp"], x["fp_type"]) for x in obs.filepaths], exp_fps)
        self.assertEqual(obs.parents, [qdb.artifact.Artifact(2)])
        self.assertEqual(
            obs.prep_templates, [qdb.metadata_template.prep_template.PrepTemplate(1)]
        )
        self.assertEqual(obs.study, qdb.study.Study(1))
        self.assertIsNone(obs.analysis)

    def test_delete_error_public(self):
        test = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )
        test.visibility = "public"
        self._clean_up_files.extend([x["fp"] for x in test.filepaths])
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(test.id)

    def test_delete_error_has_children(self):
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(1)

    def test_delete_error_analyzed(self):
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(4)

    def test_delete_error_ebi(self):
        parameters = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": 1}
        )
        obs = qdb.artifact.Artifact.create(
            self.filepaths_processed,
            "Demultiplexed",
            parents=[qdb.artifact.Artifact(1)],
            processing_parameters=parameters,
        )
        obs.ebi_run_accessions = {
            "1.SKB1.640202": "ERR1000001",
            "1.SKB2.640194": "ERR1000002",
        }
        self._clean_up_files.extend([x["fp"] for x in obs.filepaths])
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(obs.id)

    def test_delete_error_vamps(self):
        parameters = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": 1}
        )
        obs = qdb.artifact.Artifact.create(
            self.filepaths_processed,
            "Demultiplexed",
            parents=[qdb.artifact.Artifact(1)],
            processing_parameters=parameters,
        )
        obs.is_submitted_to_vamps = True
        self._clean_up_files.extend([x["fp"] for x in obs.filepaths])
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(obs.id)

    def test_delete_in_construction_job(self):
        test = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )
        self._clean_up_files.extend([x["fp"] for x in test.filepaths])
        json_str = (
            '{"input_data": %d, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0, '
            '"phred_offset": ""}' % test.id
        )
        qdb.processing_job.ProcessingJob.create(
            self.user,
            qdb.software.Parameters.load(qdb.software.Command(1), json_str=json_str),
        )
        uploads_fp = join(qdb.util.get_mountpoint("uploads")[0][1], str(test.study.id))
        self._clean_up_files.extend(
            [join(uploads_fp, basename(x["fp"])) for x in test.filepaths]
        )

        qdb.artifact.Artifact.delete(test.id)

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.artifact.Artifact(test.id)

    def test_delete_error_running_job(self):
        test = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )
        self._clean_up_files.extend([x["fp"] for x in test.filepaths])
        json_str = (
            '{"input_data": %d, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0, '
            '"phred_offset": ""}' % test.id
        )
        job = qdb.processing_job.ProcessingJob.create(
            self.user,
            qdb.software.Parameters.load(qdb.software.Command(1), json_str=json_str),
        )
        job._set_status("running")
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(test.id)

    def test_delete(self):
        test = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )

        uploads_fp = join(qdb.util.get_mountpoint("uploads")[0][1], str(test.study.id))
        self._clean_up_files.extend(
            [join(uploads_fp, basename(x["fp"])) for x in test.filepaths]
        )

        qdb.artifact.Artifact.delete(test.id)

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.artifact.Artifact(test.id)

        # Analysis artifact
        parameters = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": 1}
        )
        test = qdb.artifact.Artifact.create(
            self.filepaths_processed,
            "Demultiplexed",
            parents=[qdb.artifact.Artifact(9)],
            processing_parameters=parameters,
        )

        self._clean_up_files.extend(
            [join(uploads_fp, basename(x["fp"])) for x in test.filepaths]
        )
        qdb.artifact.Artifact.delete(test.id)

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.artifact.Artifact(test.id)

    def test_delete_with_html(self):
        # creating a single file html_summary
        fd, html_fp = mkstemp(suffix=".html")
        close(fd)
        self.filepaths_root.append((html_fp, "html_summary"))
        self._clean_up_files.append(html_fp)

        # creating a folder with a file for html_summary_dir
        summary_dir = mkdtemp()
        open(join(summary_dir, "index.html"), "w").write("this is a test")
        self.filepaths_root.append((summary_dir, "html_summary_dir"))
        self._clean_up_files.append(summary_dir)

        test = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )

        uploads_fp = join(qdb.util.get_mountpoint("uploads")[0][1], str(test.study.id))

        self._clean_up_files.extend(
            [join(uploads_fp, basename(x["fp"])) for x in test.filepaths]
        )

        qdb.artifact.Artifact.delete(test.id)

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.artifact.Artifact(test.id)

        self.assertFalse(exists(join(uploads_fp, basename(html_fp))))
        self.assertFalse(exists(join(uploads_fp, basename(summary_dir))))

    def test_delete_with_jobs(self):
        test = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )
        uploads_fp = join(qdb.util.get_mountpoint("uploads")[0][1], str(test.study.id))
        self._clean_up_files.extend(
            [join(uploads_fp, basename(x["fp"])) for x in test.filepaths]
        )

        json_str = (
            '{"input_data": %d, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0, '
            '"phred_offset": ""}' % test.id
        )
        job = qdb.processing_job.ProcessingJob.create(
            self.user,
            qdb.software.Parameters.load(qdb.software.Command(1), json_str=json_str),
        )
        job._set_status("success")

        qdb.artifact.Artifact.delete(test.id)

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.artifact.Artifact(test.id)

        # Check that the job still exists, so we cap keep track of system usage
        qdb.processing_job.ProcessingJob(job.id)

    def test_being_deleted_by(self):
        test = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )
        uploads_fp = join(qdb.util.get_mountpoint("uploads")[0][1], str(test.study.id))
        self._clean_up_files.extend(
            [join(uploads_fp, basename(x["fp"])) for x in test.filepaths]
        )

        # verifying that there are no jobs in the list
        self.assertIsNone(test.being_deleted_by)

        # creating new deleting job
        qiita_plugin = qdb.software.Software.from_name_and_version("Qiita", "alpha")
        cmd = qiita_plugin.get_command("delete_artifact")
        params = qdb.software.Parameters.load(cmd, values_dict={"artifact": test.id})
        job = qdb.processing_job.ProcessingJob.create(self.user, params, True)
        job._set_status("running")

        # verifying that there is a job and is the same than above
        self.assertEqual(job, test.being_deleted_by)

        # let's set it as error and now we should not have it anymore
        job._set_error("Killed by admin")
        self.assertIsNone(test.being_deleted_by)

        # now, let's actually remove
        job = qdb.processing_job.ProcessingJob.create(self.user, params, True)
        job.submit()
        # let's wait for job
        wait_for_processing_job(job.id)

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.artifact.Artifact(test.id)

    def test_delete_as_output_job(self):
        fd, fp = mkstemp(suffix="_table.biom")
        self._clean_up_files.append(fp)
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        data = {"OTU table": {"filepaths": [(fp, "biom")], "artifact_type": "BIOM"}}
        job = qdb.processing_job.ProcessingJob.create(
            self.user,
            qdb.software.Parameters.load(
                qdb.software.Command.get_validator("BIOM"),
                values_dict={
                    "files": dumps({"biom": [fp]}),
                    "artifact_type": "BIOM",
                    "template": 1,
                    "provenance": dumps(
                        {
                            "job": "bcc7ebcd-39c1-43e4-af2d-822e3589f14d",
                            "cmd_out_id": 3,
                            "name": "test-delete",
                        }
                    ),
                },
            ),
        )
        parent = qdb.processing_job.ProcessingJob(
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d"
        )
        parent._set_validator_jobs([job])
        job._set_status("running")
        job.complete(True, artifacts_data=data)
        job = qdb.processing_job.ProcessingJob("bcc7ebcd-39c1-43e4-af2d-822e3589f14d")
        job.release_validators()
        artifact = job.outputs["OTU table"]
        self._clean_up_files.extend([x["fp"] for x in artifact.filepaths])

        qdb.artifact.Artifact.delete(artifact.id)

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.artifact.Artifact(artifact.id)

    def test_unique_ids(self):
        art = qdb.artifact.Artifact(1)
        obs = art.unique_ids()
        exp = {name: idx for idx, name in enumerate(sorted(art.prep_templates[0].keys()), 1)}
        self.assertEqual(obs, exp)

        # verify repeat calls are unchanged
        obs = art.unique_ids()
        self.assertEqual(obs, exp)

    def test_name_setter(self):
        a = qdb.artifact.Artifact(1)
        self.assertEqual(a.name, "Raw data 1")
        a.name = "new name"
        self.assertEqual(a.name, "new name")

    def test_visibility_setter(self):
        a = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )

        self.assertEqual(a.visibility, "sandbox")
        a.visibility = "awaiting_approval"
        self.assertEqual(a.visibility, "awaiting_approval")
        a.visibility = "private"
        self.assertEqual(a.visibility, "private")
        a.visibility = "public"
        self.assertEqual(a.visibility, "public")

        # Testing that the visibility inference works as expected
        # The current artifact network that we have in the db looks as follows:
        #                              /- 4 (private)
        #              /- 2 (private) -|- 5 (private)
        # 1 (private) -|               \- 6 (private)
        #              \- 3 (private)
        # By changing the visibility of 4 to public, the visibility of all
        # should change
        a1 = qdb.artifact.Artifact(1)
        a2 = qdb.artifact.Artifact(2)
        a3 = qdb.artifact.Artifact(3)
        a4 = qdb.artifact.Artifact(4)
        a5 = qdb.artifact.Artifact(5)
        a6 = qdb.artifact.Artifact(6)

        a4.visibility = "public"

        self.assertEqual(a1.visibility, "public")
        self.assertEqual(a2.visibility, "public")
        self.assertEqual(a3.visibility, "public")
        self.assertEqual(a4.visibility, "public")
        self.assertEqual(a5.visibility, "public")
        self.assertEqual(a6.visibility, "public")

        # Same if we go back
        a4.visibility = "private"

        self.assertEqual(a1.visibility, "private")
        self.assertEqual(a2.visibility, "private")
        self.assertEqual(a3.visibility, "private")
        self.assertEqual(a4.visibility, "private")
        self.assertEqual(a5.visibility, "private")
        self.assertEqual(a6.visibility, "private")

        # testing human_reads_filter_method here as in the future we might
        # want to check that this property is inherited as visibility is;
        # however, for the time being we don't need to do that and there is
        # no downside on adding it here.
        mtd = "The greatest human filtering method"
        self.assertEqual(mtd, a1.human_reads_filter_method)
        self.assertIsNone(a2.human_reads_filter_method)
        self.assertIsNone(a3.human_reads_filter_method)

        # let's change some values
        with self.assertRaisesRegex(
            ValueError, '"This should fail" is not a valid human_reads_filter_method'
        ):
            a2.human_reads_filter_method = "This should fail"
        self.assertIsNone(a2.human_reads_filter_method)
        a2.human_reads_filter_method = mtd
        self.assertEqual(mtd, a2.human_reads_filter_method)
        self.assertIsNone(a3.human_reads_filter_method)

    def test_ebi_run_accessions_setter(self):
        a = qdb.artifact.Artifact(3)
        self.assertEqual(a.ebi_run_accessions, dict())
        new_vals = {
            "1.SKB1.640202": "ERR1000001",
            "1.SKB2.640194": "ERR1000002",
            "1.SKB3.640195": "ERR1000003",
            "1.SKB4.640189": "ERR1000004",
            "1.SKB5.640181": "ERR1000005",
            "1.SKB6.640176": "ERR1000006",
            "1.SKB7.640196": "ERR1000007",
            "1.SKB8.640193": "ERR1000008",
            "1.SKB9.640200": "ERR1000009",
            "1.SKD1.640179": "ERR1000010",
            "1.SKD2.640178": "ERR1000011",
            "1.SKD3.640198": "ERR1000012",
            "1.SKD4.640185": "ERR1000013",
            "1.SKD5.640186": "ERR1000014",
            "1.SKD6.640190": "ERR1000015",
            "1.SKD7.640191": "ERR1000016",
            "1.SKD8.640184": "ERR1000017",
            "1.SKD9.640182": "ERR1000018",
            "1.SKM1.640183": "ERR1000019",
            "1.SKM2.640199": "ERR1000020",
            "1.SKM3.640197": "ERR1000021",
            "1.SKM4.640180": "ERR1000022",
            "1.SKM5.640177": "ERR1000023",
            "1.SKM6.640187": "ERR1000024",
            "1.SKM7.640188": "ERR1000025",
            "1.SKM8.640201": "ERR1000026",
            "1.SKM9.640192": "ERR1000027",
        }
        a.ebi_run_accessions = new_vals
        self.assertEqual(a.ebi_run_accessions, new_vals)

    def test_is_submitted_to_vamps_setter(self):
        a = qdb.artifact.Artifact(2)
        self.assertFalse(a.is_submitted_to_vamps)
        a.is_submitted_to_vamps = True
        self.assertTrue(a.is_submitted_to_vamps)

    def test_html_summary_setter(self):
        a = qdb.artifact.Artifact(1)

        # Check that returns None when it doesn't exist
        self.assertIsNone(a.html_summary_fp)

        fd, fp = mkstemp(suffix=".html")
        close(fd)
        self._clean_up_files.append(fp)

        db_fastq_dir = qdb.util.get_mountpoint("FASTQ")[0][1]
        path_builder = partial(join, db_fastq_dir, str(a.id))

        # Check the setter works when the artifact does not have the summary
        a.set_html_summary(fp)
        exp1 = path_builder(basename(fp))
        self.assertEqual(a.html_summary_fp[1], exp1)

        fd, fp = mkstemp(suffix=".html")
        close(fd)
        self._clean_up_files.append(fp)

        dp = mkdtemp()
        self._clean_up_files.append(dp)

        # Check the setter works when the artifact already has a summary
        # and with a directory
        a.set_html_summary(fp, support_dir=dp)
        exp2 = path_builder(basename(fp))
        self.assertEqual(a.html_summary_fp[1], exp2)
        self.assertFalse(exists(exp1))

        # Check that the setter correctly removes the directory if a new
        # summary is added. Magic number 0. There is only one html_summary_dir
        # added on the previous test
        old_dir_fp = [
            x["fp"] for x in a.filepaths if x["fp_type"] == "html_summary_dir"
        ][0]
        fd, fp = mkstemp(suffix=".html")
        close(fd)
        self._clean_up_files.append(fp)
        a.set_html_summary(fp)
        exp3 = path_builder(basename(fp))
        self.assertEqual(a.html_summary_fp[1], exp3)
        self.assertFalse(exists(exp2))
        self.assertFalse(exists(old_dir_fp))
        summary_dir = [
            x["fp"] for x in a.filepaths if x["fp_type"] == "html_summary_dir"
        ]
        self.assertEqual(summary_dir, [])

        # let's check if we update, we do _not_ remove the files
        a.set_html_summary(exp3)
        self.assertTrue(exists(a.html_summary_fp[1]))

    def test_descendants_with_jobs_one_element(self):
        artifact = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template
        )

        obs = self.prep_template.artifact.descendants_with_jobs.nodes()
        exp = [("artifact", artifact)]
        self.assertCountEqual(obs, exp)

    def test_has_human(self):
        # testing a FASTQ artifact (1), should be False
        self.assertFalse(qdb.artifact.Artifact(1).has_human)

        # create a per_sample_FASTQ
        artifact = qdb.artifact.Artifact.create(
            [(self.fwd, 1), (self.rev, 2)],
            "per_sample_FASTQ",
            prep_template=self.prep_template_per_sample_fastq,
        )

        # this should be False as there are no human samples
        self.assertFalse(artifact.has_human)

        # let's make it True by making the samle human-*
        df = pd.DataFrame.from_dict(
            {"1.SKB8.640193": {"env_package": "human-oral"}}, orient="index", dtype=str
        )
        artifact.study.sample_template.update(df)

        self.assertTrue(artifact.has_human)

        # now if we change the pt data_type to 16S
        pt = artifact.prep_templates[0]
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(
                f"""UPDATE qiita.prep_template
                    SET data_type_id = 1
                    WHERE prep_template_id = {pt.id}"""
            )
            qdb.sql_connection.TRN.execute()
        self.assertFalse(artifact.has_human)

    def test_descendants_with_jobs(self):
        # let's tests that we can connect two artifacts with different root
        # in the same analysis
        # 1. make sure there are 3 nodes
        a = qdb.artifact.Artifact(8)
        self.assertEqual(len(a.descendants_with_jobs.nodes), 3)
        self.assertEqual(len(a.analysis.artifacts), 2)
        # 2. add a new root and make sure we see it
        c = qdb.artifact.Artifact.create(
            self.filepaths_root, "BIOM", analysis=a.analysis, data_type="16S"
        )
        self.assertEqual(len(a.analysis.artifacts), 3)
        # 3. add jobs conencting the new artifact to the other root
        #    - currently:
        #    a -> job -> b
        #    c
        #    - expected:
        #    a --> job  -> b
        #                  |-> job2 -> out
        #                        ^
        #                  |-----|---> job1 -> out
        #    c ------------|
        cmd = qdb.software.Command.create(
            qdb.software.Software(1),
            "CommandWithMultipleInputs",
            "",
            {
                "input_x": ['artifact:["BIOM"]', None],
                "input_y": ['artifact:["BIOM"]', None],
            },
            {"out": "BIOM"},
        )
        params = qdb.software.Parameters.load(
            cmd, values_dict={"input_x": a.children[0].id, "input_y": c.id}
        )
        wf = qdb.processing_job.ProcessingWorkflow.from_scratch(
            self.user, params, name="Test WF"
        )
        job1 = list(wf.graph.nodes())[0]

        cmd_dp = qdb.software.DefaultParameters.create("", cmd)
        wf.add(cmd_dp, req_params={"input_x": a.id, "input_y": c.id})
        job2 = list(wf.graph.nodes())[1]
        jobs = [j[1] for e in a.descendants_with_jobs.edges for j in e if j[0] == "job"]
        self.assertIn(job1, jobs)
        self.assertIn(job2, jobs)

        # 4. add job3 connecting job2 output with c as inputs
        #    - expected:
        #    a --> job  -> b
        #                  |-> job2 -> out -> job3 -> out
        #                        ^             ^
        #                        |             |
        #                        |             |
        #                  |-----|---> job1 -> out
        #    c ------------|
        wf.add(cmd_dp, connections={job1: {"out": "input_x"}, job2: {"out": "input_y"}})
        job3 = list(wf.graph.nodes())[2]
        jobs = [j[1] for e in a.descendants_with_jobs.edges for j in e if j[0] == "job"]
        self.assertIn(job3, jobs)


@qiita_test_checker()
class ArtifactArchiveTests(TestCase):
    def test_archive(self):
        A = qdb.artifact.Artifact
        QE = qdb.exceptions.QiitaDBOperationNotPermittedError

        # check nodes, without any change
        exp_nodes = [A(1), A(2), A(3), A(4), A(5), A(6)]
        self.assertCountEqual(A(1).descendants.nodes(), exp_nodes)
        obs_artifacts = len(qdb.util.get_artifacts_information([4, 5, 6, 8]))
        self.assertEqual(4, obs_artifacts)

        # check errors
        with self.assertRaisesRegex(QE, "Only public artifacts can be archived"):
            A.archive(1)
        A(1).visibility = "public"

        with self.assertRaisesRegex(QE, "Only BIOM artifacts can be archived"):
            A.archive(1)

        A(8).visibility = "public"
        with self.assertRaisesRegex(QE, "Only non analysis artifacts can be archived"):
            A.archive(8)

        for aid in range(5, 7):
            ms = A(aid).merging_scheme
            A.archive(aid)
            self.assertEqual(ms, A(aid).merging_scheme)
            exp_nodes.remove(A(aid))
            self.assertCountEqual(A(1).descendants.nodes(), exp_nodes)

        obs_artifacts = len(qdb.util.get_artifacts_information([4, 5, 6, 8]))
        self.assertEqual(2, obs_artifacts)

        # in the tests above we generated and validated archived artifacts
        # so this allows us to add tests to delete a prep-info with archived
        # artifacts. The first bottleneck to do this is that this tests will
        # actually remove files, which we will need for other tests so lets
        # make a copy and then restore them
        mfolder = dirname(dirname(abspath(__file__)))
        mpath = join(mfolder, "support_files", "test_data")
        mp = partial(join, mpath)
        fps = [
            mp("processed_data/1_study_1001_closed_reference_otu_table.biom"),
            mp("processed_data/1_study_1001_closed_reference_otu_table_Silva.biom"),
            mp("raw_data/1_s_G1_L001_sequences.fastq.gz"),
            mp("raw_data/1_s_G1_L001_sequences_barcodes.fastq.gz"),
        ]
        for fp in fps:
            copyfile(fp, f"{fp}.bk")

        PT = qdb.metadata_template.prep_template.PrepTemplate
        QEE = qdb.exceptions.QiitaDBExecutionError
        pt = A(1).prep_templates[0]
        # it should fail as this prep is public and have been submitted to ENA
        with self.assertRaisesRegex(QEE, "Cannot remove prep template 1"):
            PT.delete(pt.id)
        # now, remove those restrictions + analysis + linked artifacts
        sql = "DELETE FROM qiita.artifact_processing_job"
        qdb.sql_connection.perform_as_transaction(sql)
        sql = "DELETE FROM qiita.ebi_run_accession"
        qdb.sql_connection.perform_as_transaction(sql)
        sql = "UPDATE qiita.artifact SET visibility_id = 1"
        qdb.sql_connection.perform_as_transaction(sql)
        qdb.analysis.Analysis.delete_analysis_artifacts(1)
        qdb.analysis.Analysis.delete_analysis_artifacts(2)
        qdb.analysis.Analysis.delete_analysis_artifacts(3)
        for aid in [3, 2, 1]:
            A.delete(aid)

        PT.delete(pt.id)

        # bringing back the filepaths
        for fp in fps:
            copyfile(f"{fp}.bk", fp)


if __name__ == "__main__":
    main()
