# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from future.builtins import zip
from six import StringIO
from unittest import TestCase, main
from datetime import datetime
from tempfile import mkstemp
from time import strftime
from os import close, remove
from os.path import join, basename
from collections import Iterable

import pandas as pd
from pandas.util.testing import assert_frame_equal

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import (QiitaDBDuplicateError, QiitaDBUnknownIDError,
                                 QiitaDBNotImplementedError,
                                 QiitaDBDuplicateHeaderError,
                                 QiitaDBExecutionError,
                                 QiitaDBColumnError, QiitaDBError)
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.data import RawData
from qiita_db.util import exists_table, get_db_files_base_dir, get_mountpoint
from qiita_db.metadata_template import (
    _get_datatypes, _as_python_types, MetadataTemplate, SampleTemplate,
    PrepTemplate, BaseSample, PrepSample, Sample, _prefix_sample_names_with_id,
    load_template_to_dataframe)


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

    def test_prefix_sample_names_with_id(self):
        exp_metadata_dict = {
            '1.Sample1': {'int_col': 1, 'float_col': 2.1, 'str_col': 'str1'},
            '1.Sample2': {'int_col': 2, 'float_col': 3.1, 'str_col': '200'},
            '1.Sample3': {'int_col': 3, 'float_col': 3, 'str_col': 'string30'},
        }
        exp_df = pd.DataFrame.from_dict(exp_metadata_dict, orient='index')
        _prefix_sample_names_with_id(self.metadata_map, Study(1))
        self.metadata_map.sort_index(inplace=True)
        exp_df.sort_index(inplace=True)
        assert_frame_equal(self.metadata_map, exp_df)


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


@qiita_test_checker()
class TestSample(TestCase):
    """Tests the Sample class"""

    def setUp(self):
        self.sample_template = SampleTemplate(1)
        self.sample_id = '1.SKB8.640193'
        self.tester = Sample(self.sample_id, self.sample_template)
        self.exp_categories = {'physical_location', 'has_physical_specimen',
                               'has_extracted_data', 'sample_type',
                               'required_sample_info_status',
                               'collection_timestamp', 'host_subject_id',
                               'description', 'season_environment',
                               'assigned_from_geo', 'texture', 'taxon_id',
                               'depth', 'host_taxid', 'common_name',
                               'water_content_soil', 'elevation', 'temp',
                               'tot_nitro', 'samp_salinity', 'altitude',
                               'env_biome', 'country', 'ph', 'anonymized_name',
                               'tot_org_carb', 'description_duplicate',
                               'env_feature', 'latitude', 'longitude'}

    def test_init_unknown_error(self):
        """Init raises an error if the sample id is not found in the template
        """
        with self.assertRaises(QiitaDBUnknownIDError):
            Sample('Not_a_Sample', self.sample_template)

    def test_init_wrong_template(self):
        """Raises an error if using a PrepTemplate instead of SampleTemplate"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            Sample('SKB8.640193', PrepTemplate(1))

    def test_init(self):
        """Init correctly initializes the sample object"""
        sample = Sample(self.sample_id, self.sample_template)
        # Check that the internal id have been correctly set
        self.assertEqual(sample._id, '1.SKB8.640193')
        # Check that the internal template have been correctly set
        self.assertEqual(sample._md_template, self.sample_template)
        # Check that the internal dynamic table name have been correctly set
        self.assertEqual(sample._dynamic_table, "sample_1")

    def test_eq_true(self):
        """Equality correctly returns true"""
        other = Sample(self.sample_id, self.sample_template)
        self.assertTrue(self.tester == other)

    def test_eq_false_type(self):
        """Equality returns false if types are not equal"""
        other = PrepSample(self.sample_id, PrepTemplate(1))
        self.assertFalse(self.tester == other)

    def test_eq_false_id(self):
        """Equality returns false if ids are different"""
        other = Sample('1.SKD8.640184', self.sample_template)
        self.assertFalse(self.tester == other)

    def test_exists_true(self):
        """Exists returns true if the sample exists"""
        self.assertTrue(Sample.exists(self.sample_id, self.sample_template))

    def test_exists_false(self):
        """Exists returns false if the sample does not exists"""
        self.assertFalse(Sample.exists('Not_a_Sample', self.sample_template))

    def test_get_categories(self):
        """Correctly returns the set of category headers"""
        obs = self.tester._get_categories(self.conn_handler)
        self.assertEqual(obs, self.exp_categories)

    def test_len(self):
        """Len returns the correct number of categories"""
        self.assertEqual(len(self.tester), 30)

    def test_getitem_required(self):
        """Get item returns the correct metadata value from the required table
        """
        self.assertEqual(self.tester['physical_location'], 'ANL')
        self.assertEqual(self.tester['collection_timestamp'],
                         datetime(2011, 11, 11, 13, 00, 00))
        self.assertTrue(self.tester['has_physical_specimen'])

    def test_getitem_dynamic(self):
        """Get item returns the correct metadata value from the dynamic table
        """
        self.assertEqual(self.tester['SEASON_ENVIRONMENT'], 'winter')
        self.assertEqual(self.tester['depth'], 0.15)

    def test_getitem_id_column(self):
        """Get item returns the correct metadata value from the changed column
        """
        self.assertEqual(self.tester['required_sample_info_status'],
                         'completed')

    def test_getitem_error(self):
        """Get item raises an error if category does not exists"""
        with self.assertRaises(KeyError):
            self.tester['Not_a_Category']

    def test_setitem(self):
        """setitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            self.tester['DEPTH'] = 0.30

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            del self.tester['DEPTH']

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
        exp = {'ANL', True, True, 'ENVO:soil', 'completed',
               datetime(2011, 11, 11, 13, 00, 00), '1001:M7',
               'Cannabis Soil Microbiome', 'winter', 'n',
               '64.6 sand, 17.6 silt, 17.8 clay', '1118232', 0.15, '3483',
               'root metagenome', 0.164, 114, 15, 1.41, 7.15, 0,
               'ENVO:Temperate grasslands, savannas, and shrubland biome',
               'GAZ:United States of America', 6.94, 'SKB8', 5,
               'Burmese root', 'ENVO:plant-associated habitat', 74.0894932572,
               65.3283470202}
        self.assertEqual(set(obs), exp)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = {('physical_location', 'ANL'), ('has_physical_specimen', True),
               ('has_extracted_data', True), ('sample_type', 'ENVO:soil'),
               ('required_sample_info_status', 'completed'),
               ('collection_timestamp', datetime(2011, 11, 11, 13, 00, 00)),
               ('host_subject_id', '1001:M7'),
               ('description', 'Cannabis Soil Microbiome'),
               ('season_environment', 'winter'), ('assigned_from_geo', 'n'),
               ('texture', '64.6 sand, 17.6 silt, 17.8 clay'),
               ('taxon_id', '1118232'), ('depth', 0.15),
               ('host_taxid', '3483'), ('common_name', 'root metagenome'),
               ('water_content_soil', 0.164), ('elevation', 114), ('temp', 15),
               ('tot_nitro', 1.41), ('samp_salinity', 7.15), ('altitude', 0),
               ('env_biome',
                'ENVO:Temperate grasslands, savannas, and shrubland biome'),
               ('country', 'GAZ:United States of America'), ('ph', 6.94),
               ('anonymized_name', 'SKB8'), ('tot_org_carb', 5),
               ('description_duplicate', 'Burmese root'),
               ('env_feature', 'ENVO:plant-associated habitat'),
               ('latitude', 74.0894932572),
               ('longitude', 65.3283470202)}
        self.assertEqual(set(obs), exp)

    def test_get(self):
        """get returns the correct sample object"""
        self.assertEqual(self.tester.get('SEASON_ENVIRONMENT'), 'winter')
        self.assertEqual(self.tester.get('depth'), 0.15)

    def test_get_none(self):
        """get returns none if the sample id is not present"""
        self.assertTrue(self.tester.get('Not_a_Category') is None)


