# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from future.utils import PY3, viewitems
from six import StringIO
from collections import defaultdict

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


def load_template_to_dataframe(fn, index='sample_name'):
    """Load a sample/prep template or a QIIME mapping file into a data frame

    Parameters
    ----------
    fn : str or file-like object
        filename of the template to load, or an already open template file
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
        errors = defaultdict(list)
        holdfile = f.readlines()
        # here we are checking for non UTF-8 chars
        for row, line in enumerate(holdfile):
            for col, block in enumerate(line.split('\t')):
                try:
                    tblock = block.encode('utf-8')
                except UnicodeDecodeError:
                    tblock = unicode(block, errors='replace')
                    tblock = tblock.replace(u'\ufffd', '&#128062;')
                    errors[tblock].append('(%d, %d)' % (row, col))
        if bool(errors):
            raise ValueError(
                "There are invalid (non UTF-8) characters in your information "
                "file. The offending fields and their location (row, column) "
                "are listed below, invalid characters are represented using "
                "&#128062;: %s" % '; '.join(
                    ['"%s" = %s' % (k, ', '.join(v))
                     for k, v in viewitems(errors)]))

    if not holdfile:
        raise ValueError('Empty file passed!')

    if index == "#SampleID":
        # We're going to parse a QIIME mapping file. We are going to first
        # parse it with the QIIME function so we can remove the comments
        # easily and make sure that QIIME will accept this as a mapping file
        data, headers, comments = _parse_mapping_file(holdfile)
        holdfile = ["%s\n" % '\t'.join(d) for d in data]
        holdfile.insert(0, "%s\n" % '\t'.join(headers))
        # The QIIME parser fixes the index and removes the #
        index = 'SampleID'

    # Strip all values in the cells in the input file
    for pos, line in enumerate(holdfile):
        cols = line.split('\t')
        if pos == 0 and index != 'SampleID':
            # get and clean the controlled columns
            ccols = {'sample_name'}
            ccols.update(qdb.metadata_template.constants.CONTROLLED_COLS)
            newcols = [
                c.lower().strip() if c.lower().strip() in ccols
                else c.strip()
                for c in cols]

            # while we are here, let's check for duplicate columns headers
            if len(set(newcols)) != len(newcols):
                raise qdb.exceptions.QiitaDBDuplicateHeaderError(
                    find_duplicates(newcols))
        else:
            # .strip will remove odd chars, newlines, tabs and multiple
            # spaces but we need to read a new line at the end of the
            # line(+'\n')
            newcols = [d.strip(" \r\n") for d in cols]

        holdfile[pos] = '\t'.join(newcols) + '\n'

    # index_col:
    #   is set as False, otherwise it is cast as a float and we want a string
    # keep_default:
    #   is set as False, to avoid inferring empty/NA values with the defaults
    #   that Pandas has.
    # comment:
    #   using the tab character as "comment" we remove rows that are
    #   constituted only by delimiters i. e. empty rows.
    template = pd.read_csv(
        StringIO(''.join(holdfile)),
        sep='\t',
        dtype=str,
        encoding='utf-8',
        infer_datetime_format=False,
        keep_default_na=False,
        index_col=False,
        comment='\t',
        converters={index: lambda x: str(x).strip()})
    # remove newlines and tabs from fields
    template.replace(to_replace='[\t\n\r\x0b\x0c]+', value='',
                     regex=True, inplace=True)

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


def validate_invalid_column_names(column_names):
    """Validate a list of column names that are not SQL compliant

    Parameters
    ----------
    column_names : iterable
        Iterable containing the column names to check.

    Raises
    ------
    QiitaDBColumnError
        If column_name is in get_pgsql_reserved_words or contains invalid
        chars or is within the forbidden_values

    References
    ----------
    .. [1] postgresql SQL-SYNTAX-IDENTIFIERS: https://goo.gl/EF0cUV.
    """
    column_names = set(column_names)

    # testing for specific column names that are not included in the other
    # tests.
    forbidden_values = {
        # https://github.com/biocore/qiita/issues/2026
        'sampleid',
        # https://github.com/biocore/qiita/issues/1866
        'qiita_study_id',
        'qiita_prep_id'
    }
    forbidden = forbidden_values & column_names

    # pgsql reserved words
    pgsql_reserved = (
        qdb.metadata_template.util.get_pgsql_reserved_words() & column_names)

    # invalid letters in headers
    valid_initial_char = letters
    valid_rest = set(letters+digits+'_')
    invalid = []
    for s in column_names:
        if s[0] not in valid_initial_char:
            invalid.append(s)
        elif set(s) - valid_rest:
            invalid.append(s)

    error = []
    if pgsql_reserved:
        error.append(
            "The following column names in the template contain PgSQL "
            "reserved words: %s." % ", ".join(pgsql_reserved))
    if invalid:
        error.append(
            "The following column names in the template contain invalid "
            "chars: %s." % ", ".join(invalid))
    if forbidden:
        error.append(
            "The following column names in the template contain invalid "
            "values: %s." % ", ".join(forbidden))

    if error:
        raise qdb.exceptions.QiitaDBColumnError(
            "%s\nYou need to modify them." % '\n'.join(error))


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
    with open_file(fp, mode='r') as f:
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


def get_pgsql_reserved_words():
    """Returns a list of the current reserved words in pgsql

    Returns
    -------
    set: str
        The reserved words
    """
    with qdb.sql_connection.TRN:
        sql = "SELECT word FROM pg_get_keywords() WHERE catcode = 'R';"
        qdb.sql_connection.TRN.add(sql)
        return set(qdb.sql_connection.TRN.execute_fetchflatten())
