#!/usr/bin/env python

from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import os
from unittest import TestCase, main
import tempfile

import h5py
import numpy as np
from io import StringIO, BytesIO

from qiita_db.metadata_template import SampleTemplate, PrepTemplate
from qiita_ware.util import (per_sample_sequences, stats_from_df, open_file,
                             _is_string_or_bytes)


def mock_sequence_iter(items):
    return ({'SequenceID': sid, 'Sequence': seq} for sid, seq in items)


class UtilTests(TestCase):
    def setUp(self):
        np.random.seed(123)

    def test_per_sample_sequences_simple(self):
        max_seqs = 10
        # note, the result here is sorted by sequence_id but is in heap order
        # by the random values associated to each sequence
        exp = sorted([('b_2', 'AATTGGCC-b2'),
                      ('a_5', 'AATTGGCC-a5'),
                      ('a_1', 'AATTGGCC-a1'),
                      ('a_4', 'AATTGGCC-a4'),
                      ('b_1', 'AATTGGCC-b1'),
                      ('a_3', 'AATTGGCC-a3'),
                      ('c_3', 'AATTGGCC-c3'),
                      ('a_2', 'AATTGGCC-a2'),
                      ('c_2', 'AATTGGCC-c2'),
                      ('c_1', 'AATTGGCC-c1')])
        obs = per_sample_sequences(mock_sequence_iter(sequences), max_seqs)
        self.assertEqual(sorted(obs), exp)

    def test_per_sample_sequences_min_seqs(self):
        max_seqs = 10
        min_seqs = 3

        # note, the result here is sorted by sequence_id but is in heap order
        # by the random values associated to each sequence
        exp = sorted([('a_5', 'AATTGGCC-a5'),
                      ('a_1', 'AATTGGCC-a1'),
                      ('a_4', 'AATTGGCC-a4'),
                      ('a_3', 'AATTGGCC-a3'),
                      ('c_3', 'AATTGGCC-c3'),
                      ('a_2', 'AATTGGCC-a2'),
                      ('c_2', 'AATTGGCC-c2'),
                      ('c_1', 'AATTGGCC-c1')])
        obs = per_sample_sequences(mock_sequence_iter(sequences), max_seqs,
                                   min_seqs)
        self.assertEqual(sorted(obs), exp)

    def test_per_sample_sequences_complex(self):
        max_seqs = 2
        exp = sorted([('b_2', 'AATTGGCC-b2'),
                      ('b_1', 'AATTGGCC-b1'),
                      ('a_2', 'AATTGGCC-a2'),
                      ('a_3', 'AATTGGCC-a3'),
                      ('c_1', 'AATTGGCC-c1'),
                      ('c_2', 'AATTGGCC-c2')])
        obs = per_sample_sequences(mock_sequence_iter(sequences), max_seqs)
        self.assertEqual(sorted(obs), exp)

    def test_stats_from_df(self):
        obs = stats_from_df(SampleTemplate(1).to_dataframe())
        for k in obs:
            self.assertItemsEqual(obs[k], SUMMARY_STATS[k])

    def test_dataframe_from_template(self):
        template = PrepTemplate(1)
        obs = template.to_dataframe()

        # 27 samples
        self.assertEqual(len(obs), 27)
        self.assertTrue(set(obs.index), {
            u'SKB1.640202', u'SKB2.640194', u'SKB3.640195', u'SKB4.640189',
            u'SKB5.640181', u'SKB6.640176', u'SKB7.640196', u'SKB8.640193',
            u'SKB9.640200', u'SKD1.640179', u'SKD2.640178', u'SKD3.640198',
            u'SKD4.640185', u'SKD5.640186', u'SKD6.640190', u'SKD7.640191',
            u'SKD8.640184', u'SKD9.640182', u'SKM1.640183', u'SKM2.640199',
            u'SKM3.640197', u'SKM4.640180', u'SKM5.640177', u'SKM6.640187',
            u'SKM7.640188', u'SKM8.640201', u'SKM9.640192'})

        self.assertTrue(set(obs.columns), {
            u'tot_org_carb', u'common_name', u'has_extracted_data',
            u'required_sample_info_status', u'water_content_soil',
            u'env_feature', u'assigned_from_geo', u'altitude', u'env_biome',
            u'texture', u'has_physical_specimen', u'description_duplicate',
            u'physical_location', u'latitude', u'ph', u'host_taxid',
            u'elevation', u'description', u'collection_timestamp',
            u'taxon_id', u'samp_salinity', u'host_subject_id', u'sample_type',
            u'season_environment', u'temp', u'country', u'longitude',
            u'tot_nitro', u'depth', u'anonymized_name', u'target_subfragment',
            u'sample_center', u'samp_size', u'run_date', u'experiment_center',
            u'pcr_primers', u'center_name', u'barcodesequence', u'run_center',
            u'run_prefix', u'library_construction_protocol', u'emp_status',
            u'linkerprimersequence', u'experiment_design_description',
            u'target_gene', u'center_project_name', u'illumina_technology',
            u'sequencing_meth', u'platform', u'experiment_title',
            u'study_center'})


