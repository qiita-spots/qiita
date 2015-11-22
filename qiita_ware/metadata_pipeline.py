# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from future.utils import viewvalues, viewkeys

from qiita_db.metadata_template.util import load_template_to_dataframe
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.constants import (
    PREP_TEMPLATE_COLUMNS, PREP_TEMPLATE_COLUMNS_TARGET_GENE, CONTROLLED_COLS,
    TARGET_GENE_DATA_TYPES)
from qiita_db.util import convert_from_id
from qiita_ware.exceptions import QiitaWareError


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
    qiime_map = load_template_to_dataframe(fp, index='#SampleID')

    # There are a few columns in the QIIME mapping file that are special and
    # we know how to deal with them
    rename_cols = {
        'BarcodeSequence': 'barcode',
        'LinkerPrimerSequence': 'primer',
        'Description': 'description',
    }

    if 'ReverseLinkerPrimer' in qiime_map:
        rename_cols['ReverseLinkerPrimer'] = 'reverselinkerprimer'

    missing = set(rename_cols).difference(qiime_map.columns)
    if missing:
        raise QiitaWareError(
            "Error generating the templates from the QIIME mapping file. "
            "Missing QIIME mapping file columns: %s" % ', '.join(missing))

    qiime_map.rename(columns=rename_cols, inplace=True)

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
        pt_cols.add('reverselinkerprimer')

    qiime_cols = set(qiime_map.columns)
    pt_cols = qiime_cols.intersection(pt_cols)
    st_cols = qiime_cols.difference(pt_cols)

    st_md = qiime_map.ix[:, st_cols]
    pt_md = qiime_map.ix[:, pt_cols]

    return (SampleTemplate.create(st_md, study),
            PrepTemplate.create(pt_md, study, data_type))
