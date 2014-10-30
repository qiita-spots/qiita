# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from future.builtins import zip
from unittest import TestCase, main
from datetime import datetime
from tempfile import mkstemp
from os import close, remove
from os.path import join, basename
from collections import Iterable

import pandas as pd

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import (QiitaDBDuplicateError, QiitaDBUnknownIDError,
                                 QiitaDBNotImplementedError,
                                 QiitaDBDuplicateHeaderError,
                                 QiitaDBExecutionError,
                                 QiitaDBColumnError)
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.data import RawData
from qiita_db.util import exists_table, get_db_files_base_dir
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


@qiita_test_checker()
class TestSample(TestCase):
    """Tests the Sample class"""

    def setUp(self):
        self.sample_template = SampleTemplate(1)
        self.sample_id = 'SKB8.640193'
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
        self.assertEqual(sample._id, 'SKB8.640193')
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
        other = Sample('SKD8.640184', self.sample_template)
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
        self.sample_id = 'SKB8.640193'
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
            PrepSample('SKB8.640193', SampleTemplate(1))

    def test_init(self):
        """Init correctly initializes the PrepSample object"""
        sample = PrepSample(self.sample_id, self.prep_template)
        # Check that the internal id have been correctly set
        self.assertEqual(sample._id, 'SKB8.640193')
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
        other = PrepSample('SKD8.640184', self.prep_template)
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
        self.exp_sample_ids = {'SKB1.640202', 'SKB2.640194', 'SKB3.640195',
                               'SKB4.640189', 'SKB5.640181', 'SKB6.640176',
                               'SKB7.640196', 'SKB8.640193', 'SKB9.640200',
                               'SKD1.640179', 'SKD2.640178', 'SKD3.640198',
                               'SKD4.640185', 'SKD5.640186', 'SKD6.640190',
                               'SKD7.640191', 'SKD8.640184', 'SKD9.640182',
                               'SKM1.640183', 'SKM2.640199', 'SKM3.640197',
                               'SKM4.640180', 'SKM5.640177', 'SKM6.640187',
                               'SKM7.640188', 'SKM8.640201', 'SKM9.640192'}
        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

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
        obs = SampleTemplate._table_name(self.test_study)
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
        # study_id sample_id physical_location has_physical_specimen
        # has_extracted_data sample_type required_sample_info_status_id
        # collection_timestamp host_subject_id description
        exp = [[2, "Sample1", "location1", True, True, "type1", 1,
                datetime(2014, 5, 29, 12, 24, 51), "NotIdentified",
                "Test Sample 1", 42.42, 41.41],
               [2, "Sample2", "location1", True, True, "type1", 1,
                datetime(2014, 5, 29, 12, 24, 51), "NotIdentified",
                "Test Sample 2", 4.2, 1.1],
               [2, "Sample3", "location1", True, True, "type1", 1,
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
        exp = [['Sample1', "Value for sample 1"],
               ['Sample2', "Value for sample 2"],
               ['Sample3', "Value for sample 3"]]
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

    def test_exists_true(self):
        """Exists returns true when the SampleTemplate already exists"""
        self.assertTrue(SampleTemplate.exists(self.test_study))

    def test_exists_false(self):
        """Exists returns false when the SampleTemplate does not exists"""
        self.assertFalse(SampleTemplate.exists(self.new_study))

    def test_get_sample_ids(self):
        """get_sample_ids returns the correct set of sample ids"""
        obs = self.tester._get_sample_ids(self.conn_handler)
        self.assertEqual(obs, self.exp_sample_ids)

    def test_len(self):
        """Len returns the correct number of sample ids"""
        self.assertEqual(len(self.tester), 27)

    def test_getitem(self):
        """Get item returns the correct sample object"""
        obs = self.tester['SKM7.640188']
        exp = Sample('SKM7.640188', self.tester)
        self.assertEqual(obs, exp)

    def test_getitem_error(self):
        """Get item raises an error if key does not exists"""
        with self.assertRaises(KeyError):
            self.tester['Not_a_Sample']

    def test_setitem(self):
        """setitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            self.tester['SKM7.640188'] = Sample('SKM7.640188', self.tester)

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            del self.tester['SKM7.640188']

    def test_iter(self):
        """iter returns an iterator over the sample ids"""
        obs = self.tester.__iter__()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_sample_ids)

    def test_contains_true(self):
        """contains returns true if the sample id exists"""
        self.assertTrue('SKM7.640188' in self.tester)

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
        exp = {Sample('SKB1.640202', self.tester),
               Sample('SKB2.640194', self.tester),
               Sample('SKB3.640195', self.tester),
               Sample('SKB4.640189', self.tester),
               Sample('SKB5.640181', self.tester),
               Sample('SKB6.640176', self.tester),
               Sample('SKB7.640196', self.tester),
               Sample('SKB8.640193', self.tester),
               Sample('SKB9.640200', self.tester),
               Sample('SKD1.640179', self.tester),
               Sample('SKD2.640178', self.tester),
               Sample('SKD3.640198', self.tester),
               Sample('SKD4.640185', self.tester),
               Sample('SKD5.640186', self.tester),
               Sample('SKD6.640190', self.tester),
               Sample('SKD7.640191', self.tester),
               Sample('SKD8.640184', self.tester),
               Sample('SKD9.640182', self.tester),
               Sample('SKM1.640183', self.tester),
               Sample('SKM2.640199', self.tester),
               Sample('SKM3.640197', self.tester),
               Sample('SKM4.640180', self.tester),
               Sample('SKM5.640177', self.tester),
               Sample('SKM6.640187', self.tester),
               Sample('SKM7.640188', self.tester),
               Sample('SKM8.640201', self.tester),
               Sample('SKM9.640192', self.tester)}
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs), key=lambda x: x.id),
                        sorted(exp, key=lambda x: x.id)):
            self.assertEqual(o, e)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = [('SKB1.640202', Sample('SKB1.640202', self.tester)),
               ('SKB2.640194', Sample('SKB2.640194', self.tester)),
               ('SKB3.640195', Sample('SKB3.640195', self.tester)),
               ('SKB4.640189', Sample('SKB4.640189', self.tester)),
               ('SKB5.640181', Sample('SKB5.640181', self.tester)),
               ('SKB6.640176', Sample('SKB6.640176', self.tester)),
               ('SKB7.640196', Sample('SKB7.640196', self.tester)),
               ('SKB8.640193', Sample('SKB8.640193', self.tester)),
               ('SKB9.640200', Sample('SKB9.640200', self.tester)),
               ('SKD1.640179', Sample('SKD1.640179', self.tester)),
               ('SKD2.640178', Sample('SKD2.640178', self.tester)),
               ('SKD3.640198', Sample('SKD3.640198', self.tester)),
               ('SKD4.640185', Sample('SKD4.640185', self.tester)),
               ('SKD5.640186', Sample('SKD5.640186', self.tester)),
               ('SKD6.640190', Sample('SKD6.640190', self.tester)),
               ('SKD7.640191', Sample('SKD7.640191', self.tester)),
               ('SKD8.640184', Sample('SKD8.640184', self.tester)),
               ('SKD9.640182', Sample('SKD9.640182', self.tester)),
               ('SKM1.640183', Sample('SKM1.640183', self.tester)),
               ('SKM2.640199', Sample('SKM2.640199', self.tester)),
               ('SKM3.640197', Sample('SKM3.640197', self.tester)),
               ('SKM4.640180', Sample('SKM4.640180', self.tester)),
               ('SKM5.640177', Sample('SKM5.640177', self.tester)),
               ('SKM6.640187', Sample('SKM6.640187', self.tester)),
               ('SKM7.640188', Sample('SKM7.640188', self.tester)),
               ('SKM8.640201', Sample('SKM8.640201', self.tester)),
               ('SKM9.640192', Sample('SKM9.640192', self.tester))]
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs)), sorted(exp)):
            self.assertEqual(o, e)

    def test_get(self):
        """get returns the correct sample object"""
        obs = self.tester.get('SKM7.640188')
        exp = Sample('SKM7.640188', self.tester)
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
                            'run_prefix': "s_G1_L001_sequences"},
            'SKD8.640184': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 2',
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'CGTAGAGCTCTC',
                            'run_prefix': "s_G1_L001_sequences"},
            'SKB7.640196': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 3',
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'CCTCTGAGAGCT',
                            'run_prefix': "s_G1_L002_sequences"}
            }
        self.metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        self.test_raw_data = RawData(1)
        self.test_study = Study(1)

        fd, seqs_fp = mkstemp(suffix='_seqs.fastq')
        close(fd)
        fd, barcodes_fp = mkstemp(suffix='_barcodes.fastq')
        close(fd)
        filepaths = [(seqs_fp, 1), (barcodes_fp, 2)]
        with open(seqs_fp, "w") as f:
            f.write("\n")
        with open(barcodes_fp, "w") as f:
            f.write("\n")
        self.new_raw_data = RawData.create(2, [Study(1)], 1,
                                           filepaths=filepaths)
        db_test_raw_dir = join(get_db_files_base_dir(), 'raw_data')
        db_seqs_fp = join(db_test_raw_dir, "3_%s" % basename(seqs_fp))
        db_barcodes_fp = join(db_test_raw_dir, "3_%s" % basename(barcodes_fp))
        self._clean_up_files = [db_seqs_fp, db_barcodes_fp]

        self.tester = PrepTemplate(1)
        self.exp_sample_ids = {'SKB1.640202', 'SKB2.640194', 'SKB3.640195',
                               'SKB4.640189', 'SKB5.640181', 'SKB6.640176',
                               'SKB7.640196', 'SKB8.640193', 'SKB9.640200',
                               'SKD1.640179', 'SKD2.640178', 'SKD3.640198',
                               'SKD4.640185', 'SKD5.640186', 'SKD6.640190',
                               'SKD7.640191', 'SKD8.640184', 'SKD9.640182',
                               'SKM1.640183', 'SKM2.640199', 'SKM3.640197',
                               'SKM4.640180', 'SKM5.640177', 'SKM6.640187',
                               'SKM7.640188', 'SKM8.640201', 'SKM9.640192'}

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

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
        obs = PrepTemplate._table_name(self.test_raw_data)
        self.assertEqual(obs, "prep_1")

    def test_create_duplicate(self):
        """Create raises an error when creating a duplicated PrepTemplate"""
        with self.assertRaises(QiitaDBDuplicateError):
            PrepTemplate.create(self.metadata, self.test_raw_data,
                                self.test_study)

    def test_create_duplicate_header(self):
        """Create raises an error when duplicate headers are present"""
        self.metadata['STR_COLUMN'] = pd.Series(['', '', ''],
                                                index=self.metadata.index)
        with self.assertRaises(QiitaDBDuplicateHeaderError):
            PrepTemplate.create(self.metadata, self.new_raw_data,
                                self.test_study)

    def test_create(self):
        """Creates a new PrepTemplate"""
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study)
        # The returned object has the correct id
        self.assertEqual(pt.id, 3)

        # The relevant rows to common_prep_info have been added.
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.common_prep_info WHERE raw_data_id=3")
        # raw_data_id, sample_id, center_name, center_project_name,
        # ebi_submission_accession, ebi_study_accession, emp_status_id
        exp = [[3, 'SKB8.640193', 1, 'ANL', 'Test Project', 1],
               [3, 'SKD8.640184', 1, 'ANL', 'Test Project', 1],
               [3, 'SKB7.640196', 1, 'ANL', 'Test Project', 1]]
        self.assertEqual(sorted(obs), sorted(exp))

        # The relevant rows have been added to the raw_data_prep_columns
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_data_prep_columns WHERE raw_data_id=3")
        # raw_data_id, column_name, column_type
        exp = [[3, 'str_column', 'varchar'],
               [3, 'ebi_submission_accession', 'varchar'],
               [3, 'run_prefix', 'varchar'],
               [3, 'barcodesequence', 'varchar'],
               [3, 'linkerprimersequence', 'varchar']]
        self.assertEqual(obs, exp)

        # The new table exists
        self.assertTrue(exists_table("prep_3", self.conn_handler))

        # The new table hosts the correct values
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_3")
        # sample_id, study_id, str_column, ebi_submission_accession,
        # barcodesequence, linkerprimersequence
        exp = [['SKB7.640196', 1, 'Value for sample 3', None,
                's_G1_L002_sequences', 'CCTCTGAGAGCT', 'GTGCCAGCMGCCGCGGTAA'],
               ['SKB8.640193', 1, 'Value for sample 1', None,
                's_G1_L001_sequences', 'GTCCGCAAGTTA', 'GTGCCAGCMGCCGCGGTAA'],
               ['SKD8.640184', 1, 'Value for sample 2', None,
                's_G1_L001_sequences', 'CGTAGAGCTCTC', 'GTGCCAGCMGCCGCGGTAA']]
        self.assertEqual(sorted(obs), sorted(exp))

    def test_create_error(self):
        """Create raises an error if any required columns are on the template
        """
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status_id': 1,
                            'str_column': 'Value for sample 1'},
            'SKD8.640184': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status_id': 1,
                            'str_column': 'Value for sample 2'},
            'SKB7.640196': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status_id': 1,
                            'str_column': 'Value for sample 3'}
            }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        with self.assertRaises(QiitaDBColumnError):
            PrepTemplate.create(metadata, self.new_raw_data, self.test_study)

    def test_create_error_partial(self):
        """Create raises an error if not all columns are on the template"""
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 1',
                            'barcodesequence': 'GTCCGCAAGTTA'},
            'SKD8.640184': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 2',
                            'barcodesequence': 'CGTAGAGCTCTC'},
            'SKB7.640196': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'str_column': 'Value for sample 3',
                            'barcodesequence': 'CCTCTGAGAGCT'}
            }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        with self.assertRaises(QiitaDBColumnError):
            PrepTemplate.create(metadata, self.new_raw_data, self.test_study)

    def test_delete(self):
        """Deletes prep template 1"""
        PrepTemplate.delete(1)
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.common_prep_info WHERE raw_data_id=1")
        exp = []
        self.assertEqual(obs, exp)
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_data_prep_columns WHERE raw_data_id=1")
        exp = []
        self.assertEqual(obs, exp)
        with self.assertRaises(QiitaDBExecutionError):
            self.conn_handler.execute_fetchall(
                "SELECT * FROM qiita.prep_1")

    def test_exists_true(self):
        """Exists returns true when the PrepTemplate already exists"""
        self.assertTrue(PrepTemplate.exists(self.test_raw_data))

    def test_exists_false(self):
        """Exists returns false when the PrepTemplate does not exists"""
        self.assertFalse(PrepTemplate.exists(self.new_raw_data))

    def test_get_sample_ids(self):
        """get_sample_ids returns the correct set of sample ids"""
        obs = self.tester._get_sample_ids(self.conn_handler)
        self.assertEqual(obs, self.exp_sample_ids)

    def test_len(self):
        """Len returns the correct number of sample ids"""
        self.assertEqual(len(self.tester), 27)

    def test_getitem(self):
        """Get item returns the correct sample object"""
        obs = self.tester['SKM7.640188']
        exp = PrepSample('SKM7.640188', self.tester)
        self.assertEqual(obs, exp)

    def test_getitem_error(self):
        """Get item raises an error if key does not exists"""
        with self.assertRaises(KeyError):
            self.tester['Not_a_Sample']

    def test_setitem(self):
        """setitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            self.tester['SKM7.640188'] = PrepSample('SKM7.640188', self.tester)

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            del self.tester['SKM7.640188']

    def test_iter(self):
        """iter returns an iterator over the sample ids"""
        obs = self.tester.__iter__()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_sample_ids)

    def test_contains_true(self):
        """contains returns true if the sample id exists"""
        self.assertTrue('SKM7.640188' in self.tester)

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
        exp = {PrepSample('SKB1.640202', self.tester),
               PrepSample('SKB2.640194', self.tester),
               PrepSample('SKB3.640195', self.tester),
               PrepSample('SKB4.640189', self.tester),
               PrepSample('SKB5.640181', self.tester),
               PrepSample('SKB6.640176', self.tester),
               PrepSample('SKB7.640196', self.tester),
               PrepSample('SKB8.640193', self.tester),
               PrepSample('SKB9.640200', self.tester),
               PrepSample('SKD1.640179', self.tester),
               PrepSample('SKD2.640178', self.tester),
               PrepSample('SKD3.640198', self.tester),
               PrepSample('SKD4.640185', self.tester),
               PrepSample('SKD5.640186', self.tester),
               PrepSample('SKD6.640190', self.tester),
               PrepSample('SKD7.640191', self.tester),
               PrepSample('SKD8.640184', self.tester),
               PrepSample('SKD9.640182', self.tester),
               PrepSample('SKM1.640183', self.tester),
               PrepSample('SKM2.640199', self.tester),
               PrepSample('SKM3.640197', self.tester),
               PrepSample('SKM4.640180', self.tester),
               PrepSample('SKM5.640177', self.tester),
               PrepSample('SKM6.640187', self.tester),
               PrepSample('SKM7.640188', self.tester),
               PrepSample('SKM8.640201', self.tester),
               PrepSample('SKM9.640192', self.tester)}
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs), key=lambda x: x.id),
                        sorted(exp, key=lambda x: x.id)):
            self.assertEqual(o, e)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = [('SKB1.640202', PrepSample('SKB1.640202', self.tester)),
               ('SKB2.640194', PrepSample('SKB2.640194', self.tester)),
               ('SKB3.640195', PrepSample('SKB3.640195', self.tester)),
               ('SKB4.640189', PrepSample('SKB4.640189', self.tester)),
               ('SKB5.640181', PrepSample('SKB5.640181', self.tester)),
               ('SKB6.640176', PrepSample('SKB6.640176', self.tester)),
               ('SKB7.640196', PrepSample('SKB7.640196', self.tester)),
               ('SKB8.640193', PrepSample('SKB8.640193', self.tester)),
               ('SKB9.640200', PrepSample('SKB9.640200', self.tester)),
               ('SKD1.640179', PrepSample('SKD1.640179', self.tester)),
               ('SKD2.640178', PrepSample('SKD2.640178', self.tester)),
               ('SKD3.640198', PrepSample('SKD3.640198', self.tester)),
               ('SKD4.640185', PrepSample('SKD4.640185', self.tester)),
               ('SKD5.640186', PrepSample('SKD5.640186', self.tester)),
               ('SKD6.640190', PrepSample('SKD6.640190', self.tester)),
               ('SKD7.640191', PrepSample('SKD7.640191', self.tester)),
               ('SKD8.640184', PrepSample('SKD8.640184', self.tester)),
               ('SKD9.640182', PrepSample('SKD9.640182', self.tester)),
               ('SKM1.640183', PrepSample('SKM1.640183', self.tester)),
               ('SKM2.640199', PrepSample('SKM2.640199', self.tester)),
               ('SKM3.640197', PrepSample('SKM3.640197', self.tester)),
               ('SKM4.640180', PrepSample('SKM4.640180', self.tester)),
               ('SKM5.640177', PrepSample('SKM5.640177', self.tester)),
               ('SKM6.640187', PrepSample('SKM6.640187', self.tester)),
               ('SKM7.640188', PrepSample('SKM7.640188', self.tester)),
               ('SKM8.640201', PrepSample('SKM8.640201', self.tester)),
               ('SKM9.640192', PrepSample('SKM9.640192', self.tester))]
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs)), sorted(exp)):
            self.assertEqual(o, e)

    def test_get(self):
        """get returns the correct PrepSample object"""
        obs = self.tester.get('SKM7.640188')
        exp = PrepSample('SKM7.640188', self.tester)
        self.assertEqual(obs, exp)

    def test_get_none(self):
        """get returns none if the sample id is not present"""
        self.assertTrue(self.tester.get('Not_a_Sample') is None)

    def test_to_file(self):
        """to file writes a tab delimited file with all the metadata"""
        fd, fp = mkstemp()
        close(fd)
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study)
        pt.to_file(fp)
        self._clean_up_files.append(fp)
        with open(fp, 'U') as f:
            obs = f.read()
        self.assertEqual(obs, EXP_PREP_TEMPLATE)

