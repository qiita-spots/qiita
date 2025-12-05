# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import dumps, loads
from os import close, environ, remove
from os.path import abspath, dirname, exists, isdir, join
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from time import sleep, time
from unittest import TestCase, main

import numpy.testing as npt
import pandas as pd
from biom import example_table as et
from biom.util import biom_open
from h5py import File
from qiita_files.demux import to_hdf5

from qiita_core.qiita_settings import r_client
from qiita_core.util import qiita_test_checker
from qiita_db.analysis import Analysis
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBUnknownIDError, QiitaDBWarning
from qiita_db.logger import LogEntry
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Command, DefaultParameters, Parameters, Software
from qiita_db.sql_connection import TRN
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.util import get_count
from qiita_ware.private_plugin import private_task
from qiita_ware.test.test_ebi import FASTA_EXAMPLE


class BaseTestPrivatePlugin(TestCase):
    def _create_job(self, cmd_name, values_dict):
        self.user = User("test@foo.bar")
        qiita_plugin = Software.from_name_and_version("Qiita", "alpha")
        cmd = qiita_plugin.get_command(cmd_name)
        params = Parameters.load(cmd, values_dict=values_dict)
        job = ProcessingJob.create(self.user, params, True)
        job._set_status("queued")
        return job

    def setUp(self):
        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            if exists(f):
                if isdir(f):
                    rmtree(f)
                else:
                    remove(f)

        r_client.flushdb()


