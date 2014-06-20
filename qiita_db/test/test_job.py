# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os import remove, close
from os.path import exists, join, basename
from shutil import rmtree
from datetime import datetime
from tempfile import mkdtemp, mkstemp

from qiita_core.util import qiita_test_checker
from qiita_db.job import Job
from qiita_db.util import get_db_files_base_dir, get_work_base_dir
from qiita_db.analysis import Analysis
from qiita_db.exceptions import QiitaDBStatusError


@qiita_test_checker()
class JobTest(TestCase):
    """Tests that the job object works as expected"""

    def setUp(self):
        self.job = Job(1)
        self.options = {"option1": False, "option2": 25, "option3": "NEW"}
        self._delete_path = []
        self._delete_dir = []

    def tearDown(self):
        # needs to be this way because map does not play well with remove and
        # rmtree for python3
        for item in self._delete_path:
            remove(item)
        for item in self._delete_dir:
            rmtree(item)

    def test_exists(self):
        """tests that existing job returns true"""
        self.assertTrue(Job.exists("16S", "Summarize Taxa",
                                   {'option1': True, 'option2': 12,
                                    'option3': 'FCM'}))

    def test_exists_not_there(self):
        """tests that non-existant job returns false"""
        self.assertFalse(Job.exists("Metabolomic",
                                    "Summarize Taxa",
                                    {'option1': "Nope", 'option2': 10,
                                     'option3': 'FCM'}))

    def test_create(self):
        """Makes sure creation works as expected"""
        # make first job
        new = Job.create("18S", "Alpha Rarefaction",
                         self.options, Analysis(1))
        self.assertEqual(new.id, 4)
        # make sure job inserted correctly
        obs = self.conn_handler.execute_fetchall("SELECT * FROM qiita.job "
                                                 "WHERE job_id = 4")
        exp = [[4, 2, 1, 3, '{"option1":false,"option2":25,"option3":"NEW"}',
                None]]
        self.assertEqual(obs, exp)
        # make sure job added to analysis correctly
        obs = self.conn_handler.execute_fetchall("SELECT * FROM "
                                                 "qiita.analysis_job WHERE "
                                                 "job_id = 4")
        exp = [[1, 4]]
        self.assertEqual(obs, exp)

        # make second job with diff datatype and command to test column insert
        new = Job.create("16S", "Beta Diversity",
                         self.options, Analysis(1))
        self.assertEqual(new.id, 5)
        # make sure job inserted correctly
        obs = self.conn_handler.execute_fetchall("SELECT * FROM qiita.job "
                                                 "WHERE job_id = 5")
        exp = [[5, 1, 1, 2, '{"option1":false,"option2":25,"option3":"NEW"}',
                None]]
        self.assertEqual(obs, exp)
        # make sure job added to analysis correctly
        obs = self.conn_handler.execute_fetchall("SELECT * FROM "
                                                 "qiita.analysis_job WHERE "
                                                 "job_id = 5")
        exp = [[1, 5]]
        self.assertEqual(obs, exp)

    # def test_create_exists(self):
    #     """Makes sure creation doesn't duplicate a job"""
    #     with self.assertRaises(QiitaDBDuplicateError):
    #         Job.create("16S", "Summarize Taxa",
    #                    {'option1': True, 'option2': 12, 'option3': 'FCM'},
    #                    Analysis(1))

    def test_retrieve_datatype(self):
        """Makes sure datatype retriveal is correct"""
        self.assertEqual(self.job.datatype, '16S')

    def test_retrieve_command(self):
        """Makes sure command retriveal is correct"""
        self.assertEqual(self.job.command, ['Summarize Taxa',
                                            'summarize_taxa_through_plots.py'])

    def test_retrieve_options(self):
        self.assertEqual(self.job.options, {'option1': True, 'option2': 12,
                                            'option3': 'FCM'})

    def test_retrieve_results(self):
        self.assertEqual(self.job.results, [join("job", "1_job_result.txt")])

    def test_retrieve_results_empty(self):
        new = Job.create("18S", "Beta Diversity", self.options, Analysis(1))
        self.assertEqual(new.results, [])

    def test_retrieve_results_dir(self):
        self.assertEqual(Job(2).results, [join("job", "2_test_folder")])

    def test_set_error(self):
        timestamp = datetime(2014, 6, 13, 14, 19, 25)
        self.job._log_error("TESTERROR", 1, timestamp)
        self.assertEqual(self.job.status, "error")

        # make sure logging table correct
        sql = ("SELECT * FROM qiita.logging WHERE log_id = (SELECT log_id FROM"
               " qiita.job WHERE job_id = 1)")
        log = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(log, [[1, timestamp, 1, 'TESTERROR', None]])

    def test_set_error_completed(self):
        timestamp = datetime(2014, 6, 13, 14, 19, 25)
        self.job.status = "error"
        with self.assertRaises(QiitaDBStatusError):
            self.job._log_error("TESTERROR", 1, timestamp)

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
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.job_results_filepath WHERE job_id = 1")

        self.assertEqual(obs, [[1, 8], [1, 10]])

    def test_add_results_dir(self):
        # Create a test directory
        test_dir = mkdtemp(dir=get_work_base_dir())
        self._delete_dir.append(test_dir)
        fd, test_file = mkstemp(dir=test_dir, suffix='.txt')
        close(fd)
        with open(test_file, "w") as f:
            f.write('\n')
        self._delete_path.append(test_file)

        # add folder to job
        self.job.add_results([(test_dir, 7)])

        # check that the directory was copied correctly
        db_path = join(get_db_files_base_dir(), "job",
                       "1_%s" % basename(test_dir))
        self._delete_dir.append(db_path)
        self.assertTrue(exists(db_path))

        # make sure files attached to job properly
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.job_results_filepath WHERE job_id = 1")
        self.assertEqual(obs, [[1, 8], [1, 10]])

    def test_add_results_completed(self):
        self.job.status = "completed"
        with self.assertRaises(QiitaDBStatusError):
            self.job.add_results([("/fake/dir/", 7)])


if __name__ == "__main__":
    main()
