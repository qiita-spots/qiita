# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from datetime import datetime
from functools import partial
from os import close, remove
from os.path import exists, join
from tempfile import mkstemp
from unittest import TestCase, main

import numpy.testing as npt
import pandas as pd

from qiita_core.qiita_settings import r_client
from qiita_core.testing import wait_for_prep_information_job
from qiita_core.util import qiita_test_checker
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBWarning
from qiita_db.logger import LogEntry
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.software import DefaultParameters, Parameters
from qiita_db.study import Study
from qiita_db.util import get_mountpoint
from qiita_pet.handlers.api_proxy.artifact import (
    artifact_get_info,
    artifact_get_prep_req,
    artifact_get_req,
    artifact_graph_get_req,
    artifact_post_req,
    artifact_status_put_req,
    artifact_types_get_req,
)


class TestArtifactAPIReadOnly(TestCase):
    def test_artifact_get_req_no_access(self):
        obs = artifact_get_req("demo@microbio.me", 1)
        exp = {"status": "error", "message": "User has insufficient permissions"}
        self.assertEqual(obs, exp)

    def test_artifact_get_req(self):
        obs = artifact_get_req("test@foo.bar", 1)
        path_builder = partial(join, get_mountpoint("raw_data")[0][1])
        exp = {
            "id": 1,
            "type": "FASTQ",
            "study": 1,
            "data_type": "18S",
            "timestamp": datetime(2012, 10, 1, 9, 30, 27),
            "visibility": "private",
            "can_submit_vamps": False,
            "can_submit_ebi": False,
            "processing_parameters": None,
            "ebi_run_accessions": None,
            "is_submitted_vamps": False,
            "parents": [],
            "filepaths": [
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
            ],
        }
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_ancestors(self):
        obs = artifact_graph_get_req(1, "ancestors", "test@foo.bar")
        exp = {
            "status": "success",
            "message": "",
            "edge_list": [],
            "node_labels": [(1, "Raw data 1 - FASTQ")],
        }
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_descendants(self):
        obs = artifact_graph_get_req(1, "descendants", "test@foo.bar")
        exp = {
            "status": "success",
            "message": "",
            "node_labels": [
                (1, "Raw data 1 - FASTQ"),
                (3, "Demultiplexed 2 - Demultiplexed"),
                (2, "Demultiplexed 1 - Demultiplexed"),
                (4, "BIOM - BIOM"),
                (5, "BIOM - BIOM"),
                (6, "BIOM - BIOM"),
            ],
            "edge_list": [(1, 3), (1, 2), (2, 5), (2, 4), (2, 6)],
        }
        self.assertEqual(obs["message"], exp["message"])
        self.assertEqual(obs["status"], exp["status"])
        self.assertCountEqual(obs["node_labels"], exp["node_labels"])
        self.assertCountEqual(obs["edge_list"], exp["edge_list"])

    def test_artifact_graph_get_req_no_access(self):
        obs = artifact_graph_get_req(1, "ancestors", "demo@microbio.me")
        exp = {"status": "error", "message": "User has insufficient permissions"}
        self.assertEqual(obs, exp)

    def test_artifact_graph_get_req_bad_direction(self):
        obs = artifact_graph_get_req(1, "WRONG", "test@foo.bar")
        exp = {"status": "error", "message": "Unknown directon WRONG"}
        self.assertEqual(obs, exp)

    def test_artifact_types_get_req(self):
        obs = artifact_types_get_req()
        exp = {
            "message": "",
            "status": "success",
            "types": [
                ["BIOM", "BIOM table", False, False, True],
                ["Demultiplexed", "Demultiplexed and QC sequences", True, True, False],
                ["FASTA", None, False, False, False],
                ["FASTA_Sanger", None, False, False, False],
                ["FASTQ", None, False, False, True],
                ["SFF", None, False, False, False],
                [
                    "beta_div_plots",
                    "Qiime 1 beta diversity results",
                    False,
                    False,
                    False,
                ],
                ["per_sample_FASTQ", None, True, False, True],
                ["rarefaction_curves", "Rarefaction curves", False, False, False],
                ["taxa_summary", "Taxa summary plots", False, False, False],
            ],
        }

        self.assertEqual(obs["message"], exp["message"])
        self.assertEqual(obs["status"], exp["status"])
        self.assertCountEqual(obs["types"], exp["types"])


