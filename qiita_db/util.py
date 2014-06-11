r"""
Util functions (:mod: `qiita_db.util`)
======================================

..currentmodule:: qiita_db.util

This module provides different util functions.

Methods
-------

<<<<<<< HEAD
from .exceptions import QiitaDBColumnError

=======
..autosummary::
    :toctree: generated/

    quote_column_name
    quote_data_value
    get_datatypes
    scrub_data
    exists_table
    exists_dynamic_table
    get_db_files_base_dir
    compute_checksum
    check_table_cols
    check_required_columns
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from binascii import crc32

from qiita_db.sql_connection import SQLConnectionHandler
from .exceptions import QiitaDBColumnError


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
    r"""Scrubs data fields of characters not allowed by PostgreSQL

    disallowed characters:
        '   ;

    Parameters
    ----------
    s : str
        The string to clean up

    Returns
    -------
    str
        The scrubbed string
    """
    ret = s.replace("'", "")
    ret = ret.replace(";", "")
    return ret


def check_required_columns(conn_handler, keys, table):
    """Makes sure all required columns in database table are in keys

    Parameters
    ----------
    conn_handler: SQLConnectionHandler object
        Previously opened connection to the database
    keys: iterable
        Holds the keys in the dictionary
    table: str
        name of the table to check required columns

    Raises
    ------
    QiitaDBColumnError
        If keys exist that are not in the table
    RuntimeError
        Unable to get columns from database
    """
    sql = ("SELECT is_nullable, column_name FROM information_schema.columns "
           "WHERE table_name = %s")
    cols = conn_handler.execute_fetchall(sql, (table, ))
    # Test needed because a user with certain permissions can query without
    # error but be unable to get the column names
    if len(cols) == 0:
        raise RuntimeError("Unable to fetch column names for table %s" % table)
    required = set(x[1] for x in cols if x[0] == 'NO')
    # remove the table id column as required
    required.remove("%s_id" % table)
    if len(required.difference(keys)) > 0:
        raise QiitaDBColumnError("Required keys missing: %s" %
                                 required.difference(keys))


def check_table_cols(conn_handler, keys, table):
    """Makes sure all keys correspond to column headers in a table

    Parameters
    ----------
    conn_handler: SQLConnectionHandler object
        Previously opened connection to the database
    keys: iterable
        Holds the keys in the dictionary
    table: str
        name of the table to check column names

    Raises
    ------
    QiitaDBColumnError
        If a key is found that is not in table columns
    RuntimeError
        Unable to get columns from database
    """
    sql = ("SELECT column_name FROM information_schema.columns WHERE "
           "table_name = %s")
    cols = [x[0] for x in conn_handler.execute_fetchall(sql, (table, ))]
    # Test needed because a user with certain permissions can query without
    # error but be unable to get the column names
    if len(cols) == 0:
        raise RuntimeError("Unable to fetch column names for table %s" % table)
    if len(set(keys).difference(cols)) > 0:
        raise QiitaDBColumnError("Non-database keys found: %s" %
                                 set(keys).difference(cols))


def exists_table(table, conn_handler):
    r"""Checks if `table` exists on the database connected through
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
    r"""Checks if the dynamic`table` exists on the database connected through
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


def get_db_files_base_dir(conn_handler=None):
    r"""Returns the path to the base directory of all db files

    Returns
    -------
    str
        The path to the base directory of all db files
    """
    conn_handler = (conn_handler if conn_handler is not None
                    else SQLConnectionHandler())
    return conn_handler.execute_fetchone(
        "SELECT base_data_dir FROM settings")[0]


def compute_checksum(filepath):
    r"""Returns the checksum of the file pointed by filepath

    Parameters
    ----------
    filepath : str
        The path to the file

    Returns
    -------
    int
        The file checksum
    """
    crc = None
    with open(filepath, "Ub") as f:
        # Go line by line so we don't need to load the entire file in memory
        for line in f:
            if crc is None:
                crc = crc32(line)
            else:
                crc = crc32(line, crc)
    # We need the & 0xffffffff in order to get the same numeric value across
    # all python versions and platforms
    return crc & 0xffffffff
