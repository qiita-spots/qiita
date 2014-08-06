from unittest import TestCase, main

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import qiita_test_checker
from qiita_db.analysis import Analysis
from qiita_db.job import Job
from qiita_db.user import User
from qiita_db.data import ProcessedData
from qiita_db.exceptions import (QiitaDBDuplicateError, QiitaDBColumnError,
                                 QiitaDBStatusError)
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


@qiita_test_checker()
class TestAnalysis(TestCase):
    def setUp(self):
        self.analysis = Analysis(1)

    def test_lock_check(self):
        self.analysis.status = "public"
        with self.assertRaises(QiitaDBStatusError):
            self.analysis._lock_check(self.conn_handler)

    def test_lock_check_ok(self):
        self.analysis.status = "in_construction"
        self.analysis._lock_check(self.conn_handler)

    def test_get_public(self):
        self.assertEqual(Analysis.get_public(), [])
        self.analysis.status = "public"
        self.assertEqual(Analysis.get_public(), [1])

    def test_create(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis")
        self.assertEqual(new.id, 3)
        sql = "SELECT * FROM qiita.analysis WHERE analysis_id = 3"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [[3, 'admin@foo.bar', 'newAnalysis',
                                'A New Analysis', 1, None]])

    def test_create_parent(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        self.assertEqual(new.id, 3)
        sql = "SELECT * FROM qiita.analysis WHERE analysis_id = 3"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [[3, 'admin@foo.bar', 'newAnalysis',
                                'A New Analysis', 1, None]])

        sql = "SELECT * FROM qiita.analysis_chain WHERE child_id = 3"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [[1, 3]])

    def test_retrieve_owner(self):
        self.assertEqual(self.analysis.owner, "test@foo.bar")

    def test_retrieve_name(self):
        self.assertEqual(self.analysis.name, "SomeAnalysis")

    def test_retrieve_description(self):
        self.assertEqual(self.analysis.description, "A test analysis")

    def test_set_description(self):
        self.analysis.description = "New description"
        self.assertEqual(self.analysis.description, "New description")

    def test_retrieve_samples(self):
        exp = {1: ['SKB8.640193', 'SKD8.640184', 'SKB7.640196',
                   'SKM9.640192', 'SKM4.640180']}
        self.assertEqual(self.analysis.samples, exp)

    def test_retrieve_shared_with(self):
        self.assertEqual(self.analysis.shared_with, ["shared@foo.bar"])

    def test_retrieve_biom_tables(self):
        self.assertEqual(self.analysis.biom_tables, [7])

    def test_retrieve_biom_tables_none(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        self.assertEqual(new.biom_tables, None)

    def test_set_step(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        new.step = 2
        sql = "SELECT * FROM qiita.analysis_workflow WHERE analysis_id = 3"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [[3, 2]])

    def test_set_step_twice(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        new.step = 2
        new.step = 4
        sql = "SELECT * FROM qiita.analysis_workflow WHERE analysis_id = 3"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [[3, 4]])

    def test_retrive_step(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        new.step = 2
        self.assertEqual(new.step, 2)

    def test_retrieve_step_new(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        with self.assertRaises(ValueError):
            new.step

    def test_retrieve_step_locked(self):
        self.analysis.status = "queued"
        with self.assertRaises(QiitaDBStatusError):
            self.analysis.step = 3

    def test_retrieve_jobs(self):
        self.assertEqual(self.analysis.jobs, [1, 2])

    def test_retrieve_jobs_none(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        self.assertEqual(new.jobs, None)

    def test_retrieve_pmid(self):
        self.assertEqual(self.analysis.pmid, "121112")

    def test_retrieve_pmid_none(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        self.assertEqual(new.pmid, None)

    def test_set_pmid(self):
        self.analysis.pmid = "11211221212213"
        self.assertEqual(self.analysis.pmid, "11211221212213")

    # def test_get_parent(self):
    #     raise NotImplementedError()

    # def test_get_children(self):
    #     raise NotImplementedError()

    def test_add_samples(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis")
        new.add_samples([(1, 'SKB8.640193')])

    def test_remove_samples(self):
        self.analysis.remove_samples([(1, 'SKB8.640193'), (1, 'SKD8.640184')])

    def test_add_biom_tables(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis")
        new.add_biom_tables([ProcessedData(1)])
        self.assertEqual(new.biom_tables, [7])

    def test_remove_biom_tables(self):
        self.analysis.remove_biom_tables([ProcessedData(1)])
        self.assertEqual(self.analysis.biom_tables, None)

    def test_add_jobs(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis")
        new.add_jobs([Job(1)])
        self.assertEqual(new.jobs, [1])

    def test_share(self):
        self.analysis.share(User("admin@foo.bar"))
        self.assertEqual(self.analysis.shared_with, ["shared@foo.bar",
                                                     "admin@foo.bar"])

    def test_unshare(self):
        self.analysis.unshare(User("shared@foo.bar"))
        self.assertEqual(self.analysis.shared_with, [])

    def test_finish_workflow(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        new.step = 2
        new.finish_workflow()

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.analysis_workflow WHERE analysis_id = 3")
        self.assertEqual(obs, [])
        self.assertEqual(new.status, "queued")


if __name__ == "__main__":
    main()
