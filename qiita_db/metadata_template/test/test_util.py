# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from six import StringIO
from unittest import TestCase, main
from datetime import datetime

import numpy as np
import numpy.testing as npt
import pandas as pd
from pandas.util.testing import assert_frame_equal

import qiita_db as qdb


class TestUtil(TestCase):
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

    def test_type_lookup(self):
        """Correctly returns the SQL datatype of the passed dtype"""
        self.assertEqual(qdb.metadata_template.util.type_lookup(
            self.metadata_map['float_col'].dtype), 'float8')
        self.assertEqual(qdb.metadata_template.util.type_lookup(
            self.metadata_map['int_col'].dtype), 'integer')
        self.assertEqual(qdb.metadata_template.util.type_lookup(
            self.metadata_map['str_col'].dtype), 'varchar')

    def test_get_datatypes(self):
        """Correctly returns the data types of each column"""
        obs = qdb.metadata_template.util.get_datatypes(
            self.metadata_map.ix[:, self.headers])
        exp = ['float8', 'varchar', 'integer']
        self.assertEqual(obs, exp)

    def test_cast_to_python(self):
        """Correctly returns the value casted"""
        b = np.bool_(True)
        obs = qdb.metadata_template.util.cast_to_python(b)
        self.assertTrue(obs)
        self.assertFalse(isinstance(obs, np.bool_))
        self.assertTrue(isinstance(obs, bool))

        exp = datetime(2015, 9, 1, 10, 00)
        dt = np.datetime64(exp)
        obs = qdb.metadata_template.util.cast_to_python(dt)
        self.assertEqual(obs, exp)
        self.assertFalse(isinstance(obs, np.datetime64))
        self.assertTrue(isinstance(obs, datetime))

    def test_as_python_types(self):
        """Correctly returns the columns as python types"""
        obs = qdb.metadata_template.util.as_python_types(
            self.metadata_map, self.headers)
        exp = [[2.1, 3.1, 3],
               ['str1', '200', 'string30'],
               [1, 2, 3]]
        self.assertEqual(obs, exp)

    def test_prefix_sample_names_with_id(self):
        exp_metadata_dict = {
            '1.Sample1': {'int_col': 1, 'float_col': 2.1, 'str_col': 'str1'},
            '1.Sample2': {'int_col': 2, 'float_col': 3.1, 'str_col': '200'},
            '1.Sample3': {'int_col': 3, 'float_col': 3, 'str_col': 'string30'},
        }
        exp_df = pd.DataFrame.from_dict(exp_metadata_dict, orient='index')
        qdb.metadata_template.util.prefix_sample_names_with_id(
            self.metadata_map, 1)
        self.metadata_map.sort_index(inplace=True)
        exp_df.sort_index(inplace=True)
        assert_frame_equal(self.metadata_map, exp_df)

    def test_load_template_to_dataframe(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_qiime_map(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(QIIME_TUTORIAL_MAP_SUBSET), index='#SampleID')
        exp = pd.DataFrame.from_dict(QIIME_TUTORIAL_MAP_DICT_FORM)
        exp.index.name = 'SampleID'
        obs.sort_index(axis=0, inplace=True)
        obs.sort_index(axis=1, inplace=True)
        exp.sort_index(axis=0, inplace=True)
        exp.sort_index(axis=1, inplace=True)
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_duplicate_cols(self):
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateHeaderError):
            qdb.metadata_template.util.load_template_to_dataframe(
                StringIO(EXP_SAMPLE_TEMPLATE_DUPE_COLS))

    def test_load_template_to_dataframe_scrubbing(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_SPACES))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_empty_columns(self):
        obs = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.util.load_template_to_dataframe,
            StringIO(EXP_ST_SPACES_EMPTY_COLUMN))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_empty_rows(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_SPACES_EMPTY_ROW))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_no_sample_name_cast(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_NUMBER_SAMPLE_NAMES))
        exp = pd.DataFrame.from_dict(
            SAMPLE_TEMPLATE_NUMBER_SAMPLE_NAMES_DICT_FORM)
        exp.index.name = 'sample_name'
        obs.sort_index(inplace=True)
        exp.sort_index(inplace=True)
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_empty_sample_names(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(SAMPLE_TEMPLATE_NO_SAMPLE_NAMES))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(SAMPLE_TEMPLATE_NO_SAMPLE_NAMES_SOME_SPACES))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_empty_column(self):
        obs = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.util.load_template_to_dataframe,
            StringIO(SAMPLE_TEMPLATE_EMPTY_COLUMN))
        exp = pd.DataFrame.from_dict(ST_EMPTY_COLUMN_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_column_with_nas(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(SAMPLE_TEMPLATE_COLUMN_WITH_NAS))
        exp = pd.DataFrame.from_dict(ST_COLUMN_WITH_NAS_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_exception(self):
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.metadata_template.util.load_template_to_dataframe(
                StringIO(SAMPLE_TEMPLATE_NO_SAMPLE_NAME))

    def test_load_template_to_dataframe_whitespace(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_WHITESPACE))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_lowercase(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_MULTICASE))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        exp.rename(columns={"str_column": "str_CoLumn"}, inplace=True)
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_non_utf8(self):
        bad = EXP_SAMPLE_TEMPLATE.replace('Test Sample 2', 'Test Sample\x962')
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.metadata_template.util.load_template_to_dataframe(
                StringIO(bad))

    def test_load_template_to_dataframe_typechecking(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_LAT_ALL_INT))

        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_LAT_ALL_INT_DICT)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_LAT_MIXED_FLOAT_INT))

        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_MIXED_FLOAT_INT_DICT)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_with_nulls(self):
        obs = qdb.metadata_template.util.load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_NULLS))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_NULLS_DICT)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_get_invalid_sample_names(self):
        all_valid = ['2.sample.1', 'foo.bar.baz', 'roses', 'are', 'red',
                     'v10l3t5', '4r3', '81u3']
        obs = qdb.metadata_template.util.get_invalid_sample_names(all_valid)
        self.assertEqual(obs, [])

        all_valid = ['sample.1', 'sample.2', 'SAMPLE.1', 'BOOOM']
        obs = qdb.metadata_template.util.get_invalid_sample_names(all_valid)
        self.assertEqual(obs, [])

    def test_get_invalid_sample_names_str(self):
        one_invalid = ['2.sample.1', 'foo.bar.baz', 'roses', 'are', 'red',
                       'I am the chosen one', 'v10l3t5', '4r3', '81u3']
        obs = qdb.metadata_template.util.get_invalid_sample_names(one_invalid)
        self.assertItemsEqual(obs, ['I am the chosen one'])

        one_invalid = ['2.sample.1', 'foo.bar.baz', 'roses', 'are', 'red',
                       ':L{=<', ':L}=<', '4r3', '81u3']
        obs = qdb.metadata_template.util.get_invalid_sample_names(one_invalid)
        self.assertItemsEqual(obs, [':L{=<', ':L}=<'])

    def test_get_get_invalid_sample_names_mixed(self):
        one_invalid = ['.', '1', '2']
        obs = qdb.metadata_template.util.get_invalid_sample_names(one_invalid)
        self.assertItemsEqual(obs, [])

        one_invalid = [' ', ' ', ' ']
        obs = qdb.metadata_template.util.get_invalid_sample_names(one_invalid)
        self.assertItemsEqual(obs, [' ', ' ', ' '])

    def test_looks_like_qiime_mapping_file(self):
        obs = qdb.metadata_template.util.looks_like_qiime_mapping_file(
            StringIO(EXP_SAMPLE_TEMPLATE))
        self.assertFalse(obs)

        obs = qdb.metadata_template.util.looks_like_qiime_mapping_file(
            StringIO(QIIME_TUTORIAL_MAP_SUBSET))
        self.assertTrue(obs)

        obs = qdb.metadata_template.util.looks_like_qiime_mapping_file(
            StringIO())
        self.assertFalse(obs)

    def test_parse_mapping_file(self):
        # Tests ported over from QIIME
        s1 = ['#sample\ta\tb', '#comment line to skip',
              'x \t y \t z ', ' ', '#more skip', 'i\tj\tk']
        exp = ([['x', 'y', 'z'], ['i', 'j', 'k']],
               ['sample', 'a', 'b'],
               ['comment line to skip', 'more skip'])
        obs = qdb.metadata_template.util._parse_mapping_file(s1)
        self.assertEqual(obs, exp)

        # check that we strip double quotes by default
        s2 = ['#sample\ta\tb', '#comment line to skip',
              '"x "\t" y "\t z ', ' ', '"#more skip"', 'i\t"j"\tk']
        obs = qdb.metadata_template.util._parse_mapping_file(s2)
        self.assertEqual(obs, exp)


