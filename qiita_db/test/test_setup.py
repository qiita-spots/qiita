# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.util import check_count


@qiita_test_checker()
class SetupTest(TestCase):
    """Tests that the test database have been successfully populated"""

    def test_qitta_user(self):
        check_count("qiita.qiita_user", 4)

    def test_study_person(self):
        check_count("qiita.study_person", 3)

    def test_study(self):
        check_count("qiita.study", 1)

    def test_study_users(self):
        check_count("qiita.study_users", 2)

    def test_investigation(self):
        check_count("qiita.investigation", 1)

    def test_investigation_study(self):
        check_count("qiita.investigation_study", 1)

    def test_study_experimental_factor(self):
        check_count("qiita.study_experimental_factor", 1)

    def test_filepath(self):
        check_count("qiita.filepath", 9)

    def test_filepath_type(self):
        check_count("qiita.filepath_type", 8)

    def test_raw_data(self):
        check_count("qiita.raw_data", 2)

    def test_raw_filepath(self):
        check_count("qiita.raw_filepath", 4)

    def test_study_raw_data(self):
        check_count("qiita.study_raw_data", 2)

    def test_required_sample_info(self):
        check_count("qiita.required_sample_info", 27)

    def test_study_sample_columns(self):
        check_count("qiita.study_sample_columns", 23)

    def test_sample_1(self):
        check_count("qiita.sample_1", 27)

    def test_common_prep_info(self):
        check_count("qiita.common_prep_info", 27)

    def test_raw_data_prep_columns(self):
        check_count("qiita.raw_data_prep_columns", 19)

    def test_prep_1(self):
        check_count("qiita.prep_1", 27)

    def test_preprocessed_data(self):
        check_count("qiita.preprocessed_data", 2)

    def test_raw_preprocessed_data(self):
        check_count("qiita.raw_preprocessed_data", 2)

    def test_study_preprocessed_data(self):
        check_count("qiita.study_preprocessed_data", 2)

    def test_preprocessed_filepath(self):
        check_count("qiita.preprocessed_filepath", 2)

    def test_preprocessed_sequence_illumina_params(self):
        check_count("qiita.preprocessed_sequence_illumina_params", 2)

    def test_processed_data(self):
        check_count("qiita.processed_data", 1)

    def test_preprocessed_processed_data(self):
        check_count("qiita.preprocessed_processed_data", 1)

    def test_reference(self):
        check_count("qiita.reference", 1)

    def test_processed_params_uclust(self):
        check_count("qiita.processed_params_uclust", 1)

    def test_processed_filepath(self):
        check_count("qiita.processed_filepath", 1)

    def test_job(self):
        check_count("qiita.job", 2)

    def test_analysis(self):
        check_count("qiita.analysis", 1)

    def test_analysis_job(self):
        check_count("qiita.analysis_job", 3)

    def test_analysis_filepath(self):
        check_count("qiita.analysis_filepath", 1)

    def test_analysis_sample(self):
        check_count("qiita.analysis_sample", 8)

    def test_analysis_users(self):
        check_count("qiita.analysis_users", 1)

    def test_job_results_filepath(self):
        check_count("qiita.job_results_filepath", 2)

    def test_command_data_type(self):
        check_count("qiita.command_data_type", 14)

if __name__ == '__main__':
    main()