@qiita_test_checker()
class TestArtifactAPI(TestCase):
    def setUp(self):
        uploads_path = get_mountpoint("uploads")[0][1]
        # Create prep test file to point at
        self.update_fp = join(uploads_path, "1", "update.txt")
        with open(self.update_fp, "w") as f:
            f.write("""sample_name\tnew_col\n1.SKD6.640190\tnew_value\n""")

        self._files_to_remove = [self.update_fp]
        self._files_to_remove = []

        # creating temporal files and artifact
        # NOTE: we don't need to remove the artifact created cause it's
        # used to test the delete functionality
        fd, fp = mkstemp(suffix="_seqs.fna")
        close(fd)
        with open(fp, "w") as f:
            f.write(
                ">1.sid_r4_0 M02034:17:000000000-A5U18:1:1101:15370:1394 "
                "1:N:0:1 orig_bc=CATGAGCT new_bc=CATGAGCT bc_diffs=0\n"
                "GTGTGCCAGCAGCCGCGGTAATACGTAGGG\n"
            )
        # 4 Demultiplexed
        filepaths_processed = [(fp, 4)]
        # 1 for default parameters and input data
        exp_params = Parameters.from_default_params(
            DefaultParameters(1), {"input_data": 1}
        )
        self.artifact = Artifact.create(
            filepaths_processed,
            "Demultiplexed",
            parents=[Artifact(1)],
            processing_parameters=exp_params,
        )

    def tearDown(self):
        for fp in self._files_to_remove:
            if exists(fp):
                remove(fp)

        # Replace file if removed as part of function testing
        uploads_path = get_mountpoint("uploads")[0][1]
        fp = join(uploads_path, "1", "uploaded_file.txt")
        if not exists(fp):
            with open(fp, "w") as f:
                f.write("")

        r_client.flushdb()

    def test_artifact_get_prep_req(self):
        obs = artifact_get_prep_req("test@foo.bar", [4])
        exp = {
            "status": "success",
            "msg": "",
            "data": {
                4: [
                    "1.SKB1.640202",
                    "1.SKB2.640194",
                    "1.SKB3.640195",
                    "1.SKB4.640189",
                    "1.SKB5.640181",
                    "1.SKB6.640176",
                    "1.SKB7.640196",
                    "1.SKB8.640193",
                    "1.SKB9.640200",
                    "1.SKD1.640179",
                    "1.SKD2.640178",
                    "1.SKD3.640198",
                    "1.SKD4.640185",
                    "1.SKD5.640186",
                    "1.SKD6.640190",
                    "1.SKD7.640191",
                    "1.SKD8.640184",
                    "1.SKD9.640182",
                    "1.SKM1.640183",
                    "1.SKM2.640199",
                    "1.SKM3.640197",
                    "1.SKM4.640180",
                    "1.SKM5.640177",
                    "1.SKM6.640187",
                    "1.SKM7.640188",
                    "1.SKM8.640201",
                    "1.SKM9.640192",
                ]
            },
        }
        self.assertEqual(obs, exp)

        obs = artifact_get_prep_req("demo@microbio.me", [4])
        exp = {"status": "error", "message": "User has insufficient permissions"}
        self.assertEqual(obs, exp)

    def test_artifact_get_info(self):
        obs = artifact_get_info("test@foo.bar", [5, 6, 7])
        data = [
            {
                "files": ["1_study_1001_closed_reference_otu_table_Silva.biom"],
                "artifact_id": 6,
                "data_type": "16S",
                "timestamp": "2012-10-02 17:30:00",
                "active": True,
                "target_gene": "16S rRNA",
                "name": "BIOM",
                "target_subfragment": ["V4"],
                "parameters": {
                    "reference": "2",
                    "similarity": "0.97",
                    "sortmerna_e_value": "1",
                    "sortmerna_max_pos": "10000",
                    "threads": "1",
                    "sortmerna_coverage": "0.97",
                },
                "algorithm": "Pick closed-reference OTUs | Split libraries FASTQ",
                "deprecated": False,
                "platform": "Illumina",
                "algorithm_az": "d480799a0a7a2fbe0e9022bc9c602018",
                "prep_samples": 27,
            },
            {
                "files": ["1_study_1001_closed_reference_otu_table.biom"],
                "artifact_id": 5,
                "data_type": "18S",
                "timestamp": "2012-10-02 17:30:00",
                "active": True,
                "target_gene": "16S rRNA",
                "name": "BIOM",
                "target_subfragment": ["V4"],
                "parameters": {
                    "reference": "1",
                    "similarity": "0.97",
                    "sortmerna_e_value": "1",
                    "sortmerna_max_pos": "10000",
                    "threads": "1",
                    "sortmerna_coverage": "0.97",
                },
                "algorithm": "Pick closed-reference OTUs | Split libraries FASTQ",
                "deprecated": False,
                "platform": "Illumina",
                "algorithm_az": "d480799a0a7a2fbe0e9022bc9c602018",
                "prep_samples": 27,
            },
            {
                "files": ["biom_table.biom"],
                "artifact_id": 7,
                "data_type": "16S",
                "timestamp": "2012-10-02 17:30:00",
                "active": True,
                "target_gene": "16S rRNA",
                "name": "BIOM",
                "target_subfragment": ["V4"],
                "parameters": {},
                "algorithm": "",
                "deprecated": False,
                "platform": "Illumina",
                "algorithm_az": "",
                "prep_samples": 27,
            },
        ]
        exp = {"status": "success", "msg": "", "data": data}
        self.assertCountEqual(list(obs.keys()), exp.keys())
        self.assertEqual(obs["status"], exp["status"])
        self.assertEqual(obs["msg"], exp["msg"])
        self.assertCountEqual(obs["data"], exp["data"])

    def test_artifact_post_req(self):
        # Create new prep template to attach artifact to
        pt = npt.assert_warns(
            QiitaDBWarning,
            PrepTemplate.create,
            pd.DataFrame({"new_col": {"1.SKD6.640190": 1}}),
            Study(1),
            "16S",
        )
        self._files_to_remove.extend([fp for _, fp in pt.get_filepaths()])

        filepaths = {
            "raw_forward_seqs": "uploaded_file.txt",
            "raw_barcodes": "update.txt",
        }
        obs = artifact_post_req(
            "test@foo.bar", filepaths, "FASTQ", "New Test Artifact", pt.id
        )
        exp = {"status": "success", "message": ""}
        self.assertEqual(obs, exp)
        wait_for_prep_information_job(pt.id)

        # Test importing an artifact
        # Create new prep template to attach artifact to
        pt = npt.assert_warns(
            QiitaDBWarning,
            PrepTemplate.create,
            pd.DataFrame({"new_col": {"1.SKD6.640190": 1}}),
            Study(1),
            "16S",
        )
        self._files_to_remove.extend([fp for _, fp in pt.get_filepaths()])

        obs = artifact_post_req(
            "test@foo.bar", {}, "Demultiplexed", "New Test Artifact 2", pt.id, 3
        )
        exp = {"status": "success", "message": ""}
        self.assertEqual(obs, exp)

        wait_for_prep_information_job(pt.id)
        # Instantiate the artifact to make sure it was made and
        # to clean the environment
        a = Artifact(pt.artifact.id)
        self._files_to_remove.extend([x["fp"] for x in a.filepaths])

    def test_artifact_post_req_error(self):
        # Create a new prep template to attach the artifact to
        pt = npt.assert_warns(
            QiitaDBWarning,
            PrepTemplate.create,
            pd.DataFrame({"new_col": {"1.SKD6.640190": 1}}),
            Study(1),
            "16S",
        )
        self._files_to_remove.extend([fp for _, fp in pt.get_filepaths()])

        user_id = "test@foo.bar"
        filepaths = {
            "raw_barcodes": "uploaded_file.txt",
            "raw_forward_seqs": "update.txt",
        }
        artifact_type = "FASTQ"
        name = "TestArtifact"

        # The user doesn't have access to the study
        obs = artifact_post_req(
            "demo@microbio.me", filepaths, artifact_type, name, pt.id
        )
        exp = {"status": "error", "message": "User has insufficient permissions"}
        self.assertEqual(obs, exp)

        # A file does not exist
        missing_fps = {"raw_barcodes": "NOTEXISTS"}
        obs = artifact_post_req(user_id, missing_fps, artifact_type, name, pt.id)
        exp = {"status": "error", "message": "File does not exist: NOTEXISTS"}
        self.assertEqual(obs, exp)

        # Cleaned filepaths is empty
        empty_fps = {"raw_barcodes": "", "raw_forward_seqs": ""}
        obs = artifact_post_req(user_id, empty_fps, artifact_type, name, pt.id)
        exp = {
            "status": "error",
            "message": "Can't create artifact, no files provided.",
        }
        self.assertEqual(obs, exp)

    def test_artifact_status_put_req(self):
        obs = artifact_status_put_req(1, "test@foo.bar", "sandbox")
        exp = {"status": "success", "message": "Artifact visibility changed to sandbox"}
        self.assertEqual(obs, exp)

    def test_artifact_status_put_req_private(self):
        obs = artifact_status_put_req(1, "admin@foo.bar", "private")
        exp = {"status": "success", "message": "Artifact visibility changed to private"}
        self.assertEqual(obs, exp)
        # testing that the log message is generated
        self.assertEqual(
            LogEntry.newest_records(1)[0].msg,
            "admin@foo.bar changed artifact 1 (study 1) to private",
        )

    def test_artifact_status_put_req_private_bad_permissions(self):
        obs = artifact_status_put_req(1, "test@foo.bar", "private")
        exp = {
            "status": "error",
            "message": "User does not have permissions to approve change",
        }
        self.assertEqual(obs, exp)

    def test_artifact_status_put_req_no_access(self):
        obs = artifact_status_put_req(1, "demo@microbio.me", "sandbox")
        exp = {"status": "error", "message": "User has insufficient permissions"}
        self.assertEqual(obs, exp)

    def test_artifact_status_put_req_unknown_status(self):
        obs = artifact_status_put_req(1, "test@foo.bar", "BADSTAT")
        exp = {"status": "error", "message": "Unknown visibility value: BADSTAT"}
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    main()
