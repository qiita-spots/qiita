# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os import close, remove
from os.path import exists
from tempfile import mkstemp
from unittest import TestCase, main

import pandas as pd

import qiita_db as qdb
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class TestSQL(TestCase):
    """Tests that the database triggers and procedures work properly"""

    def setUp(self):
        self._files_to_remove = []

    def tearDown(self):
        for fp in self._files_to_remove:
            if exists(fp):
                remove(fp)

    def test_find_artifact_roots_is_root(self):
        """Correctly returns the root if the artifact is already the root"""
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.find_artifact_roots(%s)"
            qdb.sql_connection.TRN.add(sql, [1])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [[1]]
        self.assertEqual(obs, exp)

    def test_find_artifact_roots_is_child(self):
        """Correctly returns the root if the artifact is a child"""
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.find_artifact_roots(%s)"
            qdb.sql_connection.TRN.add(sql, [4])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [[1]]
        self.assertEqual(obs, exp)

    def test_find_artifact_roots_is_child_multiple_parents_one_root(self):
        """Correctly returns the roots if the children has multiple parents
        but a single root
        """
        fd, fp = mkstemp(suffix="_table.biom")
        close(fd)
        self._files_to_remove.append(fp)
        with open(fp, "w") as f:
            f.write("test")
        fp = [(fp, 7)]
        params = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(10), {"input_data": 2}
        )
        new = qdb.artifact.Artifact.create(
            fp,
            "BIOM",
            parents=[qdb.artifact.Artifact(2), qdb.artifact.Artifact(3)],
            processing_parameters=params,
        )
        self._files_to_remove.extend([x["fp"] for x in new.filepaths])
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.find_artifact_roots(%s)"
            qdb.sql_connection.TRN.add(sql, [new.id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [[1]]
        self.assertEqual(obs, exp)

    def _create_root_artifact(self):
        """Creates a new root artifact"""
        metadata = pd.DataFrame.from_dict(
            {
                "SKB8.640193": {
                    "center_name": "ANL",
                    "primer": "GTGCCAGCMGCCGCGGTAA",
                    "barcode": "GTCCGCAAGTTA",
                    "run_prefix": "s_G1_L001_sequences",
                    "platform": "Illumina",
                    "target_gene": "16S rRNA",
                    "target_subfragment": "V4",
                    "instrument_model": "Illumina MiSeq",
                    "library_construction_protocol": "AAAA",
                    "experiment_design_description": "BBBB",
                }
            },
            orient="index",
            dtype=str,
        )
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, qdb.study.Study(1), "18S"
        )
        fd, fp = mkstemp(suffix="_seqs.fastq")
        close(fd)
        self._files_to_remove.append(fp)
        with open(fp, "w") as f:
            f.write("test")
        fp = [(fp, 1)]
        new_root = qdb.artifact.Artifact.create(fp, "FASTQ", prep_template=pt)
        self._files_to_remove.extend([x["fp"] for x in new_root.filepaths])
        return new_root

    def _create_child_artifact(self, parents):
        """Creates a new artifact with the given parents"""
        # Add a child of 2 roots
        fd, fp = mkstemp(suffix="_seqs.fna")
        close(fd)
        self._files_to_remove.append(fp)
        with open(fp, "w") as f:
            f.write("test")
        fp = [(fp, 4)]
        params = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": 2}
        )
        new = qdb.artifact.Artifact.create(
            fp, "Demultiplexed", parents=parents, processing_parameters=params
        )
        return new

    def test_find_artifact_roots_is_root_without_children(self):
        """Correctly returns the root if the artifact is already the root
        and doesn't have any children
        """
        sql = "SELECT * FROM qiita.find_artifact_roots(%s)"

        # Add a new root
        new_root = self._create_root_artifact()
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql, [new_root.id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [[new_root.id]]
        self.assertEqual(obs, exp)

    def test_find_artifact_roots_is_child_multiple_parents_multiple_root(self):
        """Correctly returns the roots if the children has multiple roots"""
        sql = "SELECT * FROM qiita.find_artifact_roots(%s)"

        new_root = self._create_root_artifact()

        # Add a child of 2 roots
        fd, fp = mkstemp(suffix="_seqs.fna")
        close(fd)
        self._files_to_remove.append(fp)
        with open(fp, "w") as f:
            f.write("test")
        fp = [(fp, 4)]
        params = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {"input_data": 2}
        )
        new = qdb.artifact.Artifact.create(
            fp,
            "Demultiplexed",
            parents=[qdb.artifact.Artifact(1), new_root],
            processing_parameters=params,
        )
        self._files_to_remove.extend([x["fp"] for x in new.filepaths])
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql, [new.id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [[1], [new_root.id]]
        self.assertCountEqual(obs, exp)

    def test_artifact_ancestry_root(self):
        """Correctly returns the ancestry of a root artifact"""
        sql = "SELECT * FROM qiita.artifact_ancestry(%s)"
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql, [1])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = []
        self.assertEqual(obs, exp)

    def test_artifact_ancestry_leaf(self):
        """Correctly returns the ancestry of a leaf artifact"""
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.artifact_ancestry(%s)"
            qdb.sql_connection.TRN.add(sql, [4])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [[4, 2], [2, 1]]
        self.assertCountEqual(obs, exp)

    def test_artifact_ancestry_leaf_multiple_parents(self):
        """Correctly returns the ancestry of a leaf artifact w multiple parents"""
        root = self._create_root_artifact()
        parent1 = self._create_child_artifact([root])
        parent2 = self._create_child_artifact([root])
        child = self._create_child_artifact([parent1, parent2])

        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.artifact_ancestry(%s)"
            qdb.sql_connection.TRN.add(sql, [child.id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [
            [child.id, parent1.id],
            [child.id, parent2.id],
            [parent1.id, root.id],
            [parent2.id, root.id],
        ]
        self.assertCountEqual(obs, exp)

    def test_artifact_ancestry_middle(self):
        """Correctly returns the ancestry of an artifact in the middle of the
        DAG"""
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.artifact_ancestry(%s)"
            qdb.sql_connection.TRN.add(sql, [2])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [[2, 1]]
        self.assertEqual(obs, exp)

    def test_artifact_descendants_leaf(self):
        """Correctly returns the descendants of a leaf artifact"""
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.artifact_descendants(%s)"
            qdb.sql_connection.TRN.add(sql, [4])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = []
        self.assertEqual(obs, exp)

    def test_artifact_descendants_root(self):
        """Correctly returns the descendants of a root artifact"""
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.artifact_descendants(%s)"
            qdb.sql_connection.TRN.add(sql, [1])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [[2, 1], [3, 1], [4, 2], [5, 2], [6, 2]]
        self.assertCountEqual(obs, exp)

    def test_artifact_descendants_middle(self):
        """Correctly returns the descendants of an artifact in the middle of
        the DAG"""
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.artifact_descendants(%s)"
            qdb.sql_connection.TRN.add(sql, [2])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [[4, 2], [5, 2], [6, 2]]
        self.assertCountEqual(obs, exp)

    def test_isnumeric(self):
        """Test SQL function isnumeric"""
        exp = [
            ["", False],
            [".", False],
            [".0", True],
            ["0.", True],
            ["0", True],
            ["1", True],
            ["123", True],
            ["123.456", True],
            ["abc", False],
            ["1..2", False],
            ["1.2.3.4", False],
            ["1x234", False],
            ["1.234e-5", True],
        ]

        sql = (
            "WITH test(x) AS ("
            "VALUES (''), ('.'), ('.0'), ('0.'), ('0'), ('1'), ('123'), "
            "('123.456'), ('abc'), ('1..2'), ('1.2.3.4'), ('1x234'), "
            "('1.234e-5')) SELECT x, isnumeric(x) FROM test;"
        )
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql)
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        self.assertEqual(exp, obs)

    def test_artifact_descendants_with_jobs(self):
        """Test SQL function artifact_descendants_with_jobs"""
        exp = [
            ["c350b068-add7-49a5-8846-604ac032cc88", 1, 2],
            ["d883dab4-503b-45c2-815d-2126ff52dede", 1, 3],
            ["a4c4b9b9-20ca-47f5-bd30-725cce71df2b", 2, 4],
            ["624dce65-43a5-4156-a4b6-6c1d02114b67", 2, 5],
            ["81bbe8d0-b4c2-42eb-ada9-f07c1c91e59f", 2, 6],
        ]
        sql = """SELECT * FROM qiita.artifact_descendants_with_jobs(1)"""
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql)
            obs = qdb.sql_connection.TRN.execute_fetchindex()

        # lopping on results to not test the job id as is randomly generated
        for e, o in zip(exp, obs):
            self.assertEqual(e[1:], o[1:])


if __name__ == "__main__":
    main()