class TestFilePathOpening(TestCase):
    """Tests adapted from scikit-bio's skbio.io.util tests"""
    def test_is_string_or_bytes(self):
        self.assertTrue(_is_string_or_bytes('foo'))
        self.assertTrue(_is_string_or_bytes(u'foo'))
        self.assertTrue(_is_string_or_bytes(b'foo'))
        self.assertFalse(_is_string_or_bytes(StringIO('bar')))
        self.assertFalse(_is_string_or_bytes([1]))

    def test_file_closed(self):
        """File gets closed in decorator"""
        f = tempfile.NamedTemporaryFile('r')
        filepath = f.name
        with open_file(filepath) as fh:
            pass
        self.assertTrue(fh.closed)

    def test_file_closed_harder(self):
        """File gets closed in decorator, even if exceptions happen."""
        f = tempfile.NamedTemporaryFile('r')
        filepath = f.name
        try:
            with open_file(filepath) as fh:
                raise TypeError
        except TypeError:
            self.assertTrue(fh.closed)
        else:
            # If we're here, no exceptions have been raised inside the
            # try clause, so the context manager swallowed them. No
            # good.
            raise Exception("`open_file` didn't propagate exceptions")

    def test_filehandle(self):
        """Filehandles slip through untouched"""
        with tempfile.TemporaryFile('r') as fh:
            with open_file(fh) as ffh:
                self.assertTrue(fh is ffh)
            # And it doesn't close the file-handle
            self.assertFalse(fh.closed)

    def test_StringIO(self):
        """StringIO (useful e.g. for testing) slips through."""
        f = StringIO("File contents")
        with open_file(f) as fh:
            self.assertTrue(fh is f)

    def test_BytesIO(self):
        """BytesIO (useful e.g. for testing) slips through."""
        f = BytesIO(b"File contents")
        with open_file(f) as fh:
            self.assertTrue(fh is f)

    def test_hdf5IO(self):
        f = h5py.File('test', driver='core', backing_store=False)
        with open_file(f) as fh:
            self.assertTrue(fh is f)

    def test_hdf5IO_open(self):
        name = None
        with tempfile.NamedTemporaryFile(delete=False) as fh:
            name = fh.name
            fh.close()

            h5file = h5py.File(name, 'w')
            h5file.close()

            with open_file(name) as fh_inner:
                self.assertTrue(isinstance(fh_inner, h5py.File))

        os.remove(name)

# comment indicates the expected random value
sequences = [
    ('a_1', 'AATTGGCC-a1'),  # 2, 3624216819017203053
    ('a_2', 'AATTGGCC-a2'),  # 5, 5278339153051796802
    ('b_1', 'AATTGGCC-b1'),  # 4, 4184670734919783522
    ('b_2', 'AATTGGCC-b2'),  # 0, 946590342492863505
    ('a_4', 'AATTGGCC-a4'),  # 3, 4048487933969823850
    ('a_3', 'AATTGGCC-a3'),  # 7, 7804936597957240377
    ('c_1', 'AATTGGCC-c1'),  # 8, 8868534167180302049
    ('a_5', 'AATTGGCC-a5'),  # 1, 3409506807702804593
    ('c_2', 'AATTGGCC-c2'),  # 9, 8871627813779918895
    ('c_3', 'AATTGGCC-c3')   # 6, 7233291490207274528
]

