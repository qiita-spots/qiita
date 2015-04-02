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
from time import strftime
from os import close, remove
from os.path import join, basename
from collections import Iterable

import numpy.testing as npt
import pandas as pd
from pandas.util.testing import assert_frame_equal

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import (QiitaDBUnknownIDError,
                                 QiitaDBNotImplementedError,
                                 QiitaDBDuplicateHeaderError,
                                 QiitaDBExecutionError,
                                 QiitaDBColumnError,
                                 QiitaDBWarning)
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.study import Study
from qiita_db.data import RawData, ProcessedData
from qiita_db.util import (exists_table, get_db_files_base_dir, get_mountpoint,
                           get_count)
from qiita_db.metadata_template.prep_template import PrepTemplate, PrepSample
from qiita_db.metadata_template.sample_template import SampleTemplate, Sample


class SetUpTestPrepSample(TestCase):
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


class TestPrepSampleReadOnly(SetUpTestPrepSample):
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
        conn_handler = SQLConnectionHandler()
        obs = self.tester._get_categories(conn_handler)
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
class TestPrepSampleReadWrite(SetUpTestPrepSample):
    """Tests the PrepSample class"""
    def test_setitem(self):
        """setitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            self.tester['barcodesequence'] = 'GTCCGCAAGTTA'

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            del self.tester['pcr_primers']


class SetUpTestPrepTemplate(TestCase):
    def _set_up(self):
        self.metadata_dict = {
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
        self.metadata = pd.DataFrame.from_dict(self.metadata_dict,
                                               orient='index')

        metadata_prefixed_dict = {
            '1.SKB8.640193': {'center_name': 'ANL',
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
            '1.SKD8.640184': {'center_name': 'ANL',
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
            '1.SKB7.640196': {'center_name': 'ANL',
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
        self.metadata_prefixed = pd.DataFrame.from_dict(metadata_prefixed_dict,
                                                        orient='index')

        self.test_raw_data = RawData(1)
        self.test_study = Study(1)
        self.data_type = "18S"
        self.data_type_id = 2

        self.tester = PrepTemplate(1)
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


class TestPrepTemplateReadOnly(SetUpTestPrepTemplate):
    def setUp(self):
        self._set_up()

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

    def test_exists_true(self):
        """Exists returns true when the PrepTemplate already exists"""
        self.assertTrue(PrepTemplate.exists(1))

    def test_exists_false(self):
        """Exists returns false when the PrepTemplate does not exists"""
        self.assertFalse(PrepTemplate.exists(2))

    def test_get_sample_ids(self):
        """get_sample_ids returns the correct set of sample ids"""
        conn_handler = SQLConnectionHandler()
        obs = self.tester._get_sample_ids(conn_handler)
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

    def test_investigation_type(self):
        """investigation_type works correctly"""
        self.assertEqual(self.tester.investigation_type, "Metagenomics")

    def test_to_dataframe(self):
        obs = self.tester.to_dataframe()
        # We don't test the specific values as this would blow up the size
        # of this file as the amount of lines would go to ~1000

        # 27 samples
        self.assertEqual(len(obs), 27)
        self.assertEqual(set(obs.index), {
            u'1.SKB1.640202', u'1.SKB2.640194', u'1.SKB3.640195',
            u'1.SKB4.640189', u'1.SKB5.640181', u'1.SKB6.640176',
            u'1.SKB7.640196', u'1.SKB8.640193', u'1.SKB9.640200',
            u'1.SKD1.640179', u'1.SKD2.640178', u'1.SKD3.640198',
            u'1.SKD4.640185', u'1.SKD5.640186', u'1.SKD6.640190',
            u'1.SKD7.640191', u'1.SKD8.640184', u'1.SKD9.640182',
            u'1.SKM1.640183', u'1.SKM2.640199', u'1.SKM3.640197',
            u'1.SKM4.640180', u'1.SKM5.640177', u'1.SKM6.640187',
            u'1.SKM7.640188', u'1.SKM8.640201', u'1.SKM9.640192'})

        self.assertEqual(set(obs.columns), {
            u'prep_template_id', u'center_name', u'center_project_name',
            u'emp_status', u'barcodesequence',
            u'library_construction_protocol', u'linkerprimersequence',
            u'target_subfragment', u'target_gene', u'run_center',
            u'run_prefix', u'run_date', u'experiment_center',
            u'experiment_design_description', u'experiment_title', u'platform',
            u'samp_size', u'sequencing_meth', u'illumina_technology',
            u'sample_center', u'pcr_primers', u'study_center'})


@qiita_test_checker()
class TestPrepTemplateReadWrite(SetUpTestPrepTemplate):
    """Tests the PrepTemplate class"""

    def setUp(self):
        self._set_up()
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
        db_seqs_fp = join(db_test_raw_dir, "5_%s" % basename(seqs_fp))
        db_barcodes_fp = join(db_test_raw_dir, "5_%s" % basename(barcodes_fp))
        self._clean_up_files = [db_seqs_fp, db_barcodes_fp]

    def test_create_duplicate_header(self):
        """Create raises an error when duplicate headers are present"""
        self.metadata['STR_COLUMN'] = pd.Series(['', '', ''],
                                                index=self.metadata.index)
        with self.assertRaises(QiitaDBDuplicateHeaderError):
            PrepTemplate.create(self.metadata, self.new_raw_data,
                                self.test_study, self.data_type)

    def test_create_bad_sample_names(self):
        # set a horrible list of sample names
        self.metadata.index = ['o()xxxx[{::::::::>', 'sample.1', 'sample.3']
        with self.assertRaises(QiitaDBColumnError):
            PrepTemplate.create(self.metadata, self.new_raw_data,
                                self.test_study, self.data_type)

    def test_create_unknown_sample_names(self):
        # set two real and one fake sample name
        self.metadata_dict['NOTREAL'] = self.metadata_dict['SKB7.640196']
        del self.metadata_dict['SKB7.640196']
        self.metadata = pd.DataFrame.from_dict(self.metadata_dict,
                                               orient='index')
        # Test error raised and correct error given
        with self.assertRaises(QiitaDBExecutionError) as err:
            PrepTemplate.create(self.metadata, self.new_raw_data,
                                self.test_study, self.data_type)
        self.assertEqual(
            str(err.exception), 'Samples found in prep template but not sample'
            ' template: 1.NOTREAL')

    def test_create_shorter_prep_template(self):
        # remove one sample so not all samples in the prep template
        del self.metadata_dict['SKB7.640196']
        self.metadata = pd.DataFrame.from_dict(self.metadata_dict,
                                               orient='index')
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type)

        # make sure the two samples were added correctly
        self.assertEqual(pt.id, 2)
        obs = self.conn_handler.execute_fetchall(
            "SELECT sample_id FROM qiita.prep_2")
        exp = [['1.SKB8.640193'], ['1.SKD8.640184']]
        self.assertEqual(obs, exp)

    def test_create_error_cleanup(self):
        """Create does not modify the database if an error happens"""
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'ebi_submission_accession': None,
                            'EMP_status': 'EMP',
                            'group': 2,
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
                            'group': 1,
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
                            'group': 'Value for sample 3',
                            'linkerprimersequence': 'GTGCCAGCMGCCGCGGTAA',
                            'barcodesequence': 'CCTCTGAGAGCT',
                            'run_prefix': "s_G1_L002_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}
            }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')

        exp_id = get_count("qiita.prep_template") + 1

        with self.assertRaises(QiitaDBExecutionError):
            PrepTemplate.create(metadata, self.new_raw_data,
                                self.test_study, self.data_type)

        sql = """SELECT EXISTS(
                    SELECT * FROM qiita.prep_template
                    WHERE prep_template_id=%s)"""
        self.assertFalse(self.conn_handler.execute_fetchone(sql, (exp_id,))[0])

        sql = """SELECT EXISTS(
                    SELECT * FROM qiita.common_prep_info
                    WHERE prep_template_id=%s)"""
        self.assertFalse(self.conn_handler.execute_fetchone(sql, (exp_id,))[0])

        sql = """SELECT EXISTS(
                    SELECT * FROM qiita.prep_columns
                    WHERE prep_template_id=%s)"""
        self.assertFalse(self.conn_handler.execute_fetchone(sql, (exp_id,))[0])

        self.assertFalse(exists_table("prep_%d" % exp_id, self.conn_handler))

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
        self.assertEqual(obs, [[2, 2, 5, 'not_preprocessed', None]])

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
        self.assertEqual(filepaths[0][0], 22)
        self.assertEqual(filepaths[1][0], 21)

    def test_create_already_prefixed_samples(self):
        """Creates a new PrepTemplate"""
        pt = npt.assert_warns(QiitaDBWarning, PrepTemplate.create,
                              self.metadata_prefixed, self.new_raw_data,
                              self.test_study, self.data_type)
        # The returned object has the correct id
        self.assertEqual(pt.id, 2)

        # The row in the prep template table has been created
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.prep_template WHERE prep_template_id=2")
        # prep_template_id, data_type_id, raw_data_id, preprocessing_status,
        # investigation_type
        self.assertEqual(obs, [[2, 2, 5, 'not_preprocessed', None]])

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
        self.assertEqual(filepaths[0][0], 22)
        self.assertEqual(filepaths[1][0], 21)

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

        obs = pd.read_csv(obs_fp, sep='\t', infer_datetime_format=True,
                          parse_dates=True, index_col=False, comment='\t')
        exp = pd.read_csv(exp_fp, sep='\t', infer_datetime_format=True,
                          parse_dates=True, index_col=False, comment='\t')

        assert_frame_equal(obs, exp)

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
        self.assertEqual(obs, [[2, 2, 5, 'not_preprocessed', None]])

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
        with self.assertRaises(QiitaDBExecutionError):
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

    def test_setitem(self):
        """setitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            self.tester['1.SKM7.640188'] = PrepSample('1.SKM7.640188',
                                                      self.tester)

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(QiitaDBNotImplementedError):
            del self.tester['1.SKM7.640188']

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

    def test_status(self):
        pt = PrepTemplate(1)
        self.assertEqual(pt.status, 'private')

        # Check that changing the status of the processed data, the status
        # of the prep template changes
        pd = ProcessedData(1)
        pd.status = 'public'
        self.assertEqual(pt.status, 'public')

        # New prep templates have the status to sandbox because there is no
        # processed data associated with them
        pt = PrepTemplate.create(self.metadata, self.new_raw_data,
                                 self.test_study, self.data_type_id)
        self.assertEqual(pt.status, 'sandbox')


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