QIIME_TUTORIAL_MAP_SUBSET = (
    "#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tTreatment\tDOB\t"
    "Description\n"
    "PC.354\tAGCACGAGCCTA\tYATGCTGCCTCCCGTAGGAGT\tControl\t20061218\t"
    "Control_mouse_I.D._354\n"
    "PC.607\tAACTGTGCGTAC\tYATGCTGCCTCCCGTAGGAGT\tFast\t20071112\t"
    "Fasting_mouse_I.D._607\n"
)

EXP_SAMPLE_TEMPLATE = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\tstr_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\tNotIdentified"
    "\t1\t42.42\t41.41\tlocation1\treceived\ttype1\tValue for sample 1\n"
    "2.Sample2\t2014-05-29 12:24:51\tTest Sample 2\tTrue\tTrue\tNotIdentified"
    "\t2\t4.2\t1.1\tlocation1\treceived\ttype1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\tTrue\tNotIdentified"
    "\t3\t4.8\t4.41\tlocation1\treceived\ttype1\tValue for sample 3\n")

EXP_SAMPLE_TEMPLATE_MULTICASE = (
    "sAmPle_Name\tcollection_timestamp\tDescription\thas_extracted_data\t"
    "has_physical_specimen\thost_Subject_id\tint_column\tlatitude\tLongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\tstr_CoLumn\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\tNotIdentified"
    "\t1\t42.42\t41.41\tlocation1\treceived\ttype1\tValue for sample 1\n"
    "2.Sample2\t2014-05-29 12:24:51\tTest Sample 2\tTrue\tTrue\tNotIdentified"
    "\t2\t4.2\t1.1\tlocation1\treceived\ttype1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\tTrue\tNotIdentified"
    "\t3\t4.8\t4.41\tlocation1\treceived\ttype1\tValue for sample 3\n")