EXP_SAMPLE_TEMPLATE = (
    "sample_name\tcollection_timestamp\tdescription\thas_extracted_data\t"
    "has_physical_specimen\thost_subject_id\tlatitude\tlongitude\t"
    "physical_location\trequired_sample_info_status\tsample_type\t"
    "str_column\n"
    "Sample1\t2014-05-29 12:24:51\tTest Sample 1\tTrue\tTrue\tNotIdentified\t"
    "42.42\t41.41\tlocation1\treceived\ttype1\tValue for sample 1\n"
    "Sample2\t2014-05-29 12:24:51\t"
    "Test Sample 2\tTrue\tTrue\tNotIdentified\t4.2\t1.1\tlocation1\treceived\t"
    "type1\tValue for sample 2\n"
    "Sample3\t2014-05-29 12:24:51\tTest Sample 3\tTrue\t"
    "True\tNotIdentified\t4.8\t4.41\tlocation1\treceived\ttype1\t"
    "Value for sample 3\n")

EXP_PREP_TEMPLATE = (
    'sample_name\tbarcodesequence\tcenter_name\tcenter_project_name\t'
    'ebi_submission_accession\temp_status\tlinkerprimersequence\t'
    'run_prefix\tstr_column\n'
    'SKB7.640196\tCCTCTGAGAGCT\tANL\tTest Project\tNone\tEMP\t'
    'GTGCCAGCMGCCGCGGTAA\ts_G1_L002_sequences\tValue for sample 3\n'
    'SKB8.640193\tGTCCGCAAGTTA\tANL\tTest Project\tNone\tEMP\t'
    'GTGCCAGCMGCCGCGGTAA\ts_G1_L001_sequences\tValue for sample 1\n'
    'SKD8.640184\tCGTAGAGCTCTC\tANL\tTest Project\tNone\tEMP\t'
    'GTGCCAGCMGCCGCGGTAA\ts_G1_L001_sequences\tValue for sample 2\n')

if __name__ == '__main__':
    main()
