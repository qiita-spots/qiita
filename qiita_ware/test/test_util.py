#!/usr/bin/env python

from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import numpy as np
import pandas as pd

from unittest import TestCase, main

from qiita_db.metadata_template import SampleTemplate, PrepTemplate
from qiita_ware.util import (per_sample_sequences, template_to_dict,
                             metadata_stats_from_sample_and_prep_templates,
                             metadata_map_from_sample_and_prep_templates)


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

    def test_metadata_stats_from_sample_and_prep_templates(self):
        obs = metadata_stats_from_sample_and_prep_templates(SampleTemplate(1),
                                                            PrepTemplate(1))
        self.assertEqual(obs, SUMMARY_STATS)

    def test_metadata_map_from_sample_and_prep_templates(self):
        obs = metadata_map_from_sample_and_prep_templates(SampleTemplate(1),
                                                          PrepTemplate(1))

        # We don't test the specific values as this would blow up the size
        # of this file as the amount of lines would go to ~1000

        # 27 samples
        self.assertEqual(len(obs), 27)
        self.assertTrue(all(obs.index == pd.Index([
            u'SKB1.640202', u'SKB2.640194', u'SKB3.640195', u'SKB4.640189',
            u'SKB5.640181', u'SKB6.640176', u'SKB7.640196', u'SKB8.640193',
            u'SKB9.640200', u'SKD1.640179', u'SKD2.640178', u'SKD3.640198',
            u'SKD4.640185', u'SKD5.640186', u'SKD6.640190', u'SKD7.640191',
            u'SKD8.640184', u'SKD9.640182', u'SKM1.640183', u'SKM2.640199',
            u'SKM3.640197', u'SKM4.640180', u'SKM5.640177', u'SKM6.640187',
            u'SKM7.640188', u'SKM8.640201', u'SKM9.640192'], dtype='object')))

        # check the column names are correct
        self.assertTrue(all(obs.columns == pd.Index([
            u'sample_type', u'common_name', u'has_extracted_data',
            u'water_content_soil', u'env_feature', u'assigned_from_geo',
            u'altitude', u'env_biome', u'texture', u'has_physical_specimen',
            u'description_duplicate', u'physical_location', u'latitude',
            u'ph', u'host_taxid', u'elevation', u'description',
            u'collection_timestamp', u'taxon_id', u'samp_salinity',
            u'host_subject_id', u'season_environment',
            u'required_sample_info_status_id', u'temp', u'country',
            u'longitude', u'tot_nitro', u'depth', u'anonymized_name',
            u'tot_org_carb', u'experiment_center', u'center_name',
            u'run_center', u'run_prefix', u'data_type_id', u'target_gene',
            u'sequencing_meth', u'run_date', u'pcr_primers',
            u'ebi_submission_accession', u'linkerprimersequence', u'platform',
            u'library_construction_protocol', u'experiment_design_description',
            u'study_center', u'center_project_name', u'sample_center',
            u'samp_size', u'illumina_technology', u'experiment_title',
            u'emp_status_id', u'target_subfragment', u'barcodesequence',
            u'ebi_study_accession'], dtype='object')))

    def template_to_dict(self):
        template = PrepTemplate(1)
        obs = template_to_dict(template)

        # We don't test the specific values as this would blow up the size
        # of this file as the amount of lines would go to ~1000

        # twenty seven samples
        self.assertEqual(len(obs.keys()), 27)

        # the mapping file has 24 columns
        for key, value in obs.items():
            # check there are exatly these column names in the dictionary
            self.assertItemsEqual(value.keys(), [
                'experiment_center', 'center_name', 'run_center',
                'run_prefix', 'data_type_id', 'target_gene',
                'sequencing_meth', 'run_date', 'pcr_primers',
                'ebi_submission_accession', 'linkerprimersequence',
                'platform', 'library_construction_protocol',
                'experiment_design_description', 'study_center',
                'center_project_name', 'sample_center', 'samp_size',
                'illumina_technology', 'experiment_title', 'emp_status_id',
                'target_subfragment', 'barcodesequence',
                'ebi_study_accession'])


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
    'ebi_study_accession': [('None', 27)],
    'ebi_submission_accession': [('None', 27)],
    'elevation': [('114.0', 27)],
    'emp_status_id': [('1', 27)],
    'env_biome': [('ENVO:Temperate grasslands, savannas, and shrubland biome',
                   27)],
    'env_feature': [('ENVO:plant-associated habitat', 27)],
    'experiment_center': [('ANL', 27)],
    'experiment_design_description': [('micro biome of soil and rhizosphere '
                                       'of cannabis plants from CA', 27)],
    'experiment_title': [('Cannabis Soil Microbiome', 27)],
    'has_extracted_data': [('True', 27)],
    'has_physical_specimen': [('True', 27)],
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
    'latitude': [('33.193611', 27)],
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
    'longitude': [('-117.241111', 27)],
    'pcr_primers': [('FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 27)],
    'ph': [('6.8', 9), ('6.82', 10), ('6.94', 8)],
    'physical_location': [('ANL', 27)],
    'platform': [('Illumina', 27)],
    'required_sample_info_status_id': [('4', 27)],
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
    'water_content_soil': [('0.101', 9), ('0.164', 9), ('0.178', 9)]}


if __name__ == '__main__':
    main()