EXP_SAMPLE_TEMPLATE_LAT_ALL_INT = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\tstr_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\tNotIdentified"
    "\t1\t42\t41.41\tlocation1\treceived\ttype1\tValue for sample 1\n"
    "2.Sample2\t2014-05-29 12:24:51\tTest Sample 2\tTrue\tTrue\tNotIdentified"
    "\t2\t4\t1.1\tlocation1\treceived\ttype1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\tTrue\tNotIdentified"
    "\t3\t4\t4.41\tlocation1\treceived\ttype1\tValue for sample 3\n")

EXP_SAMPLE_TEMPLATE_LAT_MIXED_FLOAT_INT = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\tstr_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\tNotIdentified"
    "\t1\t42\t41.41\tlocation1\treceived\ttype1\tValue for sample 1\n"
    "2.Sample2\t2014-05-29 12:24:51\tTest Sample 2\tTrue\tTrue\tNotIdentified"
    "\t2\t4\t1.1\tlocation1\treceived\ttype1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\tTrue\tNotIdentified"
    "\t3\t4.8\t4.41\tlocation1\treceived\ttype1\tValue for sample 3\n")

EXP_SAMPLE_TEMPLATE_DUPE_COLS = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\tstr_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\tValue for sample 1\n"
    "2.Sample2\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\tValue for sample 2\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\tValue for sample 3\n")

EXP_SAMPLE_TEMPLATE_SPACES = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1         \t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t1\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample2  \t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t2\t4.2\t1.1\tlocation1\t"
    "received\ttype1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t3\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n")

