# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from datetime import datetime
from os.path import exists, join
from os import remove, close
from tempfile import mkstemp

import networkx as nx

import qiita_db as qdb
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class ProcessingJobUtilTest(TestCase):
    def test_system_call(self):
        obs_out, obs_err, obs_status = qdb.processing_job._system_call(
            'echo "Test system call stdout"')

        self.assertEqual(obs_out, "Test system call stdout\n")
        self.assertEqual(obs_err, "")
        self.assertEqual(obs_status, 0)

    def test_system_call_error(self):
        obs_out, obs_err, obs_status = qdb.processing_job._system_call(
            '>&2  echo "Test system call stderr"; exit 1')
        self.assertEqual(obs_out, "")
        self.assertEqual(obs_err, "Test system call stderr\n")
        self.assertEqual(obs_status, 1)

    def test_job_submitter(self):
        # The cmd parameter of the function should be the command that
        # actually executes the function. However, in order to avoid executing
        # a expensive command, we are just going to pass some other command.
        # In case of success, nothing happens, so we just run it and see that
        # it doesn't raise an error
        job = qdb.processing_job.ProcessingJob(
            "063e553b-327c-4818-ab4a-adfe58e49860")
        cmd = 'echo "Test system call stdout"'
        qdb.processing_job._job_submitter(job, cmd)

    def test_job_submitter_error(self):
        # Same comment as above, but here we are going to force failure, and
        # check that the job is updated correctly
        job = qdb.processing_job.ProcessingJob(
            "063e553b-327c-4818-ab4a-adfe58e49860")
        cmd = '>&2  echo "Test system call stderr"; exit 1'
        qdb.processing_job._job_submitter(job, cmd)
        self.assertEqual(job.status, 'error')
        exp = ("Error submitting job '063e553b-327c-4818-ab4a-adfe58e49860':\n"
               "Std output:\nStd error:Test system call stderr\n")
        self.assertEqual(job.log.msg, exp)


