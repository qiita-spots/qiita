# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from datetime import datetime
from tempfile import mkstemp
from os import close, remove

import pandas as pd

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import QiitaDBDuplicateError
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.util import exists_table
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.metadata_template import (_get_datatypes, _as_python_types,
                                        MetadataTemplate, SampleTemplate,
                                        PrepTemplate, BaseSample, PrepSample,
                                        Sample)


class TestUtilMetadataMap(TestCase):
    """Tests some utility functions on the metadata_template module"""
    def setUp(self):
        metadata_dict = {
            'Sample1': {'int_col': 1, 'float_col': 2.1, 'str_col': 'str1'},
            'Sample2': {'int_col': 2, 'float_col': 3.1, 'str_col': '200'},
            'Sample3': {'int_col': 3, 'float_col': 3, 'str_col': 'string30'},
        }
        self.metadata_map = pd.DataFrame.from_dict(metadata_dict,
                                                   orient='index')
        self.headers = ['float_col', 'str_col', 'int_col']

    def test_get_datatypes(self):
        """Correctly returns the data types of each column"""
        obs = _get_datatypes(self.metadata_map.ix[:, self.headers])
        exp = ['float8', 'varchar', 'integer']
        self.assertEqual(obs, exp)

    def test_as_python_types(self):
        """Correctly returns the columns as python types"""
        obs = _as_python_types(self.metadata_map, self.headers)
        exp = [[2.1, 3.1, 3],
               ['str1', '200', 'string30'],
               [1, 2, 3]]
        self.assertEqual(obs, exp)


@qiita_test_checker()
class TestBaseSample(TestCase):
    """Tests the BaseSample class"""

    def test_init(self):
        """BaseSample init should raise an error (it's a base class)"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            BaseSample('SKM7.640188', SampleTemplate(1))

    def test_exists(self):
        """exists should raise an error if called from the base class"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            BaseSample.exists('SKM7.640188', SampleTemplate(1))


# @qiita_test_checker()
# class TestSample(TestCase):
#     """Tests the PrepTemplate class"""

#     def setUp(self):
#         pass

#     def test_exists_true(self):
#         """Exists returns true when the SampleTemplate already exists"""
#         pass

#     def test_exists_false(self):
#         """Exists returns false when the SampleTemplate does not exists"""
#         pass

#     def test_create_duplicate(self):
#         """Create raises an error when creating a duplicated SampleTemplate"""
#         pass

#     def test_create_required(self):
#         """Creates a new SampleTemplate with just the required columns"""
#         pass

#     def test_len(self):
#         """Len returns the correct number of sample ids"""
#         pass

#     def test_getitem(self):
#         """Get item returns the correct sample object"""
#         pass

#     def test_getitem_error(self):
#         """Get item raises an error if key does not exists"""
#         pass

#     def test_setitem(self):
#         """setitem raises an error (currently not allowed)"""
#         pass

#     def test_delitem(self):
#         """delitem raises an error (currently not allowed)"""
#         pass

#     def test_iter(self):
#         """iter returns an iterator over the sample ids"""
#         pass

#     def test_contains_true(self):
#         """contains returns true if the sample id exists"""
#         pass

#     def test_contains_false(self):
#         """contains returns false if the sample id does not exists"""
#         pass

#     def test_keys(self):
#         """keys returns an iterator over the sample ids"""
#         pass

#     def test_values(self):
#         """values returns an iterator over the values"""
#         pass

#     def test_items(self):
#         """items returns an iterator over the (key, value) tuples"""
#         pass

#     def test_get(self):
#         """get returns the correct sample object"""
#         pass

#     def test_get_none(self):
#         """get returns none if the sample id is not present"""
#         pass


# @qiita_test_checker()
# class TestPrepSample(TestCase):
#     """Tests the PrepTemplate class"""

#     def setUp(self):
#         pass

#     def test_exists_true(self):
#         """Exists returns true when the SampleTemplate already exists"""
#         pass

#     def test_exists_false(self):
#         """Exists returns false when the SampleTemplate does not exists"""
#         pass

#     def test_create_duplicate(self):
#         """Create raises an error when creating a duplicated SampleTemplate"""
#         pass

#     def test_create_required(self):
#         """Creates a new SampleTemplate with just the required columns"""
#         pass

#     def test_len(self):
#         """Len returns the correct number of sample ids"""
#         pass

#     def test_getitem(self):
#         """Get item returns the correct sample object"""
#         pass

#     def test_getitem_error(self):
#         """Get item raises an error if key does not exists"""
#         pass

#     def test_setitem(self):
#         """setitem raises an error (currently not allowed)"""
#         pass

#     def test_delitem(self):
#         """delitem raises an error (currently not allowed)"""
#         pass

#     def test_iter(self):
#         """iter returns an iterator over the sample ids"""
#         pass

