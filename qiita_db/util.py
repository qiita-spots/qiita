r"""
Util functions (:mod: `qiita_db.util`)
======================================

..currentmodule:: qiita_db.util

This module provides different util functions.

Methods
-------

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
    insert_filepaths
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
from future.builtins import zip
from random import choice
from string import ascii_letters, digits, punctuation
from binascii import crc32
from bcrypt import hashpw, gensalt
from functools import partial
from os.path import join, basename
from shutil import copy

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .exceptions import QiitaDBColumnError
from qiita_db.sql_connection import SQLConnectionHandler


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


def create_rand_string(length, punct=True):
        """Returns a string of random ascii characters

        Parameters
        ----------
        length: int
            Length of string to return
        punct: bool, optional
            Include punctiation as well as letters and numbers. Default True.
        """
        chars = ''.join((ascii_letters, digits))
        if punct:
            chars = ''.join((chars, punctuation))
        return ''.join(choice(chars) for i in range(length))


def hash_password(password, hashedpw=None):
        """ Hashes password

        Parameters
        ----------
        password: str
            Plaintext password
        hashedpw: str, optional
            Previously hashed password for bcrypt to pull salt from. If not
            given, salt generated before hash

        Returns
        -------
        str
            Hashed password

        Notes
        -----
        Relies on bcrypt library to hash passwords, which stores the salt as
        part of the hashed password. Don't need to actually store the salt
        because of this.
        """
        # all the encode/decode as a python 3 workaround for bcrypt
        if hashedpw is None:
            hashedpw = gensalt()
        else:
            hashedpw = hashedpw.encode('utf-8')
        password = password.encode('utf-8')
        output = hashpw(password, hashedpw)
        if isinstance(output, bytes):
            output = output.decode("utf-8")
        return output


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


def get_work_base_dir(conn_handler=None):
    r"""Returns the path to the base directory of all db files

    Returns
    -------
    str
        The path to the base directory of all db files
    """
    conn_handler = (conn_handler if conn_handler is not None
                    else SQLConnectionHandler())
    return conn_handler.execute_fetchone(
        "SELECT base_work_dir FROM settings")[0]


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


def insert_filepaths(filepaths, obj_id, table, filepath_table, conn_handler):
        r"""Inserts `filepaths` in the DB connected with `conn_handler`. Since
        the files live outside the database, the directory in which the files
        lives is controlled by the database, so it copies the filepaths from
        its original location to the controlled directory.

        Parameters
        ----------
        filepaths : iterable of tuples (str, int)
            The list of paths to the raw files and its filepath type identifier
        obj_id : int
            Id of the object calling the functions
        table : str
            Table that holds the file data
        filepath_table : str
            Table that holds the filepath information
        conn_handler : SQLConnectionHandler
            The connection handler object connected to the DB

        Returns
        -------
        list
            The filepath_id in the database for each added filepath
        """
        # Get the base directory in which the type of data is stored
        base_data_dir = join(get_db_files_base_dir(), table)
        # Generate the new fileapths. Format: DataId_OriginalName
        # Keeping the original name is useful for checking if the RawData
        # alrady exists on the DB
        db_path = partial(join, base_data_dir)
        new_filepaths = [
            (db_path("%s_%s" % (obj_id, basename(path))), id)
            for path, id in filepaths]
        # Copy the original files to the controlled DB directory
        for old_fp, new_fp in zip(filepaths, new_filepaths):
            copy(old_fp[0], new_fp[0])

        paths_w_checksum = [(path, id, compute_checksum(path))
                            for path, id in new_filepaths]

        # Create the list of SQL values to add
        values = ["('%s', %s, '%s', %s)" % (scrub_data(path), id, checksum, 1)
                  for path, id, checksum in paths_w_checksum]
        # Insert all the filepaths at once and get the filepath_id back
        ids = conn_handler.execute_fetchall(
            "INSERT INTO qiita.{0} (filepath, filepath_type_id, checksum, "
            "checksum_algorithm_id) VALUES {1} "
            "RETURNING filepath_id".format(filepath_table,
                                           ', '.join(values)))

        # we will receive a list of lists with a single element on it (the id),
        # transform it to a list of ids
        return [id[0] for id in ids]


def convert_to_id(value, table, conn_handler=None):
        """Converts a string value to it's corresponding table identifier

        Parameters
        ----------
        value : str
            The string value to convert
        table : str
            The table that has the conversion
        conn_handler : SQLConnectionHandler, optional
            The sql connection object

        Returns
        -------
        int
            The id correspinding to the string

        Raises
        ------
        IncompetentQiitaDeveloperError
            The passed string has no associated id
        """
        conn_handler = conn_handler if conn_handler else SQLConnectionHandler()
        _id = conn_handler.execute_fetchone(
            "SELECT {0}_id FROM qiita.{0} WHERE {0} = %s".format(table),
            (value, ))
        if _id is None:
            raise IncompetentQiitaDeveloperError("%s not valid for table %s"
                                                 % (value, table))
        return _id[0]
