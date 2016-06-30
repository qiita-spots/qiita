# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from future.builtins import zip
from unittest import TestCase, main
from tempfile import mkstemp
from os import close, remove
from collections import Iterable
from warnings import catch_warnings

import numpy.testing as npt
import pandas as pd
from pandas.util.testing import assert_frame_equal

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
import qiita_db as qdb


class BaseTestSample(TestCase):
    def setUp(self):
        self.sample_template = \
            qdb.metadata_template.sample_template.SampleTemplate(1)
        self.sample_id = '1.SKB8.640193'
        self.tester = qdb.metadata_template.sample_template.Sample(
            self.sample_id, self.sample_template)
        self.exp_categories = {'physical_specimen_location',
                               'physical_specimen_remaining',
                               'dna_extracted', 'sample_type',
                               'collection_timestamp', 'host_subject_id',
                               'description', 'season_environment',
                               'assigned_from_geo', 'texture', 'taxon_id',
                               'depth', 'host_taxid', 'common_name',
                               'water_content_soil', 'elevation', 'temp',
                               'tot_nitro', 'samp_salinity', 'altitude',
                               'env_biome', 'country', 'ph', 'anonymized_name',
                               'tot_org_carb', 'description_duplicate',
                               'env_feature', 'latitude', 'longitude',
                               'scientific_name'}


