#!/usr/bin/env python
from __future__ import division

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


def exists_table(table, conn_handler):
    """Checks if `table` exists on the database connected through
    `conn_handler`

    Parameters
    ----------
    table : str
        The table name to check if exists
    conn_handler : SQLConnectionHandler
        The connection handler object connected to the DB
    """
    return conn_handler.execute_fetchone(
        "SELECT exists(SELECT * FROM information_schema.tables WHERE "
        "table_name=%s)", (table,))[0]


def exists_dynamic_table(table, prefix, suffix, conn_handler):
    """Checks if the dynamic`table` exists on the database connected through
    `conn_handler`, and its name starts with prefix and ends with suffix

    Parameters
    ----------
    table : str
        The table name to check if exists
    prefix : str
        The table name prefix
    suffix : str
        The table name suffix
    conn_handler : SQLConnectionHandler
        The connection handler object connected to the DB
    """
    return (table.startswith(prefix) and table.endswith(suffix) and
            exists_table(table, conn_handler))
