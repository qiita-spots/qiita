# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os import remove, mkdir
from os.path import join, exists
from shutil import rmtree
from datetime import datetime

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


@qiita_test_checker()
class JobTest(TestCase):
    """Tests that the job object works as expected"""

    def setUp(self):
        self._delete_path = []
        self._delete_dir = []

        # creating a new job for testing
        self.options = {"option1": False, "option2": 25, "option3": "NEW"}
        _, self._job_folder = qdb.util.get_mountpoint("job")[0]

        self.job_create_params = ("18S", "Alpha Rarefaction",
                                  self.options, qdb.analysis.Analysis(1),
                                  qdb.reference.Reference(1),
                                  qdb.software.Command(3))
        self.job = qdb.job.Job.create(*self.job_create_params)
        self.job_id = self.job.id

        # adding filepaths
        # file
        self.fp = join(self._job_folder, "%d_job_result.txt" % self.job_id)
        if not exists(self.fp):
            with open(self.fp, 'w') as f:
                f.write("DATA")
        self.job.add_results([(self.fp, "plain_text")])
        # folder
        self.dfp = join(self._job_folder, "my_folder")
        self.ffp = join(self.dfp, "%d_file_in_folder.html" % self.job_id)
        if not exists(self.dfp):
            mkdir(self.dfp)
        if not exists(self.ffp):
            with open(self.ffp, 'w') as f:
                f.write("DATA")
        self.job.add_results([(self.dfp, "directory")])

    def tearDown(self):
        # needs to be this way because map does not play well with remove and
        # rmtree for python3
        for item in self._delete_path:
            remove(item)
        for item in self._delete_dir:
            rmtree(item)

        if qdb.job.Job.exists(*self.job_create_params):
            qdb.job.Job.delete(self.job_id)

    def test_exists(self):
        """tests that existing job returns true"""
        # need to insert matching sample data into analysis 2
        self.conn_handler.execute(
            "DELETE FROM qiita.analysis_sample WHERE analysis_id = 2")
        sql = """INSERT INTO qiita.analysis_sample
                        (analysis_id, artifact_id, sample_id)
                 VALUES (2, 4, '1.SKB8.640193'), (2, 4, '1.SKD8.640184'),
                        (2, 4, '1.SKB7.640196'), (2, 4, '1.SKM9.640192'),
                        (2, 4, '1.SKM4.640180')"""
        self.conn_handler.execute(sql)
        self.assertTrue(qdb.job.Job.exists(
            "18S", "Beta Diversity", {"--otu_table_fp": 1, "--mapping_fp": 1},
            qdb.analysis.Analysis(1), qdb.reference.Reference(2),
            qdb.software.Command(3)))

    def test_exists_return_jobid(self):
        """tests that existing job returns true"""
        # need to insert matching sample data into analysis 2
        self.conn_handler.execute(
            "DELETE FROM qiita.analysis_sample WHERE analysis_id = 2")
        sql = """INSERT INTO qiita.analysis_sample
                        (analysis_id, artifact_id, sample_id)
                 VALUES (2, 4, '1.SKB8.640193'), (2, 4, '1.SKD8.640184'),
                        (2, 4, '1.SKB7.640196'), (2, 4, '1.SKM9.640192'),
                        (2, 4, '1.SKM4.640180')"""
        self.conn_handler.execute(sql)
        exists, jid = qdb.job.Job.exists(
            "18S", "Beta Diversity", {"--otu_table_fp": 1, "--mapping_fp": 1},
            qdb.analysis.Analysis(1), qdb.reference.Reference(2),
            qdb.software.Command(3), return_existing=True)
        self.assertTrue(exists)
        self.assertEqual(jid, qdb.job.Job(2))

    def test_exists_noexist_options(self):
        """tests that non-existant job with bad options returns false"""
        # need to insert matching sample data into analysis 2
        # makes sure failure is because options and not samples
        self.conn_handler.execute(
            "DELETE FROM qiita.analysis_sample WHERE analysis_id = 2")
        sql = """INSERT INTO qiita.analysis_sample
                        (analysis_id, artifact_id, sample_id)
                 VALUES (2, 4, '1.SKB8.640193'), (2, 4, '1.SKD8.640184'),
                        (2, 4, '1.SKB7.640196'), (2, 4, '1.SKM9.640192'),
                        (2, 4, '1.SKM4.640180')"""
        self.conn_handler.execute(sql)
        self.assertFalse(qdb.job.Job.exists(
            "18S", "Beta Diversity", {"--otu_table_fp": 1, "--mapping_fp": 27},
            qdb.analysis.Analysis(1), qdb.reference.Reference(2),
            qdb.software.Command(3)))

    def test_exists_noexist_return_jobid(self):
        """tests that non-existant job with bad samples returns false"""
        exists, jid = qdb.job.Job.exists(
            "16S", "Beta Diversity", {"--otu_table_fp": 1, "--mapping_fp": 27},
            qdb.analysis.Analysis(1), qdb.reference.Reference(2),
            qdb.software.Command(3), return_existing=True)
        self.assertFalse(exists)
        self.assertEqual(jid, None)

    def test_get_commands(self):
        exp = [
            qdb.job.Command('Summarize Taxa',
                            'summarize_taxa_through_plots.py',
                            '{"--otu_table_fp":null}', '{}',
                            '{"--mapping_category":null, "--mapping_fp":null,'
                            '"--sort":null}', '{"--output_dir":null}'),
            qdb.job.Command('Beta Diversity',
                            'beta_diversity_through_plots.py',
                            '{"--otu_table_fp":null,"--mapping_fp":null}',
                            '{}',
                            '{"--tree_fp":null,"--color_by_all_fields":null,'
                            '"--seqs_per_sample":null}',
                            '{"--output_dir":null}'),
            qdb.job.Command('Alpha Rarefaction', 'alpha_rarefaction.py',
                            '{"--otu_table_fp":null,"--mapping_fp":null}',
                            '{}',
                            '{"--tree_fp":null,"--num_steps":null,'
                            '"--min_rare_depth":null,"--max_rare_depth":null,'
                            '"--retain_intermediate_files":false}',
                            '{"--output_dir":null}')
            ]
        self.assertEqual(qdb.job.Job.get_commands(), exp)

    def test_delete_files_and_folders(self):
        qdb.job.Job.delete(self.job_id)
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.job.Job(self.job_id)

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.job_results_filepath WHERE job_id = "
            "%d" % self.job_id)
        self.assertEqual(obs, [])

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.analysis_job WHERE job_id = %d" % self.job_id)
        self.assertEqual(obs, [])

        self.assertFalse(exists(self.fp))
        self.assertFalse(exists(self.ffp))
        self.assertFalse(exists(self.dfp))

    def test_create(self):
        """Makes sure creation works as expected"""
        # make first job
        new = qdb.job.Job.create("18S", "Alpha Rarefaction", {"opt1": 4},
                                 qdb.analysis.Analysis(1),
                                 qdb.reference.Reference(1),
                                 qdb.software.Command(3))
        new_id = new.id
        # + 1 cause it should be one higher than the one created in setUp
        self.assertEqual(new_id, self.job_id + 1)

        # make sure job inserted correctly
        obs = self.conn_handler.execute_fetchall("SELECT * FROM qiita.job "
                                                 "WHERE job_id = %d" % new_id)
        exp = [[new_id, 2, 1, 3, '{"opt1":4}', None, 1, 3]]

        self.assertEqual(obs, exp)
        # make sure job added to analysis correctly
        obs = self.conn_handler.execute_fetchall("SELECT * FROM "
                                                 "qiita.analysis_job WHERE "
                                                 "job_id = %d" % new_id)
        exp = [[1, new_id]]
        self.assertEqual(obs, exp)

        # make second job with diff datatype and command to test column insert
        new = qdb.job.Job.create("16S", "Beta Diversity", {"opt1": 4},
                                 qdb.analysis.Analysis(1),
                                 qdb.reference.Reference(2),
                                 qdb.software.Command(3))
        new_id = new.id
        self.assertEqual(new_id, self.job_id + 2)
        # make sure job inserted correctly
        obs = self.conn_handler.execute_fetchall("SELECT * FROM qiita.job "
                                                 "WHERE job_id = %d" % new_id)
        exp = [[new_id, 1, 1, 2, '{"opt1":4}', None, 2, 3]]
        self.assertEqual(obs, exp)
        # make sure job added to analysis correctly
        obs = self.conn_handler.execute_fetchall("SELECT * FROM "
                                                 "qiita.analysis_job WHERE "
                                                 "job_id = %d" % new_id)
        exp = [[1, new_id]]
        self.assertEqual(obs, exp)

    def test_create_exists(self):
        """Makes sure creation doesn't duplicate a job"""
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.job.Job.create(
                "18S", "Beta Diversity",
                {"--otu_table_fp": 1, "--mapping_fp": 1},
                qdb.analysis.Analysis(1), qdb.reference.Reference(2),
                qdb.software.Command(3))

    def test_create_exists_return_existing(self):
        """Makes sure creation doesn't duplicate a job by returning existing"""
        analysis = qdb.analysis.Analysis.create(
            qdb.user.User("demo@microbio.me"), "new", "desc")
        sql = """INSERT INTO qiita.analysis_sample
                        (analysis_id, artifact_id, sample_id)
                 VALUES ({0}, 4, '1.SKB8.640193'), ({0}, 4, '1.SKD8.640184'),
                        ({0}, 4, '1.SKB7.640196'), ({0}, 4, '1.SKM9.640192'),
                        ({0}, 4, '1.SKM4.640180')""".format(analysis.id)
        self.conn_handler.execute(sql)
        new = qdb.job.Job.create(
            "18S", "Beta Diversity", {"--otu_table_fp": 1, "--mapping_fp": 1},
            analysis, qdb.reference.Reference(2), qdb.software.Command(3),
            return_existing=True)
        self.assertEqual(new.id, self.job_id + 1)

    def test_retrieve_datatype(self):
        """Makes sure datatype retrieval is correct"""
        self.assertEqual(self.job.datatype, '18S')

    def test_retrieve_command(self):
        """Makes sure command retrieval is correct"""
        self.assertEqual(self.job.command, ['Alpha Rarefaction',
                                            'alpha_rarefaction.py'])

    def test_retrieve_options(self):
        exp = {
            '--output_dir': join(self._job_folder,
                                 ('%d_alpha_rarefaction.py_output_dir' %
                                  self.job_id)),
            'option2': 25,
            'option3': 'NEW',
            'option1': False}
        self.assertEqual(self.job.options, exp)

    def test_set_options(self):
        new = qdb.job.Job.create("18S", "Alpha Rarefaction",
                                 {"opt1": 4}, qdb.analysis.Analysis(1),
                                 qdb.reference.Reference(2),
                                 qdb.software.Command(3))
        new.options = self.options
        self.options['--output_dir'] = join(
            self._job_folder,
            '%d_alpha_rarefaction.py_output_dir' % new.id)
        self.assertEqual(new.options, self.options)

    def test_retrieve_results_folder(self):
        exp = ['%d_job_result.txt' % self.job_id,
               'my_folder/%d_file_in_folder.html' % self.job_id]
        self.assertEqual(self.job.results, exp)

    def test_retrieve_results_empty(self):
        new = qdb.job.Job.create("18S", "Beta Diversity", {"opt1": 4},
                                 qdb.analysis.Analysis(1),
                                 qdb.reference.Reference(2),
                                 qdb.software.Command(3))
        self.assertEqual(new.results, [])

    def test_set_error(self):
        before = datetime.now()
        self.job.set_error("TESTERROR")
        after = datetime.now()
        self.assertEqual(self.job.status, "error")

        error = self.job.error

        self.assertEqual(error.severity, 2)
        self.assertEqual(error.msg, 'TESTERROR')
        self.assertTrue(before < error.time < after)

    def test_retrieve_error_blank(self):
        self.assertEqual(self.job.error, None)

    def test_set_error_completed(self):
        self.job.status = "error"
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.job.set_error("TESTERROR")

    def test_retrieve_error_exists(self):
        self.job.set_error("TESTERROR")
        self.assertEqual(self.job.error.msg, "TESTERROR")

    def test_add_results(self):
        curr_id = self.conn_handler.execute_fetchone(
            "SELECT last_value FROM qiita.filepath_filepath_id_seq")[0]
        fp = join(self._job_folder, "%d_job_result_new.txt" % self.job_id)
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write("DATA")

        self.job.add_results([(fp, "plain_text")])

        # make sure files attached to job properly
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.job_results_filepath WHERE job_id = "
            "%d" % self.job_id)

        # the job now has 3 files, thus the - 1 and + 1
        self.assertEqual(obs, [[self.job_id, curr_id - 1],
                               [self.job_id, curr_id],
                               [self.job_id, curr_id + 1]])

    def test_add_results_dir(self):
        curr_id = self.conn_handler.execute_fetchone(
            "SELECT last_value FROM qiita.filepath_filepath_id_seq")[0]

        dfp = join(self._job_folder, "my_new_folder")
        ffp = join(dfp, "%d_file_in_new_folder.txt" % self.job_id)
        if not exists(dfp):
            mkdir(dfp)
        if not exists(ffp):
            with open(ffp, 'w') as f:
                f.write("DATA")
        self.job.add_results([(dfp, "directory")])

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.job_results_filepath WHERE job_id = "
            "%d" % self.job_id)

        # the job now has 3 files, thus the - 1 and + 1
        self.assertEqual(obs, [[self.job_id, curr_id - 1],
                               [self.job_id, curr_id],
                               [self.job_id, curr_id + 1]])

    def test_add_results_completed(self):
        self.job.status = "completed"
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.job.add_results([("/fake/dir/", "directory")])