@qiita_test_checker()
class ProcessingJobTest(TestCase):
    def setUp(self):
        self.tester1 = qdb.processing_job.ProcessingJob(
            "063e553b-327c-4818-ab4a-adfe58e49860")
        self.tester2 = qdb.processing_job.ProcessingJob(
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d")
        self.tester3 = qdb.processing_job.ProcessingJob(
            "b72369f9-a886-4193-8d3d-f7b504168e75")
        self.tester4 = qdb.processing_job.ProcessingJob(
            "d19f76ee-274e-4c1b-b3a2-a12d73507c55")
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    def test_exists(self):
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "063e553b-327c-4818-ab4a-adfe58e49860"))
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d"))
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "b72369f9-a886-4193-8d3d-f7b504168e75"))
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "d19f76ee-274e-4c1b-b3a2-a12d73507c55"))
        self.assertFalse(qdb.processing_job.ProcessingJob.exists(
            "d19f76ee-274e-4c1b-b3a2-b12d73507c55"))
        self.assertFalse(qdb.processing_job.ProcessingJob.exists(
            "some-other-string"))

    def test_create(self):
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}')
        exp_params = qdb.software.Parameters.load(exp_command,
                                                  json_str=json_str)
        exp_user = qdb.user.User('test@foo.bar')
        obs = qdb.processing_job.ProcessingJob.create(exp_user, exp_params)
        self.assertEqual(obs.user, exp_user)
        self.assertEqual(obs.command, exp_command)
        self.assertEqual(obs.parameters, exp_params)
        self.assertEqual(obs.status, 'in_construction')
        self.assertEqual(obs.log, None)
        self.assertEqual(obs.heartbeat, None)
        self.assertEqual(obs.step, None)
        self.assertTrue(obs in qdb.artifact.Artifact(1).jobs())

    def test_user(self):
        exp_user = qdb.user.User('test@foo.bar')
        self.assertEqual(self.tester1.user, exp_user)
        self.assertEqual(self.tester2.user, exp_user)
        exp_user = qdb.user.User('shared@foo.bar')
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
            '"max_barcode_errors":1.5,"input_data":1}')
        exp_params = qdb.software.Parameters.load(qdb.software.Command(1),
                                                  json_str=json_str)
        self.assertEqual(self.tester1.parameters, exp_params)

        json_str = (
            '{"min_seq_len":100,"max_seq_len":1000,"trim_seq_length":false,'
            '"min_qual_score":25,"max_ambig":6,"max_homopolymer":6,'
            '"max_primer_mismatch":0,"barcode_type":"golay_12",'
            '"max_barcode_errors":1.5,"disable_bc_correction":false,'
            '"qual_score_window":0,"disable_primers":false,'
            '"reverse_primers":"disable","reverse_primer_mismatches":0,'
            '"truncate_ambi_bases":false,"input_data":1}')
        exp_params = qdb.software.Parameters.load(qdb.software.Command(2),
                                                  json_str=json_str)
        self.assertEqual(self.tester2.parameters, exp_params)

        json_str = (
            '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,'
            '"sequence_max_n":0,"rev_comp_barcode":false,'
            '"rev_comp_mapping_barcodes":true,"rev_comp":false,'
            '"phred_quality_threshold":3,"barcode_type":"golay_12",'
            '"max_barcode_errors":1.5,"input_data":1}')
        exp_params = qdb.software.Parameters.load(qdb.software.Command(1),
                                                  json_str=json_str)
        self.assertEqual(self.tester3.parameters, exp_params)

        json_str = (
            '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,'
            '"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,'
            '"input_data":2}')
        exp_params = qdb.software.Parameters.load(qdb.software.Command(3),
                                                  json_str=json_str)
        self.assertEqual(self.tester4.parameters, exp_params)

    def test_input_artifacts(self):
        exp = [qdb.artifact.Artifact(1)]
        self.assertEqual(self.tester1.input_artifacts, exp)
        self.assertEqual(self.tester2.input_artifacts, exp)
        self.assertEqual(self.tester3.input_artifacts, exp)
        exp = [qdb.artifact.Artifact(2)]
        self.assertEqual(self.tester4.input_artifacts, exp)

    def test_status(self):
        self.assertEqual(self.tester1.status, 'queued')
        self.assertEqual(self.tester2.status, 'running')
        self.assertEqual(self.tester3.status, 'success')
        self.assertEqual(self.tester4.status, 'error')

    def test_set_status(self):
        self.assertEqual(self.tester1.status, 'queued')
        self.tester1._set_status('running')
        self.assertEqual(self.tester1.status, 'running')
        self.tester1._set_status('error')
        self.assertEqual(self.tester1.status, 'error')
        self.tester1._set_status('running')
        self.assertEqual(self.tester1.status, 'running')
        self.tester1._set_status('success')
        self.assertEqual(self.tester1.status, 'success')

    def test_set_status_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.tester2._set_status('queued')

        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.tester3._set_status('running')

    def test_generate_cmd(self):
        obs = self.tester1._generate_cmd()
        exp = ('qiita-plugin-launcher "source activate qiita" '
               '"start_target_gene" "https://localhost" '
               '"063e553b-327c-4818-ab4a-adfe58e49860" "%s"'
               % join(qdb.util.get_work_base_dir(),
                      "063e553b-327c-4818-ab4a-adfe58e49860"))
        self.assertEqual(obs, exp)

    def test_submit(self):
        # In order to test a success, we need to actually run the job, which
        # will mean to run split libraries, for example.
        pass

    def test_submit_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester1.submit()

    def test_complete_success(self):
        fd, fp = mkstemp(suffix='_table.biom')
        self._clean_up_files.append(fp)
        close(fd)
        with open(fp, 'w') as f:
            f.write('\n')

        exp_artifact_count = qdb.util.get_count('qiita.artifact') + 1
        artifacts_data = {'OTU table': {'filepaths': [(fp, 'biom')],
                                        'artifact_type': 'BIOM'}}
        self.tester2.complete(True, artifacts_data=artifacts_data)
        self.assertTrue(self.tester2.status, 'success')
        self.assertEqual(qdb.util.get_count('qiita.artifact'),
                         exp_artifact_count)
        self._clean_up_files.extend(
            [afp for _, afp, _ in
                qdb.artifact.Artifact(exp_artifact_count).filepaths])

    def test_complete_failure(self):
        self.tester2.complete(False, error="Job failure")
        self.assertEqual(self.tester2.status, 'error')
        self.assertEqual(self.tester2.log,
                         qdb.logger.LogEntry.newest_records(numrecords=1)[0])
        self.assertEqual(self.tester2.log.msg, 'Job failure')

    def test_complete_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester1.complete(True, artifacts_data={})

    def test_log(self):
        self.assertIsNone(self.tester1.log)
        self.assertIsNone(self.tester2.log)
        self.assertIsNone(self.tester3.log)
        self.assertEqual(self.tester4.log, qdb.logger.LogEntry(1))

    def test_set_error(self):
        for t in [self.tester1, self.tester2]:
            t._set_error('Job failure')
            self.assertEqual(t.status, 'error')
            self.assertEqual(
                t.log, qdb.logger.LogEntry.newest_records(numrecords=1)[0])

    def test_set_error_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester3._set_error("Job failure")

    def test_heartbeat(self):
        self.assertIsNone(self.tester1.heartbeat)
        self.assertEqual(self.tester2.heartbeat,
                         datetime(2015, 11, 22, 21, 00, 00))
        self.assertEqual(self.tester3.heartbeat,
                         datetime(2015, 11, 22, 21, 15, 00))
        self.assertEqual(self.tester4.heartbeat,
                         datetime(2015, 11, 22, 21, 30, 00))

    def test_update_heartbeat_state(self):
        before = datetime.now()
        self.tester2.update_heartbeat_state()
        self.assertTrue(before < self.tester2.heartbeat < datetime.now())

    def test_update_heartbeat_state_queued(self):
        before = datetime.now()
        self.assertEqual(self.tester1.status, 'queued')
        self.tester1.update_heartbeat_state()
        self.assertTrue(before < self.tester1.heartbeat < datetime.now())
        self.assertEqual(self.tester1.status, 'running')

    def test_update_heartbeat_state_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester3.update_heartbeat_state()

    def test_step(self):
        self.assertIsNone(self.tester1.step)
        self.assertEqual(self.tester2.step, 'demultiplexing')
        self.assertIsNone(self.tester3.step)
        self.assertEqual(self.tester4.step, 'generating demux file')

    def test_step_setter(self):
        self.assertEqual(self.tester2.step, 'demultiplexing')
        self.tester2.step = 'generating demux file'
        self.assertEqual(self.tester2.step, 'generating demux file')

    def test_step_setter_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester1.step = 'demultiplexing'

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester3.step = 'demultiplexing'

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester4.step = 'demultiplexing'

    def test_children(self):
        self.assertEqual(list(self.tester1.children), [])
        self.assertEqual(list(self.tester3.children), [self.tester4])

    def test_update_children(self):
        # Create a workflow so we can test this functionality
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}')
        exp_params = qdb.software.Parameters.load(exp_command,
                                                  json_str=json_str)
        exp_user = qdb.user.User('test@foo.bar')
        name = "Test processing workflow"

        tester = qdb.processing_job.ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name)

        parent = tester.graph.nodes()[0]
        connections = {parent: {'demultiplexed': 'input_data'}}
        dflt_params = qdb.software.DefaultParameters(10)
        tester.add(connections, dflt_params)
        child = tester.graph.nodes()[1]

        mapping = {1: 3}
        obs = parent._update_children(mapping)
        exp = [child]
        self.assertTrue(obs, exp)

    def test_update_and_launch_children(self):
        # In order to test a success, we need to actually run the children
        # jobs, which will mean to run split libraries, for example.
        pass


