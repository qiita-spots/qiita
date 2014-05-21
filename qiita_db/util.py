#!/usr/bin/env python
from __future__ import division
from os.path import abspath, dirname, join

from .exceptions import QiitaDBExecutionError

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


def quote_column_name(c):
    """Lowercases the string and puts double quotes around it
    """
    return '"%s"' % c.lower()


def quote_data_value(c):
    """Puts single quotes around a string"""
    return "'%s'" % c


def get_datatypes(metadata_map):
    """"""
    isdigit = str.isdigit
    datatypes = []
    for header in metadata_map.CategoryNames:
        column_data = [metadata_map.getCategoryValue(sample_id, header)
                       for sample_id in metadata_map.SampleIds]

        if all([isdigit(c) for c in column_data]):
            datatypes.append('int')
        elif all([isdigit(c.replace('.', '', 1)) for c in column_data]):
            datatypes.append('float')
        else:
            datatypes.append('varchar')

    return datatypes


def scrub_data(s):
    """Scrubs data fields of characters not allowed by PostgreSQL

    disallowed characters:
        '   ;
    """
    ret = s.replace("'", "")
    ret = ret.replace(";", "")
    return ret


def check_required(keys, required):
    """Makes sure all required columns are in a list

    Parameters
    ----------
    keys: iterable
        list, set, or other iterable holding the keys in the dictionary
    required: set
        set of column names required for a table

    Raises
    ------
    QiitaDBExecutionError
        If not all required keys are in keys
    """
    if not isinstance(required, set):
        raise ValueError("required keys list must be set type object")
    if len(required.difference(set(keys))) > 0:
            raise RuntimeError("Required keys missing: %s" %
                                        required.difference(set(keys)))


def check_table_cols(conn_handler, keys, table):
    """Makes sure all keys correspond to coumn headers in a table

    Parameters
    ----------
    conn_handler: SQLConnectionHandler object
        Previously opened conection to the database
    keys: iterable
        list, set, or other iterable holding the keys in the dictionary
    table: str
        name of the table to check column names

    Raises
    ------
    QiitaDBExecutionError
        If keys exist that are not in the table
    """
    sql = ("SELECT column_name FROM information_schema.columns WHERE "
           "table_name = %s")
    cols = conn_handler.execute_fetchone(sql, (table, ))
    if len(cols) == 0:
        raise RuntimeError("Unable to fetch column names for table %s" % table)
    if len(set(keys).difference(cols)) > 0:
        raise QiitaDBExecutionError("Non-database keys found: %s" %
                                    set(keys).difference(cols))



def populate_test_db(conn_handler, schemapath=None, initpath=None,
                     testdatapath=None):
    """Populates the test database using the file initialzie_test.sql

    Parameters
    ----------
    conn_handler: SQLConnectionHandler object
        Previously opened conection to the database
    schemapath: str, optional
        Path to the test database schema sql file (default qiita.sql)
    testdatapath: str, optional
        Path to the test database setup sql file (default initialize.sql)
    testdatapath: str, optional
        Path to the test database data sql file (default initialize_test.sql)
    """
    # make sure we are on test database
    if not conn_handler.execute_fetchone("SELECT test FROM settings")[0]:
        raise IOError("Trying to test using non-test database!")

    if testdatapath is None:
        path = dirname(abspath(__file__))
        testdatapath = join((path, "setup/initialize_test.sql"))
    if initpath is None:
        path = dirname(abspath(__file__))
        initpath = join((path, "setup/initialize.sql"))
    if schemapath is None:
        path = dirname(abspath(__file__))
        schemapath = join((path, "setup/qiita.sql"))
    # build schema, then populate it
    with open(schemapath) as fin:
        conn_handler.execute(fin.read())
    with open(initpath) as fin:
        conn_handler.execute(fin.read())
    with open(testdatapath) as fin:
        conn_handler.execute(fin.read())



def teardown_qiita_schema(conn_handler):
    """removes qiita schema from test database

    Parameters
    ----------
    conn_handler: SQLConnectionHandler object
        Previously opened conection to the database
    """
    # make sure we are on test database
    if not conn_handler.execute_fetchone("SELECT test FROM settings")[0]:
        raise IOError("Trying to test using non-test database!")
    conn_handler.execute("DROP SCHEMA qiita CASCADE")