EXP_SAMPLE_TEMPLATE_WHITESPACE = (
    "sample_name \tcollection_timestamp\t description \thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t1\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample2\t      2014-05-29 12:24:51 \t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t2\t4.2\t1.1\tlocation1\t"
    "received\ttype1\t Value for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\t   Test Sample 3 \tTrue\t"
    "True\tNotIdentified\t3\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n")

EXP_SAMPLE_TEMPLATE_SPACES_EMPTY_ROW = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1         \t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t1\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample2  \t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t2\t4.2\t1.1\tlocation1\t"
    "received\ttype1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t3\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n"
    "\t\t\t\t\t\t\t\t\t\t\t\t\n"
    "\t\t\t\t\t\t\t\t\t\t\t\t\n")

EXP_ST_SPACES_EMPTY_COLUMN = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\t\n"
    "2.Sample1         \t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t1\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\t\n"
    "2.Sample2  \t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t2\t4.2\t1.1\tlocation1\t"
    "received\ttype1\tValue for sample 2\t\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t3\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\t\n")

EXP_SAMPLE_TEMPLATE_NUMBER_SAMPLE_NAMES = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "002.000\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "1.11111\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\tValue for sample 2\n"
    "0.12121\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n")

SAMPLE_TEMPLATE_NO_SAMPLE_NAMES = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t1\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample2\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t2\t4.2\t1.1\tlocation1\t"
    "received\ttype1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t3\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n"
    "\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n"
    "\t\t\t\t\t\t\t\t\t\t\t\n"
    )

SAMPLE_TEMPLATE_NO_SAMPLE_NAMES_SOME_SPACES = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t1\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample2\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t2\t4.2\t1.1\tlocation1\t"
    "received\ttype1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t3\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n"
    "\t\t\t\t\t \t\t\t\t\t \t\t\n"
    )

SAMPLE_TEMPLATE_EMPTY_COLUMN = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "\n"
    "2.Sample2\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\t\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "\n")

SAMPLE_TEMPLATE_COLUMN_WITH_NAS = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "NA\n"
    "2.Sample2\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\tNA\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "NA\n")

SAMPLE_TEMPLATE_NO_SAMPLE_NAME = (
    ":L}={\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "NA\n"
    "2.Sample2\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\tNA\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "NA\n")

SAMPLE_TEMPLATE_INVALID_LONGITUDE_COLUMNS = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "1\t11.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample2\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\1\t4.2\tXXX\tlocation1\treceived\t"
    "type1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\1\t4.8\t4.XXXXX41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n")

EXP_SAMPLE_TEMPLATE_NULLS = (
    "sample_name\tmy_bool_col\tmy_bool_col_w_nulls\n"
    "sample.1\tTrue\tFalse\n"
    "sample.2\tFalse\tUnknown\n"
    "sample.3\tTrue\tTrue\n"
    "sample.4\tFalse\t\n"
    "sample.5\tTrue\tTrue\n"
    "sample.6\tFalse\tTrue\n")


SAMPLE_TEMPLATE_NULLS_DICT = {
    'my_bool_col': {"sample.1": 'True',
                    "sample.2": 'False',
                    "sample.3": 'True',
                    "sample.4": 'False',
                    "sample.5": 'True',
                    "sample.6": 'False'},
    'my_bool_col_w_nulls': {"sample.1": 'False',
                            "sample.2": 'Unknown',
                            "sample.3": 'True',
                            "sample.4": '',
                            "sample.5": 'True',
                            "sample.6": 'True'}
}