@qiita_test_checker()
class ProcessingWorkflowTests(TestCase):
    def test_from_default_workflow(self):
        exp_user = qdb.user.User('test@foo.bar')
        dflt_wf = qdb.software.DefaultWorkflow(1)
        req_params = {qdb.software.Command(1): {'input_data': 1}}
        name = "Test processing workflow"

        obs = qdb.processing_job.ProcessingWorkflow.from_default_workflow(
            exp_user, dflt_wf, req_params, name=name)
        self.assertEqual(obs.name, name)
        self.assertEqual(obs.user, exp_user)
        obs_graph = obs.graph
        self.assertTrue(isinstance(obs_graph, nx.DiGraph))
        self.assertEqual(len(obs_graph.nodes()), 2)
        obs_edges = obs_graph.edges()
        self.assertEqual(len(obs_edges), 1)
        obs_src = obs_edges[0][0]
        obs_dst = obs_edges[0][1]
        self.assertTrue(isinstance(obs_src, qdb.processing_job.ProcessingJob))
        self.assertTrue(isinstance(obs_dst, qdb.processing_job.ProcessingJob))
        self.assertTrue(obs_src.command, qdb.software.Command(1))
        self.assertTrue(obs_dst.command, qdb.software.Command(1))
        obs_params = obs_dst.parameters.values
        exp_params = {
            'input_data': [obs_src.id, u'demultiplexed'],
            'reference': 1,
            'similarity': 0.97,
            'sortmerna_coverage': 0.97,
            'sortmerna_e_value': 1,
            'sortmerna_max_pos': 10000,
            'threads': 1}
        self.assertEqual(obs_params, exp_params)

    def test_from_default_workflow_missing(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError) as err:
            qdb.processing_job.ProcessingWorkflow.from_default_workflow(
                qdb.user.User('test@foo.bar'), qdb.software.DefaultWorkflow(1),
                {}, name="Test name")

        exp = ('Provided required parameters do not match the initial set of '
               'commands for the workflow. Command(s) "Split libraries FASTQ"'
               ' are missing the required parameter set.')
        self.assertEqual(str(err.exception), exp)

    def test_from_default_workflow_extra(self):
        req_params = {qdb.software.Command(1): {'input_data': 1},
                      qdb.software.Command(2): {'input_data': 2}}

        with self.assertRaises(qdb.exceptions.QiitaDBError) as err:
            qdb.processing_job.ProcessingWorkflow.from_default_workflow(
                qdb.user.User('test@foo.bar'), qdb.software.DefaultWorkflow(1),
                req_params, name="Test name")
        exp = ('Provided required parameters do not match the initial set of '
               'commands for the workflow. Paramters for command(s) '
               '"Split libraries" have been provided, but they are not the '
               'initial commands for the workflow.')
        self.assertEqual(str(err.exception), exp)

    def test_from_scratch(self):
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}')
        exp_params = qdb.software.Parameters.load(exp_command,
                                                  json_str=json_str)
        exp_user = qdb.user.User('test@foo.bar')
        name = "Test processing workflow"

        obs = qdb.processing_job.ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name)
        self.assertEqual(obs.name, name)
        self.assertEqual(obs.user, exp_user)
        obs_graph = obs.graph
        self.assertTrue(isinstance(obs_graph, nx.DiGraph))
        nodes = obs_graph.nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].parameters, exp_params)
        self.assertEqual(obs_graph.edges(), [])

    def test_name(self):
        self.assertEqual(qdb.processing_job.ProcessingWorkflow(1).name,
                         'Testing processing workflow')

    def test_user(self):
        self.assertEqual(qdb.processing_job.ProcessingWorkflow(1).user,
                         qdb.user.User('shared@foo.bar'))

    def test_graph(self):
        obs = qdb.processing_job.ProcessingWorkflow(1).graph
        self.assertTrue(isinstance(obs, nx.DiGraph))
        exp_nodes = [
            qdb.processing_job.ProcessingJob(
                'b72369f9-a886-4193-8d3d-f7b504168e75'),
            qdb.processing_job.ProcessingJob(
                'd19f76ee-274e-4c1b-b3a2-a12d73507c55')]
        self.assertItemsEqual(obs.nodes(), exp_nodes)
        self.assertEqual(obs.edges(), [(exp_nodes[0], exp_nodes[1])])

    def test_graph_only_root(self):
        obs = qdb.processing_job.ProcessingWorkflow(2).graph
        self.assertTrue(isinstance(obs, nx.DiGraph))
        exp_nodes = [
            qdb.processing_job.ProcessingJob(
                'ac653cb5-76a6-4a45-929e-eb9b2dee6b63')]
        self.assertItemsEqual(obs.nodes(), exp_nodes)
        self.assertEqual(obs.edges(), [])

    def test_raise_if_not_in_construction(self):
        # We just need to test that the execution continues (i.e. no raise)
        tester = qdb.processing_job.ProcessingWorkflow(2)
        tester._raise_if_not_in_construction()

    def test_raise_if_not_in_construction_error(self):
        tester = qdb.processing_job.ProcessingWorkflow(1)
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            tester._raise_if_not_in_construction()

    def test_add(self):
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}')
        exp_params = qdb.software.Parameters.load(exp_command,
                                                  json_str=json_str)
        exp_user = qdb.user.User('test@foo.bar')
        name = "Test processing workflow"

        obs = qdb.processing_job.ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name)

        parent = obs.graph.nodes()[0]
        connections = {parent: {'demultiplexed': 'input_data'}}
        dflt_params = qdb.software.DefaultParameters(10)
        obs.add(connections, dflt_params)

        obs_graph = obs.graph
        self.assertTrue(isinstance(obs_graph, nx.DiGraph))
        self.assertEqual(len(obs_graph.nodes()), 2)
        obs_edges = obs_graph.edges()
        self.assertEqual(len(obs_edges), 1)
        obs_src = obs_edges[0][0]
        obs_dst = obs_edges[0][1]
        self.assertEqual(obs_src, parent)
        self.assertTrue(isinstance(obs_dst, qdb.processing_job.ProcessingJob))
        obs_params = obs_dst.parameters.values
        exp_params = {
            'input_data': [parent.id, u'demultiplexed'],
            'reference': 1,
            'similarity': 0.97,
            'sortmerna_coverage': 0.97,
            'sortmerna_e_value': 1,
            'sortmerna_max_pos': 10000,
            'threads': 1}
        self.assertEqual(obs_params, exp_params)

    def test_add_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.processing_job.ProcessingWorkflow(1).add({}, None)

    def test_remove(self):
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}')
        exp_params = qdb.software.Parameters.load(exp_command,
                                                  json_str=json_str)
        exp_user = qdb.user.User('test@foo.bar')
        name = "Test processing workflow"

        tester = qdb.processing_job.ProcessingWorkflow.from_scratch(
            exp_user, exp_params, name=name)

        parent = tester.graph.nodes()[0]
        connections = {parent: {'demultiplexed': 'input_data'}}
        dflt_params = qdb.software.DefaultParameters(10)
        tester.add(connections, dflt_params)

        self.assertEqual(len(tester.graph.nodes()), 2)
        tester.remove(tester.graph.edges()[0][1])

        g = tester.graph
        obs_nodes = g.nodes()
        self.assertEqual(len(obs_nodes), 1)
        self.assertEqual(obs_nodes[0], parent)
        self.assertEqual(g.edges(), [])

    def test_remove_error_not_in_construction(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.processing_job.ProcessingWorkflow(1).remove(
                qdb.processing_job.ProcessingJob(
                    'b72369f9-a886-4193-8d3d-f7b504168e75'))

    def test_remove_error_children(self):
        exp_user = qdb.user.User('test@foo.bar')
        dflt_wf = qdb.software.DefaultWorkflow(1)
        req_params = {qdb.software.Command(1): {'input_data': 1}}
        name = "Test processing workflow"

        tester = qdb.processing_job.ProcessingWorkflow.from_default_workflow(
            exp_user, dflt_wf, req_params, name=name)

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            tester.remove(tester.graph.edges()[0][0])

    def test_submit(self):
        # In order to test a success, we need to actually run the jobs, which
        # will mean to run split libraries, for example.
        pass

if __name__ == '__main__':
    main()
