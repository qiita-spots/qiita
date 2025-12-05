# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
import warnings
from string import ascii_letters, digits

import numpy as np
import pandas as pd
from iteration_utilities import duplicates
from six import StringIO

import qiita_db as qdb


def prefix_sample_names_with_id(md_template, study_id):
    r"""prefix the sample_names in md_template with the study id

    Parameters
    ----------
    md_template : DataFrame
        The metadata template to modify
    study_id : int
        The study to which the metadata belongs to
    """
    # loop over the samples and prefix those that aren't prefixed
    sid = str(study_id)
    md_template["qiita_sample_name_with_id"] = pd.Series(
        [
            idx
            if idx.split(".", 1)[0] == sid and idx != sid
            else "%d.%s" % (study_id, idx)
            for idx in md_template.index
        ],
        index=md_template.index,
    )

    # get the rows that are going to change
    changes = len(
        md_template.index[md_template["qiita_sample_name_with_id"] != md_template.index]
    )
    if changes != 0 and changes != len(md_template.index):
        warnings.warn(
            "Some of the samples were already prefixed with the study id.",
            qdb.exceptions.QiitaDBWarning,
        )

    md_template.index = md_template.qiita_sample_name_with_id
    del md_template["qiita_sample_name_with_id"]
    # The original metadata template had the index column unnamed -> remove
    # the name of the index for consistency
    md_template.index.name = None


def load_template_to_dataframe(fn, index="sample_name"):
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

    While reading the file via pandas, it's possible that it will raise a
    'tokenizing' pd.errors.ParserError which is confusing for users; thus,
    rewriting the error with an explanation of what it means and how to fix.
    """
    # Load in file lines
    holdfile = None
    with qdb.util.open_file(fn, newline=None, encoding="utf8", errors="ignore") as f:
        holdfile = f.readlines()

    if not holdfile:
        raise ValueError("Empty file passed!")

    if index == "#SampleID":
        # We're going to parse a QIIME mapping file. We are going to first
        # parse it with the QIIME function so we can remove the comments
        # easily and make sure that QIIME will accept this as a mapping file
        data, headers, comments = _parse_mapping_file(holdfile)
        holdfile = ["%s\n" % "\t".join(d) for d in data]
        holdfile.insert(0, "%s\n" % "\t".join(headers))
        # The QIIME parser fixes the index and removes the #
        index = "SampleID"

    # Strip all values in the cells in the input file
    for pos, line in enumerate(holdfile):
        cols = line.split("\t")
        if pos == 0 and index != "SampleID":
            # get and clean the controlled columns
            ccols = {"sample_name"}
            ccols.update(qdb.metadata_template.constants.CONTROLLED_COLS)
            newcols = [
                c.lower().strip() if c.lower().strip() in ccols else c.strip()
                for c in cols
            ]

            # while we are here, let's check for duplicate columns headers
            ncols = set(newcols)
            if len(ncols) != len(newcols):
                if "" in ncols:
                    raise ValueError("Your file has empty columns headers.")
                raise qdb.exceptions.QiitaDBDuplicateHeaderError(
                    set(duplicates(newcols))
                )
        else:
            # .strip will remove odd chars, newlines, tabs and multiple
            # spaces but we need to read a new line at the end of the
            # line(+'\n')
            newcols = [d.strip(" \r\n") for d in cols]

        holdfile[pos] = "\t".join(newcols) + "\n"

    # index_col:
    #   is set as False, otherwise it is cast as a float and we want a string
    # keep_default:
    #   is set as False, to avoid inferring empty/NA values with the defaults
    #   that Pandas has.
    # comment:
    #   using the tab character as "comment" we remove rows that are
    #   constituted only by delimiters i. e. empty rows.
    try:
        template = pd.read_csv(
            StringIO("".join(holdfile)),
            sep="\t",
            dtype=str,
            encoding="utf-8",
            keep_default_na=False,
            index_col=False,
            comment="\t",
            converters={index: lambda x: str(x).strip()},
        )
    except pd.errors.ParserError as e:
        if "tokenizing" in str(e):
            msg = (
                "Your file has more columns with values than headers. To "
                "fix, make sure to delete any extra rows or columns; they "
                "might look empty because they have spaces. Then upload "
                "and try again."
            )
            raise RuntimeError(msg)
        else:
            raise e
    # remove newlines and tabs from fields
    template.replace(to_replace="[\t\n\r\x0b\x0c]+", value="", regex=True, inplace=True)
    # removing columns with empty values
    template.dropna(axis="columns", how="all", inplace=True)
    if template.empty:
        raise ValueError("The template is empty")

    initial_columns = set(template.columns)

    if index not in template.columns:
        raise qdb.exceptions.QiitaDBColumnError(
            "The '%s' column is missing from your template, this file cannot "
            "be parsed." % index
        )

    # remove rows that have no sample identifier but that may have other data
    # in the rest of the columns
    template.dropna(subset=[index], how="all", inplace=True)

    # set the sample name as the index
    template.set_index(index, inplace=True)

    # it is not uncommon to find templates that have empty columns so let's
    # find the columns that are all ''
    columns = np.where(np.all(template.applymap(lambda x: x == ""), axis=0))
    template.drop(template.columns[columns], axis=1, inplace=True)

    initial_columns.remove(index)
    dropped_cols = initial_columns - set(template.columns)
    if dropped_cols:
        warnings.warn(
            "The following column(s) were removed from the template because "
            "all their values are empty: %s" % ", ".join(dropped_cols),
            qdb.exceptions.QiitaDBWarning,
        )

    # removing 'sample-id' and 'sample_id' as per issue #2906
    sdrop = []
    if "sample-id" in template.columns:
        sdrop.append("sample-id")
    if "sample_id" in template.columns:
        sdrop.append("sample_id")
    if sdrop:
        template.drop(columns=sdrop, inplace=True)
        warnings.warn(
            "The following column(s) were removed from the template because "
            "they will cause conflicts with sample_name: %s" % ", ".join(sdrop),
            qdb.exceptions.QiitaDBWarning,
        )

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
    valid = set(ascii_letters + digits + ".")
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
    with qdb.util.open_file(fp, newline=None, errors="replace") as f:
        first_line = f.readline()
    if not first_line:
        return False

    first_col = first_line.split()[0]
    return first_col == "#SampleID"


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
                return x.replace('"', "")
        else:
            # remove quotes and spaces

            def strip_f(x):
                return x.replace('"', "").strip()
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

        if line.startswith("#"):
            line = line[1:]
            if not header:
                header = line.strip().split("\t")
            else:
                comments.append(line)
        else:
            # Will add empty string to empty fields
            tmp_line = list(map(strip_f, line.split("\t")))
            if len(tmp_line) < len(header):
                tmp_line.extend([""] * (len(header) - len(tmp_line)))
            mapping_data.append(tmp_line)
    if not header:
        raise qdb.exceptions.QiitaDBError("No header line was found in mapping file.")
    if not mapping_data:
        raise qdb.exceptions.QiitaDBError("No data found in mapping file.")

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


def get_qiime2_reserved_words():
    """Returns a list of the current reserved words in qiime2

    Returns
    -------
    set: str
        The reserved words
    """
    qiime2_reserved_column_names = [
        "feature id",
        "feature-id",
        "featureid",
        "id",
        "sample id",
        "sample-id",
        "sampleid",
    ]

    return set(qiime2_reserved_column_names)
