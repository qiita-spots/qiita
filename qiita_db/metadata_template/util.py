# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from future.utils import PY3
from future.utils.six import StringIO

import pandas as pd
import numpy as np
import warnings
from skbio.io.util import open_file

from qiita_db.exceptions import QiitaDBColumnError, QiitaDBWarning
from .constants import CONTROLLED_COLS

if PY3:
    from string import ascii_letters as letters, digits
else:
    from string import letters, digits


def get_datatypes(metadata_map):
    r"""Returns the datatype of each metadata_map column

    Parameters
    ----------
    metadata_map : DataFrame
        The MetadataTemplate contents

    Returns
    -------
    list of str
        The SQL datatypes for each column, in column order
    """
    datatypes = []
    for dtype in metadata_map.dtypes:
        if dtype in [np.int8, np.int16, np.int32, np.int64]:
            datatypes.append('integer')
        elif dtype in [np.float16, np.float32, np.float64]:
            datatypes.append('float8')
        elif np.issubdtype(dtype, np.datetime64):
            datatypes.append('timestamp')
        elif dtype == np.bool:
            datatypes.append('bool')
        else:
            datatypes.append('varchar')
    return datatypes


def as_python_types(metadata_map, headers):
    r"""Converts the values of metadata_map pointed by headers from numpy types
    to python types.

    Psycopg2 does not support the numpy types, so we should cast them to the
    closest python type

    Parameters
    ----------
    metadata_map : DataFrame
        The MetadataTemplate contents
    headers : list of str
        The headers of the columns of metadata_map that needs to be converted
        to a python type

    Returns
    -------
    list of lists
        The values of the columns in metadata_map pointed by headers cast to
        python types.
    """
    values = []
    for h in headers:
        # we explicitly check for cases when we have a datetime64 object
        # because otherwise doing the isinstance check against np.generic fails
        if isinstance(metadata_map[h].values[0], np.datetime64):
            values.append(list(map(pd.to_datetime, metadata_map[h])))
        elif isinstance(metadata_map[h].values[0], np.generic):
            values.append(list(map(np.asscalar, metadata_map[h])))
        else:
            values.append(list(metadata_map[h]))
    return values


def prefix_sample_names_with_id(md_template, study_id):
    r"""prefix the sample_names in md_template with the study id

    Parameters
    ----------
    md_template : DataFrame
        The metadata template to modify
    study_id : int
        The study to which the metadata belongs to
    """
    # Get all the prefixes of the index, defined as any string before a '.'
    prefixes = {idx.split('.', 1)[0] for idx in md_template.index}
    # If the samples have been already prefixed with the study id, the prefixes
    # set will contain only one element and it will be the str representation
    # of the study id
    if len(prefixes) == 1 and prefixes.pop() == str(study_id):
        # The samples were already prefixed with the study id
        warnings.warn("Sample names were already prefixed with the study id.",
                      QiitaDBWarning)
    else:
        # Create a new pandas series in which all the values are the study_id
        # and it is indexed as the metadata template
        study_ids = pd.Series([str(study_id)] * len(md_template.index),
                              index=md_template.index)
        # Create a new column on the metadata template that includes the
        # metadata template indexes prefixed with the study id
        md_template['sample_name_with_id'] = (study_ids + '.' +
                                              md_template.index)
        md_template.index = md_template.sample_name_with_id
        del md_template['sample_name_with_id']
        # The original metadata template had the index column unnamed - remove
        # the name of the index for consistency
        md_template.index.name = None


