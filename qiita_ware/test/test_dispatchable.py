# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from tempfile import mkstemp
from os import close, remove
from os.path import exists, join, dirname, abspath

import pandas as pd
import numpy.testing as npt

from qiita_core.util import qiita_test_checker
from qiita_ware.dispatchable import (
    create_sample_template, update_sample_template, delete_sample_template,
    update_prep_template, delete_artifact, copy_raw_data,
    delete_sample_or_column)
from qiita_db.study import Study
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBUnknownIDError, QiitaDBWarning
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate


@qiita_test_checker()
class TestDispatchable(TestCase):
    def setUp(self):
        fd, self.fp = mkstemp(suffix=".txt")
        close(fd)
        with open(self.fp, 'w') as f:
            f.write("sample_name\tnew_col\n"
                    "1.SKD6.640190\tnew_vale")

        self._clean_up_files = [self.fp]

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    def test_delete_artifact(self):
        obs = delete_artifact(1)
        exp = {'status': 'danger',
               'message': 'Cannot delete artifact 1: it has children: 2, 3'}
        self.assertEqual(obs, exp)

        obs = delete_artifact(3)
        exp = {'status': 'success',
               'message': ''}
        self.assertEqual(obs, exp)

        with self.assertRaises(QiitaDBUnknownIDError):
            Artifact(3)

    def test_create_sample_template(self):
        obs = create_sample_template(self.fp, Study(1), False)
        exp = {'status': 'danger',
               'message': "The 'SampleTemplate' object with attributes "
                          "(id: 1) already exists."}
        self.assertEqual(obs, exp)

    def test_create_sample_template_nonutf8(self):
        fp = join(dirname(abspath(__file__)), 'test_data',
                  'sample_info_utf8_error.txt')
        obs = create_sample_template(fp, Study(1), False)
        exp = {'status': 'danger',
               'message': 'There are invalid (non UTF-8) characters in your '
                          'information file. The offending fields and their '
                          'location (row, column) are listed below, invalid '
                          'characters are represented using &#128062;: '
                          '"&#128062;collection_timestamp" = (0, 13)'}
        self.assertEqual(obs, exp)

    def test_update_sample_template(self):
        obs = update_sample_template(1, self.fp)
        exp = {'status': 'warning',
               'message': ("Sample names were already prefixed with the study "
                           "id.\nThe following columns have been added to the "
                           "existing template: new_col\nThere are no "
                           "differences between the data stored in the DB and "
                           "the new data provided")}
        self.assertItemsEqual(obs['message'].split('\n'),
                              exp['message'].split('\n'))
        self.assertEqual(obs['status'], exp['status'])

    def test_delete_sample_template(self):
        obs = delete_sample_template(1)
        exp = {'status': 'danger',
               'message': 'Sample template cannot be erased because there '
                          'are prep templates associated.'}
        self.assertEqual(obs, exp)

    def test_update_prep_template(self):
        obs = update_prep_template(1, self.fp)
        exp = {'status': 'warning',
               'message': 'Sample names were already prefixed with the study '
                          'id.\nThe following columns have been added to the '
                          'existing template: new_col\nThere are no '
                          'differences between the data stored in the DB and '
                          'the new data provided'}
        self.assertItemsEqual(obs['message'].split('\n'),
                              exp['message'].split('\n'))
        self.assertEqual(obs['status'], exp['status'])

    def test_delete_sample_or_column(self):
        st = SampleTemplate(1)

        # Delete a sample template column
        obs = delete_sample_or_column(SampleTemplate, 1, "columns",
                                      "season_environment")
        exp = {'status': "success", 'message': ""}
        self.assertEqual(obs, exp)
        self.assertNotIn('season_environment', st.categories())

        # Delete a sample template sample - need to add one sample that we
        # will remove
        npt.assert_warns(
            QiitaDBWarning, st.extend,
            pd.DataFrame.from_dict({'Sample1': {'taxon_id': '9606'}},
                                   orient='index', dtype=str))
        self.assertIn('1.Sample1', st.keys())
        obs = delete_sample_or_column(SampleTemplate, 1, "samples",
                                      "1.Sample1")
        exp = {'status': "success", 'message': ""}
        self.assertEqual(obs, exp)
        self.assertNotIn('1.Sample1', st.keys())

        # Delete a prep template column
        pt = PrepTemplate(2)

        obs = delete_sample_or_column(PrepTemplate, 2, "columns",
                                      "target_subfragment")
        exp = {'status': "success", 'message': ""}
        self.assertEqual(obs, exp)
        self.assertNotIn('target_subfragment', pt.categories())

        # Delte a prep template sample
        metadata = pd.DataFrame.from_dict(
            {'1.SKB8.640193': {'barcode': 'GTCCGCAAGTTA',
                               'primer': 'GTGCCAGCMGCCGCGGTAA'},
             '1.SKD8.640184': {'barcode': 'CGTAGAGCTCTC',
                               'primer': 'GTGCCAGCMGCCGCGGTAA'}},
            orient='index', dtype=str)
        pt = npt.assert_warns(QiitaDBWarning, PrepTemplate.create, metadata,
                              Study(1), "16S")
        obs = delete_sample_or_column(PrepTemplate, pt.id, "samples",
                                      '1.SKD8.640184')
        exp = {'status': "success", 'message': ""}
        self.assertEqual(obs, exp)
        self.assertNotIn('1.SKD8.640184', pt.categories())

        # Exception
        obs = delete_sample_or_column(PrepTemplate, 2, "samples",
                                      "1.SKM9.640192")
        exp = {'status': "danger",
               'message': "Prep info file '2' has files attached, you cannot "
                          "delete samples."}
        self.assertEqual(obs, exp)

        # No "samples" or "columns"
        obs = delete_sample_or_column(PrepTemplate, 2, "not_samples", "NOP")
        exp = {'status': 'danger',
               'message': 'Unknown value "not_samples". Choose between '
                          '"samples" and "columns"'}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
