# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from collections import namedtuple

Restriction = namedtuple('Restriction', ['columns', 'error_msg'])

TARGET_GENE_DATA_TYPES = ['16S', '18S', 'ITS']
# TODO: remove
REQUIRED_TARGET_GENE_COLS = {'barcodesequence',
                             'linkerprimersequence',
                             'run_prefix',
                             'library_construction_protocol',
                             'experiment_design_description',
                             'platform'}
RENAME_COLS_DICT = {'barcode': 'barcodesequence',
                    'primer': 'linkerprimersequence'}

SAMPLE_TEMPLATE_COLUMNS = {
    'EBI': Restriction(columns={'collection_timestamp': 'timestamp',
                                'physical_specimen_location': 'varchar'},
                       error_msg="EBI submission disabled due to missing "
                                 "columns required by EBI"),
    'Qiita_main': Restriction(columns={'sample_type': 'varchar',
                                       'description': 'varchar',
                                       'physical_specimen_remaining': 'bool',
                                       'dna_extracted': 'bool',
                                       'latitude': 'float8',
                                       'longitude': 'float8',
                                       'host_subject_id': 'varchar'},
                              error_msg="Any processed data generated from "
                                        "this study will not be approved due "
                                        "to missing columns")
}

PREP_TEMPLATE_COLUMNS = {
    'EBI': Restriction(
        columns={'primer': 'varchar',
                 'center_name': 'varchar',
                 'platform': 'varchar',
                 'library_construction_protocol': 'varchar',
                 'experiment_design_description': 'varchar'},
        error_msg="EBI submission disabled for this prep template due to "
                  "missing columns required by EBI"),
    'Demultiplex': Restriction(
        columns={'barcode': 'varchar',
                 'primer': 'varchar'},
        error_msg="Demultiplexing disabled for this prep template due to "
                  "missing columns. If the data type of your raw data is "
                  "one of the target gene datatypes (%s), you will not be "
                  "able to preprocess your raw data"
                  % ', '.join(TARGET_GENE_DATA_TYPES)),
    'Demultiplex_multiple': Restriction(
        columns={'barcode': 'varchar',
                 'primer': 'varchar',
                 'run_prefix': 'varchar'},
        error_msg="Demultiplexing with multiple input files disabled for "
                  "this prep template due to missing columns. If the data "
                  "type of your raw data is one of the target gene datatypes "
                  "(%s) and includes multiple raw input files, you will not "
                  "be able to preprocess your raw data"
                  % ', '.join(TARGET_GENE_DATA_TYPES)),
}