@qiita_test_checker()
class TestPrepSample(TestCase):
    """Tests the PrepSample class"""

    def setUp(self):
        self.prep_template = PrepTemplate(1)
        self.sample_id = '1.SKB8.640193'
        self.tester = PrepSample(self.sample_id, self.prep_template)
        self.exp_categories = {'center_name', 'center_project_name',
                               'emp_status', 'barcodesequence',
                               'library_construction_protocol',
                               'linkerprimersequence', 'target_subfragment',
                               'target_gene', 'run_center', 'run_prefix',
                               'run_date', 'experiment_center',
                               'experiment_design_description',
                               'experiment_title', 'platform', 'samp_size',
                               'sequencing_meth', 'illumina_technology',
                               'sample_center', 'pcr_primers', 'study_center'}

    def test_init_unknown_error(self):
        """Init errors if the PrepSample id is not found in the template"""
        with self.assertRaises(QiitaDBUnknownIDError):
            PrepSample('Not_a_Sample', self.prep_template)

    def test_init_wrong_template(self):
        """Raises an error if using a SampleTemplate instead of PrepTemplate"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PrepSample('1.SKB8.640193', SampleTemplate(1))

    def test_init(self):
        """Init correctly initializes the PrepSample object"""
        sample = PrepSample(self.sample_id, self.prep_template)
        # Check that the internal id have been correctly set
        self.assertEqual(sample._id, '1.SKB8.640193')
        # Check that the internal template have been correctly set
        self.assertEqual(sample._md_template, self.prep_template)
        # Check that the internal dynamic table name have been correctly set
        self.assertEqual(sample._dynamic_table, "prep_1")

    def test_eq_true(self):
        """Equality correctly returns true"""
        other = PrepSample(self.sample_id, self.prep_template)
        self.assertTrue(self.tester == other)

    def test_eq_false_type(self):
        """Equality returns false if types are not equal"""
        other = Sample(self.sample_id, SampleTemplate(1))
        self.assertFalse(self.tester == other)

    def test_eq_false_id(self):
        """Equality returns false if ids are different"""
        other = PrepSample('1.SKD8.640184', self.prep_template)
        self.assertFalse(self.tester == other)

    def test_exists_true(self):
        """Exists returns true if the PrepSample exists"""
        self.assertTrue(PrepSample.exists(self.sample_id, self.prep_template))

    def test_exists_false(self):
        """Exists returns false if the PrepSample does not exists"""
        self.assertFalse(PrepSample.exists('Not_a_Sample', self.prep_template))

    def test_get_categories(self):
        """Correctly returns the set of category headers"""
        obs = self.tester._get_categories(self.conn_handler)
        self.assertEqual(obs, self.exp_categories)

    def test_len(self):
        """Len returns the correct number of categories"""
        self.assertEqual(len(self.tester), 21)

    def test_getitem_required(self):
        """Get item returns the correct metadata value from the required table
        """
        self.assertEqual(self.tester['center_name'], 'ANL')
        self.assertTrue(self.tester['center_project_name'] is None)

    def test_getitem_dynamic(self):
        """Get item returns the correct metadata value from the dynamic table
        """
        self.assertEqual(self.tester['pcr_primers'],
                         'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT')
        self.assertEqual(self.tester['barcodesequence'], 'AGCGCTCACATC')

    def test_getitem_id_column(self):
        """Get item returns the correct metadata value from the changed column
        """
        self.assertEqual(self.tester['emp_status'], 'EMP')

    def test_getitem_error(self):
        """Get item raises an error if category does not exists"""
        with self.assertRaises(KeyError):
            self.tester['Not_a_Category']

    def test_setitem(self):
        """setitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            self.tester['barcodesequence'] = 'GTCCGCAAGTTA'

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            del self.tester['pcr_primers']

    def test_iter(self):
        """iter returns an iterator over the category headers"""
        obs = self.tester.__iter__()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_categories)

    def test_contains_true(self):
        """contains returns true if the category header exists"""
        self.assertTrue('BarcodeSequence' in self.tester)
        self.assertTrue('barcodesequence' in self.tester)

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
        exp = {'ANL', None, None, None, 'EMP', 'AGCGCTCACATC',
               'This analysis was done as in Caporaso et al 2011 Genome '
               'research. The PCR primers (F515/R806) were developed against '
               'the V4 region of the 16S rRNA (both bacteria and archaea), '
               'which we determined would yield optimal community clustering '
               'with reads of this length using a procedure similar to that of'
               ' ref. 15. [For reference, this primer pair amplifies the '
               'region 533_786 in the Escherichia coli strain 83972 sequence '
               '(greengenes accession no. prokMSA_id:470367).] The reverse PCR'
               ' primer is barcoded with a 12-base error-correcting Golay code'
               ' to facilitate multiplexing of up to 1,500 samples per lane, '
               'and both PCR primers contain sequencer adapter regions.',
               'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL',
               's_G1_L001_sequences', '8/1/12', 'ANL',
               'micro biome of soil and rhizosphere of cannabis plants from '
               'CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g',
               'Sequencing by synthesis', 'MiSeq', 'ANL',
               'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'}
        self.assertEqual(set(obs), exp)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = {('center_name', 'ANL'), ('center_project_name', None),
               ('emp_status', 'EMP'), ('barcodesequence', 'AGCGCTCACATC'),
               ('library_construction_protocol',
                'This analysis was done as in Caporaso et al 2011 Genome '
                'research. The PCR primers (F515/R806) were developed against '
                'the V4 region of the 16S rRNA (both bacteria and archaea), '
                'which we determined would yield optimal community clustering '
                'with reads of this length using a procedure similar to that '
                'of ref. 15. [For reference, this primer pair amplifies the '
                'region 533_786 in the Escherichia coli strain 83972 sequence '
                '(greengenes accession no. prokMSA_id:470367).] The reverse '
                'PCR primer is barcoded with a 12-base error-correcting Golay '
                'code to facilitate multiplexing of up to 1,500 samples per '
                'lane, and both PCR primers contain sequencer adapter '
                'regions.'), ('linkerprimersequence', 'GTGCCAGCMGCCGCGGTAA'),
               ('target_subfragment', 'V4'), ('target_gene', '16S rRNA'),
               ('run_center', 'ANL'), ('run_prefix', 's_G1_L001_sequences'),
               ('run_date', '8/1/12'), ('experiment_center', 'ANL'),
               ('experiment_design_description',
                'micro biome of soil and rhizosphere of cannabis plants '
                'from CA'), ('experiment_title', 'Cannabis Soil Microbiome'),
               ('platform', 'Illumina'), ('samp_size', '.25,g'),
               ('sequencing_meth', 'Sequencing by synthesis'),
               ('illumina_technology', 'MiSeq'), ('sample_center', 'ANL'),
               ('pcr_primers',
                'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT'),
               ('study_center', 'CCME')}
        self.assertEqual(set(obs), exp)

    def test_get(self):
        """get returns the correct sample object"""
        self.assertEqual(self.tester.get('barcodesequence'), 'AGCGCTCACATC')

    def test_get_none(self):
        """get returns none if the sample id is not present"""
        self.assertTrue(self.tester.get('Not_a_Category') is None)