#     def test_contains_true(self):
#         """contains returns true if the sample id exists"""
#         pass

#     def test_contains_false(self):
#         """contains returns false if the sample id does not exists"""
#         pass

#     def test_keys(self):
#         """keys returns an iterator over the sample ids"""
#         pass

#     def test_values(self):
#         """values returns an iterator over the values"""
#         pass

#     def test_items(self):
#         """items returns an iterator over the (key, value) tuples"""
#         pass

#     def test_get(self):
#         """get returns the correct sample object"""
#         pass

#     def test_get_none(self):
#         """get returns none if the sample id is not present"""
#         pass


# @qiita_test_checker()
# class TestMetadataTemplate(TestCase):
#     """Tests the MetadataTemplate base class"""
#     def setUp(self):
#         self.study = Study(1)
#         self.metadata = pd.DataFrame.from_dict({})

#     def test_create(self):
#         """Create raises an error because it's not called from a subclass"""
#         with self.assertRaises(IncompetentQiitaDeveloperError):
#             MetadataTemplate.create(self.metadata, self.study)

#     def test_exist(self):
#         """Exists raises an error because it's not called from a subclass"""
#         with self.assertRaises(IncompetentQiitaDeveloperError):
#             MetadataTemplate.exists(self.study)

#     def test_table_name(self):
#         """table name raises an error because it's not called from a subclass
#         """
#         with self.assertRaises(IncompetentQiitaDeveloperError):
#             MetadataTemplate._table_name(self.study)


# @qiita_test_checker()
# class TestSampleTemplate(TestCase):
#     """Tests the SampleTemplate class"""

#     def setUp(self):
#         metadata_dict = {
#             'Sample1': {'physical_location': 'location1',
#                         'has_physical_specimen': True,
#                         'has_extracted_data': True,
#                         'sample_type': 'type1',
#                         'required_sample_info_status_id': 1,
#                         'collection_timestamp':
#                             datetime(2014, 5, 29, 12, 24, 51),
#                         'host_subject_id': 'NotIdentified',
#                         'description': 'Test Sample 1',
#                         'str_column': 'Value for sample 1'},
#             'Sample2': {'physical_location': 'location1',
#                         'has_physical_specimen': True,
#                         'has_extracted_data': True,
#                         'sample_type': 'type1',
#                         'required_sample_info_status_id': 1,
#                         'collection_timestamp':
#                             datetime(2014, 5, 29, 12, 24, 51),
#                         'host_subject_id': 'NotIdentified',
#                         'description': 'Test Sample 2',
#                         'str_column': 'Value for sample 2'},
#             'Sample3': {'physical_location': 'location1',
#                         'has_physical_specimen': True,
#                         'has_extracted_data': True,
#                         'sample_type': 'type1',
#                         'required_sample_info_status_id': 1,
#                         'collection_timestamp':
#                             datetime(2014, 5, 29, 12, 24, 51),
#                         'host_subject_id': 'NotIdentified',
#                         'description': 'Test Sample 3',
#                         'str_column': 'Value for sample 3'}
#         }
#         self.metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
#         self.test_study = Study(1)
#         info = {
#             "timeseries_type_id": 1,
#             "metadata_complete": True,
#             "mixs_compliant": True,
#             "number_samples_collected": 25,
#             "number_samples_promised": 28,
#             "portal_type_id": 3,
#             "study_alias": "FCM",
#             "study_description": "Microbiome of people who eat nothing but "
#                                  "fried chicken",
#             "study_abstract": "Exploring how a high fat diet changes the "
#                               "gut microbiome",
#             "emp_person_id": StudyPerson(2),
#             "principal_investigator_id": StudyPerson(3),
#             "lab_person_id": StudyPerson(1)
#         }
#         self.new_study = Study.create(User('test@foo.bar'),
#                                       "Fried Chicken Microbiome", [1], info)
#         self.conn_handler = SQLConnectionHandler()
#         self.tester = SampleTemplate(1)

#     def test_exists_true(self):
#         """Exists returns true when the SampleTemplate already exists"""
#         self.assertTrue(SampleTemplate.exists(self.test_study))

#     def test_exists_false(self):
#         """Exists returns false when the SampleTemplate does not exists"""
#         self.assertFalse(SampleTemplate.exists(self.new_study))

#     def test_create_duplicate(self):
#         """Create raises an error when creating a duplicated SampleTemplate"""
#         with self.assertRaises(QiitaDBDuplicateError):
#             SampleTemplate.create(self.metadata, self.test_study)

#     def test_create_required(self):
#         """Creates a new SampleTemplate with just the required columns"""
#         st = SampleTemplate.create(self.metadata, self.new_study)
#         # The returned object has the correct id
#         self.assertEqual(st.id, 2)

