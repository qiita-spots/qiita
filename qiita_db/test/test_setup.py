# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_db.util import get_count, check_count


class SetupTest(TestCase):
    """Tests that the test database have been successfully populated"""

    def test_qiita_user(self):
        self.assertEqual(get_count("qiita.qiita_user"), 4)

    def test_study_person(self):
        self.assertEqual(get_count("qiita.study_person"), 3)

    def test_study(self):
        self.assertEqual(get_count("qiita.study"), 1)

    def test_study_users(self):
        self.assertEqual(get_count("qiita.study_users"), 1)

    def test_investigation(self):
        self.assertEqual(get_count("qiita.investigation"), 1)

    def test_investigation_study(self):
        self.assertEqual(get_count("qiita.investigation_study"), 1)

    def test_study_experimental_factor(self):
        self.assertEqual(get_count("qiita.study_experimental_factor"), 1)

    def test_filepath(self):
        self.assertEqual(get_count("qiita.filepath"), 25)

    def test_filepath_type(self):
        self.assertEqual(get_count("qiita.filepath_type"), 22)

    def test_study_prep_template(self):
        self.assertEqual(get_count("qiita.study_prep_template"), 2)

    def test_required_sample_info(self):
        self.assertEqual(get_count("qiita.study_sample"), 27)

    def test_sample_1(self):
        self.assertEqual(get_count("qiita.sample_1"), 27)

    def test_prep_template(self):
        self.assertEqual(get_count("qiita.prep_template"), 2)

    def test_prep_template_sample(self):
        self.assertEqual(get_count("qiita.prep_template_sample"), 54)

    def test_prep_1(self):
        self.assertEqual(get_count("qiita.prep_1"), 27)

    def test_reference(self):
        self.assertEqual(get_count("qiita.reference"), 2)

    def test_analysis(self):
        self.assertEqual(get_count("qiita.analysis"), 10)

    def test_analysis_filepath(self):
        self.assertEqual(get_count("qiita.analysis_filepath"), 1)

    def test_analysis_sample(self):
        self.assertEqual(get_count("qiita.analysis_sample"), 31)

    def test_analysis_users(self):
        self.assertEqual(get_count("qiita.analysis_users"), 1)

    def test_ontology(self):
        self.assertTrue(check_count('qiita.ontology', 1))

    def test_ontology_terms(self):
        self.assertTrue(check_count('qiita.term', 14))


if __name__ == '__main__':
    main()