@qiita_test_checker()
class TestMetadataTemplate(TestCase):
    """Tests the MetadataTemplate base class"""
    def setUp(self):
        self.study = Study(1)

    def test_init(self):
        """Init raises an error because it's not called from a subclass"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MetadataTemplate(1)

    def test_create(self):
        """Create raises an error because it's not called from a subclass"""
        with self.assertRaises(QiitaDBNotImplementedError):
            MetadataTemplate.create()

    def test_exist(self):
        """Exists raises an error because it's not called from a subclass"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MetadataTemplate.exists(self.study)

    def test_table_name(self):
        """table name raises an error because it's not called from a subclass
        """
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MetadataTemplate._table_name(self.study)


@qiita_test_checker()
class TestSampleTemplate(TestCase):
    """Tests the SampleTemplate class"""

    def setUp(self):
        metadata_dict = {
            'Sample1': {'physical_location': 'location1',
                        'has_physical_specimen': True,
                        'has_extracted_data': True,
                        'sample_type': 'type1',
                        'required_sample_info_status': 'received',
                        'collection_timestamp':
                        datetime(2014, 5, 29, 12, 24, 51),
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 1',
                        'str_column': 'Value for sample 1',
                        'latitude': 42.42,
                        'longitude': 41.41},
            'Sample2': {'physical_location': 'location1',
                        'has_physical_specimen': True,
                        'has_extracted_data': True,
                        'sample_type': 'type1',
                        'required_sample_info_status': 'received',
                        'collection_timestamp':
                        datetime(2014, 5, 29, 12, 24, 51),
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 2',
                        'str_column': 'Value for sample 2',
                        'latitude': 4.2,
                        'longitude': 1.1},
            'Sample3': {'physical_location': 'location1',
                        'has_physical_specimen': True,
                        'has_extracted_data': True,
                        'sample_type': 'type1',
                        'required_sample_info_status': 'received',
                        'collection_timestamp':
                        datetime(2014, 5, 29, 12, 24, 51),
                        'host_subject_id': 'NotIdentified',
                        'Description': 'Test Sample 3',
                        'str_column': 'Value for sample 3',
                        'latitude': 4.8,
                        'longitude': 4.41},
            }
        self.metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')

        self.test_study = Study(1)
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "portal_type_id": 3,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "emp_person_id": StudyPerson(2),
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }
        self.new_study = Study.create(User('test@foo.bar'),
                                      "Fried Chicken Microbiome", [1], info)
        self.tester = SampleTemplate(1)
        self.exp_sample_ids = {
            '1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195', '1.SKB4.640189',
            '1.SKB5.640181', '1.SKB6.640176', '1.SKB7.640196', '1.SKB8.640193',
            '1.SKB9.640200', '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
            '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190', '1.SKD7.640191',
            '1.SKD8.640184', '1.SKD9.640182', '1.SKM1.640183', '1.SKM2.640199',
            '1.SKM3.640197', '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
            '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192'}
        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_study_id(self):
        """Ensure that the correct study ID is returned"""
        self.assertEqual(self.tester.study_id, 1)

    def test_init_unknown_error(self):
        """Init raises an error if the id is not known"""
        with self.assertRaises(QiitaDBUnknownIDError):
            SampleTemplate(2)

    def test_init(self):
        """Init successfully instantiates the object"""
        st = SampleTemplate(1)
        self.assertTrue(st.id, 1)

    def test_table_name(self):
        """Table name return the correct string"""
        obs = SampleTemplate._table_name(self.test_study.id)
        self.assertEqual(obs, "sample_1")

    def test_create_duplicate(self):
        """Create raises an error when creating a duplicated SampleTemplate"""
        with self.assertRaises(QiitaDBDuplicateError):
            SampleTemplate.create(self.metadata, self.test_study)

    def test_create_duplicate_header(self):
        """Create raises an error when duplicate headers are present"""
        self.metadata['STR_COLUMN'] = pd.Series(['', '', ''],
                                                index=self.metadata.index)
        with self.assertRaises(QiitaDBDuplicateHeaderError):
            SampleTemplate.create(self.metadata, self.new_study)

    def test_create(self):
        """Creates a new SampleTemplate"""
        st = SampleTemplate.create(self.metadata, self.new_study)
        # The returned object has the correct id
        self.assertEqual(st.id, 2)

        # The relevant rows to required_sample_info have been added.
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.required_sample_info WHERE study_id=2")
        # sample_id study_id physical_location has_physical_specimen
        # has_extracted_data sample_type required_sample_info_status_id
        # collection_timestamp host_subject_id description
        exp = [["2.Sample1", 2, "location1", True, True, "type1", 1,
                datetime(2014, 5, 29, 12, 24, 51), "NotIdentified",
                "Test Sample 1", 42.42, 41.41],
               ["2.Sample2", 2, "location1", True, True, "type1", 1,
                datetime(2014, 5, 29, 12, 24, 51), "NotIdentified",
                "Test Sample 2", 4.2, 1.1],
               ["2.Sample3", 2, "location1", True, True, "type1", 1,
                datetime(2014, 5, 29, 12, 24, 51), "NotIdentified",
                "Test Sample 3", 4.8, 4.41]]
        self.assertEqual(obs, exp)

        # The relevant rows have been added to the study_sample_columns
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_sample_columns WHERE study_id=2")
        # study_id, column_name, column_type
        exp = [[2, "str_column", "varchar"]]
        self.assertEqual(obs, exp)

        # The new table exists
        self.assertTrue(exists_table("sample_2", self.conn_handler))

        # The new table hosts the correct values
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.sample_2")
        # sample_id, str_column
        exp = [['2.Sample1', "Value for sample 1"],
               ['2.Sample2', "Value for sample 2"],
               ['2.Sample3', "Value for sample 3"]]
        self.assertEqual(obs, exp)

    def test_delete(self):
        """Deletes Sample template 1"""
        SampleTemplate.create(self.metadata, self.new_study)
        SampleTemplate.delete(2)
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.required_sample_info WHERE study_id=2")
        exp = []
        self.assertEqual(obs, exp)
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_sample_columns WHERE study_id=2")
        exp = []
        self.assertEqual(obs, exp)
        with self.assertRaises(QiitaDBExecutionError):
            self.conn_handler.execute_fetchall(
                "SELECT * FROM qiita.sample_2")

    def test_delete_unkonwn_id_error(self):
        """Try to delete a non existent prep template"""
        with self.assertRaises(QiitaDBUnknownIDError):
            SampleTemplate.delete(5)

    def test_exists_true(self):
        """Exists returns true when the SampleTemplate already exists"""
        self.assertTrue(SampleTemplate.exists(self.test_study.id))

    def test_exists_false(self):
        """Exists returns false when the SampleTemplate does not exists"""
        self.assertFalse(SampleTemplate.exists(self.new_study.id))

    def test_get_sample_ids(self):
        """get_sample_ids returns the correct set of sample ids"""
        obs = self.tester._get_sample_ids(self.conn_handler)
        self.assertEqual(obs, self.exp_sample_ids)

    def test_len(self):
        """Len returns the correct number of sample ids"""
        self.assertEqual(len(self.tester), 27)

    def test_getitem(self):
        """Get item returns the correct sample object"""
        obs = self.tester['1.SKM7.640188']
        exp = Sample('1.SKM7.640188', self.tester)
        self.assertEqual(obs, exp)

    def test_getitem_error(self):
        """Get item raises an error if key does not exists"""
        with self.assertRaises(KeyError):
            self.tester['Not_a_Sample']

    def test_setitem(self):
        """setitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            self.tester['1.SKM7.640188'] = Sample('1.SKM7.640188', self.tester)

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            del self.tester['1.SKM7.640188']

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
        exp = {Sample('1.SKB1.640202', self.tester),
               Sample('1.SKB2.640194', self.tester),
               Sample('1.SKB3.640195', self.tester),
               Sample('1.SKB4.640189', self.tester),
               Sample('1.SKB5.640181', self.tester),
               Sample('1.SKB6.640176', self.tester),
               Sample('1.SKB7.640196', self.tester),
               Sample('1.SKB8.640193', self.tester),
               Sample('1.SKB9.640200', self.tester),
               Sample('1.SKD1.640179', self.tester),
               Sample('1.SKD2.640178', self.tester),
               Sample('1.SKD3.640198', self.tester),
               Sample('1.SKD4.640185', self.tester),
               Sample('1.SKD5.640186', self.tester),
               Sample('1.SKD6.640190', self.tester),
               Sample('1.SKD7.640191', self.tester),
               Sample('1.SKD8.640184', self.tester),
               Sample('1.SKD9.640182', self.tester),
               Sample('1.SKM1.640183', self.tester),
               Sample('1.SKM2.640199', self.tester),
               Sample('1.SKM3.640197', self.tester),
               Sample('1.SKM4.640180', self.tester),
               Sample('1.SKM5.640177', self.tester),
               Sample('1.SKM6.640187', self.tester),
               Sample('1.SKM7.640188', self.tester),
               Sample('1.SKM8.640201', self.tester),
               Sample('1.SKM9.640192', self.tester)}
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs), key=lambda x: x.id),
                        sorted(exp, key=lambda x: x.id)):
            self.assertEqual(o, e)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = [('1.SKB1.640202', Sample('1.SKB1.640202', self.tester)),
               ('1.SKB2.640194', Sample('1.SKB2.640194', self.tester)),
               ('1.SKB3.640195', Sample('1.SKB3.640195', self.tester)),
               ('1.SKB4.640189', Sample('1.SKB4.640189', self.tester)),
               ('1.SKB5.640181', Sample('1.SKB5.640181', self.tester)),
               ('1.SKB6.640176', Sample('1.SKB6.640176', self.tester)),
               ('1.SKB7.640196', Sample('1.SKB7.640196', self.tester)),
               ('1.SKB8.640193', Sample('1.SKB8.640193', self.tester)),
               ('1.SKB9.640200', Sample('1.SKB9.640200', self.tester)),
               ('1.SKD1.640179', Sample('1.SKD1.640179', self.tester)),
               ('1.SKD2.640178', Sample('1.SKD2.640178', self.tester)),
               ('1.SKD3.640198', Sample('1.SKD3.640198', self.tester)),
               ('1.SKD4.640185', Sample('1.SKD4.640185', self.tester)),
               ('1.SKD5.640186', Sample('1.SKD5.640186', self.tester)),
               ('1.SKD6.640190', Sample('1.SKD6.640190', self.tester)),
               ('1.SKD7.640191', Sample('1.SKD7.640191', self.tester)),
               ('1.SKD8.640184', Sample('1.SKD8.640184', self.tester)),
               ('1.SKD9.640182', Sample('1.SKD9.640182', self.tester)),
               ('1.SKM1.640183', Sample('1.SKM1.640183', self.tester)),
               ('1.SKM2.640199', Sample('1.SKM2.640199', self.tester)),
               ('1.SKM3.640197', Sample('1.SKM3.640197', self.tester)),
               ('1.SKM4.640180', Sample('1.SKM4.640180', self.tester)),
               ('1.SKM5.640177', Sample('1.SKM5.640177', self.tester)),
               ('1.SKM6.640187', Sample('1.SKM6.640187', self.tester)),
               ('1.SKM7.640188', Sample('1.SKM7.640188', self.tester)),
               ('1.SKM8.640201', Sample('1.SKM8.640201', self.tester)),
               ('1.SKM9.640192', Sample('1.SKM9.640192', self.tester))]
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs)), sorted(exp)):
            self.assertEqual(o, e)

    def test_get(self):
        """get returns the correct sample object"""
        obs = self.tester.get('1.SKM7.640188')
        exp = Sample('1.SKM7.640188', self.tester)
        self.assertEqual(obs, exp)

    def test_get_none(self):
        """get returns none if the sample id is not present"""
        self.assertTrue(self.tester.get('Not_a_Sample') is None)

    def test_to_file(self):
        """to file writes a tab delimited file with all the metadata"""
        fd, fp = mkstemp()
        close(fd)
        st = SampleTemplate.create(self.metadata, self.new_study)
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
        exp = 17
        st = SampleTemplate.create(self.metadata, self.new_study)
        self.assertEqual(st.get_filepaths()[0][0], exp)

        # testing current functionaly, to add a new sample template
        # you need to erase it first
        SampleTemplate.delete(st.id)
        exp = 18
        st = SampleTemplate.create(self.metadata, self.new_study)
        self.assertEqual(st.get_filepaths()[0][0], exp)


