from unittest import TestCase, main
from os.path import exists, join
from os import remove

from biom import load_table

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import qiita_test_checker
from qiita_db.analysis import Analysis
from qiita_db.job import Job
from qiita_db.user import User
from qiita_db.data import ProcessedData
from qiita_db.exceptions import (QiitaDBDuplicateError, QiitaDBColumnError,
                                 QiitaDBStatusError)
from qiita_db.util import get_work_base_dir, get_db_files_base_dir
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
        for status in ["queued", "running", "public", "completed",
                       "error"]:
            new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                                  "A New Analysis")
            new.status = status
            with self.assertRaises(QiitaDBStatusError):
                new._lock_check(self.conn_handler)

    def test_lock_check_ok(self):
        self.analysis.status = "in_construction"
        self.analysis._lock_check(self.conn_handler)

    def test_status_setter_checks(self):
        self.analysis.status = "public"
        with self.assertRaises(QiitaDBStatusError):
            self.analysis.status = "queued"

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

    def test_retrieve_data_types(self):
        exp = ['18S']
        self.assertEqual(self.analysis.data_types, exp)

    def test_retrieve_shared_with(self):
        self.assertEqual(self.analysis.shared_with, ["shared@foo.bar"])

    def test_retrieve_biom_tables(self):
        exp = {"18S": join(get_db_files_base_dir(), "analysis",
                           "1_analysis_18S.biom")}
        self.assertEqual(self.analysis.biom_tables, exp)

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
        self.analysis.status = "public"
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

    def test_retrieve_mapping_file(self):
        exp = join(get_db_files_base_dir(), "analysis",
                   "1_analysis_mapping.txt")
        obs = self.analysis.mapping_file
        self.assertEqual(obs, exp)
        self.assertTrue(exists(exp))

    def test_retrieve_mapping_file_none(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        obs = new.mapping_file
        self.assertEqual(obs, None)

    # def test_get_parent(self):
    #     raise NotImplementedError()

    # def test_get_children(self):
    #     raise NotImplementedError()

    def test_add_samples(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis")
        new.add_samples([(1, 'SKB8.640193'), (1, 'SKD5.640186')])
        exp = {1: ['SKB8.640193', 'SKD5.640186']}
        self.assertEqual(new.samples, exp)

    def test_remove_samples_both(self):
        self.analysis.remove_samples(proc_data=(1, ),
                                     samples=('SKB8.640193', ))
        exp = {1: ['SKD8.640184', 'SKB7.640196', 'SKM9.640192', 'SKM4.640180']}
        self.assertEqual(self.analysis.samples, exp)

    def test_remove_samples_samples(self):
        self.analysis.remove_samples(samples=('SKD8.640184', ))
        exp = {1: ['SKB8.640193', 'SKB7.640196', 'SKM9.640192', 'SKM4.640180']}
        self.assertEqual(self.analysis.samples, exp)

    def test_remove_samples_processed_data(self):
        self.analysis.remove_samples(proc_data=(1, ))
        exp = {}
        self.assertEqual(self.analysis.samples, exp)

    def test_share(self):
        self.analysis.share(User("admin@foo.bar"))
        self.assertEqual(self.analysis.shared_with, ["shared@foo.bar",
                                                     "admin@foo.bar"])

    def test_unshare(self):
        self.analysis.unshare(User("shared@foo.bar"))
        self.assertEqual(self.analysis.shared_with, [])

    def test_get_samples(self):
        obs = self.analysis._get_samples()
        exp = {1: ['SKB7.640196', 'SKB8.640193', 'SKD8.640184', 'SKM4.640180',
                   'SKM9.640192']}
        self.assertEqual(obs, exp)

    def test_build_mapping_file(self):
        map_fp = join(get_db_files_base_dir(), "analysis",
                      "1_analysis_mapping.txt")
        try:
            samples = {1: ['SKB8.640193', 'SKD8.640184', 'SKB7.640196']}
            self.analysis._build_mapping_file(samples,
                                              conn_handler=self.conn_handler)
            obs = self.analysis.mapping_file
            self.assertEqual(obs, map_fp)

            with open(map_fp) as f:
                mapdata = f.readlines()
            # check some columns for correctness
            obs = [line.split('\t')[0] for line in mapdata]
            exp = ['#SampleID', 'SKB8.640193', 'SKD8.640184', 'SKB7.640196']
            self.assertEqual(obs, exp)

            obs = [line.split('\t')[1] for line in mapdata]
            exp = ['BarcodeSequence', 'AGCGCTCACATC', 'TGAGTGGTCTGT',
                   'CGGCCTAAGTTC']
            self.assertEqual(obs, exp)

            obs = [line.split('\t')[2] for line in mapdata]
            exp = ['LinkerPrimerSequence', 'GTGCCAGCMGCCGCGGTAA',
                   'GTGCCAGCMGCCGCGGTAA', 'GTGCCAGCMGCCGCGGTAA']
            self.assertEqual(obs, exp)

            obs = [line.split('\t')[19] for line in mapdata]
            exp = ['host_subject_id', '1001:M7', '1001:D9',
                   '1001:M8']
            self.assertEqual(obs, exp)

            obs = [line.split('\t')[47] for line in mapdata]
            exp = ['tot_org_carb', '5.0', '4.32', '5.0']
            self.assertEqual(obs, exp)

            obs = [line.split('\t')[-1] for line in mapdata]
            exp = ['Description\n'] + ['Cannabis Soil Microbiome\n'] * 3
            self.assertEqual(obs, exp)
        finally:
            with open(map_fp, 'w') as f:
                f.write("")

    def test_build_mapping_file_duplicate_samples(self):
        samples = {1: ['SKB8.640193', 'SKB8.640193', 'SKD8.640184']}
        with self.assertRaises(ValueError):
            self.analysis._build_mapping_file(samples,
                                              conn_handler=self.conn_handler)

    def test_build_biom_tables(self):
        biom_fp = join(get_db_files_base_dir(), "analysis",
                       "1_analysis_18S.biom")
        try:
            samples = {1: ['SKB8.640193', 'SKD8.640184', 'SKB7.640196']}
            self.analysis._build_biom_tables(samples,
                                             conn_handler=self.conn_handler)
            obs = self.analysis.biom_tables

            self.assertEqual(obs, {'18S': biom_fp})

            table = load_table(biom_fp)
            obs = set(table.ids(axis='sample'))
            exp = {'SKB8.640193', 'SKD8.640184', 'SKB7.640196'}
            self.assertEqual(obs, exp)
        finally:
            with open(biom_fp, 'w') as f:
                f.write("")

    def test_build_files(self):
        biom_fp = join(get_db_files_base_dir(), "analysis",
                       "1_analysis_18S.biom")
        map_fp = join(get_db_files_base_dir(), "analysis",
                      "1_analysis_mapping.txt")
        try:
            self.analysis.build_files()
        finally:
            with open(biom_fp, 'w') as f:
                f.write("")
            with open(map_fp, 'w') as f:
                f.write("")


if __name__ == "__main__":
    main()
