# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from collections import namedtuple
from future.utils import viewkeys, viewvalues
from datetime import datetime

Restriction = namedtuple('Restriction', ['columns', 'error_msg'])

# A dict containing the restrictions that apply to the sample templates
SAMPLE_TEMPLATE_COLUMNS = {
    # The following columns are required by EBI for submission
    'EBI': Restriction(columns={'collection_timestamp': datetime,
                                'physical_specimen_location': str,
                                'taxon_id': int,
                                'scientific_name': str},
                       error_msg="EBI submission disabled"),
    # The following columns are required for the official main QIITA site
    'qiita_main': Restriction(columns={'sample_type': str,
                                       'description': str,
                                       'physical_specimen_remaining': bool,
                                       'dna_extracted': bool,
                                       'latitude': float,
                                       'longitude': float,
                                       'host_subject_id': str},
                              error_msg="Processed data approval disabled")
}

# A dict containing the restrictions that apply to the prep templates
PREP_TEMPLATE_COLUMNS = {
    # The following columns are required by EBI for submission
    'EBI': Restriction(
        columns={'center_name': str,
                 'platform': str,
                 'instrument_model': str,
                 'library_construction_protocol': str,
                 'experiment_design_description': str},
        error_msg="EBI submission disabled")
}

# Different prep templates have different requirements depending on the data
# type. We create a dictionary for each of these special datatypes

TARGET_GENE_DATA_TYPES = ['16S', '18S', 'ITS']

PREP_TEMPLATE_COLUMNS_TARGET_GENE = {
    # The following columns are required by QIIME to execute split libraries
    'demultiplex': Restriction(
        columns={'barcode': str},
        error_msg="Demultiplexing disabled."),
    # The following columns are required by Qiita to know how to execute split
    # libraries using QIIME over a study with multiple illumina lanes
    'demultiplex_multiple': Restriction(
        columns={'barcode': str,
                 'primer': str,
                 'run_prefix': str},
        error_msg="Demultiplexing with multiple input files disabled.")
}

# This list is useful to have if we want to loop through all the restrictions
# in a template-independent manner
ALL_RESTRICTIONS = [SAMPLE_TEMPLATE_COLUMNS, PREP_TEMPLATE_COLUMNS,
                    PREP_TEMPLATE_COLUMNS_TARGET_GENE]

# This is what we consider as "NaN" cell values on metadata import
# from http://www.ebi.ac.uk/ena/about/missing-values-reporting
EBI_NULL_VALUES = ['Not applicable', 'Missing: Not collected',
                   'Missing: Not provided', 'Missing: Restricted access']

# These are what will be considered 'True' bool values on metadata import
TRUE_VALUES = ['Yes', 'yes', 'YES', 'Y', 'y', 'True', 'true', 'TRUE', 't', 'T']

# These are what will be considered 'False' bool values on metadata import
FALSE_VALUES = ['No', 'no', 'NO', 'N', 'n', 'False', 'false', 'FALSE',
                'f', 'F']


# A set holding all the controlled columns, useful to avoid recalculating it
def _col_iterator():
    for r_set in ALL_RESTRICTIONS:
        for restriction in viewvalues(r_set):
            for cols in viewkeys(restriction.columns):
                yield cols


CONTROLLED_COLS = set(col for col in _col_iterator())
