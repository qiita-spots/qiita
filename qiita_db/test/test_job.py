# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os import remove, makedirs
from os.path import exists, join
from shutil import rmtree
from datetime import datetime

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.job import Job
from qiita_db.util import get_db_files_base_dir, get_work_base_dir
from qiita_db.analysis import Analysis
from qiita_db.exceptions import QiitaDBDuplicateError
from qiita_db.sql_connection import SQLConnectionHandler


@qiita_test_checker()
class JobTest(TestCase):
    """Tests that the job object works as expected"""

    def setUp(self):
        self.job = Job(1)
        self.options = {"option1": False, "option2": 25, "option3": "NEW"}
        self._delete_path = []
        self._delete_dir = []

    def tearDown(self):
        map(remove, self._delete_path)
        map(rmtree, self._delete_dir)

    def test_exists(self):
        """tests that existing job returns true"""
        self.assertTrue(Job.exists("16S", "summarize_taxa_through_plots.py",
                                   {'option1': True, 'option2': 12,
                                    'option3': 'FCM'}))

    def test_exists_not_there(self):
        """tests that non-existant job returns false"""
        self.assertFalse(Job.exists("Metabolomic",
                                    "summarize_taxa_through_plots.py",
                                    {'option1': "Nope", 'option2': 10,
                                     'option3': 'FCM'}))

    def test_create(self):
        """Makes sure creation works as expected"""
        new = Job.create("18S", "beta_diversity_through_plots.py",
                         self.options, Analysis(1))
        self.assertEqual(new.id, 3)
        conn_handler = SQLConnectionHandler()
        # make sure job inserted correctly
        obs = conn_handler.execute_fetchall("SELECT * FROM qiita.job WHERE "
                                            "job_id = 3")
        exp = [[3, 2, 2, 1, '{"option1":false,"option2":25,"option3":"NEW"}',
                None]]
        self.assertEqual(obs, exp)
        # make sure job added to analysis correctly
        obs = conn_handler.execute_fetchall("SELECT * FROM qiita.analysis_job "
                                            "WHERE job_id = 3")
        exp = [[1, 3]]
        self.assertEqual(obs, exp)

    def test_create_exists(self):
        """Makes sure creation doesn't duplicate a job"""
        with self.assertRaises(QiitaDBDuplicateError):
            Job.create("16S", "summarize_taxa_through_plots.py",
                       {'option1': True, 'option2': 12, 'option3': 'FCM'},
                       Analysis(1))

    def test_retrieve_datatype(self):
        """Makes sure datatype retriveal is correct"""
        self.assertEqual(self.job.datatype, '16S')

    def test_retrieve_command(self):
        """Makes sure command retriveal is correct"""
        self.assertEqual(self.job.command, 'summarize_taxa_through_plots.py')

    def test_retrieve_options(self):
        self.assertEqual(self.job.options, {'option1': True, 'option2': 12,
                                            'option3': 'FCM'})

    def test_retrieve_results(self):
        obs = self.job.results
        self._delete_path = obs

        self.assertEqual(self.job.results, [join(get_work_base_dir(),
                                                 "job1result.txt")])
        # make sure files copied correctly
        self.assertTrue(exists(join(get_work_base_dir(), "job1result.txt")))

    def test_retrieve_results_blank(self):
        new = Job.create("18S", "beta_diversity_through_plots.py",
                         self.options, Analysis(1))
        obs = new.results
        self._delete_path = obs
        self.assertEqual(obs, [])

    def test_retrieve_results_tar(self):
        obs = Job(2).results
        self._delete_dir = obs
        self.assertEqual(obs, [join(get_work_base_dir(), "test_folder")])
        # make sure files copied correctly
        self.assertTrue(exists(join(get_work_base_dir(), "test_folder")))
        self.assertTrue(exists(join(get_work_base_dir(),
                        "test_folder/testfile.txt")))

    def test_set_error(self):
        timestamp = datetime(2014, 6, 13, 14, 19, 25)
        self.job._log_error("TESTERROR", 1, timestamp)
        self.assertEqual(self.job.status, "error")

        # make sure logging table correct
        sql = ("SELECT * FROM qiita.logging WHERE log_id = (SELECT log_id FROM"
               " qiita.job WHERE job_id = 1)")
        conn_handler = SQLConnectionHandler()
        log = conn_handler.execute_fetchall(sql)
        self.assertEqual(log, [[1, timestamp, 1, 'TESTERROR', None]])

    def test_retrieve_error_msg_blank(self):
        self.assertEqual(self.job.error_msg, None)

    def test_retrieve_error_msg_exists(self):
        self.job.set_error("TESTERROR", 1)
        self.assertEqual(self.job.error_msg, "TESTERROR")

    def test_add_results(self):
        self.job.add_results([(join(get_work_base_dir(),
                                    "placeholder.txt"), 8)])
        # make sure file copied correctly
        self._delete_path = [join(get_db_files_base_dir(), "job",
                             "1_placeholder.txt")]
        self.assertTrue(exists(join(get_db_files_base_dir(), "job",
                                    "1_placeholder.txt")))

        # make sure files attached to job properly
        conn_handler = SQLConnectionHandler()
        obs = conn_handler.execute_fetchall("SELECT * FROM "
                                            "qiita.job_results_filepath "
                                            "WHERE job_id = 1")
        self.assertEqual(obs, [[1, 8], [1, 10]])

    def test_add_results_tar(self):
        # make test directory to tar, inclluding internal file
        basedir = "/tmp/tar_folder"
        self._delete_dir = [basedir]
        self._delete_path = [join(get_db_files_base_dir(), "job",
                             "1_tar_folder.tar")]
        makedirs(basedir)
        with open(join(basedir, "tar_data.txt"), 'w'):
            pass

        # add folder to job
        self.job.add_results([(basedir, 7)])
        # make sure tar file copied correctly
        self.assertTrue(exists(join(get_db_files_base_dir(), "job",
                                    "1_tar_folder.tar")))

        # make sure temp tar files cleaned up properly
        self.assertFalse(exists("/tmp/1_tar_folder.tar"))

        # make sure files attached to job properly
        conn_handler = SQLConnectionHandler()
        obs = conn_handler.execute_fetchall("SELECT * FROM "
                                            "qiita.job_results_filepath "
                                            "WHERE job_id = 1")
        self.assertEqual(obs, [[1, 8], [1, 10]])


if __name__ == "__main__":
    main()
