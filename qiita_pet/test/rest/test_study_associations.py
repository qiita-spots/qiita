# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from tornado.escape import json_decode

from qiita_db.study import Study
from qiita_pet.test.rest.test_base import RESTHandlerTestCase


class StudyAssociationTests(RESTHandlerTestCase):
    def test_get_valid(self):
        IGNORE = IGNORE
        exp = {'study': 1,
               'prep_templates': [{'prep_id': 1,
                   'prep_filepath': IGNORE,
                   'prep_datatype': '18S',
                   'prep_human_filtering': 'The greatest human filtering method',
                   'prep_artifacts': [{'artifact_id': 1,
                     'artifact_parent_ids': [1],
                     'artifact_basal_id': 1,
                     'artifact_processing_id': None,
                     'artifact_processing_name': None,
                     'artifact_processing_arguments': None,
                     'artifact_filepaths': [{'artifact_filepath_id': 1,
                       'artifact_filepath': IGNORE,
                       'artifact_filepath_type': 'raw_forward_seqs'},
                      {'artifact_filepath_id': 2,
                       'artifact_filepath': IGNORE,
                       'artifact_filepath_type': 'raw_barcodes'}]},
                    {'artifact_id': 2,
                     'artifact_parent_ids': None,
                     'artifact_basal_id': 1,
                     'artifact_processing_id': 1,
                     'artifact_processing_name': 'Split libraries FASTQ',
                     'artifact_processing_arguments': {'input_data': '1',
                      'max_bad_run_length': '3',
                      'min_per_read_length_fraction': '0.75',
                      'sequence_max_n': '0',
                      'rev_comp_barcode': 'False',
                      'rev_comp_mapping_barcodes': 'False',
                      'rev_comp': 'False',
                      'phred_quality_threshold': '3',
                      'barcode_type': 'golay_12',
                      'max_barcode_errors': '1.5',
                      'phred_offset': 'auto'},
                     'artifact_filepaths': [{'artifact_filepath_id': 3,
                       'artifact_filepath': IGNORE,
                       'artifact_filepath_type': 'preprocessed_fasta'},
                      {'artifact_filepath': IGNORE,
                       'artifact_filepath_id': 4,
                       'artifact_filepath_type': 'preprocessed_fastq'},
                      {'artifact_filepath': IGNORE,
                       'artifact_filepath_id': 5,
                       'artifact_filepath_type': 'preprocessed_demux'}]},
                    {'artifact_id': 3,
                     'artifact_parent_ids': [1],
                     'artifact_basal_id': 1,
                     'artifact_processing_id': 1,
                     'artifact_processing_name': 'Split libraries FASTQ',
                     'artifact_processing_arguments': {'input_data': '1',
                      'max_bad_run_length': '3',
                      'min_per_read_length_fraction': '0.75',
                      'sequence_max_n': '0',
                      'rev_comp_barcode': 'False',
                      'rev_comp_mapping_barcodes': 'False',
                      'rev_comp': 'False',
                      'phred_quality_threshold': '3',
                      'barcode_type': 'golay_12',
                      'max_barcode_errors': '1.5',
                      'phred_offset': 'auto'},
                     'artifact_filepaths': []},
                    {'artifact_id': 4,
                     'artifact_parent_ids': [2],
                     'artifact_basal_id': 1,
                     'artifact_processing_id': 3,
                     'artifact_processing_name': 'Pick closed-reference OTUs',
                     'artifact_processing_arguments': {'input_data': '2',
                      'reference': '1',
                      'sortmerna_e_value': '1',
                      'sortmerna_max_pos': '10000',
                      'similarity': '0.97',
                      'sortmerna_coverage': '0.97',
                      'threads': '1'},
                     'artifact_filepaths': [{'artifact_filepath_id': 9,
                       'artifact_filepath': IGNORE,
                       'artifact_filepath_type': 'biom'}]},
                    {'artifact_id': 5,
                     'artifact_parent_ids': [2],
                     'artifact_basal_id': 1,
                     'artifact_processing_id': 3,
                     'artifact_processing_name': 'Pick closed-reference OTUs',
                     'artifact_processing_arguments': {'input_data': '2',
                      'reference': '1',
                      'sortmerna_e_value': '1',
                      'sortmerna_max_pos': '10000',
                      'similarity': '0.97',
                      'sortmerna_coverage': '0.97',
                      'threads': '1'},
                     'artifact_filepaths': [{'artifact_filepath_id': 9,
                       'artifact_filepath': IGNORE,
                       'artifact_filepath_type': 'biom'}]},
                    {'artifact_id': 6,
                     'artifact_parent_ids': [2],
                     'artifact_basal_id': 1,
                     'artifact_processing_id': 3,
                     'artifact_processing_name': 'Pick closed-reference OTUs',
                     'artifact_processing_arguments': {'input_data': '2',
                      'reference': '2',
                      'sortmerna_e_value': '1',
                      'sortmerna_max_pos': '10000',
                      'similarity': '0.97',
                      'sortmerna_coverage': '0.97',
                      'threads': '1'},
                     'artifact_filepaths': [{'artifact_filepath_id': 12,
                       'artifact_filepath': IGNORE,
                       'artifact_filepath_type': 'biom'}]}]},
                  {'prep_id': 2,
                   'prep_filepath': IGNORE,
                   'prep_datatype': '18S',
                   'prep_human_filtering': None,
                   'prep_artifacts': [{'artifact_id': 7,
                     'artifact_parent_ids': [],
                     'artifact_basal_id': 7,
                     'artifact_processing_id': None,
                     'artifact_processing_name': None,
                     'artifact_processing_arguments': None,
                     'artifact_filepaths': [{'artifact_filepath_id': 22,
                       'artifact_filepath': IGNORE,
                       'artifact_filepath_type': 'biom'}]}]}]}

        response = self.get('/api/v1/study-association/1', headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_invalid(self):
        response = self.get('/api/v1/study-association/0', headers=self.headers)
        self.assertEqual(response.code, 404)
        self.assertEqual(json_decode(response.body),
                         {'message': 'Study not found'})


if __name__ == '__main__':
    main()
