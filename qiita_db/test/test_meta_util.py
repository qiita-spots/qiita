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
from qiita_db.study import Study
from qiita_db.user import User


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
        self.assertEqual(obs, set([1, 2, 3, 4, 5, 6, 7, 11, 14, 15, 16]))

        # Now shared should not have access to the study files
        self._unshare_studies()
        obs = get_accessible_filepath_ids('shared@foo.bar')
        self.assertEqual(obs, set([14, 15]))

        # Now shared should not have access to any files
        self._unshare_analyses()
        obs = get_accessible_filepath_ids('shared@foo.bar')
        self.assertEqual(obs, set())

        # Test that it doesn't brake if the SampleTemplate hasn't been added
        exp = set([1, 2, 3, 4, 5, 6, 7, 11, 14, 15, 16])
        obs = get_accessible_filepath_ids('test@foo.bar')
        self.assertEqual(obs, exp)

        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 4,
            "number_samples_promised": 4,
            "portal_type_id": 3,
            "study_alias": "TestStudy",
            "study_description": "Description of a test study",
            "study_abstract": "No abstract right now...",
            "emp_person_id": 1,
            "principal_investigator_id": 1,
            "lab_person_id": 1
        }
        Study.create(User('test@foo.bar'), "Test study", [1], info)
        obs = get_accessible_filepath_ids('test@foo.bar')
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
