# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.ontology import Ontology
from qiita_db.sql_connection import Transaction


@qiita_test_checker()
class TestOntology(TestCase):
    def setUp(self):
        self.ontology = Ontology(999999999)

    def test_short_name(self):
        self.assertEqual(self.ontology.shortname(), 'ENA')
        with Transaction("test_short_name") as trans:
            self.assertEqual(self.ontology.shortname(trans=trans), 'ENA')

    def test_terms(self):
        exp = ['Whole Genome Sequencing',
               'Metagenomics',
               'Transcriptome Analysis',
               'Resequencing',
               'Epigenetics',
               'Synthetic Genomics',
               'Forensic or Paleo-genomics',
               'Gene Regulation Study',
               'Cancer Genomics',
               'Population Genomics',
               'RNASeq',
               'Exome Sequencing',
               'Pooled Clone Sequencing',
               'Other']
        self.assertEqual(self.ontology.terms(), exp)
        with Transaction("test_terms") as trans:
            self.assertEqual(self.ontology.terms(trans=trans), exp)

    def test_user_defined_terms(self):
        self.assertEqual(self.ontology.user_defined_terms(), [])
        with Transaction("test_user_defined_terms") as trans:
            self.assertEqual(self.ontology.user_defined_terms(trans=trans), [])

    def test_term_type(self):
        self.assertEqual(self.ontology.term_type('RNASeq'), 'ontology')
        self.assertEqual(self.ontology.term_type('Sasquatch'), 'not_ontology')

        self.ontology.add_user_defined_term('Test Term')
        self.assertEqual(self.ontology.term_type('Test Term'), 'user_defined')

        with Transaction("test_term_type") as trans:
            self.assertEqual(self.ontology.term_type('RNASeq'), 'ontology')
            self.assertEqual(
                self.ontology.term_type('Sasquatch'), 'not_ontology')
            self.assertEqual(
                self.ontology.term_type('Test Term'), 'user_defined')

    def test_add_user_defined_term(self):
        self.assertFalse('Test Term' in self.ontology.user_defined_terms())
        pre = len(self.ontology.user_defined_terms())
        self.ontology.add_user_defined_term('Test Term')
        post = len(self.ontology.user_defined_terms())
        self.assertTrue('Test Term' in self.ontology.user_defined_terms())
        self.assertEqual(post-pre, 1)

        with Transaction("test_add_user_defined_term") as trans:
            self.assertFalse('Another' in self.ontology.user_defined_terms())
            pre = len(self.ontology.user_defined_terms())
            self.ontology.add_user_defined_term('Another', trans=trans)
            post = len(self.ontology.user_defined_terms())
            self.assertTrue('Another' in self.ontology.user_defined_terms())
            self.assertEqual(post-pre, 1)

    def test_contains(self):
        self.assertTrue(self.ontology.contains('Metagenomics'))
        self.assertFalse(self.ontology.contains('NotATerm'))

        with Transaction("test_contains") as trans:
            self.assertTrue(
                self.ontology.contains('Metagenomics', trans=trans))
            self.assertFalse(self.ontology.contains('NotATerm', trans=trans))


if __name__ == '__main__':
    main()
