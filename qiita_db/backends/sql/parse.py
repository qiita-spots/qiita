__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from qiita_db.backends.sql.exceptions import QiitaBDSQLParseError


def parse_mapping_file_to_dicts(lines):
    """Parses a QIIME mapping file.

    Inputs:
        lines: Mapping file lines

    Returns:
        mapping: a dict of dicts representing the mapping file. Outer keys are
            sample names and inner keys are column headers.
        headers: A list of column headers
        datatypes The datatypes of the columns, automatically determined to be
            varchar, int, or float
    """
    # might as well do this to avoid attribute lookups
    isdigit = str.isdigit

    # Find first non-comment line, assume the previous line (i.e., the last
    # comment line at the top of the file) is the headers
    headers = []
    prev_line = ''
    for line in lines:
        if line.startswith('#'):
            prev_line = line
            continue
        else:
            headers = prev_line.strip().split('\t')[1:]
            num_columns = len(headers)
            break

    # if we get here and don't have headers, abort
    if not headers:
        raise QiitaBDSQLParseError("Empty mapping file! Aborting.")

    # seek back to the beginning of the file, and read in the data (skip
    # comment lines)
    lines.seek(0)
    mapping = {}
    for line in lines:
        if line.startswith('#'):
            continue
        elements = [e.strip() for e in line.split('\t')]
        sample_id, data = elements[0], elements[1:]
        data = dict(zip(headers, data))
        mapping[sample_id] = data

    # determine datatypes
    datatypes = []
    sample_ids = mapping.keys()
    for header in headers:
        column_data = [mapping[sample_id][header] for sample_id in sample_ids]

        if all([isdigit(c) for c in column_data]):
            datatype = 'int'
        elif all([isdigit(c.replace('.', '', 1)) for c in column_data]):
            datatype = 'float'
        else:
            datatype = 'varchar'

        datatypes.append(datatype)

    return mapping, headers, datatypes