SAMPLE_TEMPLATE_DICT_FORM = {
    'collection_timestamp': {'2.Sample1': '2014-05-29 12:24:51',
                             '2.Sample2': '2014-05-29 12:24:51',
                             '2.Sample3': '2014-05-29 12:24:51'},
    'description': {'2.Sample1': 'Test Sample 1',
                    '2.Sample2': 'Test Sample 2',
                    '2.Sample3': 'Test Sample 3'},
    'has_extracted_data': {'2.Sample1': 'True',
                           '2.Sample2': 'True',
                           '2.Sample3': 'True'},
    'has_physical_specimen': {'2.Sample1': 'True',
                              '2.Sample2': 'True',
                              '2.Sample3': 'True'},
    'host_subject_id': {'2.Sample1': 'NotIdentified',
                        '2.Sample2': 'NotIdentified',
                        '2.Sample3': 'NotIdentified'},
    'latitude': {'2.Sample1': '42.42',
                 '2.Sample2': '4.2',
                 '2.Sample3': '4.8'},
    'longitude': {'2.Sample1': '41.41',
                  '2.Sample2': '1.1',
                  '2.Sample3': '4.41'},
    'physical_location': {'2.Sample1': 'location1',
                          '2.Sample2': 'location1',
                          '2.Sample3': 'location1'},
    'required_sample_info_status': {'2.Sample1': 'received',
                                    '2.Sample2': 'received',
                                    '2.Sample3': 'received'},
    'sample_type': {'2.Sample1': 'type1',
                    '2.Sample2': 'type1',
                    '2.Sample3': 'type1'},
    'str_column': {'2.Sample1': 'Value for sample 1',
                   '2.Sample2': 'Value for sample 2',
                   '2.Sample3': 'Value for sample 3'},
    'int_column': {'2.Sample1': '1',
                   '2.Sample2': '2',
                   '2.Sample3': '3'}
    }

SAMPLE_TEMPLATE_LAT_ALL_INT_DICT = {
    'collection_timestamp': {'2.Sample1': '2014-05-29 12:24:51',
                             '2.Sample2': '2014-05-29 12:24:51',
                             '2.Sample3': '2014-05-29 12:24:51'},
    'description': {'2.Sample1': 'Test Sample 1',
                    '2.Sample2': 'Test Sample 2',
                    '2.Sample3': 'Test Sample 3'},
    'has_extracted_data': {'2.Sample1': 'True',
                           '2.Sample2': 'True',
                           '2.Sample3': 'True'},
    'has_physical_specimen': {'2.Sample1': 'True',
                              '2.Sample2': 'True',
                              '2.Sample3': 'True'},
    'host_subject_id': {'2.Sample1': 'NotIdentified',
                        '2.Sample2': 'NotIdentified',
                        '2.Sample3': 'NotIdentified'},
    'latitude': {'2.Sample1': '42',
                 '2.Sample2': '4',
                 '2.Sample3': '4'},
    'longitude': {'2.Sample1': '41.41',
                  '2.Sample2': '1.1',
                  '2.Sample3': '4.41'},
    'physical_location': {'2.Sample1': 'location1',
                          '2.Sample2': 'location1',
                          '2.Sample3': 'location1'},
    'required_sample_info_status': {'2.Sample1': 'received',
                                    '2.Sample2': 'received',
                                    '2.Sample3': 'received'},
    'sample_type': {'2.Sample1': 'type1',
                    '2.Sample2': 'type1',
                    '2.Sample3': 'type1'},
    'str_column': {'2.Sample1': 'Value for sample 1',
                   '2.Sample2': 'Value for sample 2',
                   '2.Sample3': 'Value for sample 3'},
    'int_column': {'2.Sample1': '1',
                   '2.Sample2': '2',
                   '2.Sample3': '3'}
    }