class TestSampleReadOnly(BaseTestSample):
    def test_init_unknown_error(self):
        """Init raises an error if the sample id is not found in the template
        """
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.metadata_template.sample_template.Sample(
                'Not_a_Sample', self.sample_template)

    def test_init_wrong_template(self):
        """Raises an error if using a PrepTemplate instead of SampleTemplate"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.metadata_template.sample_template.Sample(
                'SKB8.640193',
                qdb.metadata_template.prep_template.PrepTemplate(1))

    def test_init(self):
        """Init correctly initializes the sample object"""
        sample = qdb.metadata_template.sample_template.Sample(
            self.sample_id, self.sample_template)
        # Check that the internal id have been correctly set
        self.assertEqual(sample._id, '1.SKB8.640193')
        # Check that the internal template have been correctly set
        self.assertEqual(sample._md_template, self.sample_template)
        # Check that the internal dynamic table name have been correctly set
        self.assertEqual(sample._dynamic_table, "sample_1")

    def test_eq_true(self):
        """Equality correctly returns true"""
        other = qdb.metadata_template.sample_template.Sample(
            self.sample_id, self.sample_template)
        self.assertTrue(self.tester == other)

    def test_eq_false_type(self):
        """Equality returns false if types are not equal"""
        other = qdb.metadata_template.prep_template.PrepSample(
            self.sample_id,
            qdb.metadata_template.prep_template.PrepTemplate(1))
        self.assertFalse(self.tester == other)

    def test_eq_false_id(self):
        """Equality returns false if ids are different"""
        other = qdb.metadata_template.sample_template.Sample(
            '1.SKD8.640184', self.sample_template)
        self.assertFalse(self.tester == other)

    def test_exists_true(self):
        """Exists returns true if the sample exists"""
        self.assertTrue(qdb.metadata_template.sample_template.Sample.exists(
            self.sample_id, self.sample_template))

    def test_exists_false(self):
        """Exists returns false if the sample does not exists"""
        self.assertFalse(qdb.metadata_template.sample_template.Sample.exists(
            'Not_a_Sample', self.sample_template))

    def test_get_categories(self):
        """Correctly returns the set of category headers"""
        obs = self.tester._get_categories()
        self.assertEqual(obs, self.exp_categories)

    def test_len(self):
        """Len returns the correct number of categories"""
        self.assertEqual(len(self.tester), 30)

    def test_getitem_required(self):
        """Get item returns the correct metadata value from the required table
        """
        self.assertEqual(self.tester['physical_specimen_location'], 'ANL')
        self.assertEqual(self.tester['collection_timestamp'],
                         '11/11/11 13:00:00')
        self.assertTrue(self.tester['dna_extracted'])

    def test_getitem_dynamic(self):
        """Get item returns the correct metadata value from the dynamic table
        """
        self.assertEqual(self.tester['SEASON_ENVIRONMENT'], 'winter')
        self.assertEqual(self.tester['depth'], '0.15')

    def test_getitem_error(self):
        """Get item raises an error if category does not exists"""
        with self.assertRaises(KeyError):
            self.tester['Not_a_Category']

    def test_iter(self):
        """iter returns an iterator over the category headers"""
        obs = self.tester.__iter__()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_categories)

    def test_contains_true(self):
        """contains returns true if the category header exists"""
        self.assertTrue('DEPTH' in self.tester)
        self.assertTrue('depth' in self.tester)

    def test_contains_false(self):
        """contains returns false if the category header does not exists"""
        self.assertFalse('Not_a_Category' in self.tester)

    def test_keys(self):
        """keys returns an iterator over the metadata headers"""
        obs = self.tester.keys()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_categories)

    def test_values(self):
        """values returns an iterator over the values"""
        obs = self.tester.values()
        self.assertTrue(isinstance(obs, Iterable))
        exp = {'ANL', 'true', 'true', 'ENVO:soil', '11/11/11 13:00:00',
               '1001:M7', 'Cannabis Soil Microbiome', 'winter', 'n',
               '64.6 sand, 17.6 silt, 17.8 clay', '1118232', '0.15', '3483',
               'root metagenome', '0.164', '114', '15', '1.41', '7.15', '0',
               'ENVO:Temperate grasslands, savannas, and shrubland biome',
               'GAZ:United States of America', '6.94', 'SKB8', '5',
               'Burmese root', 'ENVO:plant-associated habitat',
               '74.0894932572', '65.3283470202', '1118232'}
        self.assertItemsEqual(set(obs), exp)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = {('physical_specimen_location', 'ANL'),
               ('physical_specimen_remaining', 'true'),
               ('dna_extracted', 'true'),
               ('sample_type', 'ENVO:soil'),
               ('collection_timestamp', '11/11/11 13:00:00'),
               ('host_subject_id', '1001:M7'),
               ('description', 'Cannabis Soil Microbiome'),
               ('season_environment', 'winter'), ('assigned_from_geo', 'n'),
               ('texture', '64.6 sand, 17.6 silt, 17.8 clay'),
               ('taxon_id', '1118232'), ('depth', '0.15'),
               ('host_taxid', '3483'), ('common_name', 'root metagenome'),
               ('water_content_soil', '0.164'), ('elevation', '114'),
               ('temp', '15'), ('tot_nitro', '1.41'),
               ('samp_salinity', '7.15'), ('altitude', '0'),
               ('env_biome',
                'ENVO:Temperate grasslands, savannas, and shrubland biome'),
               ('country', 'GAZ:United States of America'), ('ph', '6.94'),
               ('anonymized_name', 'SKB8'), ('tot_org_carb', '5'),
               ('description_duplicate', 'Burmese root'),
               ('env_feature', 'ENVO:plant-associated habitat'),
               ('latitude', '74.0894932572'),
               ('longitude', '65.3283470202'),
               ('scientific_name', '1118232')}
        self.assertEqual(set(obs), exp)

    def test_get(self):
        """get returns the correct sample object"""
        self.assertEqual(self.tester.get('SEASON_ENVIRONMENT'), 'winter')
        self.assertEqual(self.tester.get('depth'), '0.15')

    def test_get_none(self):
        """get returns none if the sample id is not present"""
        self.assertTrue(self.tester.get('Not_a_Category') is None)

    def test_columns_restrictions(self):
        """that it returns SAMPLE_TEMPLATE_COLUMNS"""
        self.assertEqual(
            self.sample_template.columns_restrictions,
            qdb.metadata_template.constants.SAMPLE_TEMPLATE_COLUMNS)

    def test_can_be_updated(self):
        """test if the template can be updated"""
        self.assertTrue(self.sample_template.can_be_updated())

    def test_can_be_extended(self):
        """test if the template can be extended"""
        obs_bool, obs_msg = self.sample_template.can_be_extended([], [])
        self.assertTrue(obs_bool)
        self.assertEqual(obs_msg, "")


@qiita_test_checker()
class TestSampleReadWrite(BaseTestSample):
    def test_setitem(self):
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            self.tester['column that does not exist'] = 0.30

        self.assertEqual(self.tester['tot_nitro'], '1.41')
        self.tester['tot_nitro'] = '1234.5'
        self.assertEqual(self.tester['tot_nitro'], '1234.5')

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(qdb.exceptions.QiitaDBNotImplementedError):
            del self.tester['DEPTH']


class BaseTestSampleTemplate(TestCase):
    def _set_up(self):
        self.metadata_dict = {
            'Sample1': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': 'type1',
                        'collection_timestamp': '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 1',
                        'str_column': 'Value for sample 1',
                        'int_column': '1',
                        'latitude': '42.42',
                        'longitude': '41.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            'Sample2': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': 'type1',
                        'int_column': '2',
                        'collection_timestamp': '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 2',
                        'str_column': 'Value for sample 2',
                        'latitude': '4.2',
                        'longitude': '1.1',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            'Sample3': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': 'type1',
                        'collection_timestamp': '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 3',
                        'str_column': 'Value for sample 3',
                        'int_column': '3',
                        'latitude': '4.8',
                        'longitude': '4.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            }
        self.metadata = pd.DataFrame.from_dict(self.metadata_dict,
                                               orient='index', dtype=str)

        metadata_str_prefix_dict = {
            'foo.Sample1': self.metadata_dict['Sample1'],
            'bar.Sample2': self.metadata_dict['Sample2'],
            'foo.Sample3': self.metadata_dict['Sample3'],
        }
        self.metadata_str_prefix = pd.DataFrame.from_dict(
            metadata_str_prefix_dict, orient='index', dtype=str)

        metadata_int_prefix_dict = {
            '12.Sample1': self.metadata_dict['Sample1'],
            '12.Sample2': self.metadata_dict['Sample2'],
            '12.Sample3': self.metadata_dict['Sample3']
        }
        self.metadata_int_pref = pd.DataFrame.from_dict(
            metadata_int_prefix_dict, orient='index', dtype=str)

        metadata_prefixed_dict = {
            '2.Sample1': self.metadata_dict['Sample1'],
            '2.Sample2': self.metadata_dict['Sample2'],
            '2.Sample3': self.metadata_dict['Sample3']
        }
        self.metadata_prefixed = pd.DataFrame.from_dict(
            metadata_prefixed_dict, orient='index', dtype=str)

        self.test_study = qdb.study.Study(1)
        self.tester = qdb.metadata_template.sample_template.SampleTemplate(1)
        self.exp_sample_ids = {
            '1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195', '1.SKB4.640189',
            '1.SKB5.640181', '1.SKB6.640176', '1.SKB7.640196', '1.SKB8.640193',
            '1.SKB9.640200', '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
            '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190', '1.SKD7.640191',
            '1.SKD8.640184', '1.SKD9.640182', '1.SKM1.640183', '1.SKM2.640199',
            '1.SKM3.640197', '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
            '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192'}
        self._clean_up_files = []

        self.metadata_dict_updated_dict = {
            'Sample1': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '6',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 1',
                        'str_column': 'Value for sample 1',
                        'int_column': '1',
                        'latitude': '42.42',
                        'longitude': '41.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            'Sample2': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '5',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'the only one',
                        'Description': 'Test Sample 2',
                        'str_column': 'Value for sample 2',
                        'int_column': '2',
                        'latitude': '4.2',
                        'longitude': '1.1',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            'Sample3': {'physical_specimen_location': 'new location',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '10',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 3',
                        'str_column': 'Value for sample 3',
                        'int_column': '3',
                        'latitude': '4.8',
                        'longitude': '4.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            }
        self.metadata_dict_updated = pd.DataFrame.from_dict(
            self.metadata_dict_updated_dict, orient='index', dtype=str)

        metadata_dict_updated_sample_error = {
            'Sample1': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '6',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 1',
                        'str_column': 'Value for sample 1',
                        'int_column': '1',
                        'latitude': '42.42',
                        'longitude': '41.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            'Sample2': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '5',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'the only one',
                        'Description': 'Test Sample 2',
                        'str_column': 'Value for sample 2',
                        'int_column': '2',
                        'latitude': '4.2',
                        'longitude': '1.1',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            'Sample3': {'physical_specimen_location': 'new location',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '10',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 3',
                        'str_column': 'Value for sample 3',
                        'int_column': '3',
                        'latitude': '4.8',
                        'longitude': '4.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            'Sample4': {'physical_specimen_location': 'new location',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '10',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 4',
                        'str_column': 'Value for sample 4',
                        'int_column': '4',
                        'latitude': '4.8',
                        'longitude': '4.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'}
            }
        self.metadata_dict_updated_sample_error = pd.DataFrame.from_dict(
            metadata_dict_updated_sample_error, orient='index', dtype=str)

        metadata_dict_updated_column_error = {
            'Sample1': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '6',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 1',
                        'str_column': 'Value for sample 1',
                        'int_column': '1',
                        'latitude': '42.42',
                        'longitude': '41.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens',
                        'extra_col': True},
            'Sample2': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '5',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'the only one',
                        'Description': 'Test Sample 2',
                        'str_column': 'Value for sample 2',
                        'int_column': '2',
                        'latitude': '4.2',
                        'longitude': '1.1',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens',
                        'extra_col': True},
            'Sample3': {'physical_specimen_location': 'new location',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': '10',
                        'collection_timestamp':
                        '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 3',
                        'str_column': 'Value for sample 3',
                        'int_column': '3',
                        'latitude': '4.8',
                        'longitude': '4.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens',
                        'extra_col': True},
            }
        self.metadata_dict_updated_column_error = pd.DataFrame.from_dict(
            metadata_dict_updated_column_error, orient='index', dtype=str)

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)


class TestSampleTemplateReadOnly(BaseTestSampleTemplate):
    def setUp(self):
        self._set_up()

    def test_metadata_headers(self):
        ST = qdb.metadata_template.sample_template.SampleTemplate
        obs = ST.metadata_headers()
        exp = ['physical_specimen_location', 'physical_specimen_remaining',
               'dna_extracted', 'sample_type', 'collection_timestamp',
               'host_subject_id', 'description', 'season_environment',
               'assigned_from_geo', 'texture', 'taxon_id', 'depth',
               'host_taxid', 'common_name', 'water_content_soil', 'elevation',
               'temp', 'tot_nitro', 'samp_salinity', 'altitude', 'env_biome',
               'country', 'ph', 'anonymized_name', 'tot_org_carb',
               'description_duplicate', 'env_feature', 'latitude', 'longitude',
               'sample_id', 'scientific_name']
        self.assertItemsEqual(obs, exp)

    def test_study_id(self):
        """Ensure that the correct study ID is returned"""
        self.assertEqual(self.tester.study_id, 1)

    def test_init_unknown_error(self):
        """Init raises an error if the id is not known"""
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.metadata_template.sample_template.SampleTemplate(2)

    def test_init(self):
        """Init successfully instantiates the object"""
        st = qdb.metadata_template.sample_template.SampleTemplate(1)
        self.assertTrue(st.id, 1)

    def test_table_name(self):
        """Table name return the correct string"""
        obs = qdb.metadata_template.sample_template.SampleTemplate._table_name(
            self.test_study.id)
        self.assertEqual(obs, "sample_1")

    def test_exists_true(self):
        """Exists returns true when the SampleTemplate already exists"""
        self.assertTrue(
            qdb.metadata_template.sample_template.SampleTemplate.exists(
                self.test_study.id))

    def test_get_sample_ids(self):
        """get_sample_ids returns the correct set of sample ids"""
        obs = self.tester._get_sample_ids()
        self.assertEqual(obs, self.exp_sample_ids)

    def test_len(self):
        """Len returns the correct number of sample ids"""
        self.assertEqual(len(self.tester), 27)

    def test_getitem(self):
        """Get item returns the correct sample object"""
        obs = self.tester['1.SKM7.640188']
        exp = qdb.metadata_template.sample_template.Sample(
            '1.SKM7.640188', self.tester)
        self.assertEqual(obs, exp)

    def test_getitem_error(self):
        """Get item raises an error if key does not exists"""
        with self.assertRaises(KeyError):
            self.tester['Not_a_Sample']

    def test_categories(self):
        exp = {'season_environment', 'assigned_from_geo',
               'texture', 'taxon_id', 'depth', 'host_taxid',
               'common_name', 'water_content_soil', 'elevation',
               'temp', 'tot_nitro', 'samp_salinity', 'altitude',
               'env_biome', 'country', 'ph', 'anonymized_name',
               'tot_org_carb', 'description_duplicate', 'env_feature',
               'physical_specimen_location',
               'physical_specimen_remaining', 'dna_extracted',
               'sample_type', 'collection_timestamp', 'host_subject_id',
               'description', 'latitude', 'longitude', 'scientific_name'}
        obs = set(self.tester.categories())
        self.assertItemsEqual(obs, exp)

    def test_iter(self):
        """iter returns an iterator over the sample ids"""
        obs = self.tester.__iter__()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_sample_ids)

    def test_contains_true(self):
        """contains returns true if the sample id exists"""
        self.assertTrue('1.SKM7.640188' in self.tester)

    def test_contains_false(self):
        """contains returns false if the sample id does not exists"""
        self.assertFalse('Not_a_Sample' in self.tester)

    def test_keys(self):
        """keys returns an iterator over the sample ids"""
        obs = self.tester.keys()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_sample_ids)

    def test_values(self):
        """values returns an iterator over the values"""
        obs = self.tester.values()
        self.assertTrue(isinstance(obs, Iterable))
        exp = {qdb.metadata_template.sample_template.Sample('1.SKB1.640202',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKB2.640194',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKB3.640195',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKB4.640189',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKB5.640181',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKB6.640176',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKB7.640196',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKB8.640193',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKB9.640200',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKD1.640179',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKD2.640178',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKD3.640198',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKD4.640185',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKD5.640186',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKD6.640190',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKD7.640191',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKD8.640184',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKD9.640182',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKM1.640183',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKM2.640199',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKM3.640197',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKM4.640180',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKM5.640177',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKM6.640187',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKM7.640188',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKM8.640201',
                                                            self.tester),
               qdb.metadata_template.sample_template.Sample('1.SKM9.640192',
                                                            self.tester)}
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs), key=lambda x: x.id),
                        sorted(exp, key=lambda x: x.id)):
            self.assertEqual(o, e)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = [
            ('1.SKB1.640202', qdb.metadata_template.sample_template.Sample(
                '1.SKB1.640202', self.tester)),
            ('1.SKB2.640194', qdb.metadata_template.sample_template.Sample(
                '1.SKB2.640194', self.tester)),
            ('1.SKB3.640195', qdb.metadata_template.sample_template.Sample(
                '1.SKB3.640195', self.tester)),
            ('1.SKB4.640189', qdb.metadata_template.sample_template.Sample(
                '1.SKB4.640189', self.tester)),
            ('1.SKB5.640181', qdb.metadata_template.sample_template.Sample(
                '1.SKB5.640181', self.tester)),
            ('1.SKB6.640176', qdb.metadata_template.sample_template.Sample(
                '1.SKB6.640176', self.tester)),
            ('1.SKB7.640196', qdb.metadata_template.sample_template.Sample(
                '1.SKB7.640196', self.tester)),
            ('1.SKB8.640193', qdb.metadata_template.sample_template.Sample(
                '1.SKB8.640193', self.tester)),
            ('1.SKB9.640200', qdb.metadata_template.sample_template.Sample(
                '1.SKB9.640200', self.tester)),
            ('1.SKD1.640179', qdb.metadata_template.sample_template.Sample(
                '1.SKD1.640179', self.tester)),
            ('1.SKD2.640178', qdb.metadata_template.sample_template.Sample(
                '1.SKD2.640178', self.tester)),
            ('1.SKD3.640198', qdb.metadata_template.sample_template.Sample(
                '1.SKD3.640198', self.tester)),
            ('1.SKD4.640185', qdb.metadata_template.sample_template.Sample(
                '1.SKD4.640185', self.tester)),
            ('1.SKD5.640186', qdb.metadata_template.sample_template.Sample(
                '1.SKD5.640186', self.tester)),
            ('1.SKD6.640190', qdb.metadata_template.sample_template.Sample(
                '1.SKD6.640190', self.tester)),
            ('1.SKD7.640191', qdb.metadata_template.sample_template.Sample(
                '1.SKD7.640191', self.tester)),
            ('1.SKD8.640184', qdb.metadata_template.sample_template.Sample(
                '1.SKD8.640184', self.tester)),
            ('1.SKD9.640182', qdb.metadata_template.sample_template.Sample(
                '1.SKD9.640182', self.tester)),
            ('1.SKM1.640183', qdb.metadata_template.sample_template.Sample(
                '1.SKM1.640183', self.tester)),
            ('1.SKM2.640199', qdb.metadata_template.sample_template.Sample(
                '1.SKM2.640199', self.tester)),
            ('1.SKM3.640197', qdb.metadata_template.sample_template.Sample(
                '1.SKM3.640197', self.tester)),
            ('1.SKM4.640180', qdb.metadata_template.sample_template.Sample(
                '1.SKM4.640180', self.tester)),
            ('1.SKM5.640177', qdb.metadata_template.sample_template.Sample(
                '1.SKM5.640177', self.tester)),
            ('1.SKM6.640187', qdb.metadata_template.sample_template.Sample(
                '1.SKM6.640187', self.tester)),
            ('1.SKM7.640188', qdb.metadata_template.sample_template.Sample(
                '1.SKM7.640188', self.tester)),
            ('1.SKM8.640201', qdb.metadata_template.sample_template.Sample(
                '1.SKM8.640201', self.tester)),
            ('1.SKM9.640192', qdb.metadata_template.sample_template.Sample(
                '1.SKM9.640192', self.tester))]
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs)), sorted(exp)):
            self.assertEqual(o, e)

    def test_get(self):
        """get returns the correct sample object"""
        obs = self.tester.get('1.SKM7.640188')
        exp = qdb.metadata_template.sample_template.Sample(
            '1.SKM7.640188', self.tester)
        self.assertEqual(obs, exp)

    def test_get_none(self):
        """get returns none if the sample id is not present"""
        self.assertTrue(self.tester.get('Not_a_Sample') is None)

    def test_clean_validate_template_error_bad_chars(self):
        """Raises an error if there are invalid characters in the sample names
        """
        self.metadata.index = ['o()xxxx[{::::::::>', 'sample.1', 'sample.3']
        ST = qdb.metadata_template.sample_template.SampleTemplate
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            ST._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_error_duplicate_cols(self):
        """Raises an error if there are duplicated columns in the template"""
        self.metadata['STR_COLUMN'] = pd.Series(['foo', 'bar', 'foobar'],
                                                index=self.metadata.index)

        ST = qdb.metadata_template.sample_template.SampleTemplate
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateHeaderError):
            ST._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_error_duplicate_samples(self):
        """Raises an error if there are duplicated samples in the template"""
        self.metadata.index = ['sample.1', 'sample.1', 'sample.3']
        ST = qdb.metadata_template.sample_template.SampleTemplate
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateSamplesError):
            ST._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_columns(self):
        metadata_dict = {
            'Sample1': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': 'type1',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 1',
                        'latitude': '42.42',
                        'longitude': '41.41'}
            }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        ST = qdb.metadata_template.sample_template.SampleTemplate
        obs = ST._clean_validate_template(
            metadata, 2,
            qdb.metadata_template.constants.SAMPLE_TEMPLATE_COLUMNS)
        metadata_dict = {
            '2.Sample1': {'physical_specimen_location': 'location1',
                          'physical_specimen_remaining': 'true',
                          'dna_extracted': 'true',
                          'sample_type': 'type1',
                          'host_subject_id': 'NotIdentified',
                          'description': 'Test Sample 1',
                          'latitude': '42.42',
                          'longitude': '41.41'}
            }
        exp = pd.DataFrame.from_dict(metadata_dict, orient='index', dtype=str)
        obs.sort_index(axis=0, inplace=True)
        obs.sort_index(axis=1, inplace=True)
        exp.sort_index(axis=0, inplace=True)
        exp.sort_index(axis=1, inplace=True)
        assert_frame_equal(obs, exp)

    def test_clean_validate_template(self):
        ST = qdb.metadata_template.sample_template.SampleTemplate
        obs = ST._clean_validate_template(
            self.metadata, 2,
            qdb.metadata_template.constants.SAMPLE_TEMPLATE_COLUMNS)
        metadata_dict = {
            '2.Sample1': {'physical_specimen_location': 'location1',
                          'physical_specimen_remaining': 'true',
                          'dna_extracted': 'true',
                          'sample_type': 'type1',
                          'collection_timestamp':
                          '05/29/14 12:24:15',
                          'host_subject_id': 'NotIdentified',
                          'description': 'Test Sample 1',
                          'str_column': 'Value for sample 1',
                          'int_column': '1',
                          'latitude': '42.42',
                          'longitude': '41.41',
                          'taxon_id': '9606',
                          'scientific_name': 'homo sapiens'},
            '2.Sample2': {'physical_specimen_location': 'location1',
                          'physical_specimen_remaining': 'true',
                          'dna_extracted': 'true',
                          'sample_type': 'type1',
                          'int_column': '2',
                          'collection_timestamp':
                          '05/29/14 12:24:15',
                          'host_subject_id': 'NotIdentified',
                          'description': 'Test Sample 2',
                          'str_column': 'Value for sample 2',
                          'latitude': '4.2',
                          'longitude': '1.1',
                          'taxon_id': '9606',
                          'scientific_name': 'homo sapiens'},
            '2.Sample3': {'physical_specimen_location': 'location1',
                          'physical_specimen_remaining': 'true',
                          'dna_extracted': 'true',
                          'sample_type': 'type1',
                          'collection_timestamp':
                          '05/29/14 12:24:15',
                          'host_subject_id': 'NotIdentified',
                          'description': 'Test Sample 3',
                          'str_column': 'Value for sample 3',
                          'int_column': '3',
                          'latitude': '4.8',
                          'longitude': '4.41',
                          'taxon_id': '9606',
                          'scientific_name': 'homo sapiens'},
            }
        exp = pd.DataFrame.from_dict(metadata_dict, orient='index', dtype=str)
        obs.sort_index(axis=0, inplace=True)
        obs.sort_index(axis=1, inplace=True)
        exp.sort_index(axis=0, inplace=True)
        exp.sort_index(axis=1, inplace=True)
        assert_frame_equal(obs, exp)

    def test_clean_validate_template_no_pgsql_reserved_words(self):
        ST = qdb.metadata_template.sample_template.SampleTemplate
        self.metadata.rename(columns={'taxon_id': 'select'}, inplace=True)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            ST._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_no_invalid_chars(self):
        ST = qdb.metadata_template.sample_template.SampleTemplate
        self.metadata.rename(columns={'taxon_id': 'taxon id'}, inplace=True)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            ST._clean_validate_template(self.metadata, 2)

    def test_get_category(self):
        pt = qdb.metadata_template.sample_template.SampleTemplate(1)
        obs = pt.get_category('latitude')
        exp = {'1.SKB2.640194': '35.2374368957',
               '1.SKM4.640180': 'Not applicable',
               '1.SKB3.640195': '95.2060749748',
               '1.SKB6.640176': '78.3634273709',
               '1.SKD6.640190': '29.1499460692',
               '1.SKM6.640187': '0.291867635913',
               '1.SKD9.640182': '23.1218032799',
               '1.SKM8.640201': '3.21190859967',
               '1.SKM2.640199': '82.8302905615',
               '1.SKD2.640178': '53.5050692395',
               '1.SKB7.640196': '13.089194595',
               '1.SKD4.640185': '40.8623799474',
               '1.SKB8.640193': '74.0894932572',
               '1.SKM3.640197': 'Not applicable',
               '1.SKD5.640186': '85.4121476399',
               '1.SKB1.640202': '4.59216095574',
               '1.SKM1.640183': '38.2627021402',
               '1.SKD1.640179': '68.0991287718',
               '1.SKD3.640198': '84.0030227585',
               '1.SKB5.640181': '10.6655599093',
               '1.SKB4.640189': '43.9614715197',
               '1.SKB9.640200': '12.6245524972',
               '1.SKM9.640192': '12.7065957714',
               '1.SKD8.640184': '57.571893782',
               '1.SKM5.640177': '44.9725384282',
               '1.SKM7.640188': '60.1102854322',
               '1.SKD7.640191': '68.51099627'}
        self.assertEqual(obs, exp)

    def test_get_category_no_exists(self):
        pt = qdb.metadata_template.sample_template.SampleTemplate(1)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            pt.get_category('DOESNOTEXIST')


@qiita_test_checker()
class TestSampleTemplateReadWrite(BaseTestSampleTemplate):
    """Tests the SampleTemplate class"""

    def setUp(self):
        self._set_up()
        info = {
            "timeseries_type_id": '1',
            "metadata_complete": 'true',
            "mixs_compliant": 'true',
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "emp_person_id": qdb.study.StudyPerson(2),
            "principal_investigator_id": qdb.study.StudyPerson(3),
            "lab_person_id": qdb.study.StudyPerson(1)
        }
        self.new_study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Fried Chicken Microbiome", [1],
            info)

    def test_create_duplicate(self):
        """Create raises an error when creating a duplicated SampleTemplate"""
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.metadata_template.sample_template.SampleTemplate.create(
                self.metadata, self.test_study)

    def test_create_duplicate_header(self):
        """Create raises an error when duplicate headers are present"""
        self.metadata['STR_COLUMN'] = pd.Series(['', '', ''],
                                                index=self.metadata.index)
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateHeaderError):
            qdb.metadata_template.sample_template.SampleTemplate.create(
                self.metadata, self.new_study)

    def test_create_bad_sample_names(self):
        """Create raises an error when duplicate headers are present"""
        # set a horrible list of sample names
        self.metadata.index = ['o()xxxx[{::::::::>', 'sample.1', 'sample.3']
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.metadata_template.sample_template.SampleTemplate.create(
                self.metadata, self.new_study)

    def test_create(self):
        """Creates a new SampleTemplate"""
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        new_id = self.new_study.id
        # The returned object has the correct id
        self.assertEqual(st.id, new_id)
        self.assertEqual(st.study_id, self.new_study.id)
        self.assertTrue(
            qdb.metadata_template.sample_template.SampleTemplate.exists(
                self.new_study.id))
        exp_sample_ids = {"%s.Sample1" % new_id, "%s.Sample2" % new_id,
                          "%s.Sample3" % new_id}
        self.assertEqual(st._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(st), 3)
        exp_categories = {'collection_timestamp', 'description',
                          'dna_extracted', 'host_subject_id', 'int_column',
                          'latitude', 'longitude',
                          'physical_specimen_location',
                          'physical_specimen_remaining', 'sample_type',
                          'scientific_name', 'str_column', 'taxon_id'}
        self.assertItemsEqual(st.categories(), exp_categories)
        exp_dict = {
            "%s.Sample1" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 1",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '1',
                'latitude': '42.42',
                'longitude': '41.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 1",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.Sample2" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 2",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '2',
                'latitude': '4.2',
                'longitude': '1.1',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 2",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.Sample3" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 3",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '3',
                'latitude': '4.8',
                'longitude': '4.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 3",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'}}
        for s_id in exp_sample_ids:
            self.assertEqual(st[s_id]._to_dict(), exp_dict[s_id])
        exp = {"%s.Sample1" % new_id: None,
               "%s.Sample2" % new_id: None,
               "%s.Sample3" % new_id: None}
        self.assertEqual(st.ebi_sample_accessions, exp)
        self.assertEqual(st.biosample_accessions, exp)

    def test_create_int_prefix(self):
        """Creates a new SampleTemplate with sample names int prefixed"""
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata_int_pref, self.new_study)
        new_id = self.new_study.id
        # The returned object has the correct id
        self.assertEqual(st.id, new_id)
        self.assertEqual(st.study_id, self.new_study.id)
        self.assertTrue(
            qdb.metadata_template.sample_template.SampleTemplate.exists(
                self.new_study.id))
        exp_sample_ids = {"%s.12.Sample1" % new_id, "%s.12.Sample2" % new_id,
                          "%s.12.Sample3" % new_id}
        self.assertEqual(st._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(st), 3)
        exp_categories = {'collection_timestamp', 'description',
                          'dna_extracted', 'host_subject_id', 'int_column',
                          'latitude', 'longitude',
                          'physical_specimen_location',
                          'physical_specimen_remaining', 'sample_type',
                          'scientific_name', 'str_column', 'taxon_id'}
        self.assertItemsEqual(st.categories(), exp_categories)
        exp_dict = {
            "%s.12.Sample1" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 1",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '1',
                'latitude': '42.42',
                'longitude': '41.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 1",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.12.Sample2" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 2",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '2',
                'latitude': '4.2',
                'longitude': '1.1',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 2",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.12.Sample3" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 3",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '3',
                'latitude': '4.8',
                'longitude': '4.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 3",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'}}
        for s_id in exp_sample_ids:
            self.assertEqual(st[s_id]._to_dict(), exp_dict[s_id])
        exp = {"%s.12.Sample1" % new_id: None,
               "%s.12.Sample2" % new_id: None,
               "%s.12.Sample3" % new_id: None}
        self.assertEqual(st.ebi_sample_accessions, exp)
        self.assertEqual(st.biosample_accessions, exp)

    def test_create_str_prefixes(self):
        """Creates a new SampleTemplate with sample names string prefixed"""
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata_str_prefix, self.new_study)
        new_id = self.new_study.id
        # The returned object has the correct id
        self.assertEqual(st.id, new_id)
        self.assertEqual(st.study_id, self.new_study.id)
        self.assertTrue(
            qdb.metadata_template.sample_template.SampleTemplate.exists(
                self.new_study.id))
        exp_sample_ids = {"%s.foo.Sample1" % new_id, "%s.bar.Sample2" % new_id,
                          "%s.foo.Sample3" % new_id}
        self.assertEqual(st._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(st), 3)
        exp_categories = {'collection_timestamp', 'description',
                          'dna_extracted', 'host_subject_id', 'int_column',
                          'latitude', 'longitude',
                          'physical_specimen_location',
                          'physical_specimen_remaining', 'sample_type',
                          'scientific_name', 'str_column', 'taxon_id'}
        self.assertItemsEqual(st.categories(), exp_categories)
        exp_dict = {
            "%s.foo.Sample1" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 1",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '1',
                'latitude': '42.42',
                'longitude': '41.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 1",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.bar.Sample2" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 2",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '2',
                'latitude': '4.2',
                'longitude': '1.1',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 2",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.foo.Sample3" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 3",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '3',
                'latitude': '4.8',
                'longitude': '4.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 3",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'}}
        for s_id in exp_sample_ids:
            self.assertEqual(st[s_id]._to_dict(), exp_dict[s_id])
        exp = {"%s.foo.Sample1" % new_id: None,
               "%s.bar.Sample2" % new_id: None,
               "%s.foo.Sample3" % new_id: None}
        self.assertEqual(st.ebi_sample_accessions, exp)
        self.assertEqual(st.biosample_accessions, exp)

    def test_create_already_prefixed_samples(self):
        """Creates a new SampleTemplate with the samples already prefixed"""
        st = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.sample_template.SampleTemplate.create,
            self.metadata_prefixed, self.new_study)
        new_id = self.new_study.id
        # The returned object has the correct id
        self.assertEqual(st.id, new_id)
        self.assertEqual(st.study_id, self.new_study.id)
        self.assertTrue(
            qdb.metadata_template.sample_template.SampleTemplate.exists(
                self.new_study.id))
        exp_sample_ids = {"%s.Sample1" % new_id, "%s.Sample2" % new_id,
                          "%s.Sample3" % new_id}
        self.assertEqual(st._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(st), 3)
        exp_categories = {'collection_timestamp', 'description',
                          'dna_extracted', 'host_subject_id', 'int_column',
                          'latitude', 'longitude',
                          'physical_specimen_location',
                          'physical_specimen_remaining', 'sample_type',
                          'scientific_name', 'str_column', 'taxon_id'}
        self.assertItemsEqual(st.categories(), exp_categories)
        exp_dict = {
            "%s.Sample1" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 1",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '1',
                'latitude': '42.42',
                'longitude': '41.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 1",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.Sample2" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 2",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '2',
                'latitude': '4.2',
                'longitude': '1.1',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 2",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.Sample3" % new_id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 3",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '3',
                'latitude': '4.8',
                'longitude': '4.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 3",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'}}
        for s_id in exp_sample_ids:
            self.assertEqual(st[s_id]._to_dict(), exp_dict[s_id])
        exp = {"%s.Sample1" % new_id: None,
               "%s.Sample2" % new_id: None,
               "%s.Sample3" % new_id: None}
        self.assertEqual(st.ebi_sample_accessions, exp)
        self.assertEqual(st.biosample_accessions, exp)

    def test_delete(self):
        """Deletes Sample template 1"""
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        st_id = st.id
        qdb.metadata_template.sample_template.SampleTemplate.delete(st.id)

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_sample WHERE study_id=%s" % st_id)
        exp = []
        self.assertEqual(obs, exp)

        with self.assertRaises(ValueError):
            self.conn_handler.execute_fetchall(
                "SELECT * FROM qiita.sample_%s" % st_id)

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.metadata_template.sample_template.SampleTemplate.delete(1)

    def test_delete_unkonwn_id_error(self):
        """Try to delete a non existent prep template"""
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.metadata_template.sample_template.SampleTemplate.delete(5)

    def test_exists_false(self):
        """Exists returns false when the SampleTemplate does not exists"""
        self.assertFalse(
            qdb.metadata_template.sample_template.SampleTemplate.exists(
                self.new_study.id))

    def test_update_category(self):
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            self.tester.update_category('country', {"foo": "bar"})

        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            self.tester.update_category('missing column',
                                        {'1.SKM7.640188': 'stuff'})

        negtest = self.tester['1.SKM7.640188']['country']

        mapping = {'1.SKB1.640202': "1",
                   '1.SKB5.640181': "2",
                   '1.SKD6.640190': "3"}

        self.tester.update_category('country', mapping)

        self.assertEqual(self.tester['1.SKB1.640202']['country'], "1")
        self.assertEqual(self.tester['1.SKB5.640181']['country'], "2")
        self.assertEqual(self.tester['1.SKD6.640190']['country'], "3")
        self.assertEqual(self.tester['1.SKM7.640188']['country'], negtest)

    def test_update_equal(self):
        """It doesn't fail with the exact same template"""
        # Create a new sample tempalte
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        exp = {s_id: st[s_id]._to_dict() for s_id in st}
        # Try to update the sample template with the same values
        npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, st.update, self.metadata)
        # Check that no values have been changed
        obs = {s_id: st[s_id]._to_dict() for s_id in st}
        self.assertEqual(obs, exp)

    def test_update(self):
        """Updates values in existing mapping file"""
        # creating a new sample template
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        # updating the sample template
        st.update(self.metadata_dict_updated)

        # validating values
        exp = self.metadata_dict_updated_dict['Sample1'].values()
        obs = st.get('2.Sample1').values()
        self.assertItemsEqual(obs, exp)

        exp = self.metadata_dict_updated_dict['Sample2'].values()
        obs = st.get('2.Sample2').values()
        self.assertItemsEqual(obs, exp)

        exp = self.metadata_dict_updated_dict['Sample3'].values()
        obs = st.get('2.Sample3').values()
        self.assertItemsEqual(obs, exp)

        # checking errors
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            st.update(self.metadata_dict_updated_sample_error)
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            st.update(self.metadata_dict_updated_column_error)

    def test_update_fewer_samples(self):
        """Updates using a dataframe with less samples that in the DB"""
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        new_metadata = pd.DataFrame.from_dict(
            {'Sample1': {'physical_specimen_location': 'CHANGE'}},
            orient='index', dtype=str)
        exp = {s_id: st[s_id]._to_dict() for s_id in st}
        s_id = '%d.Sample1' % self.new_study.id
        exp[s_id]['physical_specimen_location'] = 'CHANGE'
        st.update(new_metadata)
        obs = {s_id: st[s_id]._to_dict() for s_id in st}
        self.assertEqual(obs, exp)

    def test_update_numpy(self):
        """Update values in existing mapping file with numpy values"""
        ST = qdb.metadata_template.sample_template.SampleTemplate
        metadata_dict = {
            'Sample1': {'bool_col': 'true',
                        'date_col': '2015-09-01 00:00:00'},
            'Sample2': {'bool_col': 'true',
                        'date_col': '2015-09-01 00:00:00'}
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        st = npt.assert_warns(qdb.exceptions.QiitaDBWarning, ST.create,
                              metadata, self.new_study)

        metadata_dict['Sample2']['date_col'] = '2015-09-01 00:00:00'
        metadata_dict['Sample1']['bool_col'] = 'false'
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        npt.assert_warns(qdb.exceptions.QiitaDBWarning, st.update, metadata)

        sql = "SELECT * FROM qiita.sample_{0}".format(st.id)
        obs = self.conn_handler.execute_fetchall(sql)
        exp = [['2.Sample1', 'false', '2015-09-01 00:00:00'],
               ['2.Sample2', 'true', '2015-09-01 00:00:00']]
        self.assertEqual(sorted(obs), sorted(exp))

    def test_generate_files(self):
        fp_count = qdb.util.get_count("qiita.filepath")
        self.tester.generate_files()
        obs = qdb.util.get_count("qiita.filepath")
        # We just make sure that the count has been increased by 6, since
        # the contents of the files have been tested elsewhere.
        self.assertEqual(obs, fp_count + 5)

    def test_to_file(self):
        """to file writes a tab delimited file with all the metadata"""
        fd, fp = mkstemp()
        close(fd)
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        st.to_file(fp)
        self._clean_up_files.append(fp)
        with open(fp, 'U') as f:
            obs = f.read()
        self.assertEqual(obs, EXP_SAMPLE_TEMPLATE)

        fd, fp = mkstemp()
        close(fd)
        st.to_file(fp, {'2.Sample1', '2.Sample3'})
        self._clean_up_files.append(fp)

        with open(fp, 'U') as f:
            obs = f.read()
        self.assertEqual(obs, EXP_SAMPLE_TEMPLATE_FEWER_SAMPLES)

    def test_get_filepath(self):
        # we will check that there is a new id only because the path will
        # change based on time and the same functionality is being tested
        # in data.py
        exp_id = self.conn_handler.execute_fetchone(
            "SELECT count(1) FROM qiita.filepath")[0] + 1
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        self.assertEqual(st.get_filepaths()[0][0], exp_id)

        # testing current functionaly, to add a new sample template
        # you need to erase it first
        qdb.metadata_template.sample_template.SampleTemplate.delete(st.id)
        exp_id += 1
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        self.assertEqual(st.get_filepaths()[0][0], exp_id)

    def test_extend_add_samples(self):
        """extend correctly works adding new samples"""
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)

        md_dict = {
            'Sample4': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': 'type1',
                        'collection_timestamp': '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 4',
                        'str_column': 'Value for sample 4',
                        'int_column': '4',
                        'latitude': '42.42',
                        'longitude': '41.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'},
            'Sample5': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': 'type1',
                        'collection_timestamp': '05/29/14 12:24:15',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 5',
                        'str_column': 'Value for sample 5',
                        'int_column': '5',
                        'latitude': '42.42',
                        'longitude': '41.41',
                        'taxon_id': '9606',
                        'scientific_name': 'homo sapiens'}}
        md_ext = pd.DataFrame.from_dict(md_dict, orient='index', dtype=str)

        npt.assert_warns(qdb.exceptions.QiitaDBWarning, st.extend, md_ext)

        # Test samples have been added correctly
        exp_sample_ids = {"%s.Sample1" % st.id, "%s.Sample2" % st.id,
                          "%s.Sample3" % st.id, "%s.Sample4" % st.id,
                          "%s.Sample5" % st.id}
        self.assertEqual(st._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(st), 5)
        exp_categories = {'collection_timestamp', 'description',
                          'dna_extracted', 'host_subject_id', 'int_column',
                          'latitude', 'longitude',
                          'physical_specimen_location',
                          'physical_specimen_remaining', 'sample_type',
                          'scientific_name', 'str_column', 'taxon_id'}
        self.assertItemsEqual(st.categories(), exp_categories)
        exp_dict = {
            "%s.Sample1" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 1",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '1',
                'latitude': '42.42',
                'longitude': '41.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 1",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.Sample2" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 2",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '2',
                'latitude': '4.2',
                'longitude': '1.1',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 2",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.Sample3" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 3",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '3',
                'latitude': '4.8',
                'longitude': '4.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 3",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            '%s.Sample4' % st.id: {
                'int_column': '4',
                'str_column': 'Value for sample 4',
                'physical_specimen_location': 'location1',
                'physical_specimen_remaining': 'true',
                'dna_extracted': 'true',
                'sample_type': 'type1',
                'collection_timestamp': '05/29/14 12:24:15',
                'host_subject_id': 'NotIdentified',
                'description': 'Test Sample 4',
                'latitude': '42.42',
                'longitude': '41.41',
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            '%s.Sample5' % st.id: {
                'int_column': '5',
                'str_column': 'Value for sample 5',
                'physical_specimen_location': 'location1',
                'physical_specimen_remaining': 'true',
                'dna_extracted': 'true',
                'sample_type': 'type1',
                'collection_timestamp': '05/29/14 12:24:15',
                'host_subject_id': 'NotIdentified',
                'description': 'Test Sample 5',
                'latitude': '42.42',
                'longitude': '41.41',
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'}}
        for s_id in exp_sample_ids:
            self.assertEqual(st[s_id]._to_dict(), exp_dict[s_id])

    def test_extend_add_duplicate_samples(self):
        """extend correctly works adding new samples and warns for duplicates
        """
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)

        self.metadata_dict['Sample4'] = {
            'physical_specimen_location': 'location1',
            'physical_specimen_remaining': 'true',
            'dna_extracted': 'true',
            'sample_type': 'type1',
            'collection_timestamp': '05/29/14 12:24:15',
            'host_subject_id': 'NotIdentified',
            'Description': 'Test Sample 4',
            'str_column': 'Value for sample 4',
            'int_column': '4',
            'latitude': '42.42',
            'longitude': '41.41',
            'taxon_id': '9606',
            'scientific_name': 'homo sapiens'}

        # Change a couple of values on the existent samples to test that
        # they remain unchanged
        self.metadata_dict['Sample1']['Description'] = 'Changed'
        self.metadata_dict['Sample2']['str_column'] = 'Changed dynamic'

        md_ext = pd.DataFrame.from_dict(self.metadata_dict, orient='index',
                                        dtype=str)
        # Make sure adding duplicate samples raises warning
        npt.assert_warns(qdb.exceptions.QiitaDBWarning, st.extend, md_ext)

        # Make sure the new sample has been added and the values for the
        # existent samples did not change
        exp_sample_ids = {"%s.Sample1" % st.id, "%s.Sample2" % st.id,
                          "%s.Sample3" % st.id, "%s.Sample4" % st.id}
        self.assertEqual(st._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(st), 4)
        exp_categories = {'collection_timestamp', 'description',
                          'dna_extracted', 'host_subject_id', 'int_column',
                          'latitude', 'longitude',
                          'physical_specimen_location',
                          'physical_specimen_remaining', 'sample_type',
                          'scientific_name', 'str_column', 'taxon_id'}
        self.assertItemsEqual(st.categories(), exp_categories)
        exp_dict = {
            "%s.Sample1" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 1",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '1',
                'latitude': '42.42',
                'longitude': '41.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 1",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.Sample2" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 2",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '2',
                'latitude': '4.2',
                'longitude': '1.1',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 2",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            "%s.Sample3" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 3",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '3',
                'latitude': '4.8',
                'longitude': '4.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 3",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'},
            '%s.Sample4' % st.id: {
                'int_column': '4',
                'str_column': 'Value for sample 4',
                'physical_specimen_location': 'location1',
                'physical_specimen_remaining': 'true',
                'dna_extracted': 'true',
                'sample_type': 'type1',
                'collection_timestamp': '05/29/14 12:24:15',
                'host_subject_id': 'NotIdentified',
                'description': 'Test Sample 4',
                'latitude': '42.42',
                'longitude': '41.41',
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens'}}
        for s_id in exp_sample_ids:
            self.assertEqual(st[s_id]._to_dict(), exp_dict[s_id])

    def test_extend_new_columns(self):
        """extend correctly adds a new column"""
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)

        self.metadata['NEWCOL'] = pd.Series(['val1', 'val2', 'val3'],
                                            index=self.metadata.index)
        self.metadata['NEW_COL'] = pd.Series(['val_1', 'val_2', 'val_3'],
                                             index=self.metadata.index)

        # Change some values to make sure that they do not change on extend
        self.metadata_dict['Sample1']['Description'] = 'Changed'
        self.metadata_dict['Sample2']['str_column'] = 'Changed dynamic'

        # Make sure it raises a warning indicating that the new columns will
        # be added for the existing samples
        npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, st.extend, self.metadata)

        exp_sample_ids = {"%s.Sample1" % st.id, "%s.Sample2" % st.id,
                          "%s.Sample3" % st.id}
        self.assertEqual(st._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(st), 3)
        exp_categories = {'collection_timestamp', 'description',
                          'dna_extracted', 'host_subject_id', 'int_column',
                          'latitude', 'longitude',
                          'physical_specimen_location',
                          'physical_specimen_remaining', 'sample_type',
                          'scientific_name', 'str_column', 'taxon_id',
                          'newcol', 'new_col'}
        self.assertItemsEqual(st.categories(), exp_categories)
        exp_dict = {
            "%s.Sample1" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 1",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '1',
                'latitude': '42.42',
                'longitude': '41.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 1",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val1',
                'new_col': 'val_1'},
            "%s.Sample2" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 2",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '2',
                'latitude': '4.2',
                'longitude': '1.1',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 2",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val2',
                'new_col': 'val_2'},
            "%s.Sample3" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 3",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '3',
                'latitude': '4.8',
                'longitude': '4.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 3",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val3',
                'new_col': 'val_3'}}
        for s_id in exp_sample_ids:
            self.assertEqual(st[s_id]._to_dict(), exp_dict[s_id])

    def test_extend_new_samples_and_columns(self):
        """extend correctly adds new samples and columns at the same time"""
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)

        self.metadata_dict['Sample4'] = {
            'physical_specimen_location': 'location1',
            'physical_specimen_remaining': 'true',
            'dna_extracted': 'true',
            'sample_type': 'type1',
            'collection_timestamp': '05/29/14 12:24:15',
            'host_subject_id': 'NotIdentified',
            'Description': 'Test Sample 4',
            'str_column': 'Value for sample 4',
            'int_column': '4',
            'latitude': '42.42',
            'longitude': '41.41',
            'taxon_id': '9606',
            'scientific_name': 'homo sapiens'}

        # Change a couple of values on the existent samples to test that
        # they remain unchanged
        self.metadata_dict['Sample1']['Description'] = 'Changed'
        self.metadata_dict['Sample2']['str_column'] = 'Changed dynamic'

        md_ext = pd.DataFrame.from_dict(self.metadata_dict, orient='index',
                                        dtype=str)

        md_ext['NEWCOL'] = pd.Series(['val1', 'val2', 'val3', 'val4'],
                                     index=md_ext.index)
        # Make sure adding duplicate samples raises warning
        npt.assert_warns(qdb.exceptions.QiitaDBWarning, st.extend, md_ext)
        exp_sample_ids = {"%s.Sample1" % st.id, "%s.Sample2" % st.id,
                          "%s.Sample3" % st.id, "%s.Sample4" % st.id}
        self.assertEqual(st._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(st), 4)
        exp_categories = {'collection_timestamp', 'description',
                          'dna_extracted', 'host_subject_id', 'int_column',
                          'latitude', 'longitude',
                          'physical_specimen_location',
                          'physical_specimen_remaining', 'sample_type',
                          'scientific_name', 'str_column', 'taxon_id',
                          'newcol'}
        self.assertItemsEqual(st.categories(), exp_categories)
        exp_dict = {
            "%s.Sample1" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 1",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '1',
                'latitude': '42.42',
                'longitude': '41.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 1",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val1'},
            "%s.Sample2" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 2",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '2',
                'latitude': '4.2',
                'longitude': '1.1',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 2",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val2'},
            "%s.Sample3" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 3",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '3',
                'latitude': '4.8',
                'longitude': '4.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 3",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val3'},
            '%s.Sample4' % st.id: {
                'int_column': '4',
                'str_column': 'Value for sample 4',
                'physical_specimen_location': 'location1',
                'physical_specimen_remaining': 'true',
                'dna_extracted': 'true',
                'sample_type': 'type1',
                'collection_timestamp': '05/29/14 12:24:15',
                'host_subject_id': 'NotIdentified',
                'description': 'Test Sample 4',
                'latitude': '42.42',
                'longitude': '41.41',
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val4'}}
        for s_id in exp_sample_ids:
            self.assertEqual(st[s_id]._to_dict(), exp_dict[s_id])

    def test_extend_update(self):
        """extend correctly adds new samples and columns at the same time"""
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)

        self.metadata_dict['Sample4'] = {
            'physical_specimen_location': 'location1',
            'physical_specimen_remaining': 'true',
            'dna_extracted': 'true',
            'sample_type': 'type1',
            'collection_timestamp': '05/29/14 12:24:15',
            'host_subject_id': 'NotIdentified',
            'Description': 'Test Sample 4',
            'str_column': 'Value for sample 4',
            'int_column': '4',
            'latitude': '42.42',
            'longitude': '41.41',
            'taxon_id': '9606',
            'scientific_name': 'homo sapiens'}

        self.metadata_dict['Sample1']['Description'] = 'Changed'
        self.metadata_dict['Sample2']['str_column'] = 'Changed dynamic'

        md_ext = pd.DataFrame.from_dict(self.metadata_dict, orient='index',
                                        dtype=str)

        md_ext['NEWCOL'] = pd.Series(['val1', 'val2', 'val3', 'val4'],
                                     index=md_ext.index)

        npt.assert_warns(qdb.exceptions.QiitaDBWarning, st.extend, md_ext)
        st.update(md_ext)
        exp_sample_ids = {"%s.Sample1" % st.id, "%s.Sample2" % st.id,
                          "%s.Sample3" % st.id, "%s.Sample4" % st.id}
        self.assertEqual(st._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(st), 4)
        exp_categories = {'collection_timestamp', 'description',
                          'dna_extracted', 'host_subject_id', 'int_column',
                          'latitude', 'longitude',
                          'physical_specimen_location',
                          'physical_specimen_remaining', 'sample_type',
                          'scientific_name', 'str_column', 'taxon_id',
                          'newcol'}
        self.assertItemsEqual(st.categories(), exp_categories)
        exp_dict = {
            "%s.Sample1" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Changed",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '1',
                'latitude': '42.42',
                'longitude': '41.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 1",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val1'},
            "%s.Sample2" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 2",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '2',
                'latitude': '4.2',
                'longitude': '1.1',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Changed dynamic",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val2'},
            "%s.Sample3" % st.id: {
                'collection_timestamp': '05/29/14 12:24:15',
                'description': "Test Sample 3",
                'dna_extracted': 'true',
                'host_subject_id': "NotIdentified",
                'int_column': '3',
                'latitude': '4.8',
                'longitude': '4.41',
                'physical_specimen_location': "location1",
                'physical_specimen_remaining': 'true',
                'sample_type': "type1",
                'str_column': "Value for sample 3",
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val3'},
            '%s.Sample4' % st.id: {
                'int_column': '4',
                'str_column': 'Value for sample 4',
                'physical_specimen_location': 'location1',
                'physical_specimen_remaining': 'true',
                'dna_extracted': 'true',
                'sample_type': 'type1',
                'collection_timestamp': '05/29/14 12:24:15',
                'host_subject_id': 'NotIdentified',
                'description': 'Test Sample 4',
                'latitude': '42.42',
                'longitude': '41.41',
                'taxon_id': '9606',
                'scientific_name': 'homo sapiens',
                'newcol': 'val4'}}
        for s_id in exp_sample_ids:
            self.assertEqual(st[s_id]._to_dict(), exp_dict[s_id])

    def test_to_dataframe(self):
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        obs = st.to_dataframe()

        exp_dict = {
            '2.Sample1': {'physical_specimen_location': 'location1',
                          'physical_specimen_remaining': 'true',
                          'dna_extracted': 'true',
                          'sample_type': 'type1',
                          'collection_timestamp':
                          '05/29/14 12:24:15',
                          'host_subject_id': 'NotIdentified',
                          'description': 'Test Sample 1',
                          'str_column': 'Value for sample 1',
                          'int_column': '1',
                          'latitude': '42.42',
                          'longitude': '41.41',
                          'taxon_id': '9606',
                          'scientific_name': 'homo sapiens'},
            '2.Sample2': {'physical_specimen_location': 'location1',
                          'physical_specimen_remaining': 'true',
                          'dna_extracted': 'true',
                          'sample_type': 'type1',
                          'int_column': '2',
                          'collection_timestamp':
                          '05/29/14 12:24:15',
                          'host_subject_id': 'NotIdentified',
                          'description': 'Test Sample 2',
                          'str_column': 'Value for sample 2',
                          'latitude': '4.2',
                          'longitude': '1.1',
                          'taxon_id': '9606',
                          'scientific_name': 'homo sapiens'},
            '2.Sample3': {'physical_specimen_location': 'location1',
                          'physical_specimen_remaining': 'true',
                          'dna_extracted': 'true',
                          'sample_type': 'type1',
                          'collection_timestamp':
                          '05/29/14 12:24:15',
                          'host_subject_id': 'NotIdentified',
                          'description': 'Test Sample 3',
                          'str_column': 'Value for sample 3',
                          'int_column': '3',
                          'latitude': '4.8',
                          'longitude': '4.41',
                          'taxon_id': '9606',
                          'scientific_name': 'homo sapiens'},
            }
        exp = pd.DataFrame.from_dict(exp_dict, orient='index', dtype=str)
        exp.index.name = 'sample_id'
        obs.sort_index(axis=0, inplace=True)
        obs.sort_index(axis=1, inplace=True)
        exp.sort_index(axis=0, inplace=True)
        exp.sort_index(axis=1, inplace=True)
        assert_frame_equal(obs, exp)

        obs = self.tester.to_dataframe()
        # We don't test the specific values as this would blow up the size
        # of this file as the amount of lines would go to ~1000

        # 27 samples
        self.assertEqual(len(obs), 27)
        exp = {'1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195',
               '1.SKB4.640189', '1.SKB5.640181', '1.SKB6.640176',
               '1.SKB7.640196', '1.SKB8.640193', '1.SKB9.640200',
               '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
               '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190',
               '1.SKD7.640191', '1.SKD8.640184', '1.SKD9.640182',
               '1.SKM1.640183', '1.SKM2.640199', '1.SKM3.640197',
               '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
               '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192'}
        self.assertEqual(set(obs.index), exp)

        self.assertEqual(set(obs.columns), {
            'physical_specimen_location', 'physical_specimen_remaining',
            'dna_extracted', 'sample_type', 'collection_timestamp',
            'host_subject_id', 'description', 'latitude', 'longitude',
            'season_environment', 'assigned_from_geo', 'texture',
            'taxon_id', 'depth', 'host_taxid', 'common_name',
            'water_content_soil', 'elevation', 'temp', 'tot_nitro',
            'samp_salinity', 'altitude', 'env_biome', 'country', 'ph',
            'anonymized_name', 'tot_org_carb', 'description_duplicate',
            'env_feature', 'scientific_name'})

    def test_check_restrictions(self):
        obs = self.tester.check_restrictions(
            [qdb.metadata_template.constants.SAMPLE_TEMPLATE_COLUMNS['EBI']])
        self.assertEqual(obs, set([]))

    def test_ebi_sample_accessions(self):
        obs = self.tester.ebi_sample_accessions
        exp = {'1.SKB8.640193': 'ERS000000',
               '1.SKD8.640184': 'ERS000001',
               '1.SKB7.640196': 'ERS000002',
               '1.SKM9.640192': 'ERS000003',
               '1.SKM4.640180': 'ERS000004',
               '1.SKM5.640177': 'ERS000005',
               '1.SKB5.640181': 'ERS000006',
               '1.SKD6.640190': 'ERS000007',
               '1.SKB2.640194': 'ERS000008',
               '1.SKD2.640178': 'ERS000009',
               '1.SKM7.640188': 'ERS000010',
               '1.SKB1.640202': 'ERS000011',
               '1.SKD1.640179': 'ERS000012',
               '1.SKD3.640198': 'ERS000013',
               '1.SKM8.640201': 'ERS000014',
               '1.SKM2.640199': 'ERS000015',
               '1.SKB9.640200': 'ERS000016',
               '1.SKD5.640186': 'ERS000017',
               '1.SKM3.640197': 'ERS000018',
               '1.SKD9.640182': 'ERS000019',
               '1.SKB4.640189': 'ERS000020',
               '1.SKD7.640191': 'ERS000021',
               '1.SKM6.640187': 'ERS000022',
               '1.SKD4.640185': 'ERS000023',
               '1.SKB3.640195': 'ERS000024',
               '1.SKB6.640176': 'ERS000025',
               '1.SKM1.640183': 'ERS000025'}
        self.assertEqual(obs, exp)

        obs = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study).ebi_sample_accessions
        exp = {"%s.Sample1" % self.new_study.id: None,
               "%s.Sample2" % self.new_study.id: None,
               "%s.Sample3" % self.new_study.id: None}
        self.assertEqual(obs, exp)

    def test_ebi_sample_accessions_setter(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.tester.ebi_sample_accessions = {'1.SKB8.640193': 'ERS000010',
                                                 '1.SKD8.640184': 'ERS000001'}

        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        exp_acc = {"%s.Sample1" % self.new_study.id: 'ERS000100',
                   "%s.Sample2" % self.new_study.id: 'ERS000110'}
        st.ebi_sample_accessions = exp_acc
        exp_acc["%s.Sample3" % self.new_study.id] = None
        self.assertEqual(st.ebi_sample_accessions, exp_acc)
        exp_acc["%s.Sample3" % self.new_study.id] = 'ERS0000120'
        st.ebi_sample_accessions = exp_acc
        self.assertEqual(st.ebi_sample_accessions, exp_acc)

        # We need to wrap the assignment in a function so we can use
        # npt.assert_warns
        def f():
            st.ebi_sample_accessions = exp_acc
        npt.assert_warns(qdb.exceptions.QiitaDBWarning, f)

    def test_biosample_accessions(self):
        obs = self.tester.biosample_accessions
        exp = {'1.SKB8.640193': 'SAMEA0000000',
               '1.SKD8.640184': 'SAMEA0000001',
               '1.SKB7.640196': 'SAMEA0000002',
               '1.SKM9.640192': 'SAMEA0000003',
               '1.SKM4.640180': 'SAMEA0000004',
               '1.SKM5.640177': 'SAMEA0000005',
               '1.SKB5.640181': 'SAMEA0000006',
               '1.SKD6.640190': 'SAMEA0000007',
               '1.SKB2.640194': 'SAMEA0000008',
               '1.SKD2.640178': 'SAMEA0000009',
               '1.SKM7.640188': 'SAMEA0000010',
               '1.SKB1.640202': 'SAMEA0000011',
               '1.SKD1.640179': 'SAMEA0000012',
               '1.SKD3.640198': 'SAMEA0000013',
               '1.SKM8.640201': 'SAMEA0000014',
               '1.SKM2.640199': 'SAMEA0000015',
               '1.SKB9.640200': 'SAMEA0000016',
               '1.SKD5.640186': 'SAMEA0000017',
               '1.SKM3.640197': 'SAMEA0000018',
               '1.SKD9.640182': 'SAMEA0000019',
               '1.SKB4.640189': 'SAMEA0000020',
               '1.SKD7.640191': 'SAMEA0000021',
               '1.SKM6.640187': 'SAMEA0000022',
               '1.SKD4.640185': 'SAMEA0000023',
               '1.SKB3.640195': 'SAMEA0000024',
               '1.SKB6.640176': 'SAMEA0000025',
               '1.SKM1.640183': 'SAMEA0000026'}
        self.assertEqual(obs, exp)

        obs = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study).biosample_accessions
        exp = {"%s.Sample1" % self.new_study.id: None,
               "%s.Sample2" % self.new_study.id: None,
               "%s.Sample3" % self.new_study.id: None}
        self.assertEqual(obs, exp)

    def test_biosample_accessions_setter(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.tester.biosample_accessions = {'1.SKB8.640193': 'SAMEA110000',
                                                '1.SKD8.640184': 'SAMEA110000'}

        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            self.metadata, self.new_study)
        exp_acc = {"%s.Sample1" % self.new_study.id: 'SAMEA110000',
                   "%s.Sample2" % self.new_study.id: 'SAMEA120000'}
        st.biosample_accessions = exp_acc
        exp_acc["%s.Sample3" % self.new_study.id] = None
        self.assertEqual(st.biosample_accessions, exp_acc)
        exp_acc["%s.Sample3" % self.new_study.id] = 'SAMEA130000'
        st.biosample_accessions = exp_acc
        self.assertEqual(st.biosample_accessions, exp_acc)

        # We need to wrap the assignment in a function so we can use
        # npt.assert_warns
        def f():
            st.biosample_accessions = exp_acc
        npt.assert_warns(qdb.exceptions.QiitaDBWarning, f)

    def test_validate_template_warning_missing(self):
        """Warns if the template is missing a required column"""
        metadata_dict = {
            'Sample1': {'physical_specimen_location': 'location1',
                        'physical_specimen_remaining': 'true',
                        'dna_extracted': 'true',
                        'sample_type': 'type1',
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 1',
                        'latitude': '42.42',
                        'longitude': '41.41'}
            }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        ST = qdb.metadata_template.sample_template.SampleTemplate
        obs = ST._clean_validate_template(metadata, 2)
        metadata_dict = {
            '2.Sample1': {'physical_specimen_location': 'location1',
                          'physical_specimen_remaining': 'true',
                          'dna_extracted': 'true',
                          'sample_type': 'type1',
                          'host_subject_id': 'NotIdentified',
                          'description': 'Test Sample 1',
                          'latitude': '42.42',
                          'longitude': '41.41'}
            }
        exp = pd.DataFrame.from_dict(metadata_dict, orient='index', dtype=str)
        obs.sort_index(axis=0, inplace=True)
        obs.sort_index(axis=1, inplace=True)
        exp.sort_index(axis=0, inplace=True)
        exp.sort_index(axis=1, inplace=True)
        assert_frame_equal(obs, exp)

    def test_validate_template_warning_missing_restrictions(self):
        del self.metadata['collection_timestamp']
        st = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.sample_template.SampleTemplate.create,
            self.metadata, self.new_study)
        obs = st.check_restrictions(
            [qdb.metadata_template.constants.SAMPLE_TEMPLATE_COLUMNS['EBI']])
        self.assertEqual(obs, {'collection_timestamp'})

    def test_validate_errors(self):
        self.metadata.set_value('Sample1', 'collection_timestamp',
                                'wrong date')
        self.metadata.set_value('Sample2', 'latitude', 'wrong latitude')

        with catch_warnings(record=True) as warn:
            # warnings.simplefilter("always")
            qdb.metadata_template.sample_template.SampleTemplate.create(
                self.metadata, self.new_study)

            # it should only return one warning
            self.assertEqual(len(warn), 1)
            warn = warn[0]
            # it should be QiitaDBWarning
            self.assertEqual(warn.category, qdb.exceptions.QiitaDBWarning)
            # it should contain this text
            message = str(warn.message)
            self.assertIn('2.Sample2, wrong value "wrong latitude"', message)
            self.assertIn('2.Sample1, wrong value "wrong date"', message)


