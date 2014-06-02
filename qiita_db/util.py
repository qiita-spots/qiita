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
            datatypes.append('float8')
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
    cols = [x[0] for x in conn_handler.execute_fetchall(sql, (table, ))]
    if len(cols) == 0:
        raise RuntimeError("Unable to fetch column names for table %s" % table)
    if len(set(keys).difference(cols)) > 0:
        raise QiitaDBExecutionError("Non-database keys found: %s" %
                                    set(keys).difference(cols))
