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
from qiita_db.reference import Reference
from qiita_db.util import get_mountpoint, get_count
from qiita_db.sql_connection import Transaction


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

        _, self.db_dir = get_mountpoint('reference')[0]

        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_create(self):
        """Correctly creates the rows in the DB for the reference"""
        fp_count = get_count('qiita.filepath')
        # Check that the returned object has the correct id
        obs = Reference.create(self.name, self.version, self.seqs_fp,
                               self.tax_fp, self.tree_fp)
        self.assertEqual(obs.id, 2)

        seqs_id = fp_count + 1
        tax_id = fp_count + 2
        tree_id = fp_count + 3

        # Check that the information on the database is correct
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.reference WHERE reference_id=2")
        exp = [[2, self.name, self.version, seqs_id, tax_id, tree_id]]
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

    def test_exists(self):
        self.assertTrue(Reference.exists("Greengenes", "13_8"))
        self.assertFalse(Reference.exists("NotAReference", "13_8"))
        self.assertFalse(Reference.exists("Greengenes", "13_5"))
        with Transaction("test_exists") as trans:
            self.assertTrue(
                Reference.exists("Greengenes", "13_8", trans=trans))
            self.assertFalse(
                Reference.exists("NotAReference", "13_8", trans=trans))
            self.assertFalse(
                Reference.exists("Greengenes", "13_5", trans=trans))

    def test_name(self):
        ref = Reference(1)
        self.assertEqual(ref.name(), "Greengenes")
        with Transaction("test_name") as trans:
            self.assertEqual(ref.name(trans=trans), "Greengenes")

    def test_version(self):
        ref = Reference(1)
        self.assertEqual(ref.version(), "13_8")
        with Transaction("test_version") as trans:
            self.assertEqual(ref.version(trans=trans), "13_8")

    def test_sequence_fp(self):
        ref = Reference(1)
        exp = join(self.db_dir, "GreenGenes_13_8_97_otus.fasta")
        self.assertEqual(ref.sequence_fp(), exp)
        with Transaction("test_sequence_fp") as trans:
            self.assertEqual(ref.sequence_fp(trans=trans), exp)

    def test_taxonomy_fp(self):
        ref = Reference(1)
        exp = join(self.db_dir, "GreenGenes_13_8_97_otu_taxonomy.txt")
        self.assertEqual(ref.taxonomy_fp(), exp)
        with Transaction("test_taxonomy_fp") as trans:
            self.assertEqual(ref.taxonomy_fp(trans=trans), exp)

    def test_tree_fp(self):
        ref = Reference(1)
        exp = join(self.db_dir, "GreenGenes_13_8_97_otus.tree")
        self.assertEqual(ref.tree_fp(), exp)
        with Transaction("test_tree_fp") as trans:
            self.assertEqual(ref.tree_fp(trans=trans), exp)

if __name__ == '__main__':
    main()
