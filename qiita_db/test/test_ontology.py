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
from qiita_db.util import convert_from_id, convert_to_id


@qiita_test_checker()
class TestOntology(TestCase):
    def setUp(self):
        self.ontology = Ontology(999999999)

    def testConvertToID(self):
        self.assertEqual(convert_to_id('ENA_test', 'ontology'), 999999999)

    def testConvertFromID(self):
        self.assertEqual(convert_from_id(999999999, 'ontology'), 'ENA_test')

    def testShortNameProperty(self):
        self.assertEqual(self.ontology.shortname, 'ENA_test')

    def testTerms(self):
        obs = self.ontology.terms
        self.assertEqual(obs, [
            'Whole Genome Sequencing',
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
            'Other'])

    def testContains(self):
        self.assertTrue('Metagenomics' in self.ontology)
        self.assertFalse('NotATerm' in self.ontology)


if __name__ == '__main__':
    main()
