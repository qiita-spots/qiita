# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


@qiita_test_checker()
class ArchiveTest(TestCase):
    def test_insert_from_biom_and_retrieve_feature_values(self):
        # 1 - to test error as it's FASTQ
        with self.assertRaises(ValueError) as err:
            qdb.archive.Archive.insert_from_artifact(
                qdb.artifact.Artifact(1), {})
        self.assertEqual(
            str(err.exception), 'To archive artifact must be BIOM but FASTQ')

        # 7 - to test error due to not filepath biom
        with self.assertRaises(ValueError) as err:
            qdb.archive.Archive.insert_from_artifact(
                qdb.artifact.Artifact(7), {})
        self.assertEqual(
            str(err.exception), 'The artifact has no biom files')

        # testing specific artifacts and parameters
        for i in [4, 5, 8, 9]:
            qdb.archive.Archive.insert_from_artifact(
                qdb.artifact.Artifact(i), {
                    'featureA%d' % i: '{valuesA: vA, int: 1}',
                    'featureB%d' % i: '{valuesB: vB, float: 1.1}'})

        # now let's tests that all the inserts happen as expected
        exp = [
            ['', 'featureA8', '{valuesA: vA, int: 1}'],
            ['', 'featureB8', '{valuesB: vB, float: 1.1}'],
            ['Pick closed-reference OTUs | Split libraries FASTQ',
             'featureA4', '{valuesA: vA, int: 1}'],
            ['Pick closed-reference OTUs | Split libraries FASTQ',
             'featureA5', '{valuesA: vA, int: 1}'],
            ['Pick closed-reference OTUs | Split libraries FASTQ',
             'featureB4', '{valuesB: vB, float: 1.1}'],
            ['Pick closed-reference OTUs | Split libraries FASTQ',
             'featureB5', '{valuesB: vB, float: 1.1}'],
            ['Single Rarefaction | N/A', 'featureA9',
             '{valuesA: vA, int: 1}'],
            ['Single Rarefaction | N/A', 'featureB9',
             '{valuesB: vB, float: 1.1}']]
        obs = qdb.archive.Archive.retrieve_feature_values()
        self.assertEqual(obs, exp)

        # that we retrieve only one kind
        exp = [
            ['Single Rarefaction | N/A', 'featureA9',
             '{valuesA: vA, int: 1}'],
            ['Single Rarefaction | N/A', 'featureB9',
             '{valuesB: vB, float: 1.1}']]
        obs = qdb.archive.Archive.retrieve_feature_values(
            'Single Rarefaction | N/A')
        self.assertEqual(obs, exp)

        # and nothing
        exp = []
        obs = qdb.archive.Archive.retrieve_feature_values('Nothing')
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