EXP_SAMPLE_TEMPLATE = (
    "sample_name\tcollection_timestamp\tdescription\tdna_extracted\t"
    "host_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_specimen_location\tphysical_specimen_remaining\tsample_type\t"
    "scientific_name\tstr_column\ttaxon_id\n"
    "2.Sample1\t05/29/14 12:24:15\tTest Sample 1\ttrue\tNotIdentified\t1\t"
    "42.42\t41.41\tlocation1\ttrue\ttype1\thomo sapiens\tValue for sample 1\t"
    "9606\n"
    "2.Sample2\t05/29/14 12:24:15\tTest Sample 2\ttrue\tNotIdentified\t2\t"
    "4.2\t1.1\tlocation1\ttrue\ttype1\thomo sapiens\tValue for sample 2\t"
    "9606\n"
    "2.Sample3\t05/29/14 12:24:15\tTest Sample 3\ttrue\tNotIdentified\t3\t"
    "4.8\t4.41\tlocation1\ttrue\ttype1\thomo sapiens\tValue for sample 3\t"
    "9606\n")

EXP_SAMPLE_TEMPLATE_FEWER_SAMPLES = (
    "sample_name\tcollection_timestamp\tdescription\tdna_extracted\t"
    "host_subject_id\tint_column\tlatitude\tlongitude\t"
    "physical_specimen_location\tphysical_specimen_remaining\tsample_type\t"
    "scientific_name\tstr_column\ttaxon_id\n"
    "2.Sample1\t05/29/14 12:24:15\tTest Sample 1\ttrue\tNotIdentified\t1\t"
    "42.42\t41.41\tlocation1\ttrue\ttype1\thomo sapiens\tValue for sample 1\t"
    "9606\n"
    "2.Sample3\t05/29/14 12:24:15\tTest Sample 3\ttrue\tNotIdentified\t3\t"
    "4.8\t4.41\tlocation1\ttrue\ttype1\thomo sapiens\tValue for sample 3\t"
    "9606\n")


if __name__ == '__main__':
    main()
