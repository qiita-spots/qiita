# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from datetime import datetime
from json import dumps, loads
from os import close
from tempfile import mkstemp
from time import sleep
from unittest import TestCase, main

import networkx as nx
import pandas as pd

import qiita_db as qdb
from qiita_core.qiita_settings import qiita_config
from qiita_core.util import qiita_test_checker


def _create_job(force=True):
    job = qdb.processing_job.ProcessingJob.create(
        qdb.user.User("test@foo.bar"),
        qdb.software.Parameters.load(
            qdb.software.Command(2),
            values_dict={
                "min_seq_len": 100,
                "max_seq_len": 1000,
                "trim_seq_length": False,
                "min_qual_score": 25,
                "max_ambig": 6,
                "max_homopolymer": 6,
                "max_primer_mismatch": 0,
                "barcode_type": "golay_12",
                "max_barcode_errors": 1.5,
                "disable_bc_correction": False,
                "qual_score_window": 0,
                "disable_primers": False,
                "reverse_primers": "disable",
                "reverse_primer_mismatches": 0,
                "truncate_ambi_bases": False,
                "input_data": 1,
            },
        ),
        force,
    )
    return job


@qiita_test_checker()
class ProcessingJobUtilTest(TestCase):
    def test_system_call(self):
        obs_out, obs_err, obs_status = qdb.processing_job._system_call(
            'echo "Test system call stdout"'
        )

        self.assertEqual(obs_out, "Test system call stdout\n")
        self.assertEqual(obs_err, "")
        self.assertEqual(obs_status, 0)

    def test_system_call_error(self):
        obs_out, obs_err, obs_status = qdb.processing_job._system_call(
            '>&2  echo "Test system call stderr"; exit 1'
        )
        self.assertEqual(obs_out, "")
        self.assertEqual(obs_err, "Test system call stderr\n")
        self.assertEqual(obs_status, 1)


