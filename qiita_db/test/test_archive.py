# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from json import dumps

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


@qiita_test_checker()
class ArchiveTest(TestCase):
    def test_insert_from_biom_and_retrieve_feature_values(self):
        # merging_scheme should be empty
        self.assertDictEqual(qdb.archive.Archive.merging_schemes(), dict())

        # 1 - to test error as it's FASTQ
        with self.assertRaises(ValueError) as err:
            qdb.archive.Archive.insert_from_artifact(
                qdb.artifact.Artifact(1), {})
        self.assertEqual(
            str(err.exception), 'To archive artifact must be BIOM but FASTQ')

        # 7 - to test error due to not filepath biom
        aid = 7
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add("DELETE FROM qiita.artifact_filepath "
                                       "WHERE artifact_id = %d" % aid)
            qdb.sql_connection.TRN.execute()
        with self.assertRaises(ValueError) as err:
            qdb.archive.Archive.insert_from_artifact(
                qdb.artifact.Artifact(aid), {})
        self.assertEqual(
            str(err.exception), 'The artifact has no biom files')

        # testing specific artifacts and parameters
        for i in [4, 5, 8, 9]:
            qdb.archive.Archive.insert_from_artifact(
                qdb.artifact.Artifact(i), {
                    'featureA%d' % i: dumps({'valuesA': 'vA', 'int': 1}),
                    'featureB%d' % i: dumps({'valuesB': 'vB', 'float': 1.1})})

        # now let's tests that all the inserts happen as expected
        exp = {
            'featureA4': dumps({'valuesA': 'vA', 'int': 1}),
            'featureA5': dumps({'valuesA': 'vA', 'int': 1}),
            'featureB9': dumps({'valuesB': 'vB', 'float': 1.1}),
            'featureB8': dumps({'valuesB': 'vB', 'float': 1.1}),
            'featureB5': dumps({'valuesB': 'vB', 'float': 1.1}),
            'featureB4': dumps({'valuesB': 'vB', 'float': 1.1}),
            'featureA8': dumps({'valuesA': 'vA', 'int': 1}),
            'featureA9': dumps({'valuesA': 'vA', 'int': 1})}
        obs = qdb.archive.Archive.retrieve_feature_values()
        self.assertEqual(obs, exp)

        # that we retrieve only one kind
        exp = dumps({
            'featureA9': dumps({'valuesA': 'vA', 'int': 1}),
            'featureB9': dumps({'valuesB': 'vB', 'float': 1.1}),
        })
        obs = qdb.archive.Archive.retrieve_feature_values(
            'Single Rarefaction | N/A')
        self.assertEqual(dumps(obs), exp)

        # and nothing
        exp = {}
        obs = qdb.archive.Archive.retrieve_feature_values('Nothing')
        self.assertEqual(obs, exp)

        # now merging_schemes should have 3 elements; note that 2 is empty
        # string because we are inserting an artifact [8] that was a direct
        # upload
        self.assertDictEqual(qdb.archive.Archive.merging_schemes(), {
            1: 'Pick closed-reference OTUs | Split libraries FASTQ',
            2: '', 3: 'Single Rarefaction | N/A'})

    def test_get_merging_scheme_from_job(self):
        exp = 'Split libraries FASTQ | N/A'
        obs = qdb.archive.Archive.get_merging_scheme_from_job(
            qdb.processing_job.ProcessingJob(
                '6d368e16-2242-4cf8-87b4-a5dc40bb890b'))
        self.assertEqual(obs, exp)

        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.software_command
                     SET ignore_parent_command = True"""
            qdb.sql_connection.TRN.add(sql)
            qdb.sql_connection.TRN.execute()

            exp = 'Split libraries FASTQ'
            obs = qdb.archive.Archive.get_merging_scheme_from_job(
                qdb.processing_job.ProcessingJob(
                    '6d368e16-2242-4cf8-87b4-a5dc40bb890b'))
            self.assertEqual(obs, exp)

            # returning to previous state
            sql = """UPDATE qiita.software_command
                     SET ignore_parent_command = False"""
            qdb.sql_connection.TRN.add(sql)
            qdb.sql_connection.TRN.execute()


if __name__ == '__main__':
    main()
