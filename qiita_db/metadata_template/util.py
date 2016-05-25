# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from collections import defaultdict
from future.utils import PY3, viewitems
from six import StringIO

import pandas as pd
import numpy as np
import warnings
from skbio.io.util import open_file
from skbio.util import find_duplicates

import qiita_db as qdb

if PY3:
    from string import ascii_letters as letters, digits
else:
    from string import letters, digits


def type_lookup(dtype):
    """Lookup function to transform from python type to SQL type

    Parameters
    ----------
    dtype : object
        The python type

    Returns
    -------
    str
        The SQL type
    """
    if dtype in [np.int8, np.int16, np.int32, np.int64]:
        return 'integer'
    elif dtype in [np.float16, np.float32, np.float64]:
        return 'float8'
    elif np.issubdtype(dtype, np.datetime64):
        return 'timestamp'
    elif dtype == np.bool:
        return 'bool'
    else:
        return 'varchar'


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
    return [type_lookup(dtype) for dtype in metadata_map.dtypes]


def cast_to_python(value):
    """Casts the value from numpy types to python types

    Parameters
    ----------
    value : object
        The value to cast

    Returns
    -------
    object
        The input value casted to a python type
    """
    if isinstance(value, np.generic):
        value = np.asscalar(value)
    return value


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
                      qdb.exceptions.QiitaDBWarning)
    else:
        # Create a new pandas series in which all the values are the study_id
        # and it is indexed as the metadata template
        study_ids = pd.Series([str(study_id)] * len(md_template.index),
                              index=md_template.index)
        # Create a new column on the metadata template that includes the
        # metadata template indexes prefixed with the study id
        md_template['sample_name_with_id'] = (study_ids + '.' +
                                              md_template.index.values)
        md_template.index = md_template.sample_name_with_id
        del md_template['sample_name_with_id']
        # The original metadata template had the index column unnamed - remove
        # the name of the index for consistency
        md_template.index.name = None


def load_template_to_dataframe(fn, strip_whitespace=True, index='sample_name'):
    """Load a sample/prep template or a QIIME mapping file into a data frame

    Parameters
    ----------
    fn : str or file-like object
        filename of the template to load, or an already open template file
    strip_whitespace : bool, optional
        Defaults to True. Whether or not to strip whitespace from values in the
        input file
    index : str, optional
        Defaults to 'sample_name'. The index to use in the loaded information

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
    QiitaDBWarning
        When columns are dropped because they have no content for any sample.
    QiitaDBError
        When non UTF-8 characters are found in the file.
    QiitaDBDuplicateHeaderError
        If duplicate columns are present in the template

    Notes
    -----
    The index attribute of the DataFrame will be forced to be 'sample_name'
    and will be cast to a string. Additionally rows that start with a '\t'
    character will be ignored and columns that are empty will be removed. Empty
    sample names will be removed from the DataFrame.

    Column names are case-insensitive but will be lowercased on addition to
    the database

    Everything in the DataFrame will be read and managed as string
    """
    # Load in file lines
    holdfile = None
    with open_file(fn, mode='U') as f:
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
    controlled_cols.update(qdb.metadata_template.constants.CONTROLLED_COLS)
    holdfile[0] = '\t'.join(c.lower() if c.lower() in controlled_cols else c
                            for c in cols)

    if index == "#SampleID":
        # We're going to parse a QIIME mapping file. We are going to first
        # parse it with the QIIME function so we can remove the comments
        # easily and make sure that QIIME will accept this as a mapping file
        data, headers, comments = _parse_mapping_file(holdfile)
        holdfile = ["%s\n" % '\t'.join(d) for d in data]
        holdfile.insert(0, "%s\n" % '\t'.join(headers))
        # The QIIME parser fixes the index and removes the #
        index = 'SampleID'

    # index_col:
    #   is set as False, otherwise it is cast as a float and we want a string
    # keep_default:
    #   is set as False, to avoid inferring empty/NA values with the defaults
    #   that Pandas has.
    # na_values:
    #   the values that should be considered as empty
    # true_values:
    #   the values that should be considered "True" for boolean columns
    # false_values:
    #   the values that should be considered "False" for boolean columns
    # comment:
    #   using the tab character as "comment" we remove rows that are
    #   constituted only by delimiters i. e. empty rows.
    try:
        template = pd.read_csv(
            StringIO(''.join(holdfile)),
            sep='\t',
            dtype=str,
            encoding='utf-8',
            infer_datetime_format=False,
            keep_default_na=False,
            index_col=False,
            comment='\t',
            mangle_dupe_cols=False,
            converters={index: lambda x: str(x).strip()})
    except UnicodeDecodeError:
        # Find row number and col number for utf-8 encoding errors
        headers = holdfile[0].strip().split('\t')
        errors = defaultdict(list)
        for row, line in enumerate(holdfile, 1):
            for col, cell in enumerate(line.split('\t')):
                try:
                    cell.encode('utf-8')
                except UnicodeError:
                    errors[headers[col]].append(row)
        lines = ['%s: row(s) %s' % (header, ', '.join(map(str, rows)))
                 for header, rows in viewitems(errors)]
        raise qdb.exceptions.QiitaDBError(
            'Non UTF-8 characters found in columns:\n' + '\n'.join(lines))

    # Check that we don't have duplicate columns
    if len(set(template.columns)) != len(template.columns):
        raise qdb.exceptions.QiitaDBDuplicateHeaderError(
            find_duplicates(template.columns))

    initial_columns = set(template.columns)

    if index not in template.columns:
        raise qdb.exceptions.QiitaDBColumnError(
            "The '%s' column is missing from your template, this file cannot "
            "be parsed." % index)

    # remove rows that have no sample identifier but that may have other data
    # in the rest of the columns
    template.dropna(subset=[index], how='all', inplace=True)

    # set the sample name as the index
    template.set_index(index, inplace=True)

    # it is not uncommon to find templates that have empty columns so let's
    # find the columns that are all ''
    columns = np.where(np.all(template.applymap(lambda x: x == ''), axis=0))
    template.drop(template.columns[columns], axis=1, inplace=True)

    initial_columns.remove(index)
    dropped_cols = initial_columns - set(template.columns)
    if dropped_cols:
        warnings.warn(
            'The following column(s) were removed from the template because '
            'all their values are empty: %s'
            % ', '.join(dropped_cols), qdb.exceptions.QiitaDBWarning)

    # Pandas represents data with np.nan rather than Nones, change it to None
    # because psycopg2 knows that a None is a Null in SQL, while it doesn't
    # know what to do with NaN
    template = template.where((pd.notnull(template)), None)

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