@qiita_test_checker()
class TestPrepTemplate(TestCase):
    """Tests the PrepTemplate class"""

    def setUp(self):
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 1',
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'},
            'SKD8.640184': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 2',
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'CGTAGAGCTCTC',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'},
            'SKB7.640196': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 3',
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'CCTCTGAGAGCT',
                            'run_prefix': "s_G1_L002_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}
            }
        self.metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        self.test_raw_data = RawData(1)
        self.test_study = Study(1)
        self.data_type = "18S"
        self.data_type_id = 2

        fd, seqs_fp = mkstemp(suffix='_seqs.fastq')
        close(fd)
        fd, barcodes_fp = mkstemp(suffix='_barcodes.fastq')
        close(fd)
        filepaths = [(seqs_fp, 1), (barcodes_fp, 2)]
        with open(seqs_fp, "w") as f:
            f.write("\n")
        with open(barcodes_fp, "w") as f:
            f.write("\n")
        self.new_raw_data = RawData.create(2, [Study(1)], filepaths=filepaths)
        db_test_raw_dir = join(get_db_files_base_dir(), 'raw_data')
        db_seqs_fp = join(db_test_raw_dir, "3_%s" % basename(seqs_fp))
        db_barcodes_fp = join(db_test_raw_dir, "3_%s" % basename(barcodes_fp))
        self._clean_up_files = [db_seqs_fp, db_barcodes_fp]

        self.tester = PrepTemplate(1)
        self.exp_sample_ids = {
            '1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195', '1.SKB4.640189',
            '1.SKB5.640181', '1.SKB6.640176', '1.SKB7.640196', '1.SKB8.640193',
            '1.SKB9.640200', '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
            '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190', '1.SKD7.640191',
            '1.SKD8.640184', '1.SKD9.640182', '1.SKM1.640183', '1.SKM2.640199',
            '1.SKM3.640197', '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
            '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192'}

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_study_id(self):
        """Ensure that the correct study ID is returned"""
        self.assertEqual(self.tester.study_id, 1)

    def test_init_unknown_error(self):
        """Init raises an error if the id is not known"""
        with self.assertRaises(QiitaDBUnknownIDError):
            PrepTemplate(2)

    def test_init(self):
        """Init successfully instantiates the object"""
        st = PrepTemplate(1)
        self.assertTrue(st.id, 1)

    def test_table_name(self):
        """Table name return the correct string"""
        obs = PrepTemplate._table_name(1)
        self.assertEqual(obs, "prep_1")

    def test_create_duplicate_header(self):
        """Create raises an error when duplicate headers are present"""
        self.metadata['STR_COLUMN'] = pd.Series(['', '', ''],
                                                index=self.metadata.index)
        with self.assertRaises(QiitaDBDuplicateHeaderError):
            PrepTemplate.create(self.metadata, self.new_raw_data,
                                self.test_study, self.data_type)

    def test_create(self):
        """Creates a new PrepTemplate"""
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type)
        # The returned object has the correct id
        self.assertEqual(pt.id, 2)

        # The row in the prep template table has been created
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_template WHERE prep_template_id=2")
        # prep_template_id, data_type_id, raw_data_id, preprocessing_status,
        # investigation_type
        self.assertEqual(obs, [[2, 2, 3, 'not_preprocessed', None]])

        # The relevant rows to common_prep_info have been added.
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.common_prep_info WHERE prep_template_id=2")
        # prep_template_id, sample_id, study_id, center_name,
        # center_project_name, emp_status_id
        exp = [[2, '1.SKB8.640193', 'ANL', 'Test Project', 1],
               [2, '1.SKD8.640184', 'ANL', 'Test Project', 1],
               [2, '1.SKB7.640196', 'ANL', 'Test Project', 1]]
        self.assertEqual(sorted(obs), sorted(exp))

        # The relevant rows have been added to the prep_columns table
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_columns WHERE prep_template_id=2")
        # prep_template_id, column_name, column_type
        exp = [[2, 'str_column', 'varchar'],
               [2, 'ebi_submission_accession', 'varchar'],
               [2, 'run_prefix', 'varchar'],
               [2, 'barcodesequence', 'varchar'],
               [2, 'linkerprimersequence', 'varchar'],
               [2, 'platform', 'varchar'],
               [2, 'experiment_design_description', 'varchar'],
               [2, 'library_construction_protocol', 'varchar']]
        self.assertEqual(sorted(obs), sorted(exp))

        # The new table exists
        self.assertTrue(exists_table("prep_2", self.conn_handler))

        # The new table hosts the correct values
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_2")
        # sample_id, study_id, str_column, ebi_submission_accession,
        # run_prefix, barcodesequence, linkerprimersequence
        exp = [['1.SKB7.640196', 'Value for sample 3', 'ILLUMINA',
                's_G1_L002_sequences', 'CCTCTGAGAGCT', None,
                'GTGCCAGCMGCCGCGGTAA', 'BBBB', 'AAAA'],
               ['1.SKB8.640193', 'Value for sample 1', 'ILLUMINA',
                's_G1_L001_sequences', 'GTCCGCAAGTTA', None,
                'GTGCCAGCMGCCGCGGTAA', 'BBBB', 'AAAA'],
               ['1.SKD8.640184', 'Value for sample 2', 'ILLUMINA',
                's_G1_L001_sequences', 'CGTAGAGCTCTC', None,
                'GTGCCAGCMGCCGCGGTAA', 'BBBB', 'AAAA']]
        self.assertEqual(sorted(obs), sorted(exp))

        # prep and qiime files have been created
        filepaths = pt.get_filepaths()
        self.assertEqual(len(filepaths), 2)
        self.assertEqual(filepaths[0][0], 20)
        self.assertEqual(filepaths[1][0], 19)

    def test_create_qiime_mapping_file(self):
        pt = PrepTemplate(1)

        # creating prep template file
        _id, fp = get_mountpoint('templates')[0]
        fpp = join(fp, '%d_prep_%d_%s.txt' % (pt.study_id, pt.id,
                   strftime("%Y%m%d-%H%M%S")))
        pt.to_file(fpp)
        pt.add_filepath(fpp)

        _, filepath = pt.get_filepaths()[0]
        obs_fp = pt.create_qiime_mapping_file(filepath)
        exp_fp = join(fp, '1_prep_1_qiime_19700101-000000.txt')

        with open(obs_fp, 'r') as obs_fh:
            obs = obs_fh.read()
        with open(exp_fp, 'r') as exp_fh:
            exp = exp_fh.read()

        self.assertEqual(obs, exp)

        # testing failure, first lest remove some lines of the prep template
        with open(filepath, 'r') as filepath_fh:
            data = filepath_fh.read().splitlines()
        with open(filepath, 'w') as filepath_fh:
            for i, d in enumerate(data):
                if i == 4:
                    # adding fake sample
                    line = d.split('\t')
                    line[0] = 'fake_sample'
                    line = '\t'.join(line)
                    filepath_fh.write(line + '\n')
                    break
                filepath_fh.write(d + '\n')

        with self.assertRaises(ValueError):
            pt.create_qiime_mapping_file(filepath)

    def test_create_data_type_id(self):
        """Creates a new PrepTemplate passing the data_type_id"""
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type_id)
        # The returned object has the correct id
        self.assertEqual(pt.id, 2)

        # The row in the prep template table have been created
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_template WHERE prep_template_id=2")
        # prep_template_id, data_type_id, raw_data_id, preprocessing_status,
        # investigation_type
        self.assertEqual(obs, [[2, 2, 3, 'not_preprocessed', None]])

        # The relevant rows to common_prep_info have been added.
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.common_prep_info WHERE prep_template_id=2")
        # prep_template_id, sample_id, center_name,
        # center_project_name, emp_status_id
        exp = [[2, '1.SKB8.640193', 'ANL', 'Test Project', 1],
               [2, '1.SKD8.640184', 'ANL', 'Test Project', 1],
               [2, '1.SKB7.640196', 'ANL', 'Test Project', 1]]
        self.assertEqual(sorted(obs), sorted(exp))

        # The relevant rows have been added to the prep_columns table
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_columns WHERE prep_template_id=2")
        # prep_template_id, column_name, column_type
        exp = [[2, 'str_column', 'varchar'],
               [2, 'ebi_submission_accession', 'varchar'],
               [2, 'run_prefix', 'varchar'],
               [2, 'barcodesequence', 'varchar'],
               [2, 'linkerprimersequence', 'varchar'],
               [2, 'platform', 'varchar'],
               [2, 'experiment_design_description', 'varchar'],
               [2, 'library_construction_protocol', 'varchar']]
        self.assertEqual(sorted(obs), sorted(exp))

        # The new table exists
        self.assertTrue(exists_table("prep_2", self.conn_handler))

        # The new table hosts the correct values
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_2")
        # sample_id, str_column, ebi_submission_accession,
        # run_prefix, barcodesequence, linkerprimersequence
        exp = [['1.SKB7.640196', 'Value for sample 3', 'ILLUMINA',
                's_G1_L002_sequences', 'CCTCTGAGAGCT', None,
                'GTGCCAGCMGCCGCGGTAA', 'BBBB', 'AAAA'],
               ['1.SKB8.640193', 'Value for sample 1', 'ILLUMINA',
                's_G1_L001_sequences', 'GTCCGCAAGTTA', None,
                'GTGCCAGCMGCCGCGGTAA', 'BBBB', 'AAAA'],
               ['1.SKD8.640184', 'Value for sample 2', 'ILLUMINA',
                's_G1_L001_sequences', 'CGTAGAGCTCTC', None,
                'GTGCCAGCMGCCGCGGTAA', 'BBBB', 'AAAA']]
        self.assertEqual(sorted(obs), sorted(exp))

    def test_create_error(self):
        """Create raises an error if any required columns are missing
        """
        metadata_dict = {
            '1.SKB8.640193': {'center_name': 'ANL',
                              'center_project_name': 'Test Project',
                              'ebi_submission_accession': None,
                              'EMP_status_id': 1,
                              'str_column': 'Value for sample 1'},
            '1.SKD8.640184': {'center_name': 'ANL',
                              'center_project_name': 'Test Project',
                              'ebi_submission_accession': None,
                              'EMP_status_id': 1,
                              'str_column': 'Value for sample 2'},
            '1.SKB7.640196': {'center_name': 'ANL',
                              'center_project_name': 'Test Project',
                              'ebi_submission_accession': None,
                              'EMP_status_id': 1,
                              'str_column': 'Value for sample 3'}
            }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        with self.assertRaises(QiitaDBColumnError):
            PrepTemplate.create(metadata, self.new_raw_data, self.test_study,
                                self.data_type)

    def test_create_error_template_special(self):
        """Create raises an error if not all columns are on the template"""
        metadata_dict = {
            '1.SKB8.640193': {'center_name': 'ANL',
                              'center_project_name': 'Test Project',
                              'ebi_submission_accession': None,
                              'EMP_status': 'EMP',
                              'str_column': 'Value for sample 1',
                              'barcodesequence': 'GTCCGCAAGTTA'},
            '1.SKD8.640184': {'center_name': 'ANL',
                              'center_project_name': 'Test Project',
                              'ebi_submission_accession': None,
                              'EMP_status': 'EMP',
                              'str_column': 'Value for sample 2',
                              'barcodesequence': 'CGTAGAGCTCTC'},
            '1.SKB7.640196': {'center_name': 'ANL',
                              'center_project_name': 'Test Project',
                              'ebi_submission_accession': None,
                              'EMP_status': 'EMP',
                              'str_column': 'Value for sample 3',
                              'barcodesequence': 'CCTCTGAGAGCT'}
            }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        with self.assertRaises(QiitaDBColumnError):
            PrepTemplate.create(metadata, self.new_raw_data, self.test_study,
                                self.data_type)

    def test_create_investigation_type_error(self):
        """Create raises an error if the investigation_type does not exists"""
        with self.assertRaises(QiitaDBColumnError):
            PrepTemplate.create(self.metadata, self.new_raw_data,
                                self.test_study, self.data_type_id,
                                'Not a term')

    def test_delete_error(self):
        """Try to delete a prep template that already has preprocessed data"""
        with self.assertRaises(QiitaDBError):
            PrepTemplate.delete(1)

    def test_delete_unkonwn_id_error(self):
        """Try to delete a non existent prep template"""
        with self.assertRaises(QiitaDBUnknownIDError):
            PrepTemplate.delete(5)

    def test_delete(self):
        """Deletes prep template 2"""
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type_id)
        PrepTemplate.delete(pt.id)

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_template WHERE prep_template_id=2")
        exp = []
        self.assertEqual(obs, exp)

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.common_prep_info WHERE prep_template_id=2")
        exp = []
        self.assertEqual(obs, exp)

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_columns WHERE prep_template_id=2")
        exp = []
        self.assertEqual(obs, exp)

        with self.assertRaises(QiitaDBExecutionError):
            self.conn_handler.execute_fetchall(
                "SELECT * FROM qiita.prep_2")

    def test_exists_true(self):
        """Exists returns true when the PrepTemplate already exists"""
        self.assertTrue(PrepTemplate.exists(1))

    def test_exists_false(self):
        """Exists returns false when the PrepTemplate does not exists"""
        self.assertFalse(PrepTemplate.exists(2))

    def test_get_sample_ids(self):
        """get_sample_ids returns the correct set of sample ids"""
        obs = self.tester._get_sample_ids(self.conn_handler)
        self.assertEqual(obs, self.exp_sample_ids)

    def test_len(self):
        """Len returns the correct number of sample ids"""
        self.assertEqual(len(self.tester), 27)

    def test_getitem(self):
        """Get item returns the correct sample object"""
        obs = self.tester['1.SKM7.640188']
        exp = PrepSample('1.SKM7.640188', self.tester)
        self.assertEqual(obs, exp)

    def test_getitem_error(self):
        """Get item raises an error if key does not exists"""
        with self.assertRaises(KeyError):
            self.tester['Not_a_Sample']

    def test_setitem(self):
        """setitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            self.tester['1.SKM7.640188'] = PrepSample('1.SKM7.640188',
                                                      self.tester)

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            del self.tester['1.SKM7.640188']

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
        exp = {PrepSample('1.SKB1.640202', self.tester),
               PrepSample('1.SKB2.640194', self.tester),
               PrepSample('1.SKB3.640195', self.tester),
               PrepSample('1.SKB4.640189', self.tester),
               PrepSample('1.SKB5.640181', self.tester),
               PrepSample('1.SKB6.640176', self.tester),
               PrepSample('1.SKB7.640196', self.tester),
               PrepSample('1.SKB8.640193', self.tester),
               PrepSample('1.SKB9.640200', self.tester),
               PrepSample('1.SKD1.640179', self.tester),
               PrepSample('1.SKD2.640178', self.tester),
               PrepSample('1.SKD3.640198', self.tester),
               PrepSample('1.SKD4.640185', self.tester),
               PrepSample('1.SKD5.640186', self.tester),
               PrepSample('1.SKD6.640190', self.tester),
               PrepSample('1.SKD7.640191', self.tester),
               PrepSample('1.SKD8.640184', self.tester),
               PrepSample('1.SKD9.640182', self.tester),
               PrepSample('1.SKM1.640183', self.tester),
               PrepSample('1.SKM2.640199', self.tester),
               PrepSample('1.SKM3.640197', self.tester),
               PrepSample('1.SKM4.640180', self.tester),
               PrepSample('1.SKM5.640177', self.tester),
               PrepSample('1.SKM6.640187', self.tester),
               PrepSample('1.SKM7.640188', self.tester),
               PrepSample('1.SKM8.640201', self.tester),
               PrepSample('1.SKM9.640192', self.tester)}
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs), key=lambda x: x.id),
                        sorted(exp, key=lambda x: x.id)):
            self.assertEqual(o, e)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = [('1.SKB1.640202', PrepSample('1.SKB1.640202', self.tester)),
               ('1.SKB2.640194', PrepSample('1.SKB2.640194', self.tester)),
               ('1.SKB3.640195', PrepSample('1.SKB3.640195', self.tester)),
               ('1.SKB4.640189', PrepSample('1.SKB4.640189', self.tester)),
               ('1.SKB5.640181', PrepSample('1.SKB5.640181', self.tester)),
               ('1.SKB6.640176', PrepSample('1.SKB6.640176', self.tester)),
               ('1.SKB7.640196', PrepSample('1.SKB7.640196', self.tester)),
               ('1.SKB8.640193', PrepSample('1.SKB8.640193', self.tester)),
               ('1.SKB9.640200', PrepSample('1.SKB9.640200', self.tester)),
               ('1.SKD1.640179', PrepSample('1.SKD1.640179', self.tester)),
               ('1.SKD2.640178', PrepSample('1.SKD2.640178', self.tester)),
               ('1.SKD3.640198', PrepSample('1.SKD3.640198', self.tester)),
               ('1.SKD4.640185', PrepSample('1.SKD4.640185', self.tester)),
               ('1.SKD5.640186', PrepSample('1.SKD5.640186', self.tester)),
               ('1.SKD6.640190', PrepSample('1.SKD6.640190', self.tester)),
               ('1.SKD7.640191', PrepSample('1.SKD7.640191', self.tester)),
               ('1.SKD8.640184', PrepSample('1.SKD8.640184', self.tester)),
               ('1.SKD9.640182', PrepSample('1.SKD9.640182', self.tester)),
               ('1.SKM1.640183', PrepSample('1.SKM1.640183', self.tester)),
               ('1.SKM2.640199', PrepSample('1.SKM2.640199', self.tester)),
               ('1.SKM3.640197', PrepSample('1.SKM3.640197', self.tester)),
               ('1.SKM4.640180', PrepSample('1.SKM4.640180', self.tester)),
               ('1.SKM5.640177', PrepSample('1.SKM5.640177', self.tester)),
               ('1.SKM6.640187', PrepSample('1.SKM6.640187', self.tester)),
               ('1.SKM7.640188', PrepSample('1.SKM7.640188', self.tester)),
               ('1.SKM8.640201', PrepSample('1.SKM8.640201', self.tester)),
               ('1.SKM9.640192', PrepSample('1.SKM9.640192', self.tester))]
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs)), sorted(exp)):
            self.assertEqual(o, e)

    def test_get(self):
        """get returns the correct PrepSample object"""
        obs = self.tester.get('1.SKM7.640188')
        exp = PrepSample('1.SKM7.640188', self.tester)
        self.assertEqual(obs, exp)

    def test_get_none(self):
        """get returns none if the sample id is not present"""
        self.assertTrue(self.tester.get('Not_a_Sample') is None)

    def test_to_file(self):
        """to file writes a tab delimited file with all the metadata"""
        fd, fp = mkstemp()
        close(fd)
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type)
        pt.to_file(fp)
        self._clean_up_files.append(fp)
        with open(fp, 'U') as f:
            obs = f.read()
        self.assertEqual(obs, EXP_PREP_TEMPLATE)

    def test_data_type(self):
        """data_type returns the string with the data_type"""
        self.assertTrue(self.tester.data_type(), "18S")

    def test_data_type_id(self):
        """data_type returns the int with the data_type_id"""
        self.assertTrue(self.tester.data_type(ret_id=True), 2)

    def test_raw_data(self):
        """Returns the raw_data associated with the prep template"""
        self.assertEqual(self.tester.raw_data, 1)

    def test_preprocessed_data(self):
        """Returns the preprocessed data list generated from this template"""
        self.assertEqual(self.tester.preprocessed_data, [1, 2])

    def test_preprocessing_status(self):
        """preprocessing_status works correctly"""
        # Success case
        pt = PrepTemplate(1)
        self.assertEqual(pt.preprocessing_status, 'success')

        # not preprocessed case
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type_id)
        self.assertEqual(pt.preprocessing_status, 'not_preprocessed')

    def test_preprocessing_status_setter(self):
        """Able to update the preprocessing status"""
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type_id)
        self.assertEqual(pt.preprocessing_status, 'not_preprocessed')
        pt.preprocessing_status = 'preprocessing'
        self.assertEqual(pt.preprocessing_status, 'preprocessing')
        pt.preprocessing_status = 'success'
        self.assertEqual(pt.preprocessing_status, 'success')

    def test_preprocessing_status_setter_failed(self):
        """Able to update preprocessing_status with a failure message"""
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type_id)
        state = 'failed: some error message'
        self.assertEqual(pt.preprocessing_status, 'not_preprocessed')
        pt.preprocessing_status = state
        self.assertEqual(pt.preprocessing_status, state)

    def test_preprocessing_status_setter_valueerror(self):
        """Raises an error if the status is not recognized"""
        with self.assertRaises(ValueError):
            self.tester.preprocessing_status = 'not a valid state'

    def test_investigation_type(self):
        """investigation_type works correctly"""
        self.assertEqual(self.tester.investigation_type, "Metagenomics")

    def test_investigation_type_setter(self):
        """Able to update the investigation type"""
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type_id)
        self.assertEqual(pt.investigation_type, None)
        pt.investigation_type = "Other"
        self.assertEqual(pt.investigation_type, 'Other')
        with self.assertRaises(QiitaDBColumnError):
            pt.investigation_type = "should fail"

    def test_investigation_type_instance_setter(self):
        pt = PrepTemplate(1)
        pt.investigation_type = 'RNASeq'
        self.assertEqual(pt.investigation_type, 'RNASeq')


class TestUtilities(TestCase):

    def test_load_template_to_dataframe(self):
        obs = load_template_to_dataframe(StringIO(EXP_SAMPLE_TEMPLATE))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_scrubbing(self):
        obs = load_template_to_dataframe(StringIO(EXP_SAMPLE_TEMPLATE_SPACES))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_empty_columns(self):
        obs = load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_SPACES_EMPTY_COLUMN))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_empty_rows(self):
        obs = load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_SPACES_EMPTY_ROW))
        exp = pd.DataFrame.from_dict(SAMPLE_TEMPLATE_DICT_FORM)
        exp.index.name = 'sample_name'
        assert_frame_equal(obs, exp)

    def test_load_template_to_dataframe_no_sample_name_cast(self):
        obs = load_template_to_dataframe(
            StringIO(EXP_SAMPLE_TEMPLATE_NUMBER_SAMPLE_NAMES))
        exp = pd.DataFrame.from_dict(
            SAMPLE_TEMPLATE_NUMBER_SAMPLE_NAMES_DICT_FORM)
        exp.index.name = 'sample_name'
        obs.sort_index(inplace=True)
        exp.sort_index(inplace=True)
        assert_frame_equal(obs, exp)


EXP_SAMPLE_TEMPLATE = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample2\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n")

EXP_SAMPLE_TEMPLATE_FEWER_SAMPLES = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n")

EXP_SAMPLE_TEMPLATE_SPACES = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1         \t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample2  \t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n")

EXP_SAMPLE_TEMPLATE_SPACES_EMPTY_ROW = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "2.Sample1         \t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\n"
    "2.Sample2  \t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\tValue for sample 2\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n"
    "\t\t\t\t\t\t\t\t\t\t\t\n"
    "\t\t\t\t\t\t\t\t\t\t\t\n")

EXP_SAMPLE_TEMPLATE_SPACES_EMPTY_COLUMN = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\t\n"
    "2.Sample1         \t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\t"
    "NotIdentified\t42.42\t41.41\tlocation1\treceived\ttype1\t"
    "Value for sample 1\t\n"
    "2.Sample2  \t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\tValue for sample 2\t\n"
    "2.Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
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

SAMPLE_TEMPLATE_DICT_FORM = {
    'collection_timestamp': {'2.Sample1': '2014-05-29 12:24:51',
                             '2.Sample2': '2014-05-29 12:24:51',
                             '2.Sample3': '2014-05-29 12:24:51'},
    'description': {'2.Sample1': 'Test Sample 1',
                    '2.Sample2': 'Test Sample 2',
                    '2.Sample3': 'Test Sample 3'},
    'has_extracted_data': {'2.Sample1': True,
                           '2.Sample2': True,
                           '2.Sample3': True},
    'has_physical_specimen': {'2.Sample1': True,
                              '2.Sample2': True,
                              '2.Sample3': True},
    'host_subject_id': {'2.Sample1': 'NotIdentified',
                        '2.Sample2': 'NotIdentified',
                        '2.Sample3': 'NotIdentified'},
    'latitude': {'2.Sample1': 42.420000000000002,
                 '2.Sample2': 4.2000000000000002,
                 '2.Sample3': 4.7999999999999998},
    'longitude': {'2.Sample1': 41.409999999999997,
                  '2.Sample2': 1.1000000000000001,
                  '2.Sample3': 4.4100000000000001},
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
                   '2.Sample3': 'Value for sample 3'}}

SAMPLE_TEMPLATE_NUMBER_SAMPLE_NAMES_DICT_FORM = {
    'collection_timestamp': {'002.000': '2014-05-29 12:24:51',
                             '1.11111': '2014-05-29 12:24:51',
                             '0.12121': '2014-05-29 12:24:51'},
    'description': {'002.000': 'Test Sample 1',
                    '1.11111': 'Test Sample 2',
                    '0.12121': 'Test Sample 3'},
    'has_extracted_data': {'002.000': True,
                           '1.11111': True,
                           '0.12121': True},
    'has_physical_specimen': {'002.000': True,
                              '1.11111': True,
                              '0.12121': True},
    'host_subject_id': {'002.000': 'NotIdentified',
                        '1.11111': 'NotIdentified',
                        '0.12121': 'NotIdentified'},
    'latitude': {'002.000': 42.420000000000002,
                 '1.11111': 4.2000000000000002,
                 '0.12121': 4.7999999999999998},
    'longitude': {'002.000': 41.409999999999997,
                  '1.11111': 1.1000000000000001,
                  '0.12121': 4.4100000000000001},
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