SUMMARY_STATS = {
    'altitude': [('0.0', 27)],
    'anonymized_name': [('SKB1', 1),
                        ('SKB2', 1),
                        ('SKB3', 1),
                        ('SKB4', 1),
                        ('SKB5', 1),
                        ('SKB6', 1),
                        ('SKB7', 1),
                        ('SKB8', 1),
                        ('SKB9', 1),
                        ('SKD1', 1),
                        ('SKD2', 1),
                        ('SKD3', 1),
                        ('SKD4', 1),
                        ('SKD5', 1),
                        ('SKD6', 1),
                        ('SKD7', 1),
                        ('SKD8', 1),
                        ('SKD9', 1),
                        ('SKM1', 1),
                        ('SKM2', 1),
                        ('SKM3', 1),
                        ('SKM4', 1),
                        ('SKM5', 1),
                        ('SKM6', 1),
                        ('SKM7', 1),
                        ('SKM8', 1),
                        ('SKM9', 1)],
    'assigned_from_geo': [('n', 27)],
    'barcodesequence': [('AACTCCTGTGGA', 1),
                        ('ACCTCAGTCAAG', 1),
                        ('ACGCACATACAA', 1),
                        ('AGCAGGCACGAA', 1),
                        ('AGCGCTCACATC', 1),
                        ('ATATCGCGATGA', 1),
                        ('ATGGCCTGACTA', 1),
                        ('CATACACGCACC', 1),
                        ('CCACCCAGTAAC', 1),
                        ('CCGATGCCTTGA', 1),
                        ('CCTCGATGCAGT', 1),
                        ('CCTCTGAGAGCT', 1),
                        ('CGAGGTTCTGAT', 1),
                        ('CGCCGGTAATCT', 1),
                        ('CGGCCTAAGTTC', 1),
                        ('CGTAGAGCTCTC', 1),
                        ('CGTGCACAATTG', 1),
                        ('GATAGCACTCGT', 1),
                        ('GCGGACTATTCA', 1),
                        ('GTCCGCAAGTTA', 1),
                        ('TAATGGTCGTAG', 1),
                        ('TAGCGCGAACTT', 1),
                        ('TCGACCAAACAC', 1),
                        ('TGAGTGGTCTGT', 1),
                        ('TGCTACAGACGT', 1),
                        ('TGGTTATGGCAC', 1),
                        ('TTGCACCGTCGA', 1)],
    'center_name': [('ANL', 27)],
    'center_project_name': [('None', 27)],
    'collection_timestamp': [('2011-11-11 13:00:00', 27)],
    'common_name': [('rhizosphere metagenome', 9),
                    ('root metagenome', 9),
                    ('soil metagenome', 9)],
    'country': [('GAZ:United States of America', 27)],
    'data_type_id': [('2', 27)],
    'depth': [('0.15', 27)],
    'description': [('Cannabis Soil Microbiome', 27)],
    'description_duplicate': [('Bucu Rhizo', 3),
                              ('Bucu Roots', 3),
                              ('Bucu bulk', 3),
                              ('Burmese Rhizo', 3),
                              ('Burmese bulk', 3),
                              ('Burmese root', 3),
                              ('Diesel Rhizo', 3),
                              ('Diesel Root', 3),
                              ('Diesel bulk', 3)],
    'dna_extracted': [('True', 27)],
    'ebi_study_accession': [('None', 27)],
    'ebi_submission_accession': [('None', 27)],
    'elevation': [('114.0', 27)],
    'emp_status': [('EMP', 27)],
    'env_biome': [('ENVO:Temperate grasslands, savannas, and shrubland biome',
                   27)],
    'env_feature': [('ENVO:plant-associated habitat', 27)],
    'experiment_center': [('ANL', 27)],
    'experiment_design_description': [('micro biome of soil and rhizosphere '
                                       'of cannabis plants from CA', 27)],
    'experiment_title': [('Cannabis Soil Microbiome', 27)],
    'host_subject_id': [('1001:B1', 1),
                        ('1001:B2', 1),
                        ('1001:B3', 1),
                        ('1001:B4', 1),
                        ('1001:B5', 1),
                        ('1001:B6', 1),
                        ('1001:B7', 1),
                        ('1001:B8', 1),
                        ('1001:B9', 1),
                        ('1001:D1', 1),
                        ('1001:D2', 1),
                        ('1001:D3', 1),
                        ('1001:D4', 1),
                        ('1001:D5', 1),
                        ('1001:D6', 1),
                        ('1001:D7', 1),
                        ('1001:D8', 1),
                        ('1001:D9', 1),
                        ('1001:M1', 1),
                        ('1001:M2', 1),
                        ('1001:M3', 1),
                        ('1001:M4', 1),
                        ('1001:M5', 1),
                        ('1001:M6', 1),
                        ('1001:M7', 1),
                        ('1001:M8', 1),
                        ('1001:M9', 1)],
    'host_taxid': [('3483', 27)],
    'illumina_technology': [('MiSeq', 27)],
    'latitude': [('0.291867635913', 1),
                 ('3.21190859967', 1),
                 ('4.59216095574', 1),
                 ('10.6655599093', 1),
                 ('12.6245524972', 1),
                 ('12.7065957714', 1),
                 ('13.089194595', 1),
                 ('23.1218032799', 1),
                 ('29.1499460692', 1),
                 ('35.2374368957', 1),
                 ('38.2627021402', 1),
                 ('40.8623799474', 1),
                 ('43.9614715197', 1),
                 ('44.9725384282', 1),
                 ('53.5050692395', 1),
                 ('57.571893782', 1),
                 ('60.1102854322', 1),
                 ('68.0991287718', 1),
                 ('68.51099627', 1),
                 ('74.0894932572', 1),
                 ('78.3634273709', 1),
                 ('82.8302905615', 1),
                 ('84.0030227585', 1),
                 ('85.4121476399', 1),
                 ('95.2060749748', 1)],
    'library_construction_protocol': [('This analysis was done as in Caporaso '
                                       'et al 2011 Genome research. The PCR '
                                       'primers (F515/R806) were developed '
                                       'against the V4 region of the 16S rRNA '
                                       '(both bacteria and archaea), which we '
                                       'determined would yield optimal '
                                       'community clustering with reads of '
                                       'this length using a procedure '
                                       'similar to that of ref. 15. [For '
                                       'reference, this primer pair amplifies '
                                       'the region 533_786 in the Escherichia '
                                       'coli strain 83972 sequence '
                                       '(greengenes accession no. '
                                       'prokMSA_id:470367).] The reverse PCR '
                                       'primer is barcoded with a 12-base '
                                       'error-correcting Golay code to '
                                       'facilitate multiplexing of up '
                                       'to 1,500 samples per lane, and both '
                                       'PCR primers contain sequencer adapter '
                                       'regions.', 27)],
    'linkerprimersequence': [('GTGCCAGCMGCCGCGGTAA', 27)],
    'longitude': [
        ('2.35063674718', 1),
        ('3.48274264219', 1),
        ('6.66444220187', 1),
        ('15.6526750776', 1),
        ('26.8138925876', 1),
        ('27.3592668624', 1),
        ('31.2003474585', 1),
        ('31.6056761814', 1),
        ('32.5563076447', 1),
        ('34.8360987059', 1),
        ('42.838497795', 1),
        ('63.5115213108', 1),
        ('65.3283470202', 1),
        ('66.1920014699', 1),
        ('66.8954849864', 1),
        ('68.5041623253', 1),
        ('68.5945325743', 1),
        ('70.784770579', 1),
        ('74.423907894', 1),
        ('74.7123248382', 1),
        ('82.1270418227', 1),
        ('82.8516734159', 1),
        ('84.9722975792', 1),
        ('86.3615778099', 1),
        ('92.5274472082', 1),
        ('96.0693176066', 1)],
    'pcr_primers': [('FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 27)],
    'ph': [('6.8', 9), ('6.82', 10), ('6.94', 8)],
    'physical_specimen_location': [('ANL', 27)],
    'physical_specimen_remaining': [('True', 27)],
    'platform': [('Illumina', 27)],
    'required_sample_info_status': [('completed', 27)],
    'run_center': [('ANL', 27)],
    'run_date': [('8/1/12', 27)],
    'run_prefix': [('s_G1_L001_sequences', 27)],
    'samp_salinity': [('7.1', 9), ('7.15', 9), ('7.44', 9)],
    'samp_size': [('.25,g', 27)],
    'sample_center': [('ANL', 27)],
    'sample_type': [('ENVO:soil', 27)],
    'season_environment': [('winter', 27)],
    'sequencing_meth': [('Sequencing by synthesis', 27)],
    'study_center': [('CCME', 27)],
    'target_gene': [('16S rRNA', 27)],
    'target_subfragment': [('V4', 27)],
    'taxon_id': [('410658', 9), ('939928', 9), ('1118232', 9)],
    'temp': [('15.0', 27)],
    'texture': [('63.1 sand, 17.7 silt, 19.2 clay', 9),
                ('64.6 sand, 17.6 silt, 17.8 clay', 9),
                ('66 sand, 16.3 silt, 17.7 clay', 9)],
    'tot_nitro': [('1.3', 9), ('1.41', 9), ('1.51', 9)],
    'tot_org_carb': [('3.31', 9), ('4.32', 9), ('5.0', 9)],
    'water_content_soil': [('0.101', 9), ('0.164', 9), ('0.178', 9)],
    'scientific_name': [('1118232', 27)]}


if __name__ == '__main__':
    main()