@qiita_test_checker()
class CommandTest(TestCase):
    def setUp(self):
        com1 = qdb.job.Command(
            'Summarize Taxa', 'summarize_taxa_through_plots.py',
            '{"--otu_table_fp":null}', '{}',
            '{"--mapping_category":null, "--mapping_fp":null,'
            '"--sort":null}', '{"--output_dir":null}')
        com2 = qdb.job.Command(
            'Beta Diversity', 'beta_diversity_through_plots.py',
            '{"--otu_table_fp":null,"--mapping_fp":null}', '{}',
            '{"--tree_fp":null,"--color_by_all_fields":null,'
            '"--seqs_per_sample":null}', '{"--output_dir":null}')
        com3 = qdb.job.Command(
            'Alpha Rarefaction', 'alpha_rarefaction.py',
            '{"--otu_table_fp":null,"--mapping_fp":null}', '{}',
            '{"--tree_fp":null,"--num_steps":null,'
            '"--min_rare_depth"'
            ':null,"--max_rare_depth":null,'
            '"--retain_intermediate_files":false}',
            '{"--output_dir":null}')
        self.all_comms = {
            "16S": [com1, com2, com3],
            "18S": [com1, com2, com3],
            "ITS": [com2, com3],
            "Proteomic": [com2, com3],
            "Metabolomic": [com2, com3],
            "Metagenomic": [com2, com3],
        }

    def test_get_commands_by_datatype(self):
        obs = qdb.job.Command.get_commands_by_datatype()
        self.assertEqual(obs, self.all_comms)
        obs = qdb.job.Command.get_commands_by_datatype(["16S", "Metabolomic"])
        exp = {k: self.all_comms[k] for k in ('16S', 'Metabolomic')}
        self.assertEqual(obs, exp)

    def test_equal(self):
        commands = qdb.job.Command.create_list()
        self.assertTrue(commands[1] == commands[1])
        self.assertFalse(commands[1] == commands[2])
        self.assertFalse(commands[1] == qdb.job.Job(1))

    def test_not_equal(self):
        commands = qdb.job.Command.create_list()
        self.assertFalse(commands[1] != commands[1])
        self.assertTrue(commands[1] != commands[2])
        self.assertTrue(commands[1] != qdb.job.Job(1))


if __name__ == "__main__":
    main()
