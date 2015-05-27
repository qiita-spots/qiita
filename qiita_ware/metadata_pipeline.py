# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from future.utils import viewvalues, viewkeys

from qiita_db.metadata_template import (load_template_to_dataframe,
                                        SampleTemplate, PrepTemplate,
                                        PREP_TEMPLATE_COLUMNS,
                                        PREP_TEMPLATE_COLUMNS_TARGET_GENE,
                                        CONTROLLED_COLS)
from qiita_db.util import convert_to_id


def create_templates_from_qiime_mapping_file(fp, study, data_type):
    """Creates a sample template and a prep template from qiime mapping file

    Parameters
    ----------
    fp : str or file-like object
        Path to the QIIME mapping file
    study : Study
        The study to which the sample template belongs to
    data_type : str or int
        The data_type of the prep_template

    Returns
    -------
    (SampleTemplate, PrepTemplate)
        The templates created from the QIIME mapping file
    """
    qiime_map = load_template_to_dataframe(fp)

    # Fix the casing in the columns that we control
    qiime_map.columns = [c.lower() if c.lower() in CONTROLLED_COLS else c
                         for c in qiime_map.columns]

    # Figure out which columns belong to the prep template
    def _col_iterator(restriction_set):
        for restriction in viewvalues(restriction_set):
            for cols in viewkeys(restriction.columns):
                yield cols

    pt_cols = set(col for col in _col_iterator(PREP_TEMPLATE_COLUMNS))

    data_type_str = (convert_from_id(data_type, "data_type")
                     if isinstance(data_type, (int, long)) else data_type)

    if data_type_str in TARGET_GENE_DATA_TYPES:
        pt_cols.update(
            col for col in _col_iterator(PREP_TEMPLATE_COLUMNS_TARGET_GENE))

    st_md = TODO
    pt_md = TODO

    return SampleTemplate(st_md, study), PrepTemplate(pt_md, data_type)
