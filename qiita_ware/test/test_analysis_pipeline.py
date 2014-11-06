from unittest import TestCase, main
from os.path import exists, join
from os import remove, rename

from qiita_core.util import qiita_test_checker
from qiita_db.analysis import Analysis
from qiita_db.job import Job
from qiita_db.util import get_db_files_base_dir
from qiita_ware import r_server
from qiita_ware.analysis_pipeline import (
    RunAnalysis, _build_analysis_files, _job_comm_wrapper, _finish_analysis)


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


@qiita_test_checker()
class TestRun(TestCase):
    def setUp(self):
        self._del_files = []

    def tearDown(self):
        for delfile in self._del_files:
            remove(delfile)

    def test_finish_analysis(self):
        pubsub = r_server.pubsub()
        pubsub.subscribe("demo@microbio.me")
        msgs = []

        _finish_analysis("demo@microbio.me", Analysis(1))
        for msg in pubsub.listen():
            if msg['type'] == 'message':
                msgs.append(msg['data'])
                if "allcomplete" in msg['data']:
                    pubsub.unsubscribe("demo@microbio.me")
                    break
        self.assertEqual(msgs, ['{"msg": "allcomplete", "analysis": 1}'])

    def test_failure_callback(self):
        """Make sure failure at file creation step doesn't hang everything"""
        # rename a needed file for creating the biom table
        base = get_db_files_base_dir()
        rename(join(base, "processed_data",
                    "1_study_1001_closed_reference_otu_table.biom"),
               join(base, "processed_data", "1_study_1001.bak"))

        try:
            app = RunAnalysis()
            app("demo@microbio.me", Analysis(2), [], rarefaction_depth=100)
            # make sure analysis set to error
            analysis = Analysis(2)
            self.assertEqual(analysis.status, 'error')
            for job_id in analysis.jobs:
                self.assertEqual(Job(job_id).status, 'error')
        finally:
            rename(join(base, "processed_data", "1_study_1001.bak"),
                   join(base, "processed_data",
                        "1_study_1001_closed_reference_otu_table.biom"))

    def test_build_files_job_comm_wrapper(self):
        # basic setup needed for test
        job = Job(3)

        # create the files needed for job, testing _build_analysis_files
        analysis = Analysis(2)
        _build_analysis_files(analysis, 100)
        self._del_files.append(join(get_db_files_base_dir(), "analysis",
                                    "2_analysis_mapping.txt"))
        self._del_files.append(join(get_db_files_base_dir(), "analysis",
                                    "2_analysis_18S.biom"))
        self.assertTrue(exists(join(get_db_files_base_dir(), "analysis",
                                    "2_analysis_mapping.txt")))
        self.assertTrue(exists(join(get_db_files_base_dir(), "analysis",
                                    "2_analysis_18S.biom")))
        self.assertEqual([3], analysis.jobs)

        _job_comm_wrapper("demo@microbio.me", 2, job)

        self.assertEqual(job.status, "error")

    def test_redis_comms(self):
        """Make sure redis communication happens"""
        msgs = []
        pubsub = r_server.pubsub()
        pubsub.subscribe("demo@microbio.me")

        app = RunAnalysis()
        app("demo@microbio.me", Analysis(2), [], rarefaction_depth=100)
        for msg in pubsub.listen():
            if msg['type'] == 'message':
                msgs.append(msg['data'])
                if "allcomplete" in msg['data']:
                    pubsub.unsubscribe("demo@microbio.me")
                    break
        self.assertEqual(
            msgs,
            ['{"msg": "Running", "command": "18S: Beta Diversity", '
             '"analysis": 2}',
             '{"msg": "ERROR", "command": "18S: Beta Diversity", '
             '"analysis": 2}',
             '{"msg": "allcomplete", "analysis": 2}'])
        log = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.logging")
        self.assertEqual(1, len(log))
        log = log[0]
        self.assertEqual(1, log[0])
        self.assertEqual(2, log[2])
        self.assertTrue(len(log[3]) > 0)
        self.assertTrue('[{"job": 3, "analysis": 2}]')

    def test_add_jobs_in_construct_job_graphs(self):
        analysis = Analysis(2)
        RunAnalysis()._construct_job_graph(
            "demo@microbio.me", analysis, [('18S', 'Summarize Taxa')],
            comm_opts={'Summarize Taxa': {'opt1': 5}})
        self.assertEqual(analysis.jobs, [3, 4])
        job = Job(4)
        self.assertEqual(job.datatype, '18S')
        self.assertEqual(job.command,
                         ['Summarize Taxa', 'summarize_taxa_through_plots.py'])
        expopts = {
            '--output_dir': join(
                get_db_files_base_dir(), 'job',
                '4_summarize_taxa_through_plots.py_output_dir'),
            'opt1': 5}
        self.assertEqual(job.options, expopts)

if __name__ == "__main__":
    main()
