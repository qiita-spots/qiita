# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


TARGET_GENE_DATA_TYPES = ['16S', '18S', 'ITS']
REQUIRED_TARGET_GENE_COLS = {'barcodesequence', 'linkerprimersequence',
                             'run_prefix', 'library_construction_protocol',
                             'experiment_design_description', 'platform'}
RENAME_COLS_DICT = {'barcode': 'barcodesequence',
                    'primer': 'linkerprimersequence'}