@qiita_test_checker()
class TestPrivatePlugin(BaseTestPrivatePlugin):
    def setUp(self):
        fd, self.fp = mkstemp(suffix=".txt")
        close(fd)
        with open(self.fp, "w") as f:
            f.write("sample_name\tnew_col\n1.SKD6.640190\tnew_vale")

        self.temp_dir = mkdtemp()
        self._clean_up_files = [self.fp, self.temp_dir]

    def test_copy_artifact(self):
        # Failure test
        job = self._create_job("copy_artifact", {"artifact": 1, "prep_template": 1})

        private_task(job.id)
        self.assertEqual(job.status, "error")
        self.assertIn("Prep template 1 already has an artifact associated", job.log.msg)

        # Success test
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
        metadata = pd.DataFrame.from_dict(metadata_dict, orient="index", dtype=str)
        prep = PrepTemplate.create(metadata, Study(1), "16S")
        job = self._create_job(
            "copy_artifact", {"artifact": 1, "prep_template": prep.id}
        )
        private_task(job.id)
        self.assertEqual(job.status, "success")

    def test_delete_artifact(self):
        job = self._create_job("delete_artifact", {"artifact": 1})
        private_task(job.id)
        self.assertEqual(job.status, "error")
        obs = job.log.msg
        exp = "Cannot delete artifact 1: it or one of its children has been analyzed by"
        self.assertIn(exp, obs)

        job = self._create_job("delete_artifact", {"artifact": 3})
        private_task(job.id)
        self.assertEqual(job.status, "success")
        with self.assertRaises(QiitaDBUnknownIDError):
            Artifact(3)

    def test_create_sample_template(self):
        # Test error
        job = self._create_job(
            "create_sample_template",
            {"fp": self.fp, "study_id": 1, "is_mapping_file": False, "data_type": None},
        )
        private_task(job.id)
        self.assertEqual(job.status, "error")
        self.assertIn(
            "The 'SampleTemplate' object with attributes (id: 1) already exists.",
            job.log.msg,
        )

        # Test success with a warning
        info = {
            "timeseries_type_id": "1",
            "metadata_complete": "true",
            "mixs_compliant": "true",
            "study_alias": "TDST",
            "study_description": "Test create sample template",
            "study_abstract": "Test create sample template",
            "principal_investigator_id": StudyPerson(1),
        }
        study = Study.create(User("test@foo.bar"), "Create Sample Template test", info)
        job = self._create_job(
            "create_sample_template",
            {
                "fp": self.fp,
                "study_id": study.id,
                "is_mapping_file": False,
                "data_type": None,
            },
        )
        private_task(job.id)
        self.assertEqual(job.status, "success")
        obs = r_client.get("sample_template_%d" % study.id)
        self.assertIsNotNone(obs)
        obs = loads(obs)
        self.assertCountEqual(obs, ["job_id", "alert_type", "alert_msg"])
        self.assertEqual(obs["job_id"], job.id)
        self.assertEqual(obs["alert_type"], "warning")
        self.assertIn(
            "Some functionality will be disabled due to missing columns:",
            obs["alert_msg"],
        )
        # making sure that the error name is not in the messages
        self.assertNotIn("QiitaDBWarning", obs["alert_msg"])

    def test_create_sample_template_nonutf8(self):
        fp = join(dirname(abspath(__file__)), "test_data", "sample_info_utf8_error.txt")
        job = self._create_job(
            "create_sample_template",
            {"fp": fp, "study_id": 1, "is_mapping_file": False, "data_type": None},
        )
        private_task(job.id)
        self.assertEqual(job.status, "error")
        self.assertIn(
            "The 'SampleTemplate' object with attributes (id: 1) already exists.",
            job.log.msg,
        )

    def test_update_sample_template(self):
        fd, fp = mkstemp(suffix=".txt")
        close(fd)
        with open(fp, "w") as f:
            f.write("sample_name\tnew_col\n1.SKD6.640190\tnew_value")
        self._clean_up_files.append(fp)

        job = self._create_job(
            "update_sample_template", {"study": 1, "template_fp": fp}
        )
        private_task(job.id)
        self.assertEqual(job.status, "success")
        self.assertEqual(SampleTemplate(1)["1.SKD6.640190"]["new_col"], "new_value")
        obs = r_client.get("sample_template_1")
        self.assertIsNotNone(obs)
        obs = loads(obs)
        self.assertCountEqual(obs, ["job_id", "alert_type", "alert_msg"])
        self.assertEqual(obs["job_id"], job.id)
        self.assertEqual(obs["alert_type"], "warning")
        self.assertIn(
            "The following columns have been added to the existing template: new_col",
            obs["alert_msg"],
        )
        # making sure that the error name is not in the messages
        self.assertNotIn("QiitaDBWarning", obs["alert_msg"])

    def test_delete_sample_template(self):
        # Error case
        job = self._create_job("delete_sample_template", {"study": 1})
        private_task(job.id)
        self.assertEqual(job.status, "error")
        self.assertIn(
            "Sample template cannot be erased because there are "
            "prep templates associated",
            job.log.msg,
        )

        # Success case
        info = {
            "timeseries_type_id": "1",
            "metadata_complete": "true",
            "mixs_compliant": "true",
            "study_alias": "TDST",
            "study_description": "Test delete sample template",
            "study_abstract": "Test delete sample template",
            "principal_investigator_id": StudyPerson(1),
        }
        study = Study.create(User("test@foo.bar"), "Delete Sample Template test", info)
        metadata = pd.DataFrame.from_dict(
            {
                "Sample1": {
                    "physical_specimen_location": "location1",
                    "physical_specimen_remaining": "true",
                    "dna_extracted": "true",
                    "sample_type": "type1",
                    "collection_timestamp": "2014-05-29 12:24:15",
                    "host_subject_id": "NotIdentified",
                    "Description": "Test Sample 1",
                    "latitude": "42.42",
                    "longitude": "41.41",
                    "taxon_id": "9606",
                    "scientific_name": "homo sapiens",
                }
            },
            orient="index",
            dtype=str,
        )
        SampleTemplate.create(metadata, study)

        job = self._create_job("delete_sample_template", {"study": study.id})
        private_task(job.id)
        self.assertEqual(job.status, "success")
        self.assertFalse(SampleTemplate.exists(study.id))

    def test_update_prep_template(self):
        fd, fp = mkstemp(suffix=".txt")
        close(fd)
        with open(fp, "w") as f:
            f.write("sample_name\tnew_col\n1.SKD6.640190\tnew_value")
        job = self._create_job(
            "update_prep_template", {"prep_template": 1, "template_fp": fp}
        )
        private_task(job.id)
        self.assertEqual(job.status, "success")
        self.assertEqual(PrepTemplate(1)["1.SKD6.640190"]["new_col"], "new_value")
        obs = r_client.get("prep_template_1")
        self.assertIsNotNone(obs)
        obs = loads(obs)
        self.assertCountEqual(obs, ["job_id", "alert_type", "alert_msg"])
        self.assertEqual(obs["job_id"], job.id)
        self.assertEqual(obs["alert_type"], "warning")
        self.assertIn(
            "The following columns have been added to the existing template: new_col",
            obs["alert_msg"],
        )
        # making sure that the error name is not in the messages
        self.assertNotIn("QiitaDBWarning", obs["alert_msg"])

    # This is a long test but it includes the 3 important cases that need
    # to be tested on this function (job success, job error, and internal error
    # when completing the job)
    def test_complete_job(self):
        # Complete success
        pt = npt.assert_warns(
            QiitaDBWarning,
            PrepTemplate.create,
            pd.DataFrame({"new_col": {"1.SKD6.640190": 1}}),
            Study(1),
            "16S",
        )
        c_job = ProcessingJob.create(
            User("test@foo.bar"),
            Parameters.load(
                Command.get_validator("BIOM"),
                values_dict={
                    "template": pt.id,
                    "files": dumps({"BIOM": ["file"]}),
                    "artifact_type": "BIOM",
                },
            ),
            True,
        )
        c_job._set_status("running")
        fd, fp = mkstemp(suffix="_table.biom")
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        self._clean_up_files.append(fp)
        exp_artifact_count = get_count("qiita.artifact") + 1

        # the main job (c_job) is still not completing so the step hasn't been
        # updated since creation === None
        self.assertIsNone(c_job.step)

        payload = dumps(
            {
                "success": True,
                "error": "",
                "artifacts": {
                    "OTU table": {"filepaths": [(fp, "biom")], "artifact_type": "BIOM"}
                },
            }
        )
        job = self._create_job("complete_job", {"job_id": c_job.id, "payload": payload})
        private_task(job.id)

        # the complete job has started so now the step of c_job should report
        # the complete information
        self.assertEqual(c_job.step, f"Completing via {job.id} [Not Available]")

        self.assertEqual(job.status, "success")
        self.assertEqual(c_job.status, "success")
        self.assertEqual(get_count("qiita.artifact"), exp_artifact_count)

        # Complete job error
        payload = dumps({"success": False, "error": "Job failure"})
        job = self._create_job(
            "complete_job",
            {"job_id": "bcc7ebcd-39c1-43e4-af2d-822e3589f14d", "payload": payload},
        )
        private_task(job.id)
        self.assertEqual(job.status, "success")
        c_job = ProcessingJob("bcc7ebcd-39c1-43e4-af2d-822e3589f14d")
        self.assertEqual(c_job.status, "error")
        self.assertEqual(c_job.log, LogEntry.newest_records(numrecords=1)[0])
        self.assertEqual(c_job.log.msg, "Job failure")

        # Complete internal error
        pt = npt.assert_warns(
            QiitaDBWarning,
            PrepTemplate.create,
            pd.DataFrame({"new_col": {"1.SKD6.640190": 1}}),
            Study(1),
            "16S",
        )
        c_job = ProcessingJob.create(
            User("test@foo.bar"),
            Parameters.load(
                Command.get_validator("BIOM"),
                values_dict={
                    "template": pt.id,
                    "files": dumps({"BIOM": ["file"]}),
                    "artifact_type": "BIOM",
                },
            ),
            True,
        )
        c_job._set_status("running")
        fp = "/surprised/if/this/path/exists.biom"
        payload = dumps(
            {
                "success": True,
                "error": "",
                "artifacts": {
                    "OTU table": {"filepaths": [(fp, "biom")], "artifact_type": "BIOM"}
                },
            }
        )
        job = self._create_job("complete_job", {"job_id": c_job.id, "payload": payload})
        private_task(job.id)
        self.assertEqual(job.status, "success")
        self.assertEqual(c_job.status, "error")
        self.assertIn("No such file or directory", c_job.log.msg)

    def test_submit_to_EBI(self):
        # setting up test
        fna_fp = join(self.temp_dir, "seqs.fna")
        demux_fp = join(self.temp_dir, "demux.seqs")
        with open(fna_fp, "w") as f:
            f.write(FASTA_EXAMPLE)
        with File(demux_fp, "w") as f:
            to_hdf5(fna_fp, f)

        pt = PrepTemplate(1)
        params = Parameters.from_default_params(
            DefaultParameters(1), {"input_data": pt.artifact.id}
        )
        artifact = Artifact.create(
            [(demux_fp, 6)],
            "Demultiplexed",
            parents=[pt.artifact],
            processing_parameters=params,
        )

        # submit job
        job = self._create_job(
            "submit_to_EBI", {"artifact": artifact.id, "submission_type": "VALIDATE"}
        )
        job._set_status("in_construction")
        job.submit()

        # wait for the job to fail, and check that the status is submitting
        checked_submitting = True
        while job.status != "error":
            if checked_submitting:
                self.assertEqual("submitting", artifact.study.ebi_submission_status)
                checked_submitting = False
        # once it fails wait for a few to check status again
        sleep(5)
        exp = "Some artifact submissions failed: %d" % artifact.id
        obs = artifact.study.ebi_submission_status
        self.assertEqual(obs, exp)
        # make sure that the error is correct, we have 2 options
        if environ.get("ASPERA_SCP_PASS", "") != "":
            self.assertIn("1.SKM2.640199", job.log.msg)
        else:
            self.assertIn("ASCP Error:", job.log.msg)
        # wait for everything to finish to avoid DB deadlocks
        sleep(5)

    def test_build_analysis_files(self):
        job = self._create_job(
            "build_analysis_files",
            {"analysis": 3, "merge_dup_sample_ids": True, "categories": None},
        )

        # testing shape and get_resource_allocation_info as
        # build_analysis_files is a special case
        def _set_allocation(memory):
            with TRN:
                sql = """UPDATE qiita.processing_job_resource_allocation
                         SET allocation = '{0}'
                         WHERE name = 'build_analysis_files'""".format(
                    "-p qiita --mem %s" % memory
                )
                TRN.add(sql)
                TRN.execute()

        self.assertEqual(job.shape, (4, None, 1256812))
        self.assertEqual(
            job.resource_allocation_info,
            "-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00 --nice=10000",
        )
        _set_allocation("{samples}*1000")
        self.assertEqual(job.resource_allocation_info, "-p qiita --mem 4K --nice=10000")
        _set_allocation("{columns}*1000")
        self.assertEqual(job.resource_allocation_info, "Not valid")
        self.assertEqual(job.status, "error")
        self.assertEqual(
            job.log.msg, "Obvious incorrect allocation. Please contact foo@bar.com"
        )

        # now let's test something that will cause not a number input_size*N
        job = self._create_job(
            "build_analysis_files",
            {"analysis": 3, "merge_dup_sample_ids": True, "categories": None},
        )
        _set_allocation("{input_size}*N")
        self.assertEqual(job.resource_allocation_info, "Not valid")
        self.assertEqual(job.status, "error")
        self.assertEqual(
            job.log.msg, "Obvious incorrect allocation. Please contact foo@bar.com"
        )

        # now let's test something that will return a negative number -samples
        job = self._create_job(
            "build_analysis_files",
            {"analysis": 3, "merge_dup_sample_ids": True, "categories": None},
        )
        _set_allocation("-{samples}")
        self.assertEqual(job.resource_allocation_info, "Not valid")
        self.assertEqual(job.status, "error")
        self.assertEqual(
            job.log.msg, "Obvious incorrect allocation. Please contact foo@bar.com"
        )

        # now let's test a full build_analysis_files job
        job = self._create_job(
            "build_analysis_files",
            {"analysis": 3, "merge_dup_sample_ids": True, "categories": None},
        )
        job._set_status("in_construction")
        job.submit()

        while job.status not in ("error", "success"):
            sleep(0.5)

        self.assertEqual(job.status, "error")
        self.assertIn("1 validator jobs failed", job.log.msg)


