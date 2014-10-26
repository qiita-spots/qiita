r"""
Util functions (:mod: `qiita_db.util`)
======================================

..currentmodule:: qiita_db.util

This module provides different util functions.

Methods
-------

..autosummary::
    :toctree: generated/

    quote_data_value
    scrub_data
    exists_table
    exists_dynamic_table
    get_db_files_base_dir
    compute_checksum
    insert_filepaths
    check_table_cols
    check_required_columns
    convert_from_id
    convert_to_id
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
from os.path import join, basename, isdir, relpath
from os import walk
from shutil import move
from json import dumps

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.qiita_settings import qiita_config
from .exceptions import QiitaDBColumnError
from .sql_connection import SQLConnectionHandler


def params_dict_to_json(options):
    """Convert a dict of parameter key-value pairs to JSON string

    Parameters
    ----------
    options : dict
        The dict of options
    """
    return dumps(options, sort_keys=True, separators=(',', ':'))


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


def typecast_string(string):
    """Converts a string to a number if possible

    Parameters
    ----------
    string : str
        String to evaluate

    Returns
    -------
    float, int, or str
        Re-typed information from string

    Notes
    -----
    The function first tries to convert to an int. If that fails, it tries to
    convert to a float. If that fails it returns the original string.
    """
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return string


def get_filetypes(key='type'):
    """Gets the list of possible filetypes from the filetype table

    Parameters
    ----------
    key : {'type', 'filetype_id'}, optional
        Defaults to "type". Determines the format of the returned dict.

    Returns
    -------
    dict
        If `key` is "type", dict is of the form {type: filetype_id}
        If `key` is "filetype_id", dict is of the form {filetype_id: type}
    """
    con = SQLConnectionHandler()
    if key == 'type':
        cols = 'type, filetype_id'
    elif key == 'filetype_id':
        cols = 'filetype_id, type'
    else:
        raise QiitaDBColumnError("Unknown key. Pass either 'type' or "
                                 "'filetype_id'.")
    sql = 'select {} from qiita.filetype'.format(cols)
    return dict(con.execute_fetchall(sql))


def get_filepath_types(key='filepath_type'):
    """Gets the list of possible filepath types from the filetype table

    Parameters
    ----------
    key : {'filepath_type', 'filepath_type_id'}, optional
        Defaults to "filepath_type". Determines the format of the returned
        dict.

    Returns
    -------
    dict
        - If `key` is "filepath_type", dict is of the form
          {filepath_type: filepath_type_id}
        - If `key` is "filepath_type_id", dict is of the form
          {filepath_type_id: filepath_type}
    """
    con = SQLConnectionHandler()
    if key == 'filepath_type':
        cols = 'filepath_type, filepath_type_id'
    elif key == 'filepath_type_id':
        cols = 'filepath_type_id, filepath_type'
    else:
        raise QiitaDBColumnError("Unknown key. Pass either 'filepath_type' or "
                                 "'filepath_type_id'.")
    sql = 'select {} from qiita.filepath_type'.format(cols)
    return dict(con.execute_fetchall(sql))


def get_data_types(key='data_type'):
    """Gets the list of possible data types from the data_type table

    Parameters
    ----------
    key : {'data_type', 'data_type_id'}, optional
        Defaults to "data_type". Determines the format of the returned dict.

    Returns
    -------
    dict
        - If `key` is "data_type", dict is of the form
          {data_type: data_type_id}
        - If `key` is "data_type_id", dict is of the form
          {data_type_id: data_type}
    """
    con = SQLConnectionHandler()
    if key == 'data_type':
        cols = 'data_type, data_type_id'
    elif key == 'data_type_id':
        cols = 'data_type_id, data_type'
    else:
        raise QiitaDBColumnError("Unknown key. Pass either 'data_type_id' or "
                                 "'data_type'.")
    sql = 'select {} from qiita.data_type'.format(cols)
    return dict(con.execute_fetchall(sql))


def get_required_sample_info_status(key='status'):
    """Gets the list of possible required sample info status

    Parameters
    ----------
    key : {'status', 'required_sample_info_status_id'}, optional
        Defaults to 'status'. Determines the format of the returned dict.

    Returns
    -------
    dict
        - If `key` is "status", dict is of the form
          {status: required_sample_info_status_id}
        - If `key` is "required_sample_info_status_id", dict is of the form
          {required_sample_info_status_id: status}
    """
    con = SQLConnectionHandler()
    if key == 'status':
        cols = 'status, required_sample_info_status_id'
    elif key == 'required_sample_info_status_id':
        cols = 'required_sample_info_status_id, status'
    else:
        raise QiitaDBColumnError("Unknown key. Pass either 'status' or "
                                 "'required_sample_info_status_id'")
    sql = 'select {} from qiita.required_sample_info_status'.format(cols)
    return dict(con.execute_fetchall(sql))


def get_emp_status(key='emp_status'):
    """Gets the list of possible emp statuses

    Parameters
    ----------
    key : {'emp_status', 'emp_status_id'}, optional
        Defaults to 'status'. Determines the format of the returned dict.

    Returns
    -------
    dict
        - If `key` is "emp_status", dict is of the form
          {emp_status: emp_status_id}
        - If `key` is "emp_status_id", dict is of the form
          {emp_status_id: emp_status}
    """
    con = SQLConnectionHandler()
    if key == 'emp_status':
        cols = 'emp_status, emp_status_id'
    elif key == 'emp_status_id':
        cols = 'emp_status_id, emp_status'
    else:
        raise QiitaDBColumnError("Unknown key. Pass either 'emp_status' or "
                                 "'emp_status_id'")
    sql = 'select {} from qiita.emp_status'.format(cols)
    return dict(con.execute_fetchall(sql))


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
    sql = ("SELECT is_nullable, column_name, column_default "
           "FROM information_schema.columns "
           "WHERE table_name = %s")
    cols = conn_handler.execute_fetchall(sql, (table, ))
    # Test needed because a user with certain permissions can query without
    # error but be unable to get the column names
    if len(cols) == 0:
        raise RuntimeError("Unable to fetch column names for table %s" % table)
    required = set(x[1] for x in cols if x[0] == 'NO' and x[2] is None)
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


def get_table_cols(table, conn_handler=None):
    """Returns the column headers of table

    Parameters
    ----------
    table : str
        The table name
    conn_handler : SQLConnectionHandler, optional
        The connection handler object connected to the DB

    Returns
    -------
    list of str
        The column headers of `table`
    """
    conn_handler = conn_handler if conn_handler else SQLConnectionHandler()
    headers = conn_handler.execute_fetchall(
        "SELECT column_name FROM information_schema.columns WHERE "
        "table_name=%s", (table, ))
    return [h[0] for h in headers]


def get_table_cols_w_type(table, conn_handler=None):
    """Returns the column headers and its type

    Parameters
    ----------
    table : str
        The table name
    conn_handler : SQLConnectionHandler, optional
        The connection handler object connected to the db

    Returns
    -------
    list of tuples of (str, str)
        The column headers and data type of `table`
    """
    conn_handler = conn_handler if conn_handler else SQLConnectionHandler()
    return conn_handler.execute_fetchall(
        "SELECT column_name, data_type FROM information_schema.columns WHERE "
        "table_name=%s", (table,))


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
    r"""Checks if the dynamic `table` exists on the database connected through
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