def looks_like_qiime_mapping_file(fp):
    """Checks if the file looks like a QIIME mapping file

    Parameters
    ----------
    fp : str or file-like object
        filepath to check if it looks like a QIIME mapping file

    Returns
    -------
    bool
        True if fp looks like a QIIME mapping file, false otherwise.


    Notes
    -----
    This is not doing a validation of the QIIME mapping file. It simply checks
    the first line in the file and it returns true if the line starts with
    '#SampleID', since a sample/prep template will start with 'sample_name' or
    some other different column.
    """
    first_line = None
    with open_file(fp, mode='U') as f:
        first_line = f.readline()
    if not first_line:
        return False

    first_col = first_line.split()[0]
    return first_col == '#SampleID'


def _parse_mapping_file(lines, strip_quotes=True, suppress_stripping=False):
    """Parser for map file that relates samples to metadata.

    Format: header line with fields
            optionally other comment lines starting with #
            tab-delimited fields

    Parameters
    ----------
    lines : iterable of str
        The contents of the QIIME mapping file
    strip_quotes : bool, optional
        Defaults to true. If true, quotes are removed from the data
    suppress_stripping : bool, optional
        Defaults to false. If true, spaces are not stripped

    Returns
    -------
    list of lists, list of str, list of str
        The data in the mapping file, the headers and the comments

    Raises
    ------
    QiitaDBError
        If there is any error parsing the mapping file

    Notes
    -----
    This code has been ported from QIIME.
    """
    if strip_quotes:
        if suppress_stripping:
            # remove quotes but not spaces

            def strip_f(x):
                return x.replace('"', '')
        else:
            # remove quotes and spaces

            def strip_f(x):
                return x.replace('"', '').strip()
    else:
        if suppress_stripping:
            # don't remove quotes or spaces

            def strip_f(x):
                return x
        else:
            # remove spaces but not quotes

            def strip_f(x):
                return x.strip()

    # Create lists to store the results
    mapping_data = []
    header = []
    comments = []

    # Begin iterating over lines
    for line in lines:
        line = strip_f(line)
        if not line or (suppress_stripping and not line.strip()):
            # skip blank lines when not stripping lines
            continue

        if line.startswith('#'):
            line = line[1:]
            if not header:
                header = line.strip().split('\t')
            else:
                comments.append(line)
        else:
            # Will add empty string to empty fields
            tmp_line = map(strip_f, line.split('\t'))
            if len(tmp_line) < len(header):
                tmp_line.extend([''] * (len(header) - len(tmp_line)))
            mapping_data.append(tmp_line)
    if not header:
        raise qdb.exceptions.QiitaDBError(
            "No header line was found in mapping file.")
    if not mapping_data:
        raise qdb.exceptions.QiitaDBError(
            "No data found in mapping file.")

    return mapping_data, header, comments
