#!/usr/bin/env python
from __future__ import division

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from itertools import izip
from qiita_db.backends.sql.exceptions import QiitaDBSQLExecutionError
from qiita_db.backends.sql.utils import (get_postgres_cursor, sql_execute,
                                         sql_executemany)


def scrub_data(s):
    """Scrubs data fields of characters not allowed by PostgreSQL

    disallowed characters:
        '
    """
    ret = s.replace("'", "")
    return ret


def quote_column_name(c):
    """Lowercases the string and puts double quotes around it
    """
    return '"%s"' % c.lower()


def quote_data_value(c):
    """Puts single quotes around a string"""
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


def add_mapping_file(study_id, mapping, headers, datatypes, clear_tables):
    """ Adds the mapping file to the SQL database

    Inputs:
        study_id: study id
        mapping: a dict of dicts representing the mapping file. Outer keys are
            sample names and inner keys are column headers.
        headers: a list of column headers
        datatypes: The datatypes of the columns, automatically determined to
            be varchar, int, or float
        clear_tables: if true, drop the study's table and delete the rows for
            that table from the column_tables table
    """
    # Get the table name
    table_name = "study_%s" % study_id

    # Get the postgres cursor to execute the queries
    cur = get_postgres_cursor()

    # if clear_tables is true, drop the study's table and delete the rows for
    # that table from the column_tables table
    if clear_tables:
        # Dropping table
        try:
            sql_execute(cur, 'drop table %s' % table_name, None)
        except QiitaDBSQLExecutionError:
            # The table did not already exist, but that's okay, just skip
            pass

        # Deleting rows from column_tables for the study
        # Do not need try/except here because the query should never fail;
        # even when there are no rows for this study, the query will
        # do nothing but complete successfully
        sql_execute(cur, "delete from column_tables where table_name = %s",
                    (table_name,))

    # Get the columns names in SQL safe
    sql_safe_column_names = [quote_column_name(h) for h in headers]

    # Get the column names paired with its datatype for SQL
    columns = []
    for column_name, datatype in izip(sql_safe_column_names, datatypes):
        columns.append('%s %s' % (column_name, datatype))
    # Get the columns in a comma-separated string
    columns = ", ".join(columns)
    # Create a table for the study
    sql_execute(cur, "create table %s (sampleid varchar, %s)" %
                     (table_name, columns), None)

    # Might as well do this to avoid the attribute lookup... probably not
    # a huge amount of speedup, but I'm never using any other kind of "lower"
    # or "isdigit" function...
    lower = str.lower
    # Add rows to the column_tables table
    lc_table_name = lower(table_name)
    quoted_lc_table_name = quote_data_value(lc_table_name)
    column_tables_sql_template = ("insert into column_tables (column_name, "
                                  "table_name, datatype) values (%s, " +
                                  quoted_lc_table_name+", %s)")
    lc_headers = [lower(h) for h in headers]
    quoted_lc_headers = [quote_data_value(h) for h in lc_headers]
    sql_args_list = [(column_name, datatype) for column_name, datatype in
                     izip(quoted_lc_headers, datatypes)]
    sql_executemany(cur, column_tables_sql_template, sql_args_list)

    # Add rows into the study table
    columns = ', '.join(sql_safe_column_names)
    insert_sql_template = ('insert into '+table_name+' (sampleid, ' +
                           columns+') values (%s)')

    sql_args_list = []
    for sample_id, data in mapping.iteritems():
        values = [quote_data_value(scrub_data(sample_id))]
        values += [quote_data_value(scrub_data(data[header]))
                   for header in headers]

        values = ', '.join(values)

        # Replace 'None' with null. This might be dangerous if a mapping file
        # actually has None as a valid data value!
        values = values.replace(", 'None'", ", null")
        sql_execute(cur, insert_sql_template % values, None)

    cur.close()
