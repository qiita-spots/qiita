#!/usr/bin/env python

from os.path import exists
from re import search
from itertools import izip

from argparse import ArgumentParser
from psycopg2 import connect, DataError, ProgrammingError

parser = ArgumentParser()
parser.add_argument(
    '-m',
    '--mapping_file',
    type=str,
    help=("The path to the mapping file to be added to the database"),
    required=True
)

parser.add_argument(
    '-d',
    '--clear_tables',
    action='store_true',
    help=("Deletes all rows from column_tables for this study, and drops the "
          "study's table")
)

parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help=("Prints information to stdout during load.")
)

def scrub_data(s):
    """Scrubs data fields of characters not allowed by PostgreSQL

    disallowed characters:
        '
    """
    ret = s.replace("'", "")
    return ret

def quote_column_name(c):
    """Puts double quotes around a string
    """
    return '"%s"' % c.lower()

def quote_data_value(c):
    """Puts single quotes around a string
    """
    return "'%s'" % c

def str_or_none(value):
    """Returns a string version of the input, or None

    If there is no value (e.g., empty string), or the value is 'None',
    returns None.
    """
    if not value or value == 'None':
        return None

    return str(value)

def int_or_none(value):
    """Returns a int version of the input, or None

    If there is no value (e.g., empty string), or the value is 'None',
    returns None.
    """
    if not value or value == 'None':
        return None

    return int(value)

def float_or_none(value):
    """Returns a float version of the input, or None

    If there is no value (e.g., empty string), or the value is 'None',
    returns None.
    """
    if not value or value == 'None':
        return None

    return float(value)

def parse_mapping_file_to_dicts(mapping_file):
    """Parses a QIIME mapping file.

    Returns:
        - a dict of dicts representing the mapping file. Outer keys are
          sample names and inner keys are column headers.
        - A list of column headers
        - The datatypes of the columns, automatically determined to be varchar,
          int, or float
    """
    # Find first non-comment line, assume the previous line (i.e., the last
    # comment line at the top of the file) is the headers
    headers = []
    lastline = ''
    for line in mapping_file:
        if line.startswith('#'):
            lastline = line
            continue
        else:
            headers = lastline.strip().split('\t')[1:]
            num_columns = len(headers)
            break

    # if we get here and don't have headers, abort
    if not headers:
        raise IOError("Empty mapping file! Aborting.")

    # seek back to the beginning of the file, and read in the data (skip
    # comment lines)
    mapping_file.seek(0)
    mapping = {}
    for line in mapping_file:
        if line.startswith('#'):
            continue
        elements = line.strip().split('\t')
        sample_id, data = elements[0], elements[1:]
        data = dict(zip(headers, data))
        mapping[sample_id] = data

    # determine datatypes
    types = []
    sample_ids = mapping.keys()
    for header in headers:
        column_data = [mapping[sample_id][header] for sample_id in sample_ids]

        # default type is varchar
        datatype = map(str_or_none, column_data)
        datatype = 'varchar'

        # check of all values in the column can be converted to either a float
        # or an int
        try:
            datatype = map(float_or_none, column_data)
            datatype = 'float'
        except ValueError:
            pass

        try:
            datatype = map(int_or_none, column_data)
            datatype = 'int'
        except ValueError:
            pass

        types.append(datatype)

    return mapping, headers, types

def main():
    args = parser.parse_args()
    mapping_fp = args.mapping_file
    clear = args.clear_tables
    verbose = args.verbose

    if not exists(mapping_fp):
        raise IOError("Could not find file: %s" % mapping_fp)

    # Pull the study ID from the mapping file name
    study_id = search('study_(\d+)_mapping_file.txt', mapping_fp)
    if study_id:
        study_id = study_id.group(1)
    else:
        raise IOError("Could not parse study id from filename: %s" %
                      mapping_fp)

    if verbose:
        print "Connecting to database..."

    conn = connect(user='adro2179', database='qiime_md')
    cur = conn.cursor()

    if verbose:
        print "Connected!"

    # if the clear_tables (-d) flag is passed, drop the study's table and
    # delete the rows for that table from the column_tables table
    if clear:
        if verbose:
            print "dropping table study_%s" % study_id
        drop_sql = 'drop table study_%s' % study_id
        try:
            cur.execute(drop_sql)
            if verbose:
                print "Dropped table!"
        except ProgrammingError:
            # The table did not already exist, but that's okay, just skip
            if verbose:
                print "Table did not exist, skipping this step"

        conn.commit()

        if verbose:
            print "Deleting rows from column_tables for study %s..." % study_id
        delete_sql = ("delete from column_tables where "
                      "table_name = 'study_%s'" % study_id)
        cur.execute(delete_sql)
        if verbose:
            print "Deleted!"

        conn.commit()

    mapping, headers, datatypes = \
        parse_mapping_file_to_dicts(open(mapping_fp, 'U'))

    sql_safe_column_names = map(quote_column_name, headers)

    # we don't know what size varchars to use a priori, so we have to determine
    # this information for each column
    sample_ids = mapping.keys()
    column_lengths = []
    for header in headers:
        lengths = [len(mapping[sample_id][header]) for sample_id in sample_ids]

        if lengths:
            column_lengths.append(int(max(lengths) * 1.25))
        else:
            column_lengths.append(255)

    # create a table for the study
    if verbose:
        print "Creating table study_%s..." % study_id
    create_table_sql = 'create table study_%s (SampleID varchar(256), ' % \
        study_id

    columns = []
    for column_name, column_length, datatype in izip(sql_safe_column_names,
            column_lengths, datatypes):
        if datatype == 'varchar':
            columns.append('%s varchar(%d)' % (column_name, column_length))
        elif datatype == 'int':
            columns.append('%s int' % column_name)
        elif datatype == 'float':
            columns.append('%s float' % column_name)

    columns = ', '.join(columns)
    create_table_sql  += columns + ')'
    cur.execute(create_table_sql)
    #print create_table_sql
    conn.commit()
    if verbose:
        print "Created!"

    # add rows to the column_tables table
    column_tables_sql_template = ("insert into column_tables (column_name, "
                                  "table_name, datatype) values (%s, ")
    column_tables_sql_template += "'study_%s', " % study_id
    column_tables_sql_template += "'%s')"

    if verbose:
        print "Adding rows to column_tables..."
    for column_name, datatype in izip(map(quote_data_value, headers),
            datatypes):
        cur.execute(column_tables_sql_template % (column_name, datatype))
        #print column_tables_sql_template % (column_name, datatype)
    conn.commit()
    if verbose:
        print "Added!"

    # add rows into the study table
    if verbose:
        print "Inserting rows into table study_%s..." % study_id
    insert_sql_template = 'insert into study_%s (sampleid, ' % study_id
    columns = ', '.join(sql_safe_column_names)
    insert_sql_template += columns + ') values (%s)'

    for sample_id, data in mapping.iteritems():
        values = [quote_data_value(scrub_data(sample_id))]
        values += [quote_data_value(scrub_data(data[header]))
                   for header in headers]

        values = ', '.join(values)
        values = values.replace(", 'None'", ", null")

        cur.execute(insert_sql_template % values)
        #print insert_sql_template % values

    if verbose:
        print "Inserted rows!"

    conn.commit()
    conn.close()
    if verbose:
        print "Database connection closed"

if __name__ == '__main__':
    main()
