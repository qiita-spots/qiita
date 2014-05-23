from unittest import TestCase, main

from qiita_db.study import Study
from qiita_core.util import qiita_test_checker
from qiita_db.exceptions import QiitaDBExecutionError, QiitaDBConnectionError
from qiita_db.sql_connection import SQLConnectionHandler


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


@qiita_test_checker()
class TestStudy(TestCase):
    def setUp(self):

        self.info = {
            "emp_person_id": 2,
            "timeseries_type_id": 1,
            "lab_person_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "portal_type_id": 3,
            "principal_investigator_id": 3,
            "study_title": "Fried chicken microbiome",
            "study_alias": "FCM",
            "study_description": ("Microbiome of people who eat nothing but "
                                  "fried chicken"),
            "study_abstract": ("We wanted to see if we could get funding for "
                               "giving people heart attacks")
        }

    def test_create_study(self):
        """Insert a study into the database"""
        Study.create('test@foo.bar', self.info)

    def test_create_study_with_investigation(self):
        """Insert a study into the database with an investingation"""
        Study.create('test@foo.bar', self.info, 0)

    def test_create_study_with_efo(self):
        """Insert a study into the database with efo information"""
        self.info["study_experimental_factor"] = [1, 2]
        Study.create('test@foo.bar', self.info)

    def test_insert_missing_requred(self):
        """ Insert a study that is missing a required info key"""
        raise NotImplementedError()

    def test_insert_unknown_db_col(self):
        """ Insert a study with an info key not in the database"""
        raise NotImplementedError()

    def test_retrieve_name(self):
        raise NotImplementedError()

    def test_set_name(self):
        raise NotImplementedError()

    def test_retrieve_info(self):
        raise NotImplementedError()

    def test_set_info(self):
        raise NotImplementedError()

    def test_retrieve_status(self):
        raise NotImplementedError()

    def test_set_status(self):
        raise NotImplementedError()

    def test_retrieve_sample_ids(self):
        raise NotImplementedError()

    def test_retrieve_shared_with(self):
        raise NotImplementedError()

    def test_retrieve_pmids(self):
        raise NotImplementedError()

    def test_retrieve_investigations(self):
        raise NotImplementedError()

    def test_retrieve_metadata(self):
        raise NotImplementedError()

    def test_retrieve_raw_data(self):
        raise NotImplementedError()

    def test_retrieve_preprocessed_data(self):
        raise NotImplementedError()

    def test_retrieve_processed_data(self):
        raise NotImplementedError()

    def test_share_with(self):
        raise NotImplementedError()

    def test_add_raw_data(self):
        raise NotImplementedError()

    def test_add_pmid(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
