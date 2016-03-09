from unittest import TestCase, main
from os.path import join
from os import remove, rename
import numpy.testing as npt

from moi.group import get_id_from_user
from moi import ctx_default

from qiita_core.util import qiita_test_checker
from qiita_db.analysis import Analysis
from qiita_db.job import Job
from qiita_db.util import get_db_files_base_dir
from qiita_db.exceptions import QiitaDBWarning
from qiita_ware.analysis_pipeline import RunAnalysis


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

    def test_failure_callback(self):
        """Make sure failure at file creation step doesn't hang everything"""
        # rename a needed file for creating the biom table
        base = get_db_files_base_dir()
        rename(join(base, "processed_data",
                    "1_study_1001_closed_reference_otu_table.biom"),
               join(base, "processed_data", "1_study_1001.bak"))
        analysis = Analysis(2)
        group = get_id_from_user("demo@microbio.me")
        try:
            app = RunAnalysis(moi_context=ctx_default,
                              moi_parent_id=group)
            app(analysis, [], rarefaction_depth=100)
            self.assertEqual(analysis.status, 'error')
            for job in analysis.jobs:
                self.assertEqual(job.status, 'error')
        finally:
            rename(join(base, "processed_data", "1_study_1001.bak"),
                   join(base, "processed_data",
                        "1_study_1001_closed_reference_otu_table.biom"))

    def test_add_jobs_in_construct_job_graphs(self):
        analysis = Analysis(2)
        npt.assert_warns(QiitaDBWarning, analysis.build_files)
        RunAnalysis()._construct_job_graph(
            analysis, [('18S', 'Summarize Taxa')],
            comm_opts={'Summarize Taxa': {'opt1': 5}})
        self.assertEqual(analysis.jobs, [Job(3), Job(4), Job(5)])
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