#         # The relevant rows to required_sample_info have been added.
#         obs = self.conn_handler.execute_fetchall(
#             "SELECT * FROM qiita.required_sample_info WHERE study_id=2")
#         # study_id sample_id physical_location has_physical_specimen
#         # has_extracted_data sample_type required_sample_info_status_id
#         # collection_timestamp host_subject_id description
#         exp = [[2, "Sample1", "location1", True, True, "type1", 1,
#                 datetime(2014, 5, 29, 12, 24, 51), "NotIdentified",
#                 "Test Sample 1"],
#                [2, "Sample2", "location1", True, True, "type1", 1,
#                 datetime(2014, 5, 29, 12, 24, 51), "NotIdentified",
#                 "Test Sample 2"],
#                [2, "Sample3", "location1", True, True, "type1", 1,
#                 datetime(2014, 5, 29, 12, 24, 51), "NotIdentified",
#                 "Test Sample 3"]]
#         self.assertEqual(obs, exp)

#         # The relevant rows have been added to the study_sample_columns
#         obs = self.conn_handler.execute_fetchall(
#             "SELECT * FROM qiita.study_sample_columns WHERE study_id=2")
#         # study_id, column_name, column_type
#         exp = [[2, "str_column", "varchar"]]
#         self.assertEqual(obs, exp)

#         # The new table exists
#         self.assertTrue(exists_table("sample_2", self.conn_handler))

#         # The new table hosts the correct values
#         obs = self.conn_handler.execute_fetchall(
#             "SELECT * FROM qiita.sample_2")
#         # sample_id, str_column
#         exp = [['Sample1', "Value for sample 1"],
#                ['Sample2', "Value for sample 2"],
#                ['Sample3', "Value for sample 3"]]
#         self.assertEqual(obs, exp)

#     def test_len(self):
#         """Len returns the correct number of sample ids"""
#         self.assertEqual(len(self.tester), 27)

#     def test_getitem(self):
#         """Get item returns the correct sample object"""
#         obs = self.tester['SKM7.640188']
#         exp = Sample['SKM7.640188']
#         self.assertEqual(obs, exp)

#     def test_getitem_error(self):
#         """Get item raises an error if key does not exists"""
#         pass

#     def test_setitem(self):
#         """setitem raises an error (currently not allowed)"""
#         pass

#     def test_delitem(self):
#         """delitem raises an error (currently not allowed)"""
#         pass

#     def test_iter(self):
#         """iter returns an iterator over the sample ids"""
#         pass

#     def test_contains_true(self):
#         """contains returns true if the sample id exists"""
#         pass

#     def test_contains_false(self):
#         """contains returns false if the sample id does not exists"""
#         pass

#     def test_keys(self):
#         """keys returns an iterator over the sample ids"""
#         pass

#     def test_values(self):
#         """values returns an iterator over the values"""
#         pass

#     def test_items(self):
#         """items returns an iterator over the (key, value) tuples"""
#         pass

#     def test_get(self):
#         """get returns the correct sample object"""
#         pass

#     def test_get_none(self):
#         """get returns none if the sample id is not present"""
#         pass


# @qiita_test_checker()
# class TestPrepTemplate(TestCase):
#     """Tests the PrepTemplate class"""

#     def setUp(self):
#         pass

#     def test_exists_true(self):
#         """Exists returns true when the SampleTemplate already exists"""
#         pass

#     def test_exists_false(self):
#         """Exists returns false when the SampleTemplate does not exists"""
#         pass

#     def test_create_duplicate(self):
#         """Create raises an error when creating a duplicated SampleTemplate"""
#         pass

#     def test_create_required(self):
#         """Creates a new SampleTemplate with just the required columns"""
#         pass

#     def test_len(self):
#         """Len returns the correct number of sample ids"""
#         pass

#     def test_getitem(self):
#         """Get item returns the correct sample object"""
#         pass

#     def test_getitem_error(self):
#         """Get item raises an error if key does not exists"""
#         pass

#     def test_setitem(self):
#         """setitem raises an error (currently not allowed)"""
#         pass

#     def test_delitem(self):
#         """delitem raises an error (currently not allowed)"""
#         pass

#     def test_iter(self):
#         """iter returns an iterator over the sample ids"""
#         pass

#     def test_contains_true(self):
#         """contains returns true if the sample id exists"""
#         pass

#     def test_contains_false(self):
#         """contains returns false if the sample id does not exists"""
#         pass

#     def test_keys(self):
#         """keys returns an iterator over the sample ids"""
#         pass

#     def test_values(self):
#         """values returns an iterator over the values"""
#         pass

#     def test_items(self):
#         """items returns an iterator over the (key, value) tuples"""
#         pass

#     def test_get(self):
#         """get returns the correct sample object"""
#         pass

#     def test_get_none(self):
#         """get returns none if the sample id is not present"""
#         pass


if __name__ == '__main__':
    main()