SAMPLE_TEMPLATE_MIXED_FLOAT_INT_DICT = {
    'collection_timestamp': {'2.Sample1': '2014-05-29 12:24:51',
                             '2.Sample2': '2014-05-29 12:24:51',
                             '2.Sample3': '2014-05-29 12:24:51'},
    'description': {'2.Sample1': 'Test Sample 1',
                    '2.Sample2': 'Test Sample 2',
                    '2.Sample3': 'Test Sample 3'},
    'has_extracted_data': {'2.Sample1': 'True',
                           '2.Sample2': 'True',
                           '2.Sample3': 'True'},
    'has_physical_specimen': {'2.Sample1': 'True',
                              '2.Sample2': 'True',
                              '2.Sample3': 'True'},
    'host_subject_id': {'2.Sample1': 'NotIdentified',
                        '2.Sample2': 'NotIdentified',
                        '2.Sample3': 'NotIdentified'},
    'latitude': {'2.Sample1': '42',
                 '2.Sample2': '4',
                 '2.Sample3': '4.8'},
    'longitude': {'2.Sample1': '41.41',
                  '2.Sample2': '1.1',
                  '2.Sample3': '4.41'},
    'physical_location': {'2.Sample1': 'location1',
                          '2.Sample2': 'location1',
                          '2.Sample3': 'location1'},
    'required_sample_info_status': {'2.Sample1': 'received',
                                    '2.Sample2': 'received',
                                    '2.Sample3': 'received'},
    'sample_type': {'2.Sample1': 'type1',
                    '2.Sample2': 'type1',
                    '2.Sample3': 'type1'},
    'str_column': {'2.Sample1': 'Value for sample 1',
                   '2.Sample2': 'Value for sample 2',
                   '2.Sample3': 'Value for sample 3'},
    'int_column': {'2.Sample1': '1',
                   '2.Sample2': '2',
                   '2.Sample3': '3'}
    }

SAMPLE_TEMPLATE_NUMBER_SAMPLE_NAMES_DICT_FORM = {
    'collection_timestamp': {'002.000': '2014-05-29 12:24:51',
                             '1.11111': '2014-05-29 12:24:51',
                             '0.12121': '2014-05-29 12:24:51'},
    'description': {'002.000': 'Test Sample 1',
                    '1.11111': 'Test Sample 2',
                    '0.12121': 'Test Sample 3'},
    'has_extracted_data': {'002.000': 'True',
                           '1.11111': 'True',
                           '0.12121': 'True'},
    'has_physical_specimen': {'002.000': 'True',
                              '1.11111': 'True',
                              '0.12121': 'True'},
    'host_subject_id': {'002.000': 'NotIdentified',
                        '1.11111': 'NotIdentified',
                        '0.12121': 'NotIdentified'},
    'latitude': {'002.000': '42.42',
                 '1.11111': '4.2',
                 '0.12121': '4.8'},
    'longitude': {'002.000': '41.41',
                  '1.11111': '1.1',
                  '0.12121': '4.41'},
    'physical_location': {'002.000': 'location1',
                          '1.11111': 'location1',
                          '0.12121': 'location1'},
    'required_sample_info_status': {'002.000': 'received',
                                    '1.11111': 'received',
                                    '0.12121': 'received'},
    'sample_type': {'002.000': 'type1',
                    '1.11111': 'type1',
                    '0.12121': 'type1'},
    'str_column': {'002.000': 'Value for sample 1',
                   '1.11111': 'Value for sample 2',
                   '0.12121': 'Value for sample 3'}}

ST_EMPTY_COLUMN_DICT_FORM = \
    {'collection_timestamp': {'2.Sample1': '2014-05-29 12:24:51',
                              '2.Sample2': '2014-05-29 12:24:51',
                              '2.Sample3': '2014-05-29 12:24:51'},
     'description': {'2.Sample1': 'Test Sample 1',
                     '2.Sample2': 'Test Sample 2',
                     '2.Sample3': 'Test Sample 3'},
     'has_extracted_data': {'2.Sample1': 'True',
                            '2.Sample2': 'True',
                            '2.Sample3': 'True'},
     'has_physical_specimen': {'2.Sample1': 'True',
                               '2.Sample2': 'True',
                               '2.Sample3': 'True'},
     'host_subject_id': {'2.Sample1': 'NotIdentified',
                         '2.Sample2': 'NotIdentified',
                         '2.Sample3': 'NotIdentified'},
     'latitude': {'2.Sample1': '42.42',
                  '2.Sample2': '4.2',
                  '2.Sample3': '4.8'},
     'longitude': {'2.Sample1': '41.41',
                   '2.Sample2': '1.1',
                   '2.Sample3': '4.41'},
     'physical_location': {'2.Sample1': 'location1',
                           '2.Sample2': 'location1',
                           '2.Sample3': 'location1'},
     'required_sample_info_status': {'2.Sample1': 'received',
                                     '2.Sample2': 'received',
                                     '2.Sample3': 'received'},
     'sample_type': {'2.Sample1': 'type1',
                     '2.Sample2': 'type1',
                     '2.Sample3': 'type1'}}

