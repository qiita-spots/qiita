from unittest import TestCase, main
from tempfile import mkstemp
from os import close, remove
from os.path import exists

import pandas as pd

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


@qiita_test_checker()
class TestSQL(TestCase):
    """Tests that the database triggers and procedures work properly"""
    def setUp(self):
        self._files_to_remove = []

    def tearDown(self):
        for fp in self._files_to_remove:
            if exists(fp):
                remove(fp)

    def test_collection_job_trigger_bad_insert(self):
        # make sure an incorrect job raises an error
        with self.assertRaises(ValueError):
            self.conn_handler.execute(
                'INSERT INTO qiita.collection_job (collection_id, job_id) '
                'VALUES (1, 3)')
        obs = self.conn_handler.execute_fetchall(
            'SELECT * FROM qiita.collection_job')
        exp = [[1, 1]]
        self.assertEqual(obs, exp)

    def test_collection_job_trigger(self):
        # make sure a correct job inserts successfully
        self.conn_handler.execute(
            'INSERT INTO qiita.collection_job (collection_id, job_id) '
            'VALUES (1, 2)')
        obs = self.conn_handler.execute_fetchall(
            'SELECT * FROM qiita.collection_job')
        exp = [[1, 1], [1, 2]]
        self.assertEqual(obs, exp)

    def test_find_artifact_roots_is_root(self):
        """Correctly returns the root if the artifact is already the root"""
        sql = "SELECT * FROM qiita.find_artifact_roots(%s)"
        obs = self.conn_handler.execute_fetchall(sql, [1])
        exp = [[1]]
        self.assertEqual(obs, exp)

    def test_find_artifact_roots_is_child(self):
        """Correctly returns the root if the artifact is a child"""
        sql = "SELECT * FROM qiita.find_artifact_roots(%s)"
        obs = self.conn_handler.execute_fetchall(sql, [4])
        exp = [[1]]
        self.assertEqual(obs, exp)

    def test_find_artifact_roots_is_child_multiple_parents_one_root(self):
        """Correctly returns the roots if the children has multiple parents
           but a single root
        """
        sql = "SELECT * FROM qiita.find_artifact_roots(%s)"
        fd, fp = mkstemp(suffix='_table.biom')
        close(fd)
        self._files_to_remove.append(fp)
        with open(fp, 'w') as f:
            f.write("test")
        fp = [(fp, 7)]
        params = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(10), {'input_data': 2})
        new = qdb.artifact.Artifact.create(
            fp, "BIOM",
            parents=[qdb.artifact.Artifact(2), qdb.artifact.Artifact(3)],
            processing_parameters=params,
            can_be_submitted_to_ebi=True,
            can_be_submitted_to_vamps=True)
        self._files_to_remove.extend([afp for _, afp, _ in new.filepaths])
        obs = self.conn_handler.execute_fetchall(sql, [new.id])
        exp = [[1]]
        self.assertEqual(obs, exp)

    def _create_root_artifact(self):
        """Creates a new root artifact"""
        metadata = pd.DataFrame.from_dict(
            {'SKB8.640193': {'center_name': 'ANL',
                             'primer': 'GTGCCAGCMGCCGCGGTAA',
                             'barcode': 'GTCCGCAAGTTA',
                             'run_prefix': "s_G1_L001_sequences",
                             'platform': 'ILLUMINA',
                             'instrument_model': 'Illumina MiSeq',
                             'library_construction_protocol': 'AAAA',
                             'experiment_design_description': 'BBBB'}},
            orient='index')
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, qdb.study.Study(1), "18S")
        fd, fp = mkstemp(suffix='_seqs.fastq')
        close(fd)
        self._files_to_remove.append(fp)
        with open(fp, 'w') as f:
            f.write("test")
        fp = [(fp, 1)]
        new_root = qdb.artifact.Artifact.create(fp, "FASTQ", prep_template=pt)
        self._files_to_remove.extend(
            [afp for _, afp, _ in new_root.filepaths])
        return new_root

    def test_find_artifact_roots_is_root_without_children(self):
        """Correctly returns the root if the artifact is already the root
           and doesn't have any children
         """
        sql = "SELECT * FROM qiita.find_artifact_roots(%s)"

        # Add a new root
        new_root = self._create_root_artifact()
        obs = self.conn_handler.execute_fetchall(sql, [new_root.id])
        exp = [[new_root.id]]
        self.assertEqual(obs, exp)

    def test_find_artifact_roots_is_child_multiple_parents_multiple_root(self):
        """Correctly returns the roots if the children has multiple roots"""
        sql = "SELECT * FROM qiita.find_artifact_roots(%s)"

        new_root = self._create_root_artifact()

        # Add a child of 2 roots
        fd, fp = mkstemp(suffix='_seqs.fna')
        close(fd)
        self._files_to_remove.append(fp)
        with open(fp, 'w') as f:
            f.write("test")
        fp = [(fp, 4)]
        params = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 2})
        new = qdb.artifact.Artifact.create(
            fp, "Demultiplexed", parents=[qdb.artifact.Artifact(1), new_root],
            processing_parameters=params)
        self._files_to_remove.extend([afp for _, afp, _ in new.filepaths])
        obs = self.conn_handler.execute_fetchall(sql, [new.id])
        exp = [[1], [new_root.id]]
        self.assertEqual(obs, exp)

    def test_artifact_ancestry_root(self):
        """Correctly returns the ancestry of a root artifact"""
        sql = "SELECT * FROM qiita.artifact_ancestry(%s)"
        obs = self.conn_handler.execute_fetchall(sql, [1])
        exp = []
        self.assertEqual(obs, exp)

    def test_artifact_ancestry_leaf(self):
        """Correctly returns the ancestry of a leaf artifact"""
        sql = "SELECT * FROM qiita.artifact_ancestry(%s)"
        obs = self.conn_handler.execute_fetchall(sql, [4])
        exp = [[4, 2], [2, 1]]
        self.assertItemsEqual(obs, exp)

    def test_artifact_ancestry_leaf_multiple_parents(self):
        """Correctly returns the ancestry of a leaf artifact w multiple parents
        """
        sql = """INSERT INTO qiita.parent_artifact (artifact_id, parent_id)
                 VALUES (%s, %s)"""
        self.conn_handler.execute(sql, [4, 3])
        sql = "SELECT * FROM qiita.artifact_ancestry(%s)"
        obs = self.conn_handler.execute_fetchall(sql, [4])
        exp = [[4, 3], [3, 1], [4, 2], [2, 1]]
        self.assertItemsEqual(obs, exp)

    def test_artifact_ancestry_middle(self):
        """Correctly returns the ancestry of an artifact in the middle of the
        DAG"""
        sql = "SELECT * FROM qiita.artifact_ancestry(%s)"
        obs = self.conn_handler.execute_fetchall(sql, [2])
        exp = [[2, 1]]
        self.assertEqual(obs, exp)

    def test_artifact_descendants_leaf(self):
        """Correctly returns the descendants of a leaf artifact"""
        sql = "SELECT * FROM qiita.artifact_descendants(%s)"
        obs = self.conn_handler.execute_fetchall(sql, [4])
        exp = []
        self.assertEqual(obs, exp)

    def test_artifact_descendants_root(self):
        """Correctly returns the descendants of a root artifact"""
        sql = "SELECT * FROM qiita.artifact_descendants(%s)"
        obs = self.conn_handler.execute_fetchall(sql, [1])
        exp = [[2, 1], [3, 1], [4, 2], [5, 2], [6L, 2L]]
        self.assertItemsEqual(obs, exp)

    def test_artifact_descendants_middle(self):
        """Correctly returns the descendants of an artifact in the middle of
        the DAG"""
        sql = "SELECT * FROM qiita.artifact_descendants(%s)"
        obs = self.conn_handler.execute_fetchall(sql, [2])
        exp = [[4, 2], [5, 2], [6L, 2L]]
        self.assertItemsEqual(obs, exp)


if __name__ == '__main__':
    main()
