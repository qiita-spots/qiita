# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os import close, remove
from os.path import basename, join
from tempfile import mkstemp

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


@qiita_test_checker()
class ReferenceTests(TestCase):
    def setUp(self):
        self.name = "Fake Greengenes"
        self.version = "13_8"

        fd, self.seqs_fp = mkstemp(suffix="_seqs.fna")
        close(fd)
        fd, self.tax_fp = mkstemp(suffix="_tax.txt")
        close(fd)
        fd, self.tree_fp = mkstemp(suffix="_tree.tre")
        close(fd)

        _, self.db_dir = qdb.util.get_mountpoint('reference')[0]

        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_create(self):
        """Correctly creates the rows in the DB for the reference"""
        # Check that the returned object has the correct id
        obs = qdb.reference.Reference.create(
            self.name, self.version, self.seqs_fp, self.tax_fp, self.tree_fp)
        self.assertEqual(obs.id, 3)

        # Check that the information on the database is correct
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.reference WHERE reference_id=3")
        self.assertEqual(obs[0][1], self.name)
        self.assertEqual(obs[0][2], self.version)

        seqs_id = obs[0][3]
        tax_id = obs[0][4]
        tree_id = obs[0][5]

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

    def test_sequence_fp(self):
        ref = qdb.reference.Reference(1)
        exp = join(self.db_dir, "GreenGenes_13_8_97_otus.fasta")
        self.assertEqual(ref.sequence_fp, exp)

    def test_taxonomy_fp(self):
        ref = qdb.reference.Reference(1)
        exp = join(self.db_dir, "GreenGenes_13_8_97_otu_taxonomy.txt")
        self.assertEqual(ref.taxonomy_fp, exp)

    def test_tree_fp(self):
        ref = qdb.reference.Reference(1)
        exp = join(self.db_dir, "GreenGenes_13_8_97_otus.tree")
        self.assertEqual(ref.tree_fp, exp)

    def test_tree_fp_empty(self):
        ref = qdb.reference.Reference(2)
        self.assertEqual(ref.tree_fp, '')

if __name__ == '__main__':
    main()