@qiita_test_checker()
class TestPrivatePluginDeleteStudy(BaseTestPrivatePlugin):
    def test_delete_study(self):
        # as samples have been submitted to EBI, this will fail
        job = self._create_job("delete_study", {"study": 1})
        private_task(job.id)
        self.assertEqual(job.status, "error")
        self.assertIn("Artifact 2 has been submitted to EBI", job.log.msg)
        # making sure the analysis, first thing to delete, still exists
        self.assertTrue(Analysis.exists(1))

        info = {
            "timeseries_type_id": "1",
            "metadata_complete": "true",
            "mixs_compliant": "true",
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
            "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
            "gut microbiome",
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1),
        }
        new_study = Study.create(
            User("test@foo.bar"), "Fried Chicken Microbiome %s" % time(), info
        )

        # adding tags
        new_study.update_tags(User("test@foo.bar"), ["my new tag!"])

        # creating a sample information file
        metadata = pd.DataFrame.from_dict(
            {
                "Sample1": {
                    "physical_specimen_location": "location1",
                    "taxon_id": "9606",
                    "scientific_name": "homo sapiens",
                },
                "Sample2": {
                    "physical_specimen_location": "location1",
                    "taxon_id": "9606",
                    "scientific_name": "homo sapiens",
                },
                "Sample3": {
                    "physical_specimen_location": "location1",
                    "taxon_id": "9606",
                    "scientific_name": "homo sapiens",
                },
            },
            orient="index",
        )
        SampleTemplate.create(metadata, new_study)
        # creating a preparation information file
        metadata = pd.DataFrame.from_dict(
            {
                "Sample1": {
                    "center_name": "ANL",
                    "target_subfragment": "V4",
                    "center_project_name": "Test Project",
                }
            },
            orient="index",
            dtype=str,
        )
        PrepTemplate.create(metadata, new_study, "16S")

        job = self._create_job("delete_study", {"study": new_study.id})
        private_task(job.id)
        self.assertEqual(job.status, "success")

        # making sure the study doesn't exist
        with self.assertRaises(QiitaDBUnknownIDError):
            Study(new_study.id)