@qiita_test_checker()
class ProcessingJobTest(TestCase):
    def setUp(self):
        self.tester1 = qdb.processing_job.ProcessingJob(
            "063e553b-327c-4818-ab4a-adfe58e49860"
        )
        self.tester2 = qdb.processing_job.ProcessingJob(
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d"
        )
        self.tester3 = qdb.processing_job.ProcessingJob(
            "b72369f9-a886-4193-8d3d-f7b504168e75"
        )
        self.tester4 = qdb.processing_job.ProcessingJob(
            "d19f76ee-274e-4c1b-b3a2-a12d73507c55"
        )

        self._clean_up_files = []

    def _get_all_job_ids(self):
        sql = "SELECT processing_job_id FROM qiita.processing_job"
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql)
            return qdb.sql_connection.TRN.execute_fetchflatten()

    def _wait_for_job(self, job):
        while job.status not in ("error", "success"):
            sleep(0.5)

    def test_exists(self):
        self.assertTrue(
            qdb.processing_job.ProcessingJob.exists(
                "063e553b-327c-4818-ab4a-adfe58e49860"
            )
        )
        self.assertTrue(
            qdb.processing_job.ProcessingJob.exists(
                "bcc7ebcd-39c1-43e4-af2d-822e3589f14d"
            )
        )
        self.assertTrue(
            qdb.processing_job.ProcessingJob.exists(
                "b72369f9-a886-4193-8d3d-f7b504168e75"
            )
        )
        self.assertTrue(
            qdb.processing_job.ProcessingJob.exists(
                "d19f76ee-274e-4c1b-b3a2-a12d73507c55"
            )
        )
        self.assertFalse(
            qdb.processing_job.ProcessingJob.exists(
                "d19f76ee-274e-4c1b-b3a2-b12d73507c55"
            )
        )
        self.assertFalse(qdb.processing_job.ProcessingJob.exists("some-other-string"))

    def test_user(self):
        exp_user = qdb.user.User("test@foo.bar")
        self.assertEqual(self.tester1.user, exp_user)
        self.assertEqual(self.tester2.user, exp_user)
        exp_user = qdb.user.User("shared@foo.bar")
        self.assertEqual(self.tester3.user, exp_user)
        self.assertEqual(self.tester4.user, exp_user)

    def test_command(self):
        cmd1 = qdb.software.Command(1)
        cmd2 = qdb.software.Command(2)
        cmd3 = qdb.software.Command(3)
        self.assertEqual(self.tester1.command, cmd1)
        self.assertEqual(self.tester2.command, cmd2)
        self.assertEqual(self.tester3.command, cmd1)
        self.assertEqual(self.tester4.command, cmd3)

    def test_parameters(self):
        json_str = (
            '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,'
            '"sequence_max_n":0,"rev_comp_barcode":false,'
            '"rev_comp_mapping_barcodes":false,"rev_comp":false,'
            '"phred_quality_threshold":3,"barcode_type":"golay_12",'
            '"max_barcode_errors":1.5,"input_data":1,"phred_offset":"auto"}'
        )
        exp_params = qdb.software.Parameters.load(
            qdb.software.Command(1), json_str=json_str
        )
        self.assertEqual(self.tester1.parameters, exp_params)

        json_str = (
            '{"min_seq_len":100,"max_seq_len":1000,"trim_seq_length":false,'
            '"min_qual_score":25,"max_ambig":6,"max_homopolymer":6,'
            '"max_primer_mismatch":0,"barcode_type":"golay_12",'
            '"max_barcode_errors":1.5,"disable_bc_correction":false,'
            '"qual_score_window":0,"disable_primers":false,'
            '"reverse_primers":"disable","reverse_primer_mismatches":0,'
            '"truncate_ambi_bases":false,"input_data":1}'
        )
        exp_params = qdb.software.Parameters.load(
            qdb.software.Command(2), json_str=json_str
        )
        self.assertEqual(self.tester2.parameters, exp_params)

        json_str = (
            '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,'
            '"sequence_max_n":0,"rev_comp_barcode":false,'
            '"rev_comp_mapping_barcodes":true,"rev_comp":false,'
            '"phred_quality_threshold":3,"barcode_type":"golay_12",'
            '"max_barcode_errors":1.5,"input_data":1,"phred_offset":"auto"}'
        )
        exp_params = qdb.software.Parameters.load(
            qdb.software.Command(1), json_str=json_str
        )
        self.assertEqual(self.tester3.parameters, exp_params)

        json_str = (
            '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,'
            '"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,'
            '"input_data":2}'
        )
        exp_params = qdb.software.Parameters.load(
            qdb.software.Command(3), json_str=json_str
        )
        self.assertEqual(self.tester4.parameters, exp_params)

    def test_input_artifacts(self):
        exp = [qdb.artifact.Artifact(1)]
        self.assertEqual(self.tester1.input_artifacts, exp)
        self.assertEqual(self.tester2.input_artifacts, exp)
        self.assertEqual(self.tester3.input_artifacts, exp)
        exp = [qdb.artifact.Artifact(2)]
        self.assertEqual(self.tester4.input_artifacts, exp)

    def test_status(self):
        self.assertEqual(self.tester1.status, "queued")
        self.assertEqual(self.tester2.status, "running")
        self.assertEqual(self.tester3.status, "success")
        self.assertEqual(self.tester4.status, "error")

    def test_submit(self):
        # In order to test a success, we need to actually run the job, which
        # will mean to run split libraries, for example.
        # TODO: rewrite this test
        pass

    def test_log(self):
        self.assertIsNone(self.tester1.log)
        self.assertIsNone(self.tester2.log)
        self.assertIsNone(self.tester3.log)
        self.assertEqual(self.tester4.log, qdb.logger.LogEntry(1))

    def test_heartbeat(self):
        self.assertIsNone(self.tester1.heartbeat)
        self.assertEqual(self.tester2.heartbeat, datetime(2015, 11, 22, 21, 00, 00))
        self.assertEqual(self.tester3.heartbeat, datetime(2015, 11, 22, 21, 15, 00))
        self.assertEqual(self.tester4.heartbeat, datetime(2015, 11, 22, 21, 30, 00))

    def test_step(self):
        self.assertIsNone(self.tester1.step)
        self.assertEqual(self.tester2.step, "demultiplexing")
        self.assertIsNone(self.tester3.step)
        self.assertEqual(self.tester4.step, "generating demux file")

    def test_children(self):
        self.assertEqual(list(self.tester1.children), [])
        self.assertEqual(list(self.tester3.children), [self.tester4])

    def test_update_and_launch_children(self):
        # In order to test a success, we need to actually run the children
        # jobs, which will mean to run split libraries, for example.
        pass

    def test_create(self):
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0, '
            '"phred_offset": "auto"}'
        )
        exp_params = qdb.software.Parameters.load(exp_command, json_str=json_str)
        exp_user = qdb.user.User("test@foo.bar")
        obs = qdb.processing_job.ProcessingJob.create(exp_user, exp_params, True)
        self.assertEqual(obs.user, exp_user)
        self.assertEqual(obs.command, exp_command)
        self.assertEqual(obs.parameters, exp_params)
        self.assertEqual(obs.status, "in_construction")
        self.assertEqual(obs.log, None)
        self.assertEqual(obs.heartbeat, None)
        self.assertEqual(obs.step, None)
        self.assertTrue(obs in qdb.artifact.Artifact(1).jobs())

        # test with paramters with '
        exp_command = qdb.software.Command(1)
        exp_params.values["a tests with '"] = 'this is a tests with "'
        exp_params.values['a tests with "'] = "this is a tests with '"
        obs = qdb.processing_job.ProcessingJob.create(exp_user, exp_params)
        self.assertEqual(obs.user, exp_user)
        self.assertEqual(obs.command, exp_command)
        self.assertEqual(obs.status, "in_construction")
        self.assertEqual(obs.log, None)
        self.assertEqual(obs.heartbeat, None)
        self.assertEqual(obs.step, None)
        self.assertTrue(obs in qdb.artifact.Artifact(1).jobs())

    def test_set_status(self):
        job = _create_job()
        self.assertEqual(job.status, "in_construction")
        job._set_status("queued")
        self.assertEqual(job.status, "queued")
        job._set_status("running")
        self.assertEqual(job.status, "running")
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            job._set_status("queued")
        job._set_status("error")
        self.assertEqual(job.status, "error")
        job._set_status("running")
        self.assertEqual(job.status, "running")
        job._set_status("success")
        self.assertEqual(job.status, "success")
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            job._set_status("running")

    def test_submit_error(self):
        job = _create_job()
        job._set_status("queued")
        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            job.submit()

    def test_submit_environment(self):
        job = _create_job()
        software = job.command.software
        current = software.environment_script

        # temporal update and then rollback to not commit change
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.software SET environment_script = %s
                     WHERE software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [f"{current} ENVIRONMENT", software.id])

            job.submit()

            self.assertEqual(job.status, "error")

            qdb.sql_connection.TRN.rollback()

    def test_complete_multiple_outputs(self):
        # This test performs the test of multiple functions at the same
        # time. "release", "release_validators" and
        # "_set_validator_jobs" are tested here for correct execution.
        # Those functions are designed to work together, so it becomes
        # really hard to test each of the functions individually for
        # successfull execution.
        # We need to create a new command with multiple outputs, since
        # in the test DB there is no command with such characteristics
        cmd = qdb.software.Command.create(
            qdb.software.Software(1),
            "TestCommand",
            "Test command",
            {"input": ['artifact:["Demultiplexed"]', None]},
            {"out1": "BIOM", "out2": "BIOM"},
        )
        job = qdb.processing_job.ProcessingJob.create(
            qdb.user.User("test@foo.bar"),
            qdb.software.Parameters.load(cmd, values_dict={"input": 1}),
        )
        job._set_status("running")

        fd, fp1 = mkstemp(suffix="_table.biom")
        self._clean_up_files.append(fp1)
        close(fd)
        with open(fp1, "w") as f:
            f.write("\n")

        fd, fp2 = mkstemp(suffix="_table.biom")
        self._clean_up_files.append(fp2)
        close(fd)
        with open(fp2, "w") as f:
            f.write("\n")

        # `job` has 2 output artifacts. Each of these artifacts needs to be
        # validated by 2 different validation jobs. We are creating those jobs
        # here, and add in the 'procenance' parameter that links the original
        # jobs with the validator jobs.
        params = qdb.software.Parameters.load(
            qdb.software.Command(4),
            values_dict={
                "template": 1,
                "files": fp1,
                "artifact_type": "BIOM",
                "provenance": dumps(
                    {
                        "job": job.id,
                        "cmd_out_id": qdb.util.convert_to_id(
                            "out1", "command_output", "name"
                        ),
                        "name": "out1",
                    }
                ),
            },
        )
        user = qdb.user.User("test@foo.bar")
        obs1 = qdb.processing_job.ProcessingJob.create(user, params, True)
        obs1._set_status("running")
        params = qdb.software.Parameters.load(
            qdb.software.Command(4),
            values_dict={
                "template": 1,
                "files": fp2,
                "artifact_type": "BIOM",
                "provenance": dumps(
                    {
                        "job": job.id,
                        "cmd_out_id": qdb.util.convert_to_id(
                            "out1", "command_output", "name"
                        ),
                        "name": "out1",
                    }
                ),
            },
        )
        obs2 = qdb.processing_job.ProcessingJob.create(user, params, True)
        obs2._set_status("running")
        # Make sure that we link the original job with its validator jobs
        job._set_validator_jobs([obs1, obs2])

        artifact_data_1 = {"filepaths": [(fp1, "biom")], "artifact_type": "BIOM"}
        # Complete one of the validator jobs. This jobs should store all the
        # information about the new artifact, but it does not create it. The
        # job then goes to a "waiting" state, where it waits until all the
        # validator jobs are completed.
        obs1._complete_artifact_definition(artifact_data_1)
        self.assertEqual(obs1.status, "waiting")
        self.assertEqual(job.status, "running")

        # When we complete the second validation job, the previous validation
        # job is realeaed from its waiting state. All jobs then create the
        # artifacts in a single transaction, so either all of them successfully
        # complete, or all of them fail.
        artifact_data_2 = {"filepaths": [(fp2, "biom")], "artifact_type": "BIOM"}
        obs2._complete_artifact_definition(artifact_data_2)
        self.assertEqual(obs1.status, "waiting")
        self.assertEqual(obs2.status, "waiting")
        self.assertEqual(job.status, "running")

        job.release_validators()

        self.assertEqual(obs1.status, "success")
        self.assertEqual(obs2.status, "success")
        self.assertEqual(job.status, "success")

    def test_complete_artifact_definition(self):
        job = _create_job()
        job._set_status("running")
        fd, fp = mkstemp(suffix="_table.biom")
        self._clean_up_files.append(fp)
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")

        artifact_data = {"filepaths": [(fp, "biom")], "artifact_type": "BIOM"}
        params = qdb.software.Parameters.load(
            qdb.software.Command(4),
            values_dict={
                "template": 1,
                "files": fp,
                "artifact_type": "BIOM",
                "provenance": dumps({"job": job.id, "cmd_out_id": 3}),
            },
        )
        obs = qdb.processing_job.ProcessingJob.create(
            qdb.user.User("test@foo.bar"), params
        )
        job._set_validator_jobs([obs])
        obs._complete_artifact_definition(artifact_data)
        self.assertEqual(obs.status, "waiting")
        self.assertEqual(job.status, "running")
        # Upload case implicitly tested by "test_complete_type"

    def test_complete_artifact_transformation(self):
        # Implicitly tested by "test_complete"
        pass

    def test_complete_no_artifact_data(self):
        job = qdb.processing_job.ProcessingJob.create(
            qdb.user.User("test@foo.bar"),
            qdb.software.Parameters.load(
                qdb.software.Command(5), values_dict={"input_data": 1}
            ),
        )
        job._set_status("running")
        job.complete(True)
        self.assertEqual(job.status, "success")
        job = qdb.processing_job.ProcessingJob.create(
            qdb.user.User("test@foo.bar"),
            qdb.software.Parameters.load(
                qdb.software.Command(5), values_dict={"input_data": 1}
            ),
            True,
        )
        job._set_status("running")
        job.complete(False, error="Some Error")
        self.assertEqual(job.status, "error")

    def test_complete_type(self):
        fd, fp = mkstemp(suffix="_table.biom")
        self._clean_up_files.append(fp)
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")

        exp_artifact_count = qdb.util.get_count("qiita.artifact") + 1
        artifacts_data = {
            "ignored": {"filepaths": [(fp, "biom")], "artifact_type": "BIOM"}
        }
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
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, qdb.study.Study(1), "16S"
        )
        self._clean_up_files.extend([ptfp for _, ptfp in pt.get_filepaths()])
        params = qdb.software.Parameters.load(
            qdb.software.Command(4),
            values_dict={"template": pt.id, "files": fp, "artifact_type": "BIOM"},
        )
        obs = qdb.processing_job.ProcessingJob.create(
            qdb.user.User("test@foo.bar"), params, True
        )
        obs._set_status("running")
        obs.complete(True, artifacts_data=artifacts_data)
        self.assertEqual(obs.status, "success")
        self.assertEqual(qdb.util.get_count("qiita.artifact"), exp_artifact_count)
        self._clean_up_files.extend(
            [x["fp"] for x in qdb.artifact.Artifact(exp_artifact_count).filepaths]
        )

    def test_complete_success(self):
        # Note that here we are submitting and creating other multiple jobs;
        # thus here is the best place to test any intermediary steps/functions
        # of the job creation, submission, exectution, and completion.
        #
        # This first part of the test is just to test that by default the
        # naming of the output artifact will be the name of the output
        fd, fp = mkstemp(suffix="_table.biom")
        self._clean_up_files.append(fp)
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        artifacts_data = {
            "demultiplexed": {"filepaths": [(fp, "biom")], "artifact_type": "BIOM"}
        }
        job = _create_job()
        job._set_status("running")

        # here we can test that job.release_validator_job hasn't been created
        # yet so it has to be None
        self.assertIsNone(job.release_validator_job)
        job.complete(True, artifacts_data=artifacts_data)
        self._wait_for_job(job)
        # let's check for the job that released the validators
        self.assertIsNotNone(job.release_validator_job)
        self.assertEqual(job.release_validator_job.parameters.values["job"], job.id)
        # Retrieve the job that is performing the validation:
        validators = list(job.validator_jobs)
        self.assertEqual(len(validators), 1)
        # the validator actually runs on the system so it gets an external_id
        # assigned, let's test that is not None
        self.assertFalse(validators[0].external_id == "Not Available")
        # Test the output artifact is going to be named based on the
        # input parameters
        self.assertEqual(
            loads(validators[0].parameters.values["provenance"])["name"],
            "demultiplexed",
        )

        # To test that the naming of the output artifact is based on the
        # parameters that the command is indicating, we need to update the
        # parameter information of the command - since the ones existing
        # in the database currently do not require using any input parameter
        # to name the output artifact
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.command_parameter
                     SET name_order = %s
                     WHERE command_parameter_id = %s"""
            # Hard-coded values; 19 -> barcode_type, 20 -> max_barcode_errors
            qdb.sql_connection.TRN.add(sql, [[1, 19], [2, 20]], many=True)
            qdb.sql_connection.TRN.execute()

        fd, fp = mkstemp(suffix="_table.biom")
        self._clean_up_files.append(fp)
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")

        artifacts_data = {
            "demultiplexed": {"filepaths": [(fp, "biom")], "artifact_type": "BIOM"}
        }

        job = _create_job()
        job._set_status("running")
        alljobs = set(self._get_all_job_ids())

        job.complete(True, artifacts_data=artifacts_data)
        # When completing the previous job, it creates a new job that needs
        # to validate the BIOM table that is being added as new artifact.
        # Hence, this job is still in running state until the validation job
        # is completed. Note that this is tested by making sure that the status
        # of this job is running, and that we have one more job than before
        # (see assertEqual with len of all jobs)
        self.assertEqual(job.status, "running")
        self.assertTrue(
            job.step.startswith("Validating outputs (1 remaining) via job(s)")
        )

        obsjobs = set(self._get_all_job_ids())

        # The complete call above submits 2 new jobs: the validator job and
        # the release validators job. Hence the +2
        self.assertEqual(len(obsjobs), len(alljobs) + 2)
        self._wait_for_job(job)

        # Retrieve the job that is performing the validation:
        validators = list(job.validator_jobs)
        self.assertEqual(len(validators), 1)
        # here we can test that the validator shape and allocation is correct
        validator = validators[0]
        self.assertEqual(validator.parameters.values["artifact_type"], "BIOM")
        self.assertEqual(
            validator.resource_allocation_info,
            "-p qiita -N 1 -n 1 --mem 90gb --time 150:00:00 --nice=10000",
        )
        self.assertEqual(validator.shape, (27, 53, None))
        # Test the output artifact is going to be named based on the
        # input parameters
        self.assertEqual(
            loads(validator.parameters.values["provenance"])["name"],
            "demultiplexed golay_12 1.5",
        )

    def test_complete_failure(self):
        job = _create_job()
        job.complete(False, error="Job failure")
        self.assertEqual(job.status, "error")
        self.assertEqual(job.log, qdb.logger.LogEntry.newest_records(numrecords=1)[0])
        self.assertEqual(job.log.msg, "Job failure")

        # Test the artifact definition case
        job = _create_job()
        job._set_status("running")

        params = qdb.software.Parameters.load(
            qdb.software.Command(4),
            values_dict={
                "template": 1,
                "files": "ignored",
                "artifact_type": "BIOM",
                "provenance": dumps({"job": job.id, "cmd_out_id": 3}),
            },
        )
        obs = qdb.processing_job.ProcessingJob.create(
            qdb.user.User("test@foo.bar"), params, True
        )
        job._set_validator_jobs([obs])
        obs.complete(False, error="Validation failure")
        self.assertEqual(obs.status, "error")
        self.assertEqual(obs.log.msg, "Validation failure")

        self.assertEqual(job.status, "running")
        job.release_validators()
        self.assertEqual(job.status, "error")
        self.assertEqual(
            job.log.msg,
            "1 validator jobs failed: Validator %s "
            "error message: Validation failure" % obs.id,
        )

    def test_complete_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester1.complete(True, artifacts_data={})

    def test_set_error(self):
        job1 = _create_job()
        job1._set_status("queued")
        job2 = _create_job()
        job2._set_status("running")

        for t in [job1, job2]:
            t._set_error("Job failure")
            self.assertEqual(t.status, "error")
            self.assertEqual(t.log, qdb.logger.LogEntry.newest_records(numrecords=1)[0])

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester3._set_error("Job failure")

    def test_update_heartbeat_state(self):
        job = _create_job()
        job._set_status("running")
        before = datetime.now()
        job.update_heartbeat_state()
        self.assertTrue(before < job.heartbeat < datetime.now())

        job = _create_job()
        job._set_status("queued")
        before = datetime.now()
        job.update_heartbeat_state()
        self.assertTrue(before < job.heartbeat < datetime.now())
        self.assertEqual(job.status, "running")

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester3.update_heartbeat_state()

    def test_step_setter(self):
        job = _create_job()
        job._set_status("running")
        job.step = "demultiplexing"
        self.assertEqual(job.step, "demultiplexing")
        job.step = "generating demux file"
        self.assertEqual(job.step, "generating demux file")

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester1.step = "demultiplexing"

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester3.step = "demultiplexing"

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester4.step = "demultiplexing"

    def test_update_children(self):
        # Create a workflow so we can test this functionality
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0, '
            '"phred_offset": "auto"}'
        )
        exp_params = qdb.software.Parameters.load(exp_command, json_str=json_str)
        exp_user = qdb.user.User("test@foo.bar")
        name = "Test processing workflow"

        tester = qdb.processing_job.ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name, force=True
        )

        parent = list(tester.graph.nodes())[0]
        connections = {parent: {"demultiplexed": "input_data"}}
        dflt_params = qdb.software.DefaultParameters(10)
        tester.add(dflt_params, connections=connections)
        # we could get the child using tester.graph.nodes()[1] but networkx
        # doesn't assure order so using the actual graph to get the child
        child = list(nx.topological_sort(tester.graph))[1]

        mapping = {1: 3}
        obs = parent._update_children(mapping)
        exp = [child]
        self.assertTrue(obs, exp)
        self.assertEqual(child.input_artifacts, [qdb.artifact.Artifact(3)])

    def test_outputs(self):
        job = _create_job()
        job._set_status("running")

        QE = qdb.exceptions
        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            job.outputs

        fd, fp = mkstemp(suffix="_table.biom")
        self._clean_up_files.append(fp)
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")

        artifact_data = {"filepaths": [(fp, "biom")], "artifact_type": "BIOM"}
        params = qdb.software.Parameters.load(
            qdb.software.Command(4),
            values_dict={
                "template": 1,
                "files": fp,
                "artifact_type": "BIOM",
                "provenance": dumps(
                    {"job": job.id, "cmd_out_id": 3, "name": "outArtifact"}
                ),
            },
        )
        obs = qdb.processing_job.ProcessingJob.create(
            qdb.user.User("test@foo.bar"), params, True
        )
        job._set_validator_jobs([obs])
        exp_artifact_count = qdb.util.get_count("qiita.artifact") + 1
        obs._complete_artifact_definition(artifact_data)
        job.release_validators()
        self.assertEqual(job.status, "success")

        artifact = qdb.artifact.Artifact(exp_artifact_count)
        obs = job.outputs
        self.assertEqual(obs, {"OTU table": artifact})
        self._clean_up_files.extend([x["fp"] for x in artifact.filepaths])
        self.assertEqual(artifact.name, "outArtifact")

    def test_processing_job_workflow(self):
        # testing None
        job = qdb.processing_job.ProcessingJob("063e553b-327c-4818-ab4a-adfe58e49860")
        self.assertIsNone(job.processing_job_workflow)

        # testing actual workflow
        job = qdb.processing_job.ProcessingJob("b72369f9-a886-4193-8d3d-f7b504168e75")
        self.assertEqual(
            job.processing_job_workflow, qdb.processing_job.ProcessingWorkflow(1)
        )

        # testing child job from workflow
        job = qdb.processing_job.ProcessingJob("d19f76ee-274e-4c1b-b3a2-a12d73507c55")
        self.assertEqual(
            job.processing_job_workflow, qdb.processing_job.ProcessingWorkflow(1)
        )

    def test_hidden(self):
        self.assertTrue(self.tester1.hidden)
        self.assertTrue(self.tester2.hidden)
        self.assertFalse(self.tester3.hidden)
        self.assertTrue(self.tester4.hidden)

    def test_hide(self):
        QE = qdb.exceptions
        # It's in a queued state
        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            self.tester1.hide()

        # It's in a running state
        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            self.tester2.hide()

        # It's in a success state
        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            self.tester3.hide()

        job = _create_job()
        job._set_error("Setting to error for testing")
        self.assertFalse(job.hidden)
        job.hide()
        self.assertTrue(job.hidden)

    def test_shape(self):
        jids = {
            # Split libraries FASTQ
            "6d368e16-2242-4cf8-87b4-a5dc40bb890b": (27, 53, 116),
            # Pick closed-reference OTUs
            "80bf25f3-5f1d-4e10-9369-315e4244f6d5": (27, 53, 0),
            # Single Rarefaction / Analysis
            "8a7a8461-e8a1-4b4e-a428-1bc2f4d3ebd0": (5, 56, 3770436),
            # Split libraries
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d": (27, 53, 116),
        }

        for jid, shape in jids.items():
            job = qdb.processing_job.ProcessingJob(jid)
            self.assertEqual(job.shape, shape)

    def test_shape_special_cases(self):
        # get any given job/command/allocation and make sure nothing changed
        pj = qdb.processing_job.ProcessingJob("6d368e16-2242-4cf8-87b4-a5dc40bb890b")
        command = pj.command
        current_allocation = pj.resource_allocation_info
        self.assertEqual(
            current_allocation,
            "-p qiita -N 1 -n 1 --mem 120gb --time 80:00:00 --nice=10000",
        )

        # now, let's update that job allocation and make sure that things
        # work as expected
        tests = [
            # (resource allocation, specific allocation)
            # 1. tests that nlog works
            (
                "-p qiita -N 1 -n 1 --mem nlog({samples})*100 --time {columns}",
                "-p qiita -N 1 -n 1 --mem 329B --time 0:00:53 --nice=10000",
            ),
            # 2. days in time works fine
            (
                "-p qiita -N 1 -n 1 --mem 10g --time {columns}*10000",
                "-p qiita -N 1 -n 1 --mem 10g --time 6-3:13:20 --nice=10000",
            ),
            (
                "-p qiita -N 1 -n 1 --mem 20g --time {columns}*1631",
                "-p qiita -N 1 -n 1 --mem 20g --time 1-0:00:43 --nice=10000",
            ),
            # 3. conditionals work
            (
                "-p qiita -N 1 -n 1 --mem 10g --time {columns}*1631 "
                "if {columns}*1631 < 86400 else 86400",
                "-p qiita -N 1 -n 1 --mem 10g --time 1-0:00:00 --nice=10000",
            ),
            (
                "-p qiita -N 1 -n 1 --mem 10g --time {columns}*1631 "
                "if {columns}*1631 > 86400 else 86400",
                "-p qiita -N 1 -n 1 --mem 10g --time 1-0:00:43 --nice=10000",
            ),
            # --qos=qiita_prio
            (
                "-p qiita -N 1 -n 1 --mem 10g --time 1:00:00 --qos=qiita_prio",
                "-p qiita -N 1 -n 1 --mem 10g --time 1:00:00 --qos=qiita_prio "
                "--nice=10000",
            ),
            # all the combinations
            (
                "-p qiita -N 1 -n 1 --mem nlog({samples})*100000 --time "
                "{columns}*1631 if {columns}*1631 > 86400 else 86400 "
                "--qos=qiita_prio",
                "-p qiita -N 1 -n 1 --mem 322K --time 1-0:00:43 "
                "--qos=qiita_prio --nice=10000",
            ),
        ]
        for ra, sra in tests:
            sql = (
                "UPDATE qiita.processing_job_resource_allocation "
                f"SET allocation = '{ra}'"
                f"WHERE name = '{command.name}'"
            )
            qdb.sql_connection.perform_as_transaction(sql)
            self.assertEqual(sra, pj.resource_allocation_info)

        # return allocation
        sql = (
            "UPDATE qiita.processing_job_resource_allocation "
            f"SET allocation = '{current_allocation}'"
            f"WHERE name = '{command.name}'"
        )
        qdb.sql_connection.perform_as_transaction(sql)

    def test_get_resource_allocation_info(self):
        jids = {
            # Split libraries FASTQ
            "6d368e16-2242-4cf8-87b4-a5dc40bb890b": "-p qiita -N 1 -n 1 --mem 120gb --time 80:00:00 --nice=10000",
            # Pick closed-reference OTUs
            "80bf25f3-5f1d-4e10-9369-315e4244f6d5": "-p qiita -N 1 -n 5 --mem 120gb --time 130:00:00 --nice=10000",
            # Single Rarefaction / Analysis
            "8a7a8461-e8a1-4b4e-a428-1bc2f4d3ebd0": "-p qiita -N 1 -n 5 --mem-per-cpu 8gb --time 168:00:00 "
            "--nice=10000",
            # Split libraries
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d": "-p qiita -N 1 -n 1 --mem 60gb --time 25:00:00 --nice=10000",
        }

        for jid, allocation in jids.items():
            job = qdb.processing_job.ProcessingJob(jid)
            self.assertEqual(job.resource_allocation_info, allocation)

        # now let's test get_resource_allocation_info formulas, fun!!
        job_changed = qdb.processing_job.ProcessingJob(
            "6d368e16-2242-4cf8-87b4-a5dc40bb890b"
        )
        job_not_changed = qdb.processing_job.ProcessingJob(
            "80bf25f3-5f1d-4e10-9369-315e4244f6d5"
        )

        # helper to set memory allocations easier
        def _set_allocation(memory):
            sql = """UPDATE qiita.processing_job_resource_allocation
                     SET allocation = '{0}'
                     WHERE name = 'Split libraries FASTQ'""".format(
                "-p qiita --mem %s" % memory
            )
            qdb.sql_connection.perform_as_transaction(sql)

        # let's start with something simple, samples*1000
        #                                         27*1000 ~ 27000
        _set_allocation("{samples}*1000")
        self.assertEqual(
            job_not_changed.resource_allocation_info,
            "-p qiita -N 1 -n 5 --mem 120gb --time 130:00:00 --nice=10000",
        )
        self.assertEqual(
            job_changed.resource_allocation_info, "-p qiita --mem 26K --nice=10000"
        )

        # a little more complex ((samples+columns)*1000000)+4000000
        #                       ((   27  +  31   )*1000000)+4000000 ~ 62000000
        _set_allocation("(({samples}+{columns})*1000000)+4000000")
        self.assertEqual(
            job_not_changed.resource_allocation_info,
            "-p qiita -N 1 -n 5 --mem 120gb --time 130:00:00 --nice=10000",
        )
        self.assertEqual(
            job_changed.resource_allocation_info, "-p qiita --mem 80M --nice=10000"
        )

        # now something real input_size+(2*1e+9)
        #                        116   +(2*1e+9) ~ 2000000116
        _set_allocation("{input_size}+(2*1e+9)")
        self.assertEqual(
            job_not_changed.resource_allocation_info,
            "-p qiita -N 1 -n 5 --mem 120gb --time 130:00:00 --nice=10000",
        )
        self.assertEqual(
            job_changed.resource_allocation_info, "-p qiita --mem 2G --nice=10000"
        )

        # restore allocation
        sql = (
            "UPDATE qiita.processing_job_resource_allocation "
            "SET allocation = '-p qiita -N 1 -n 1 --mem 120gb "
            "--time 80:00:00' "
            "WHERE name = 'Split libraries FASTQ'"
        )
        qdb.sql_connection.perform_as_transaction(sql)

    def test_notification_mail_generation(self):
        # Almost all processing-jobs in testing are owned by test@foo.bar
        # and are of type 'Split libraries FASTQ'.

        # as 'test@foo.bar' is not set to receive notifications, let's
        # first manually set their configuration to 'true'.
        sql = (
            "UPDATE qiita.qiita_user SET receive_processing_job_emails"
            " = true WHERE email = 'test@foo.bar'"
        )

        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql)

        # with or w/out an error message, a status of 'waiting' should
        # immediately return with a 'None' message.
        obs = self.tester1._generate_notification_message("waiting", None)
        self.assertEqual(obs, None)
        obs = self.tester1._generate_notification_message("waiting", "Hello World")
        self.assertEqual(obs, None)

        # An error message in the parameter should show a difference for
        # messages of type 'error'.
        obs = self.tester1._generate_notification_message("error", None)

        exp = {
            "subject": (
                "Split libraries FASTQ: error, 063e553b-327c-4818-"
                "ab4a-adfe58e49860 [Not Available]"
            ),
            "message": (
                "Split libraries FASTQ\nPrep IDs: 1"
                f"\n{qiita_config.base_url}/study/description/1?"
                "prep_id=1\nData Type: 18S\nNew status: error"
            ),
        }
        self.assertDictEqual(obs, exp)

        obs = self.tester1._generate_notification_message("error", "An Error Message")
        exp = {
            "subject": (
                "Split libraries FASTQ: error, 063e553b-327c-4818-"
                "ab4a-adfe58e49860 [Not Available]"
            ),
            "message": (
                "Split libraries FASTQ\nPrep IDs: 1"
                f"\n{qiita_config.base_url}/study/description/1?"
                "prep_id=1\nData Type: 18S\nNew status: error"
                "\n\nError:\nAn Error Message"
            ),
        }
        self.assertDictEqual(obs, exp)

        # The inclusion of an error message has no effect on other valid
        # status types e.g. 'running'.
        obs = self.tester1._generate_notification_message("running", None)
        exp = {
            "subject": (
                "Split libraries FASTQ: running, 063e553b-327c-"
                "4818-ab4a-adfe58e49860 [Not Available]"
            ),
            "message": (
                "Split libraries FASTQ\nPrep IDs: 1"
                f"\n{qiita_config.base_url}/study/description/1?"
                "prep_id=1\nData Type: 18S\nNew status: running"
            ),
        }
        self.assertDictEqual(obs, exp)

        obs = self.tester1._generate_notification_message("running", "Yahoo!")
        exp = {
            "subject": (
                "Split libraries FASTQ: running, 063e553b-327c-"
                "4818-ab4a-adfe58e49860 [Not Available]"
            ),
            "message": (
                "Split libraries FASTQ\nPrep IDs: 1"
                f"\n{qiita_config.base_url}/study/description/1?"
                "prep_id=1\nData Type: 18S\nNew status: running"
            ),
        }
        self.assertDictEqual(obs, exp)

        # checking analysis emails
        jid = "8a7a8461-e8a1-4b4e-a428-1bc2f4d3ebd0"
        pj = qdb.processing_job.ProcessingJob(jid)
        obs = pj._generate_notification_message("running", "Yahoo!")
        exp = {
            "subject": (
                "Single Rarefaction: running, 8a7a8461-e8a1-"
                "4b4e-a428-1bc2f4d3ebd0 [126652530]"
            ),
            "message": "Analysis Job Single Rarefaction\n"
            f"{qiita_config.base_url}/analysis/description/1/\n"
            "New status: running",
        }
        self.assertDictEqual(obs, exp)

        # as 'test@foo.bar' is not set to receive notifications, let's
        # first manually set their configuration to 'true'.
        # reset test@foo.bar to 'false' to test expectations for a non-
        # privileged user.
        sql = (
            "UPDATE qiita.qiita_user SET receive_processing_job_emails"
            " = false WHERE email = 'test@foo.bar'"
        )
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql)

        # waiting should still return w/out a message.
        obs = self.tester1._generate_notification_message("waiting", None)
        self.assertEqual(obs, None)

        # an error status should now return nothing.
        obs = self.tester1._generate_notification_message("error", "An Error Message")
        self.assertEqual(obs, None)

        # other status messages should also return nothing.
        obs = self.tester1._generate_notification_message("running", None)
        self.assertEqual(obs, None)


@qiita_test_checker()
class ProcessingWorkflowTests(TestCase):
    def test_name(self):
        self.assertEqual(
            qdb.processing_job.ProcessingWorkflow(1).name, "Testing processing workflow"
        )

    def test_user(self):
        self.assertEqual(
            qdb.processing_job.ProcessingWorkflow(1).user,
            qdb.user.User("shared@foo.bar"),
        )

    def test_graph(self):
        obs = qdb.processing_job.ProcessingWorkflow(1).graph
        self.assertTrue(isinstance(obs, nx.DiGraph))
        exp_nodes = [
            qdb.processing_job.ProcessingJob("b72369f9-a886-4193-8d3d-f7b504168e75"),
            qdb.processing_job.ProcessingJob("d19f76ee-274e-4c1b-b3a2-a12d73507c55"),
        ]
        self.assertCountEqual(obs.nodes(), exp_nodes)
        self.assertEqual(list(obs.edges()), [(exp_nodes[0], exp_nodes[1])])

    def test_graph_only_root(self):
        obs = qdb.processing_job.ProcessingWorkflow(2).graph
        self.assertTrue(isinstance(obs, nx.DiGraph))
        exp_nodes = [
            qdb.processing_job.ProcessingJob("ac653cb5-76a6-4a45-929e-eb9b2dee6b63")
        ]
        self.assertCountEqual(obs.nodes(), exp_nodes)
        self.assertEqual(list(obs.edges()), [])

    def test_raise_if_not_in_construction(self):
        # We just need to test that the execution continues (i.e. no raise)
        tester = qdb.processing_job.ProcessingWorkflow(2)
        tester._raise_if_not_in_construction()

    def test_raise_if_not_in_construction_error(self):
        tester = qdb.processing_job.ProcessingWorkflow(1)
        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            tester._raise_if_not_in_construction()

    def test_submit(self):
        # The submit method is being tested in test_complete_success via
        # a job, its release validators and validators submissions.
        # Leaving this note here in case it's helpful for future development
        pass

    def test_from_default_workflow(self):
        exp_user = qdb.user.User("test@foo.bar")
        dflt_wf = qdb.software.DefaultWorkflow(1)
        req_params = {qdb.software.Command(1): {"input_data": 1}}
        name = "Test processing workflow"

        obs = qdb.processing_job.ProcessingWorkflow.from_default_workflow(
            exp_user, dflt_wf, req_params, name=name, force=True
        )
        self.assertEqual(obs.name, name)
        self.assertEqual(obs.user, exp_user)
        obs_graph = obs.graph
        self.assertTrue(isinstance(obs_graph, nx.DiGraph))
        self.assertEqual(len(obs_graph.nodes()), 2)
        obs_edges = obs_graph.edges()
        self.assertEqual(len(obs_edges), 1)
        obs_edges = list(obs_edges)[0]
        obs_src, obs_dst = list(obs_edges)
        self.assertTrue(isinstance(obs_src, qdb.processing_job.ProcessingJob))
        self.assertTrue(isinstance(obs_dst, qdb.processing_job.ProcessingJob))
        self.assertTrue(obs_src.command, qdb.software.Command(1))
        self.assertTrue(obs_dst.command, qdb.software.Command(1))
        obs_params = obs_dst.parameters.values
        exp_params = {
            "input_data": [obs_src.id, "demultiplexed"],
            "reference": 1,
            "similarity": 0.97,
            "sortmerna_coverage": 0.97,
            "sortmerna_e_value": 1,
            "sortmerna_max_pos": 10000,
            "threads": 1,
        }
        self.assertEqual(obs_params, exp_params)
        exp_pending = {obs_src.id: {"input_data": "demultiplexed"}}
        self.assertEqual(obs_dst.pending, exp_pending)

    def test_from_default_workflow_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError) as err:
            qdb.processing_job.ProcessingWorkflow.from_default_workflow(
                qdb.user.User("test@foo.bar"),
                qdb.software.DefaultWorkflow(1),
                {},
                name="Test name",
            )

        exp = (
            "Provided required parameters do not match the initial set of "
            'commands for the workflow. Command(s) "Split libraries FASTQ"'
            " are missing the required parameter set."
        )
        self.assertEqual(str(err.exception), exp)

        req_params = {
            qdb.software.Command(1): {"input_data": 1},
            qdb.software.Command(2): {"input_data": 2},
        }

        with self.assertRaises(qdb.exceptions.QiitaDBError) as err:
            qdb.processing_job.ProcessingWorkflow.from_default_workflow(
                qdb.user.User("test@foo.bar"),
                qdb.software.DefaultWorkflow(1),
                req_params,
                name="Test name",
            )
        exp = (
            "Provided required parameters do not match the initial set of "
            "commands for the workflow. Paramters for command(s) "
            '"Split libraries" have been provided, but they are not the '
            "initial commands for the workflow."
        )
        self.assertEqual(str(err.exception), exp)

    def test_from_scratch(self):
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0, '
            '"phred_offset": "auto"}'
        )
        exp_params = qdb.software.Parameters.load(exp_command, json_str=json_str)
        exp_user = qdb.user.User("test@foo.bar")
        name = "Test processing workflow"

        obs = qdb.processing_job.ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name, force=True
        )
        self.assertEqual(obs.name, name)
        self.assertEqual(obs.user, exp_user)
        obs_graph = obs.graph
        self.assertTrue(isinstance(obs_graph, nx.DiGraph))
        nodes = obs_graph.nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(list(nodes)[0].parameters, exp_params)
        self.assertEqual(list(obs_graph.edges()), [])

    def test_add(self):
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0, '
            '"phred_offset": "auto"}'
        )
        exp_params = qdb.software.Parameters.load(exp_command, json_str=json_str)
        exp_user = qdb.user.User("test@foo.bar")
        name = "Test processing workflow"

        obs = qdb.processing_job.ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name, force=True
        )

        parent = list(obs.graph.nodes())[0]
        connections = {parent: {"demultiplexed": "input_data"}}
        dflt_params = qdb.software.DefaultParameters(10)
        obs.add(dflt_params, connections=connections, force=True)

        obs_graph = obs.graph
        self.assertTrue(isinstance(obs_graph, nx.DiGraph))
        obs_nodes = obs_graph.nodes()
        self.assertEqual(len(obs_nodes), 2)
        obs_edges = obs_graph.edges()
        self.assertEqual(len(obs_edges), 1)
        obs_edges = list(obs_edges)[0]
        obs_src, obs_dst = list(obs_edges)
        self.assertEqual(obs_src, parent)
        self.assertTrue(isinstance(obs_dst, qdb.processing_job.ProcessingJob))
        obs_params = obs_dst.parameters.values
        exp_params = {
            "input_data": [parent.id, "demultiplexed"],
            "reference": 1,
            "similarity": 0.97,
            "sortmerna_coverage": 0.97,
            "sortmerna_e_value": 1,
            "sortmerna_max_pos": 10000,
            "threads": 1,
        }
        self.assertEqual(obs_params, exp_params)

        # Adding a new root job
        # This also tests that the `graph` property returns the graph correctly
        # when there are root nodes that don't have any children
        dflt_params = qdb.software.DefaultParameters(1)
        obs.add(dflt_params, req_params={"input_data": 1}, force=True)

        obs_graph = obs.graph
        self.assertTrue(isinstance(obs_graph, nx.DiGraph))
        root_obs_nodes = obs_graph.nodes()
        self.assertEqual(len(root_obs_nodes), 3)
        obs_edges = obs_graph.edges()
        self.assertEqual(len(obs_edges), 1)
        obs_new_jobs = set(root_obs_nodes) - set(obs_nodes)
        self.assertEqual(len(obs_new_jobs), 1)
        obs_job = obs_new_jobs.pop()
        exp_params = {
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
        }
        self.assertEqual(obs_job.parameters.values, exp_params)

    def test_add_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.processing_job.ProcessingWorkflow(1).add({}, None)

        # test that the qdb.util.max_artifacts_in_workflow
        with qdb.sql_connection.TRN:
            qdb.sql_connection.perform_as_transaction(
                "UPDATE settings set max_artifacts_in_workflow = 1"
            )
            with self.assertRaisesRegex(
                ValueError, "Cannot add new job because it will create more artifacts "
            ):
                qdb.processing_job.ProcessingWorkflow(2).add(
                    qdb.software.DefaultParameters(1),
                    req_params={"input_data": 1},
                    force=True,
                )
            qdb.sql_connection.TRN.rollback()

    def test_remove(self):
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0,'
            '"phred_offset": "auto"}'
        )
        exp_params = qdb.software.Parameters.load(exp_command, json_str=json_str)
        exp_user = qdb.user.User("test@foo.bar")
        name = "Test processing workflow"

        tester = qdb.processing_job.ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name, force=True
        )

        parent = list(tester.graph.nodes())[0]
        connections = {parent: {"demultiplexed": "input_data"}}
        dflt_params = qdb.software.DefaultParameters(10)
        tester.add(dflt_params, connections=connections)

        self.assertEqual(len(tester.graph.nodes()), 2)
        element = list(tester.graph.edges())[0]
        tester.remove(element[1])

        g = tester.graph
        obs_nodes = g.nodes()
        self.assertEqual(len(obs_nodes), 1)
        self.assertEqual(list(obs_nodes)[0], parent)
        self.assertEqual(list(g.edges()), [])

        # Test with cascade = true
        exp_user = qdb.user.User("test@foo.bar")
        dflt_wf = qdb.software.DefaultWorkflow(1)
        req_params = {qdb.software.Command(1): {"input_data": 1}}
        name = "Test processing workflow"

        tester = qdb.processing_job.ProcessingWorkflow.from_default_workflow(
            exp_user, dflt_wf, req_params, name=name, force=True
        )

        element = list(tester.graph.edges())[0]
        tester.remove(element[0], cascade=True)

        self.assertEqual(list(tester.graph.nodes()), [])

    def test_remove_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.processing_job.ProcessingWorkflow(1).remove(
                qdb.processing_job.ProcessingJob("b72369f9-a886-4193-8d3d-f7b504168e75")
            )

        exp_user = qdb.user.User("test@foo.bar")
        dflt_wf = qdb.software.DefaultWorkflow(1)
        req_params = {qdb.software.Command(1): {"input_data": 1}}
        name = "Test processing workflow"

        tester = qdb.processing_job.ProcessingWorkflow.from_default_workflow(
            exp_user, dflt_wf, req_params, name=name, force=True
        )

        with self.assertRaises(qdb.exceptions.QiitaDBOperationNotPermittedError):
            element = list(tester.graph.edges())[0]
            tester.remove(element[0])


@qiita_test_checker()
class ProcessingJobDuplicated(TestCase):
    def test_create_duplicated(self):
        job = _create_job()
        job._set_status("success")
        with self.assertRaisesRegex(
            ValueError,
            "Cannot create job because "
            "the parameters are the same as jobs "
            "that are queued, running or already "
            "have succeeded:",
        ) as context:
            _create_job(False)

        # If it failed it's because we have jobs in non finished status so
        # setting them as error. This is basically testing that the duplicated
        # job creation allows to create if all jobs are error and if success
        # that the job doesn't have children
        for jobs in str(context.exception).split("\n")[1:]:
            jid, status = jobs.split(": ")
            if status != "success":
                qdb.processing_job.ProcessingJob(jid)._set_status("error")
        _create_job(False)


if __name__ == "__main__":
    main()
