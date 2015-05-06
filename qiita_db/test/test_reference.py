# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os import close, remove, listdir
from os.path import basename, join
from tempfile import mkstemp, mkdtemp

from qiita_core.util import qiita_test_checker
from qiita_db.exceptions import QiitaDBError
from qiita_db.reference import Reference, _rename_sortmerna_indexed_db_files
from qiita_db.util import get_mountpoint, get_count


@qiita_test_checker()
class ReferenceTests(TestCase):
    def setUp(self):
        self.name = "Fake_Greengenes"
        self.version = "13_8"

        fd, self.seqs_fp = mkstemp(suffix="_seqs.fna")
        close(fd)
        fd, self.tax_fp = mkstemp(suffix="_tax.txt")
        close(fd)
        fd, self.tree_fp = mkstemp(suffix="_tree.tre")
        close(fd)

        _, self.db_dir = get_mountpoint('reference')[0]

        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_create(self):
        """Correctly creates the rows in the DB for the reference"""
        fp_count = get_count('qiita.filepath')
        # Check that the returned object has the correct id
        # It raises a warning because the SortMeRNA DB is not provided
        obs = Reference.create(self.name, self.version, self.seqs_fp,
                               self.tax_fp, self.tree_fp)
        self.assertEqual(obs.id, 2)

        seqs_id = fp_count + 1
        tax_id = fp_count + 2
        tree_id = fp_count + 3

        # Check that the information on the database is correct
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.reference WHERE reference_id=2")
        exp = [[2, self.name, self.version, seqs_id, tax_id, tree_id, None]]
        self.assertEqual(obs, exp)

        # Check that the filepaths have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%s or "
            "filepath_id=%s or filepath_id=%s", (seqs_id, tax_id, tree_id))
        exp_seq = "%s_%s_%s" % (self.name, self.version,
                                basename(self.seqs_fp))
        exp_tax = "%s_%s_%s" % (self.name, self.version,
                                basename(self.tax_fp))
        exp_tree = "%s_%s_%s" % (self.name, self.version,
                                 basename(self.tree_fp))
        exp = [[seqs_id, exp_seq, 10, '0', 1, 6],
               [tax_id, exp_tax, 11, '0', 1, 6],
               [tree_id, exp_tree, 12, '0', 1, 6]]
        self.assertEqual(obs, exp)

    def test_create_with_smr_indexed_db(self):
        fp_count = get_count('qiita.filepath')

        # We need to create a sortmerna db
        suffixes = ['.bursttrie_0.dat', '.kmer_0.dat', '.pos_0.dat', '.stats']
        smr_dir = mkdtemp()
        for suf in suffixes:
            with open(join(smr_dir, "smr_db%s" % suf), 'w') as f:
                f.write('\n')
        smr_idx_db = join(smr_dir, "smr_db")

        new_id = get_count('qiita.reference') + 1
        obs = Reference.create(self.name, self.version, self.seqs_fp,
                               self.tax_fp, self.tree_fp,
                               sortmerna_indexed_db=smr_idx_db)

        self.assertEqual(obs.id, new_id)

        seqs_id = fp_count + 1
        tax_id = fp_count + 2
        tree_id = fp_count + 3
        smr_db_id = fp_count + 4

        # Check that the information on the DB is correct
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.reference WHERE reference_id = %s", (new_id,))
        exp = [[new_id, self.name, self.version, seqs_id, tax_id, tree_id,
                smr_db_id]]
        self.assertEqual(obs, exp)

        # Check that the filepaths have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath "
            "WHERE filepath_id IN (%s, %s, %s, %s) "
            "ORDER BY filepath_id",
            (seqs_id, tax_id, tree_id, smr_db_id))
        exp_seq = "%s_%s_%s" % (self.name, self.version,
                                basename(self.seqs_fp))
        exp_tax = "%s_%s_%s" % (self.name, self.version,
                                basename(self.tax_fp))
        exp_tree = "%s_%s_%s" % (self.name, self.version,
                                 basename(self.tree_fp))
        exp_smr_db = "%s_%s_smr_idx_%s" % (self.name, self.version,
                                           basename(smr_dir))
        exp = [[seqs_id, exp_seq, 10, '0', 1, 6],
               [tax_id, exp_tax, 11, '0', 1, 6],
               [tree_id, exp_tree, 12, '0', 1, 6],
               [smr_db_id, exp_smr_db, 8, '1498725178', 1, 6]]
        self.assertEqual(obs, exp)

        exp = {"%s_%s%s" % (self.name, self.version, suf) for suf in suffixes}
        obs = set(listdir(join(self.db_dir, exp_smr_db)))
        self.assertEqual(obs, exp)

    def test_sequence_fp(self):
        ref = Reference(1)
        exp = join(self.db_dir, "GreenGenes_13_8_97_otus.fasta")
        self.assertEqual(ref.sequence_fp, exp)

    def test_taxonomy_fp(self):
        ref = Reference(1)
        exp = join(self.db_dir, "GreenGenes_13_8_97_otu_taxonomy.txt")
        self.assertEqual(ref.taxonomy_fp, exp)

    def test_no_taxonomy_fp(self):
        ref = Reference.create(self.name, self.version, self.seqs_fp,
                               tree_fp=self.tree_fp)
        self.assertEqual(ref.taxonomy_fp, None)

    def test_tree_fp(self):
        ref = Reference(1)
        exp = join(self.db_dir, "GreenGenes_13_8_97_otus.tree")
        self.assertEqual(ref.tree_fp, exp)

    def test_no_tree_fp(self):
        ref = Reference.create(self.name, self.version, self.seqs_fp,
                               tax_fp=self.tax_fp)
        self.assertEqual(ref.tree_fp, None)

    def test_no_sortmerna_db(self):
        ref = Reference(1)
        self.assertEqual(ref.sortmerna_db, None)

    def test_sortmerna_db(self):
        # We need to create a sortmerna db
        suffixes = ['.bursttrie_0.dat', '.kmer_0.dat', '.pos_0.dat', '.stats']
        smr_dir = mkdtemp()
        for suf in suffixes:
            with open(join(smr_dir, "smr_db%s" % suf), 'w') as f:
                f.write('\n')
        smr_idx_db = join(smr_dir, "smr_db")

        ref = Reference.create(self.name, self.version, self.seqs_fp,
                               self.tax_fp, self.tree_fp,
                               sortmerna_indexed_db=smr_idx_db)

        exp = join(
            self.db_dir,
            "%s_%s_smr_idx_%s" % (self.name, self.version, basename(smr_dir)),
            "%s_%s" % (self.name, self.version))
        self.assertEqual(ref.sortmerna_db, exp)

    def test_rename_sortmerna_indexed_db_files(self):
        suffixes = ['.bursttrie_0.dat', '.kmer_0.dat', '.pos_0.dat',
                    '.bursttrie_10.dat', '.kmer_10.dat', '.pos_10.dat',
                    '.stats']
        smr_dir = mkdtemp()
        for suf in suffixes:
            with open(join(smr_dir, "smr_db%s" % suf), 'w') as f:
                f.write('\n')
        smr_idx_db = join(smr_dir, "smr_db")

        # Add non-SortMeRNA db files to the folder to check that they're
        # not renames
        with open(join(smr_dir, "test.txt"), 'w') as f:
            f.write('\n')

        _rename_sortmerna_indexed_db_files(smr_idx_db, "test_db",  "v_0_1")

        obs = set(listdir(join(self.db_dir, smr_dir)))
        exp = {"test_db_v_0_1%s" % suf for suf in suffixes}
        exp.add("test.txt")
        self.assertEqual(obs, exp)

    def test_rename_sortmerna_indexed_db_files_error_no_stats(self):
        suffixes = ['.bursttrie_0.dat', '.kmer_0.dat', '.pos_0.dat']
        smr_dir = mkdtemp()
        for suf in suffixes:
            with open(join(smr_dir, "smr_db%s" % suf), 'w') as f:
                f.write('\n')
        smr_idx_db = join(smr_dir, "smr_db")

        with self.assertRaises(QiitaDBError):
            _rename_sortmerna_indexed_db_files(smr_idx_db, "test_db",  "v_0_1")

    def test_rename_sortmerna_indexed_db_files_error_no_dynamic(self):
        suffixes = ['.bursttrie_0.dat', '.kmer_0.dat', '.stats']
        smr_dir = mkdtemp()
        for suf in suffixes:
            with open(join(smr_dir, "smr_db%s" % suf), 'w') as f:
                f.write('\n')
        smr_idx_db = join(smr_dir, "smr_db")

        with self.assertRaises(QiitaDBError):
            _rename_sortmerna_indexed_db_files(smr_idx_db, "test_db",  "v_0_1")

if __name__ == '__main__':
    main()