@qiita_test_checker()
class TestPrivatePluginDeleteAnalysis(BaseTestPrivatePlugin):
    def test_delete_analysis(self):
        # adding extra filepaths to make sure the delete works as expected, we
        # basically want 8 -> 9 -> 10 -> 12 -> 14
        #                       -> 11 -> 13
        fd, fp10 = mkstemp(suffix="_table.biom")
        close(fd)
        fd, fp11 = mkstemp(suffix="_table.biom")
        close(fd)
        fd, fp12 = mkstemp(suffix="_table.biom")
        close(fd)
        fd, fp13 = mkstemp(suffix="_table.biom")
        close(fd)
        fd, fp14 = mkstemp(suffix="_table.biom")
        close(fd)
        with biom_open(fp10, "w") as f:
            et.to_hdf5(f, "test")
        with biom_open(fp11, "w") as f:
            et.to_hdf5(f, "test")
        with biom_open(fp12, "w") as f:
            et.to_hdf5(f, "test")
        with biom_open(fp13, "w") as f:
            et.to_hdf5(f, "test")
        with biom_open(fp14, "w") as f:
            et.to_hdf5(f, "test")
        self._clean_up_files.extend([fp10, fp11, fp12, fp13, fp14])

        # copying some processing parameters
        a9 = Artifact(9)
        pp = a9.processing_parameters

        # 7: BIOM
        a10 = Artifact.create(
            [(fp10, 7)], "BIOM", parents=[a9], processing_parameters=pp
        )
        a11 = Artifact.create(
            [(fp11, 7)], "BIOM", parents=[a9], processing_parameters=pp
        )
        a12 = Artifact.create(
            [(fp12, 7)], "BIOM", parents=[a10], processing_parameters=pp
        )
        Artifact.create([(fp13, 7)], "BIOM", parents=[a11], processing_parameters=pp)
        Artifact.create([(fp14, 7)], "BIOM", parents=[a12], processing_parameters=pp)

        job = self._create_job("delete_analysis", {"analysis_id": 1})
        private_task(job.id)
        self.assertEqual(job.status, "success")
        with self.assertRaises(QiitaDBUnknownIDError):
            Analysis(1)


