# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial
from json import dumps, loads
from os import close, remove
from os.path import exists, isfile, join
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from time import sleep
from unittest import TestCase, main

import pandas as pd
from biom import example_table as et
from biom.util import biom_open
from tornado.web import HTTPError

import qiita_db as qdb
from qiita_db.handlers.artifact import _get_artifact
from qiita_db.handlers.tests.oauthbase import OauthTestingBase


class UtilTests(TestCase):
    def test_get_artifact(self):
        obs = _get_artifact(1)
        exp = qdb.artifact.Artifact(1)
        self.assertEqual(obs, exp)

        # It does not exist
        with self.assertRaises(HTTPError):
            _get_artifact(100)


class ArtifactHandlerTests(OauthTestingBase):
    def setUp(self):
        super(ArtifactHandlerTests, self).setUp()

        self._clean_up_files = []

    def tearDown(self):
        super(ArtifactHandlerTests, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isfile(fp):
                    remove(fp)
                else:
                    rmtree(fp)

    def test_get_artifact_does_not_exist(self):
        obs = self.get("/qiita_db/artifacts/100/", headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get_no_header(self):
        obs = self.get("/qiita_db/artifacts/100/")
        self.assertEqual(obs.code, 400)

    def test_get_artifact(self):
        obs = self.get("/qiita_db/artifacts/1/", headers=self.header)
        self.assertEqual(obs.code, 200)
        db_test_raw_dir = qdb.util.get_mountpoint("raw_data")[0][1]
        path_builder = partial(join, db_test_raw_dir)
        exp_fps = {
            "raw_forward_seqs": [
                {"filepath": path_builder("1_s_G1_L001_sequences.fastq.gz"), "size": 58}
            ],
            "raw_barcodes": [
                {
                    "filepath": path_builder("1_s_G1_L001_sequences_barcodes.fastq.gz"),
                    "size": 58,
                }
            ],
        }
        exp = {
            "name": "Raw data 1",
            "timestamp": "2012-10-01 09:30:27",
            "visibility": "private",
            "type": "FASTQ",
            "data_type": "18S",
            "can_be_submitted_to_ebi": False,
            "ebi_run_accessions": None,
            "can_be_submitted_to_vamps": False,
            "is_submitted_to_vamps": None,
            "prep_information": [1],
            "study": 1,
            "analysis": None,
            "parents": [],
            "processing_parameters": None,
            "files": exp_fps,
        }
        self.assertEqual(loads(obs.body), exp)

        obs = self.get("/qiita_db/artifacts/9/", headers=self.header)
        self.assertEqual(obs.code, 200)
        db_test_raw_dir = qdb.util.get_mountpoint("analysis")[0][1]
        path_builder = partial(join, db_test_raw_dir)
        exp_fps = {
            "biom": [{"filepath": path_builder("1_analysis_18S.biom"), "size": 1093210}]
        }
        exp = {
            "name": "noname",
            "visibility": "sandbox",
            "type": "BIOM",
            "data_type": "18S",
            "can_be_submitted_to_ebi": False,
            "ebi_run_accessions": None,
            "can_be_submitted_to_vamps": False,
            "is_submitted_to_vamps": None,
            "prep_information": [],
            "study": None,
            "analysis": 1,
            "parents": [8],
            "processing_parameters": {
                "biom_table": "8",
                "depth": "9000",
                "subsample_multinomial": "False",
            },
            "files": exp_fps,
        }
        obs = loads(obs.body)
        # The timestamp is genreated at patch time, so we can't check for it
        del obs["timestamp"]
        self.assertEqual(obs, exp)

    def test_patch(self):
        fd, html_fp = mkstemp(suffix=".html")
        close(fd)
        self._clean_up_files.append(html_fp)
        # correct argument with a single HTML
        arguments = {"op": "add", "path": "/html_summary/", "value": html_fp}
        artifact = qdb.artifact.Artifact(1)
        self.assertIsNone(artifact.html_summary_fp)
        obs = self.patch("/qiita_db/artifacts/1/", headers=self.header, data=arguments)
        self.assertEqual(obs.code, 200)
        self.assertIsNotNone(artifact.html_summary_fp)

        # Correct argument with an HMTL and a directory
        fd, html_fp = mkstemp(suffix=".html")
        close(fd)
        self._clean_up_files.append(html_fp)
        html_dir = mkdtemp()
        self._clean_up_files.append(html_dir)
        arguments = {
            "op": "add",
            "path": "/html_summary/",
            "value": dumps({"html": html_fp, "dir": html_dir}),
        }
        obs = self.patch("/qiita_db/artifacts/1/", headers=self.header, data=arguments)
        self.assertEqual(obs.code, 200)
        self.assertIsNotNone(artifact.html_summary_fp)
        html_dir = [
            x["fp"] for x in artifact.filepaths if x["fp_type"] == "html_summary_dir"
        ]
        self.assertEqual(len(html_dir), 1)

        # Wrong operation
        arguments = {"op": "wrong", "path": "/html_summary/", "value": html_fp}
        obs = self.patch("/qiita_db/artifacts/1/", headers=self.header, data=arguments)
        self.assertEqual(obs.code, 400)
        self.assertEqual(
            obs.reason,
            'Operation "wrong" not supported. Current supported operations: add',
        )

        # Wrong path parameter
        arguments = {"op": "add", "path": "/wrong/", "value": html_fp}
        obs = self.patch("/qiita_db/artifacts/1/", headers=self.header, data=arguments)
        self.assertEqual(obs.code, 400)
        self.assertEqual(obs.reason, "Incorrect path parameter value")

        # Wrong value parameter
        arguments = {"op": "add", "path": "/html_summary/", "value": html_fp}
        obs = self.patch("/qiita_db/artifacts/1/", headers=self.header, data=arguments)
        self.assertEqual(obs.code, 500)
        self.assertIn("No such file or directory", obs.reason)


class ArtifactAPItestHandlerTests(OauthTestingBase):
    def setUp(self):
        super(ArtifactAPItestHandlerTests, self).setUp()

        metadata_dict = {
            "SKB8.640193": {
                "center_name": "ANL",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "GTCCGCAAGTTA",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "experiment_design_description": "BBBB",
            }
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient="index")
        self.prep_template = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, qdb.study.Study(1), "16S"
        )

        self._clean_up_files = []

    def tearDown(self):
        super(ArtifactAPItestHandlerTests, self).tearDown()

        for f in self._clean_up_files:
            if exists(f):
                remove(f)

    def test_post(self):
        fd, fp1 = mkstemp(suffix="_seqs.fastq")
        close(fd)
        self._clean_up_files.append(fp1)
        with open(fp1, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 1:N:0:\n"
                "NACGTAGGGTGCAAGCGTTGTCCGGAATNA\n"
                "+\n"
                "#1=DDFFFHHHHHJJJJJJJJJJJJGII#0\n"
            )

        fd, fp2 = mkstemp(suffix="_barcodes.fastq")
        close(fd)
        self._clean_up_files.append(fp2)
        with open(fp2, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 2:N:0:\n"
                "NNNCNNNNNNNNN\n"
                "+\n"
                "#############\n"
            )

        data = {
            "filepaths": dumps([(fp1, "raw_forward_seqs"), (fp2, "raw_barcodes")]),
            "type": "FASTQ",
            "name": "New test artifact",
            "prep": self.prep_template.id,
        }
        obs = self.post("/apitest/artifact/", headers=self.header, data=data)
        self.assertEqual(obs.code, 200)
        obs = loads(obs.body)
        self.assertCountEqual(obs.keys(), ["artifact"])

        a = qdb.artifact.Artifact(obs["artifact"])
        self._clean_up_files.extend([x["fp"] for x in a.filepaths])
        self.assertEqual(a.name, "New test artifact")

    def test_post_analysis(self):
        fd, fp = mkstemp(suffix="_table.biom")
        close(fd)
        with biom_open(fp, "w") as f:
            et.to_hdf5(f, "test")
        self._clean_up_files.append(fp)

        data = {
            "filepaths": dumps([(fp, "biom")]),
            "type": "BIOM",
            "name": "New biom artifact",
            "analysis": 1,
            "data_type": "16S",
        }
        obs = self.post("/apitest/artifact/", headers=self.header, data=data)
        self.assertEqual(obs.code, 200)
        obs = loads(obs.body)
        self.assertCountEqual(obs.keys(), ["artifact"])

        a = qdb.artifact.Artifact(obs["artifact"])
        self._clean_up_files.extend([x["fp"] for x in a.filepaths])
        self.assertEqual(a.name, "New biom artifact")

    def test_post_error(self):
        data = {
            "filepaths": dumps([("Do not exist", "raw_forward_seqs")]),
            "type": "FASTQ",
            "name": "New test artifact",
            "prep": 1,
        }
        obs = self.post("/apitest/artifact/", headers=self.header, data=data)
        self.assertEqual(obs.code, 500)
        self.assertIn(
            "Prep template 1 already has an artifact associated",
            obs.body.decode("ascii"),
        )


class ArtifactTypeHandlerTests(OauthTestingBase):
    def test_post_no_header(self):
        obs = self.post("/qiita_db/artifacts/types/", data={})
        self.assertEqual(obs.code, 400)

    def test_post(self):
        data = {
            "type_name": "new_type",
            "description": "some_description",
            "can_be_submitted_to_ebi": False,
            "can_be_submitted_to_vamps": False,
            "is_user_uploadable": False,
            "filepath_types": dumps([("log", False), ("raw_forward_seqs", True)]),
        }
        obs = self.post("/qiita_db/artifacts/types/", headers=self.header, data=data)
        self.assertEqual(obs.code, 200)
        self.assertIn(
            ["new_type", "some_description", False, False, False],
            qdb.artifact.Artifact.types(),
        )

        obs = self.post("/qiita_db/artifacts/types/", headers=self.header, data=data)
        self.assertEqual(obs.code, 200)

    def test_get(self):
        obs = self.get("/qiita_db/artifacts/types/", headers=self.header)
        self.assertEqual(obs.code, 200)

        basedir = qdb.util.get_db_files_base_dir()
        exp = {
            "SFF": f"{basedir}/SFF",
            "FASTA": f"{basedir}/FASTA",
            "FASTA_Sanger": f"{basedir}/FASTA_Sanger",
            "Demultiplexed": f"{basedir}/Demultiplexed",
            "FASTQ": f"{basedir}/FASTQ",
            "per_sample_FASTQ": f"{basedir}/per_sample_FASTQ",
            "BIOM": f"{basedir}/BIOM",
            "uploads": f"{basedir}/uploads",
        }
        self.assertDictEqual(loads(obs.body), exp)


class APIArtifactHandlerTests(OauthTestingBase):
    def setUp(self):
        super(APIArtifactHandlerTests, self).setUp()
        self._clean_up_files = []

    def tearDown(self):
        super(APIArtifactHandlerTests, self).tearDown()

        for f in self._clean_up_files:
            if exists(f):
                remove(f)

    def test_post(self):
        # no header
        obs = self.post("/qiita_db/artifact/", data={})
        self.assertEqual(obs.code, 400)

        fd, fp = mkstemp(suffix="_table.biom")
        close(fd)
        # renaming samples
        et.update_ids(
            {"S1": "1.SKB1.640202", "S2": "1.SKD3.640198", "S3": "1.SKM4.640180"},
            inplace=True,
        )
        with biom_open(fp, "w") as f:
            et.to_hdf5(f, "test")
        self._clean_up_files.append(fp)

        # no job_id or prep_id
        data = {
            "user_email": "demo@microbio.me",
            "artifact_type": "BIOM",
            "command_artifact_name": "OTU table",
            "files": dumps({"biom": [fp]}),
        }

        obs = self.post("/qiita_db/artifact/", headers=self.header, data=data)
        self.assertEqual(obs.code, 400)
        self.assertIn("You need to specify a job_id or a prep_id", str(obs.error))

        # both job_id and prep_id defined
        data["job_id"] = "e5609746-a985-41a1-babf-6b3ebe9eb5a9"
        data["prep_id"] = "prep_id"
        obs = self.post("/qiita_db/artifact/", headers=self.header, data=data)
        self.assertEqual(obs.code, 400)
        self.assertIn("You need to specify only a job_id or a prep_id", str(obs.error))

        # make sure that all the plugins are on
        qdb.util.activate_or_update_plugins(update=True)

        # tests success by inserting a new artifact into an existing job
        original_job = qdb.processing_job.ProcessingJob(data["job_id"])
        input_artifact = original_job.input_artifacts[0]
        original_children = input_artifact.children
        self.assertEqual(len(original_children), 3)

        # send the new data
        del data["prep_id"]
        obs = self.post("/qiita_db/artifact/", headers=self.header, data=data)
        jid = loads(obs.body)["job_id"]

        job = qdb.processing_job.ProcessingJob(jid)
        while job.status not in ("error", "success"):
            sleep(0.5)

        # now the original job should have 4 children and make sure they have
        # the same parent and parameters
        children = input_artifact.children
        new_children = list(set(children) - set(original_children))[0]
        self.assertEqual(len(children), 4)
        for c in children[1:]:
            self.assertCountEqual(
                children[0].processing_parameters.values, c.processing_parameters.values
            )
            self.assertEqual(children[0].parents, c.parents)

        # making sure the new artifact is part of the descendants, which is a
        # different method and usage than children method
        self.assertIn(new_children, input_artifact.descendants.nodes)

        # now let's test adding an artifact directly to a new prep
        new_prep = qdb.metadata_template.prep_template.PrepTemplate.create(
            pd.DataFrame(
                {
                    "new_col": {
                        "1.SKB1.640202": 1,
                        "1.SKD3.640198": 2,
                        "1.SKM4.640180": 3,
                    }
                }
            ),
            qdb.study.Study(1),
            "16S",
        )
        fd, fp = mkstemp(suffix="_table.biom")
        close(fd)
        with biom_open(fp, "w") as f:
            et.to_hdf5(f, "test")
        self._clean_up_files.append(fp)
        data = {
            "user_email": "demo@microbio.me",
            "artifact_type": "BIOM",
            "prep_id": new_prep.id,
            "files": dumps({"biom": [fp]}),
        }

        obs = self.post("/qiita_db/artifact/", headers=self.header, data=data)
        jid = loads(obs.body)["job_id"]

        job = qdb.processing_job.ProcessingJob(jid)
        while job.status not in ("error", "success"):
            sleep(0.5)
        self.assertIsNotNone(new_prep.artifact)

    def test_post_insert_artifact_and_add_default_processing(self):
        # now let's test adding an artifact + default processing to a new
        # preparation
        new_prep = qdb.metadata_template.prep_template.PrepTemplate.create(
            pd.DataFrame(
                {
                    "new_col": {
                        "1.SKB1.640202": 1,
                        "1.SKD3.640198": 2,
                        "1.SKM4.640180": 3,
                    }
                }
            ),
            qdb.study.Study(1),
            "16S",
        )

        # creating the fastq files to be added
        fd, fp1 = mkstemp(suffix="_seqs.fastq")
        close(fd)
        self._clean_up_files.append(fp1)
        with open(fp1, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 1:N:0:\n"
                "NACGTAGGGTGCAAGCGTTGTCCGGAATNA\n"
                "+\n"
                "#1=DDFFFHHHHHJJJJJJJJJJJJGII#0\n"
            )

        fd, fp2 = mkstemp(suffix="_barcodes.fastq")
        close(fd)
        self._clean_up_files.append(fp2)
        with open(fp2, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 2:N:0:\n"
                "NNNCNNNNNNNNN\n"
                "+\n"
                "#############\n"
            )

        data = {
            "user_email": "demo@microbio.me",
            "artifact_type": "FASTQ",
            "prep_id": new_prep.id,
            "files": dumps([(fp1, "raw_forward_seqs"), (fp2, "raw_barcodes")]),
            "add_default_workflow": False,
        }
        obs = self.post("/qiita_db/artifact/", headers=self.header, data=data)
        self.assertEqual(obs.code, 200)
        jid = loads(obs.body)["job_id"]
        # if we got to this point, then we should have a job and that job
        # should have children jobs (generated by the default workflow)
        job = qdb.processing_job.ProcessingJob(jid)
        children = [c.command.name for c in job.children]
        grandchildren = [gc.command.name for c in job.children for gc in c.children]
        self.assertEqual("Validate", job.command.name)
        self.assertEqual(["Split libraries FASTQ"], children)
        self.assertEqual(["Pick closed-reference OTUs"], grandchildren)

        # just to avoid any tentative issues, let's wait for the main job to
        # finish
        while job.status not in ("error", "success"):
            sleep(0.5)


if __name__ == "__main__":
    main()