def compute_checksum(path):
    r"""Returns the checksum of the file pointed by path

    Parameters
    ----------
    path : str
        The path to compute the checksum

    Returns
    -------
    int
        The file checksum
    """
    crc = 0
    filepaths = []
    if isdir(path):
        for name, dirs, files in walk(path):
            join_f = partial(join, name)
            filepaths.extend(list(map(join_f, files)))
    else:
        filepaths.append(path)

    for fp in filepaths:
        with open(fp, "Ub") as f:
            # Go line by line so we don't need to load the entire file
            for line in f:
                if crc is None:
                    crc = crc32(line)
                else:
                    crc = crc32(line, crc)
    # We need the & 0xffffffff in order to get the same numeric value across
    # all python versions and platforms
    return crc & 0xffffffff


def insert_filepaths(filepaths, obj_id, table, filepath_table, conn_handler,
                     move_files=True):
        r"""Inserts `filepaths` in the DB connected with `conn_handler`. Since
        the files live outside the database, the directory in which the files
        lives is controlled by the database, so it copies the filepaths from
        its original location to the controlled directory.

        Parameters
        ----------
        filepaths : iterable of tuples (str, int)
            The list of paths to the raw files and its filepath type identifier
        obj_id : int
            Id of the object calling the functions. Disregarded if move_files
            is False
        table : str
            Table that holds the file data. Disregarded if move_files is False
        filepath_table : str
            Table that holds the filepath information
        conn_handler : SQLConnectionHandler
            The connection handler object connected to the DB
        move_files : bool, optional
            Whether or not to copy from the given filepaths to the db filepaths
            default: True

        Returns
        -------
        list
            The filepath_id in the database for each added filepath
        """
        new_filepaths = filepaths
        base_fp = get_db_files_base_dir()
        if move_files:
            # Get the base directory in which the type of data is stored
            base_data_dir = join(get_db_files_base_dir(), table)
            # Generate the new fileapths. Format: DataId_OriginalName
            # Keeping the original name is useful for checking if the RawData
            # alrady exists on the DB
            db_path = partial(join, base_data_dir)
            new_filepaths = [
                (db_path("%s_%s" % (obj_id, basename(path))), id)
                for path, id in filepaths]
            # Move the original files to the controlled DB directory
            for old_fp, new_fp in zip(filepaths, new_filepaths):
                    move(old_fp[0], new_fp[0])

        str_to_id = lambda x: (x if isinstance(x, (int, long))
                               else convert_to_id(x, "filepath_type",
                                                  conn_handler))
        paths_w_checksum = [(relpath(path, base_fp), str_to_id(id),
                            compute_checksum(path))
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


def convert_from_id(value, table, conn_handler=None):
        """Converts an id value to it's corresponding string value

        Parameters
        ----------
        value : int
            The id value to convert
        table : str
            The table that has the conversion
        conn_handler : SQLConnectionHandler, optional
            The sql connection object

        Returns
        -------
        str
            The string correspinding to the id

        Raises
        ------
        ValueError
            The passed id has no associated string
        """
        conn_handler = conn_handler if conn_handler else SQLConnectionHandler()
        string = conn_handler.execute_fetchone(
            "SELECT {0} FROM qiita.{0} WHERE {0}_id = %s".format(table),
            (value, ))
        if string is None:
            raise ValueError("%s not valid for table %s" % (value, table))
        return string[0]


def get_count(table):
    """Counts the number of rows in a table

    Parameters
    ----------
    table : str
        The name of the table of which to count the rows

    Returns
    -------
    int
    """
    conn = SQLConnectionHandler()
    sql = "SELECT count(1) FROM %s" % table
    return conn.execute_fetchone(sql)[0]


def check_count(table, exp_count):
    """Checks that the number of rows in a table equals the expected count

    Parameters
    ----------
    table : str
        The name of the table of which to count the rows
    exp_count : int
        The expected number of rows in the table

    Returns
    -------
    bool
    """
    obs_count = get_count(table)
    return obs_count == exp_count


def get_preprocessed_params_tables():
    """returns a list of preprocessed parmaeter tables

    Returns
    -------
    list or str
    """
    sql = ("SELECT * FROM information_schema.tables WHERE table_schema = "
           "'qiita' AND SUBSTR(table_name, 1, 13) = 'preprocessed_'")
    conn = SQLConnectionHandler()
    return [x[2] for x in conn.execute_fetchall(sql)]


def get_processed_params_tables():
    """Returns a list of all tables starting with "processed_params_"

    Returns
    -------
    list of str
    """
    sql = ("SELECT * FROM information_schema.tables WHERE table_schema = "
           "'qiita' AND SUBSTR(table_name, 1, 17) = 'processed_params_'")

    conn = SQLConnectionHandler()
    return sorted([x[2] for x in conn.execute_fetchall(sql)])


def get_user_fp(email):
    """Returns the user's working filepath

    Parameters
    ----------
    email : str
        The email of the user

    Returns
    -------
    str
        The user's working filepath, a join of the
        qiita_config.upload_data_dir and the host and name of the user's email
    """
    fp_vals = email.split('@')
    fp = join(qiita_config.upload_data_dir, fp_vals[1], fp_vals[0])

    return fp


def get_study_fp(study_id):
    """Returns the study's working filepath

    Parameters
    ----------
    study_id : int
        The study id

    Returns
    -------
    str
        The study's working filepath, a join of the
        qiita_config.upload_data_dir and the study's email
    """
    fp = join(qiita_config.upload_data_dir, str(study_id))

    return fp
