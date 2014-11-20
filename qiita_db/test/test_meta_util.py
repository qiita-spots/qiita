# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.meta_util import get_accessible_filepath_ids


@qiita_test_checker()
class MetaUtilTests(TestCase):
    def _set_studies_private(self):
        self.conn_handler.execute("UPDATE qiita.study SET study_status_id=3")

    def _unshare_studies(self):
        self.conn_handler.execute("DELETE FROM qiita.study_users")

    def _unshare_analyses(self):
        self.conn_handler.execute("DELETE FROM qiita.analysis_users")

    def test_get_accessible_filepath_ids(self):
        self._set_studies_private()

        # shared has access to all study files and analysis files
        obs = get_accessible_filepath_ids('shared@foo.bar')
        self.assertEqual(obs, set([1, 2, 3, 4, 5, 6, 7, 11, 14, 15]))

        # Now shared should not have access to the study files
        self._unshare_studies()
        obs = get_accessible_filepath_ids('shared@foo.bar')
        self.assertEqual(obs, set([14, 15]))

        # Now shared should not have access to any files
        self._unshare_analyses()
        obs = get_accessible_filepath_ids('shared@foo.bar')
        self.assertEqual(obs, set())

if __name__ == '__main__':
    main()
