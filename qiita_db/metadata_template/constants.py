# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from collections import namedtuple

Restriction = namedtuple('Restriction', ['columns', 'error_msg'])

# A dict containing the restrictions that apply to the sample templates
SAMPLE_TEMPLATE_COLUMNS = {
    'EBI': Restriction(columns={'collection_timestamp': 'timestamp',
                                'physical_specimen_location': 'varchar'},
                       error_msg="EBI submission disabled"),
    'Qiita_main': Restriction(columns={'sample_type': 'varchar',
                                       'description': 'varchar',
                                       'physical_specimen_remaining': 'bool',
                                       'dna_extracted': 'bool',
                                       'latitude': 'float8',
                                       'longitude': 'float8',
                                       'host_subject_id': 'varchar'},
                              error_msg="Processed data approval disabled")
}

# A dict containing the restrictions that apply to the sample templates
PREP_TEMPLATE_COLUMNS = {
    'EBI': Restriction(
        columns={'primer': 'varchar',
                 'center_name': 'varchar',
                 'platform': 'varchar',
                 'library_construction_protocol': 'varchar',
                 'experiment_design_description': 'varchar'},
        error_msg="EBI submission disabled")
}

# Different prep templates have different requirements depending on the data
# type. We create a dictionary for each of these special datatypes

TARGET_GENE_DATA_TYPES = ['16S', '18S', 'ITS']

PREP_TEMPLATE_COLUMNS_TARGET_GENE = {
    'Demultiplex': Restriction(
        columns={'barcode': 'varchar',
                 'primer': 'varchar'},
        error_msg="Demultiplexing disabled. You will not be able to "
                  "preprocess your raw data"),
    'Demultiplex_multiple': Restriction(
        columns={'barcode': 'varchar',
                 'primer': 'varchar',
                 'run_prefix': 'varchar'},
        error_msg="Demultiplexing with multiple input files disabled. If your "
                  "raw data includes multiple raw input files, you will not "
                  "be able to preprocess your raw data")
}


REQUIRED_TARGET_GENE_COLS = {'barcodesequence', 'linkerprimersequence',
                             'run_prefix', 'library_construction_protocol',
                             'experiment_design_description', 'platform'}
RENAME_COLS_DICT = {'barcode': 'barcodesequence',
                    'primer': 'linkerprimersequence'}