ST_COLUMN_WITH_NAS_DICT_FORM = \
    {'collection_timestamp': {'2.Sample1': '2014-05-29 12:24:51',
                              '2.Sample2': '2014-05-29 12:24:51',
                              '2.Sample3': '2014-05-29 12:24:51'},
     'description': {'2.Sample1': 'Test Sample 1',
                     '2.Sample2': 'Test Sample 2',
                     '2.Sample3': 'Test Sample 3'},
     'has_extracted_data': {'2.Sample1': 'True',
                            '2.Sample2': 'True',
                            '2.Sample3': 'True'},
     'has_physical_specimen': {'2.Sample1': 'True',
                               '2.Sample2': 'True',
                               '2.Sample3': 'True'},
     'host_subject_id': {'2.Sample1': 'NotIdentified',
                         '2.Sample2': 'NotIdentified',
                         '2.Sample3': 'NotIdentified'},
     'latitude': {'2.Sample1': '42.42',
                  '2.Sample2': '4.2',
                  '2.Sample3': '4.8'},
     'longitude': {'2.Sample1': '41.41',
                   '2.Sample2': '1.1',
                   '2.Sample3': '4.41'},
     'physical_location': {'2.Sample1': 'location1',
                           '2.Sample2': 'location1',
                           '2.Sample3': 'location1'},
     'required_sample_info_status': {'2.Sample1': 'received',
                                     '2.Sample2': 'received',
                                     '2.Sample3': 'received'},
     'sample_type': {'2.Sample1': 'type1',
                     '2.Sample2': 'type1',
                     '2.Sample3': 'type1'},
     'str_column': {'2.Sample1': 'NA', '2.Sample2': 'NA', '2.Sample3': 'NA'}}

QIIME_TUTORIAL_MAP_DICT_FORM = {
    'BarcodeSequence': {'PC.354': 'AGCACGAGCCTA',
                        'PC.607': 'AACTGTGCGTAC'},
    'LinkerPrimerSequence': {'PC.354': 'YATGCTGCCTCCCGTAGGAGT',
                             'PC.607': 'YATGCTGCCTCCCGTAGGAGT'},
    'Treatment': {'PC.354': 'Control',
                  'PC.607': 'Fast'},
    'DOB': {'PC.354': '20061218',
            'PC.607': '20071112'},
    'Description': {'PC.354': 'Control_mouse_I.D._354',
                    'PC.607': 'Fasting_mouse_I.D._607'}
}

EXP_PREP_TEMPLATE = (
    'sample_name\tbarcodesequence\tcenter_name\tcenter_project_name\t'
    'ebi_submission_accession\temp_status\texperiment_design_description\t'
    'library_construction_protocol\tlinkerprimersequence\tplatform\t'
    'run_prefix\tstr_column\n'
    '1.SKB7.640196\tCCTCTGAGAGCT\tANL\tTest Project\tNone\tEMP\tBBBB\tAAAA\t'
    'GTGCCAGCMGCCGCGGTAA\tILLUMINA\ts_G1_L002_sequences\tValue for sample 3\n'
    '1.SKB8.640193\tGTCCGCAAGTTA\tANL\tTest Project\tNone\tEMP\tBBBB\tAAAA\t'
    'GTGCCAGCMGCCGCGGTAA\tILLUMINA\ts_G1_L001_sequences\tValue for sample 1\n'
    '1.SKD8.640184\tCGTAGAGCTCTC\tANL\tTest Project\tNone\tEMP\tBBBB\tAAAA\t'
    'GTGCCAGCMGCCGCGGTAA\tILLUMINA\ts_G1_L001_sequences\tValue for sample 2\n')

if __name__ == '__main__':
    main()