def load_template_to_dataframe(fn, strip_whitespace=True):
    """Load a sample or a prep template into a data frame

    Parameters
    ----------
    fn : str or file-like object
        filename of the template to load, or an already open template file
    strip_whitespace : bool, optional
        Defaults to True. Whether or not to strip whitespace from values in the
        input file

    Returns
    -------
    DataFrame
        Pandas dataframe with the loaded information

    Raises
    ------
    ValueError
        Empty file passed
    QiitaDBColumnError
        If the sample_name column is not present in the template.
        If there's a value in one of the reserved columns that cannot be cast
        to the needed type.
    QiitaDBWarning
        When columns are dropped because they have no content for any sample.

    Notes
    -----
    The index attribute of the DataFrame will be forced to be 'sample_name'
    and will be cast to a string. Additionally rows that start with a '\t'
    character will be ignored and columns that are empty will be removed. Empty
    sample names will be removed from the DataFrame.

    The following table describes the data type per column that will be
    enforced in `fn`. Column names are case-insensitive but will be lowercased
    on addition to the database.

    +-----------------------+--------------+
    |      Column Name      |  Python Type |
    +=======================+==============+
    |           sample_name |          str |
    +-----------------------+--------------+
    |     physical_location |          str |
    +-----------------------+--------------+
    | has_physical_specimen |         bool |
    +-----------------------+--------------+
    |    has_extracted_data |         bool |
    +-----------------------+--------------+
    |           sample_type |          str |
    +-----------------------+--------------+
    |       host_subject_id |          str |
    +-----------------------+--------------+
    |           description |          str |
    +-----------------------+--------------+
    |              latitude |        float |
    +-----------------------+--------------+
    |             longitude |        float |
    +-----------------------+--------------+
    """
    # Load in file lines
    holdfile = None
    with open_file(fn) as f:
        holdfile = f.readlines()
    if not holdfile:
        raise ValueError('Empty file passed!')

    # Strip all values in the cells in the input file, if requested
    if strip_whitespace:
        for pos, line in enumerate(holdfile):
            holdfile[pos] = '\t'.join(d.strip(" \r\x0b\x0c")
                                      for d in line.split('\t'))

    # get and clean the controlled columns
    cols = holdfile[0].split('\t')
    controlled_cols = {'sample_name'}
    controlled_cols.update(CONTROLLED_COLS)
    holdfile[0] = '\t'.join(c.lower() if c.lower() in controlled_cols else c
                            for c in cols)
    # index_col:
    #   is set as False, otherwise it is cast as a float and we want a string
    # keep_default:
    #   is set as False, to avoid inferring empty/NA values with the defaults
    #   that Pandas has.
    # na_values:
    #   the values that should be considered as empty, in this case only empty
    #   strings.
    # converters:
    #   ensure that sample names are not converted into any other types but
    #   strings and remove any trailing spaces. Don't let pandas try to guess
    #   the dtype of the other columns, force them to be a str.
    # comment:
    #   using the tab character as "comment" we remove rows that are
    #   constituted only by delimiters i. e. empty rows.
    template = pd.read_csv(StringIO(''.join(holdfile)), sep='\t',
                           infer_datetime_format=True,
                           keep_default_na=False, na_values=[''],
                           parse_dates=True, index_col=False, comment='\t',
                           mangle_dupe_cols=False, converters={
                               'sample_name': lambda x: str(x).strip(),
                               # required_sample_info
                               'physical_location': str,
                               'sample_type': str,
                               # collection_timestamp is not added here
                               'host_subject_id': str,
                               'description': str,
                               # common_prep_info
                               'center_name': str,
                               'center_projct_name': str})

    # let pandas infer the dtypes of these columns, if the inference is
    # not correct, then we have to raise an error
    columns_to_dtype = [(['latitude', 'longitude'], (np.int, np.float),
                         'integer or decimal'),
                        (['has_physical_specimen', 'has_extracted_data'],
                         np.bool_, 'boolean')]
    for columns, c_dtype, english_desc in columns_to_dtype:
        for n in columns:
            if n in template.columns and not all([isinstance(val, c_dtype)
                                                  for val in template[n]]):
                raise QiitaDBColumnError("The '%s' column includes values "
                                         "that cannot be cast into a %s "
                                         "value " % (n, english_desc))

    initial_columns = set(template.columns)

    if 'sample_name' not in template.columns:
        raise QiitaDBColumnError("The 'sample_name' column is missing from "
                                 "your template, this file cannot be parsed.")

    # remove rows that have no sample identifier but that may have other data
    # in the rest of the columns
    template.dropna(subset=['sample_name'], how='all', inplace=True)

    # set the sample name as the index
    template.set_index('sample_name', inplace=True)

    # it is not uncommon to find templates that have empty columns
    template.dropna(how='all', axis=1, inplace=True)

    initial_columns.remove('sample_name')
    dropped_cols = initial_columns - set(template.columns)
    if dropped_cols:
        warnings.warn('The following column(s) were removed from the template '
                      'because all their values are empty: '
                      '%s' % ', '.join(dropped_cols), QiitaDBWarning)

    return template


def get_invalid_sample_names(sample_names):
    """Get a list of sample names that are not QIIME compliant

    Parameters
    ----------
    sample_names : iterable
        Iterable containing the sample names to check.

    Returns
    -------
    list
        List of str objects where each object is an invalid sample name.

    References
    ----------
    .. [1] QIIME File Types documentaiton:
    http://qiime.org/documentation/file_formats.html#mapping-file-overview.
    """

    # from the QIIME mapping file documentation
    valid = set(letters+digits+'.')
    inv = []

    for s in sample_names:
        if set(s) - valid:
            inv.append(s)

    return inv