@qiita_test_checker()
class TestPrivatePluginDeleteTests(BaseTestPrivatePlugin):
    def test_delete_sample_or_column(self):
        st = SampleTemplate(1)

        # Delete a sample template column
        job = self._create_job(
            "delete_sample_or_column",
            {
                "obj_class": "SampleTemplate",
                "obj_id": 1,
                "sample_or_col": "columns",
                "name": "season_environment",
            },
        )
        private_task(job.id)
        self.assertEqual(job.status, "success")
        self.assertNotIn("season_environment", st.categories)

        # Delete a sample template sample - need to add one
        # sample that we will remove
        npt.assert_warns(
            QiitaDBWarning,
            st.extend,
            pd.DataFrame.from_dict(
                {"Sample1": {"taxon_id": "9606"}}, orient="index", dtype=str
            ),
        )
        self.assertIn("1.Sample1", st.keys())
        job = self._create_job(
            "delete_sample_or_column",
            {
                "obj_class": "SampleTemplate",
                "obj_id": 1,
                "sample_or_col": "samples",
                "name": "1.Sample1",
            },
        )
        private_task(job.id)
        self.assertEqual(job.status, "success")
        self.assertNotIn("1.Sample1", st.keys())

        # Delete a prep template column
        pt = PrepTemplate(1)
        job = self._create_job(
            "delete_sample_or_column",
            {
                "obj_class": "PrepTemplate",
                "obj_id": 1,
                "sample_or_col": "columns",
                "name": "target_subfragment",
            },
        )
        private_task(job.id)
        self.assertEqual(job.status, "success")
        self.assertNotIn("target_subfragment", pt.categories)

        # Delete a prep template sample
        metadata = pd.DataFrame.from_dict(
            {
                "1.SKB8.640193": {
                    "barcode": "GTCCGCAAGTTA",
                    "primer": "GTGCCAGCMGCCGCGGTAA",
                },
                "1.SKD8.640184": {
                    "barcode": "CGTAGAGCTCTC",
                    "primer": "GTGCCAGCMGCCGCGGTAA",
                },
            },
            orient="index",
            dtype=str,
        )
        pt = npt.assert_warns(
            QiitaDBWarning, PrepTemplate.create, metadata, Study(1), "16S"
        )
        job = self._create_job(
            "delete_sample_or_column",
            {
                "obj_class": "PrepTemplate",
                "obj_id": pt.id,
                "sample_or_col": "samples",
                "name": "1.SKD8.640184",
            },
        )
        private_task(job.id)
        self.assertNotIn("1.SKD8.640184", pt.keys())

        # Test exceptions
        job = self._create_job(
            "delete_sample_or_column",
            {
                "obj_class": "UnknownClass",
                "obj_id": 1,
                "sample_or_col": "columns",
                "name": "column",
            },
        )
        private_task(job.id)
        self.assertEqual(job.status, "error")
        self.assertIn(
            'Unknown value "UnknownClass". Choose between '
            '"SampleTemplate" and "PrepTemplate"',
            job.log.msg,
        )

        job = self._create_job(
            "delete_sample_or_column",
            {
                "obj_class": "SampleTemplate",
                "obj_id": 1,
                "sample_or_col": "unknown",
                "name": "column",
            },
        )
        private_task(job.id)
        self.assertEqual(job.status, "error")
        self.assertIn(
            'Unknown value "unknown". Choose between "samples" and "columns"',
            job.log.msg,
        )


if __name__ == "__main__":
    main()
