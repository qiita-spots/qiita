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
    get_files_from_uploads_folders
    get_mountpoint
    insert_filepaths
    check_table_cols
    check_required_columns
    convert_from_id
    convert_to_id
    get_lat_longs
    get_environmental_packages
    purge_filepaths
    move_filepaths_to_upload_folder
    move_upload_files_to_trash
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
from os.path import join, basename, isdir, relpath, exists
from os import walk, remove, listdir, makedirs, rename
from shutil import move, rmtree
from json import dumps
from datetime import datetime
from itertools import chain

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .exceptions import QiitaDBColumnError, QiitaDBError
from .sql_connection import TRN


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


def convert_type(obj):
    """Converts a passed item to int, float, or str in that order

    Parameters
    ----------
    obj : object
        object to evaluate

    Returns
    -------
    int, float, or str
        Re-typed information from obj

    Raises
    ------
    IncompetentQiitaDeveloperError
        If the object can't be converted to int, float, or string

    Notes
    -----
    The function first tries to convert to an int. If that fails, it tries to
    convert to a float. If that fails it returns the original string.
    """
    item = None
    if isinstance(obj, datetime):
        item = str(obj)
    else:
        for fn in (int, float, str):
            try:
                item = fn(obj)
            except ValueError:
                continue
            else:
                break
    if item is None:
        raise IncompetentQiitaDeveloperError("Can't convert item of type %s!" %
                                             str(type(obj)))
    return item


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
    with TRN:
        if key == 'type':
            cols = 'type, filetype_id'
        elif key == 'filetype_id':
            cols = 'filetype_id, type'
        else:
            raise QiitaDBColumnError("Unknown key. Pass either 'type' or "
                                     "'filetype_id'.")
        sql = 'SELECT {} FROM qiita.filetype'.format(cols)
        TRN.add(sql)
        return dict(TRN.execute_fetchindex())


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
    with TRN:
        if key == 'filepath_type':
            cols = 'filepath_type, filepath_type_id'
        elif key == 'filepath_type_id':
            cols = 'filepath_type_id, filepath_type'
        else:
            raise QiitaDBColumnError("Unknown key. Pass either 'filepath_type'"
                                     " or 'filepath_type_id'.")
        sql = 'SELECT {} FROM qiita.filepath_type'.format(cols)
        TRN.add(sql)
        return dict(TRN.execute_fetchindex())


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
    with TRN:
        if key == 'data_type':
            cols = 'data_type, data_type_id'
        elif key == 'data_type_id':
            cols = 'data_type_id, data_type'
        else:
            raise QiitaDBColumnError("Unknown key. Pass either 'data_type_id' "
                                     "or 'data_type'.")
        sql = 'SELECT {} FROM qiita.data_type'.format(cols)
        TRN.add(sql)
        return dict(TRN.execute_fetchindex())


def create_rand_string(length, punct=True):
    """Returns a string of random ascii characters

    Parameters
    ----------
    length: int
        Length of string to return
    punct: bool, optional
        Include punctuation as well as letters and numbers. Default True.
    """
    chars = ''.join((ascii_letters, digits))
    if punct:
        chars = ''.join((chars, punctuation))
    return ''.join(choice(chars) for i in range(length))


def hash_password(password, hashedpw=None):
    """Hashes password

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


def check_required_columns(keys, table):
    """Makes sure all required columns in database table are in keys

    Parameters
    ----------
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
    with TRN:
        sql = """SELECT is_nullable, column_name, column_default
                 FROM information_schema.columns WHERE table_name = %s"""
        TRN.add(sql, [table])
        cols = TRN.execute_fetchindex()
        # Test needed because a user with certain permissions can query without
        # error but be unable to get the column names
        if len(cols) == 0:
            raise RuntimeError("Unable to fetch column names for table %s"
                               % table)
        required = set(x[1] for x in cols if x[0] == 'NO' and x[2] is None)
        if len(required.difference(keys)) > 0:
            raise QiitaDBColumnError("Required keys missing: %s" %
                                     required.difference(keys))


def check_table_cols(keys, table):
    """Makes sure all keys correspond to column headers in a table

    Parameters
    ----------
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
    with TRN:
        sql = """SELECT column_name FROM information_schema.columns
                 WHERE table_name = %s"""
        TRN.add(sql, [table])
        cols = [x[0] for x in TRN.execute()[-1]]
        # Test needed because a user with certain permissions can query without
        # error but be unable to get the column names
        if len(cols) == 0:
            raise RuntimeError("Unable to fetch column names for table %s"
                               % table)
        if len(set(keys).difference(cols)) > 0:
            raise QiitaDBColumnError("Non-database keys found: %s" %
                                     set(keys).difference(cols))


def get_table_cols(table):
    """Returns the column headers of table

    Parameters
    ----------
    table : str
        The table name

    Returns
    -------
    list of str
        The column headers of `table`
    """
    with TRN:
        sql = """SELECT column_name FROM information_schema.columns
                 WHERE table_name=%s AND table_schema='qiita'"""
        TRN.add(sql, [table])
        return [h[0] for h in TRN.execute_fetchindex()]


def get_table_cols_w_type(table):
    """Returns the column headers and its type

    Parameters
    ----------
    table : str
        The table name

    Returns
    -------
    list of tuples of (str, str)
        The column headers and data type of `table`
    """
    with TRN:
        sql = """SELECT column_name, data_type FROM information_schema.columns
                 WHERE table_name=%s"""
        TRN.add(sql, [table])
        return TRN.execute_fetchindex()


def exists_table(table):
    r"""Checks if `table` exists on the database

    Parameters
    ----------
    table : str
        The table name to check if exists

    Returns
    -------
    bool
        Whether `table` exists on the database or not
    """
    with TRN:
        sql = """SELECT exists(
                    SELECT * FROM information_schema.tables
                    WHERE table_name=%s)"""
        TRN.add(sql, [table])
        return TRN.execute_fetchlast()


def exists_dynamic_table(table, prefix, suffix):
    r"""Checks if the dynamic `table` exists on the database, and its name
    starts with prefix and ends with suffix

    Parameters
    ----------
    table : str
        The table name to check if exists
    prefix : str
        The table name prefix
    suffix : str
        The table name suffix

    Returns
    -------
    bool
       Whether `table` exists on the database or not and its name
        starts with prefix and ends with suffix
    """
    return (table.startswith(prefix) and table.endswith(suffix) and
            exists_table(table))


def get_db_files_base_dir():
    r"""Returns the path to the base directory of all db files

    Returns
    -------
    str
        The path to the base directory of all db files
    """
    with TRN:
        TRN.add("SELECT base_data_dir FROM settings")
        return TRN.execute_fetchlast()


def get_work_base_dir():
    r"""Returns the path to the base directory of all db files

    Returns
    -------
    str
        The path to the base directory of all db files
    """
    with TRN:
        TRN.add("SELECT base_work_dir FROM settings")
        return TRN.execute_fetchlast()


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


def get_files_from_uploads_folders(study_id):
    """Retrieve files in upload folders

    Parameters
    ----------
    study_id : str
        The study id of which to retrieve all upload folders

    Returns
    -------
    list
        List of the filepaths for upload for that study
    """
    fp = []
    for pid, p in get_mountpoint("uploads", retrieve_all=True):
        t = join(p, study_id)
        if exists(t):
            fp.extend([(pid, f)
                       for f in listdir(t)
                       if not f.startswith('.') and not isdir(join(t, f))])

    return fp


def move_upload_files_to_trash(study_id, files_to_move):
    """Move files to a trash folder within the study_id upload folder

    Parameters
    ----------
    study_id : int
        The study id
    files_to_move : list
        List of tuples (folder_id, filename)

    Raises
    ------
    QiitaDBError
        If folder_id or the study folder don't exist and if the filename to
        erase matches the trash_folder, internal variable
    """
    trash_folder = 'trash'
    folders = {k: v for k, v in get_mountpoint("uploads", retrieve_all=True)}

    for fid, filename in files_to_move:
        if filename == trash_folder:
            raise QiitaDBError("You can not erase the trash folder: %s"
                               % trash_folder)

        if fid not in folders:
            raise QiitaDBError("The filepath id: %d doesn't exist in the "
                               "database" % fid)

        foldername = join(folders[fid], str(study_id))
        if not exists(foldername):
            raise QiitaDBError("The upload folder for study id: %d doesn't "
                               "exist" % study_id)

        trashpath = join(foldername, trash_folder)
        if not exists(trashpath):
            makedirs(trashpath)

        fullpath = join(foldername, filename)
        new_fullpath = join(foldername, trash_folder, filename)

        if not exists(fullpath):
            raise QiitaDBError("The filepath %s doesn't exist in the system" %
                               fullpath)

        rename(fullpath, new_fullpath)


def get_mountpoint(mount_type, retrieve_all=False):
    r""" Returns the most recent values from data directory for the given type

    Parameters
    ----------
    mount_type : str
        The data mount type
    retrieve_all : bool
        Retrieve all the available mount points or just the active one

    Returns
    -------
    list
        List of tuple, where: [(id_mountpoint, filepath_of_mountpoint)]
    """
    with TRN:
        if retrieve_all:
            sql = """SELECT data_directory_id, mountpoint, subdirectory
                     FROM qiita.data_directory
                     WHERE data_type=%s ORDER BY active DESC"""
        else:
            sql = """SELECT data_directory_id, mountpoint, subdirectory
                     FROM qiita.data_directory
                     WHERE data_type=%s AND active=true"""
        TRN.add(sql, [mount_type])
        result = TRN.execute_fetchindex()
        basedir = get_db_files_base_dir()
        return [(d, join(basedir, m, s)) for d, m, s in result]


def get_mountpoint_path_by_id(mount_id):
    r""" Returns the mountpoint path for the mountpoint with id = mount_id

    Parameters
    ----------
    mount_id : int
        The mountpoint id

    Returns
    -------
    str
        The mountpoint path
    """
    with TRN:
        sql = """SELECT mountpoint, subdirectory FROM qiita.data_directory
                 WHERE data_directory_id=%s"""
        TRN.add(sql, [mount_id])
        mountpoint, subdirectory = TRN.execute_fetchindex()[0]
        return join(get_db_files_base_dir(), mountpoint, subdirectory)


def insert_filepaths(filepaths, obj_id, table, filepath_table,
                     move_files=True):
    r"""Inserts `filepaths` in the database.

    Since the files live outside the database, the directory in which the files
    lives is controlled by the database, so it mvoes the filepaths from
    its original location to the controlled directory.

    Parameters
    ----------
    filepaths : iterable of tuples (str, int)
        The list of paths to the raw files and its filepath type identifier
    obj_id : int
        Id of the object calling the functions. Disregarded if move_files
        is False
    table : str
        Table that holds the file data.
    filepath_table : str
        Table that holds the filepath information
    move_files : bool, optional
        Whether or not to copy from the given filepaths to the db filepaths
        default: True

    Returns
    -------
    list of int
        List of the filepath_id in the database for each added filepath
    """
    with TRN:
        new_filepaths = filepaths

        dd_id, mp = get_mountpoint(table)[0]
        base_fp = join(get_db_files_base_dir(), mp)

        if move_files:
            # Generate the new fileapths. Format: DataId_OriginalName
            # Keeping the original name is useful for checking if the RawData
            # alrady exists on the DB
            db_path = partial(join, base_fp)
            new_filepaths = [
                (db_path("%s_%s" % (obj_id, basename(path))), id)
                for path, id in filepaths]
            # Move the original files to the controlled DB directory
            for old_fp, new_fp in zip(filepaths, new_filepaths):
                    move(old_fp[0], new_fp[0])

        def str_to_id(x):
            return (x if isinstance(x, (int, long))
                    else convert_to_id(x, "filepath_type"))
        paths_w_checksum = [(relpath(path, base_fp), str_to_id(id),
                            compute_checksum(path))
                            for path, id in new_filepaths]
        # Create the list of SQL values to add
        values = [[path, pid, checksum, 1, dd_id]
                  for path, pid, checksum in paths_w_checksum]
        # Insert all the filepaths at once and get the filepath_id back
        sql = """INSERT INTO qiita.{0}
                    (filepath, filepath_type_id, checksum,
                     checksum_algorithm_id, data_directory_id)
                 VALUES (%s, %s, %s, %s, %s)
                 RETURNING filepath_id""".format(filepath_table)
        idx = TRN.index
        TRN.add(sql, values, many=True)
        # Since we added the query with many=True, we've added len(values)
        # queries to the transaction, so the ids are in the last idx queries
        return list(chain.from_iterable(
            chain.from_iterable(TRN.execute()[idx:])))


def purge_filepaths():
    r"""Goes over the filepath table and remove all the filepaths that are not
    used in any place

    Raises
    ------
    IOError
        If any error occurs while removing the fileapths from the file system

    Notes
    -----
    This function can potentially leave the DB and the file system out of
    sync if purge_filepaths is execute inside a bigger transaction. Thus,
    care should be taken when using this function and do not include it in
    a bigger transactions, as it can leave the database pointing to files that
    no longer exist.
    """
    with TRN:
        # Get all the (table, column) pairs that reference to the filepath
        # table. Adapted from http://stackoverflow.com/q/5347050/3746629
        sql = """SELECT R.TABLE_NAME, R.column_name
            FROM INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE u
            INNER JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS FK
                ON U.CONSTRAINT_CATALOG = FK.UNIQUE_CONSTRAINT_CATALOG
                AND U.CONSTRAINT_SCHEMA = FK.UNIQUE_CONSTRAINT_SCHEMA
                AND U.CONSTRAINT_NAME = FK.UNIQUE_CONSTRAINT_NAME
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE R
                ON R.CONSTRAINT_CATALOG = FK.CONSTRAINT_CATALOG
                AND R.CONSTRAINT_SCHEMA = FK.CONSTRAINT_SCHEMA
                AND R.CONSTRAINT_NAME = FK.CONSTRAINT_NAME
            WHERE U.COLUMN_NAME = 'filepath_id'
                AND U.TABLE_SCHEMA = 'qiita'
                AND U.TABLE_NAME = 'filepath'"""
        TRN.add(sql)

        union_str = " UNION ".join(
            ["SELECT %s FROM qiita.%s WHERE %s IS NOT NULL" % (col, table, col)
             for table, col in TRN.execute_fetchindex()])
        # Get all the filepaths from the filepath table that are not
        # referenced from any place in the database
        sql = """SELECT filepath_id, filepath, filepath_type, data_directory_id
            FROM qiita.filepath FP JOIN qiita.filepath_type FPT
                ON FP.filepath_type_id = FPT.filepath_type_id
            WHERE filepath_id NOT IN (%s)""" % union_str
        TRN.add(sql)

        # We can now go over and remove all the filepaths
        sql = "DELETE FROM qiita.filepath WHERE filepath_id=%s"
        funcs = []
        for fp_id, fp, fp_type, dd_id in TRN.execute_fetchindex():
            TRN.add(sql, [fp_id])

            # Remove the data
            fp = join(get_mountpoint_path_by_id(dd_id), fp)
            if exists(fp):
                if fp_type is 'directory':
                    funcs.append(partial(rmtree, fp))
                else:
                    funcs.append(partial(remove, fp))

        TRN.execute()
    # Now that the filepaths have been removed from the DB, we can go and
    # remove them from the file system
    error_msg = []
    for f in funcs:
        try:
            f()
        except Exception as e:
            error_msg.append(str(e))
    if error_msg:
        raise IOError("An error occurred while purging filepaths:\n\t%s"
                      % "\n\t".join(error_msg))


def move_filepaths_to_upload_folder(study_id, filepaths):
    r"""Goes over the filepaths list and moves all the filepaths that are not
    used in any place to the upload folder of the study

    Parameters
    ----------
    study_id : int
        The study id to where the files should be returned to
    filepaths : list
        List of filepaths to move to the upload folder
    """
    with TRN:
        uploads_fp = join(get_mountpoint("uploads")[0][1], str(study_id))
        path_builder = partial(join, uploads_fp)

        # We can now go over and remove all the filepaths
        sql = """DELETE FROM qiita.filepath WHERE filepath_id=%s"""
        moved_files = []
        for fp_id, fp, _ in filepaths:
            TRN.add(sql, [fp_id])

            # removing id from the raw data filename
            filename = basename(fp).split('_', 1)[1]
            destination = path_builder(filename)

            moved_files.append((fp, destination))
            move(fp, destination)

        try:
            TRN.execute()
        except Exception:
            # Undo the moving of the files
            for dest, src in moved_files:
                move(src, dest)


def get_filepath_id(table, fp):
    """Return the filepath_id of fp

    Parameters
    ----------
    table : str
        The table type so we can search on this one
    fp : str
        The filepath

    Returns
    -------
    int
        The filepath id forthe given filepath

    Raises
    ------
    QiitaDBError
        If fp is not stored in the DB.
    """
    with TRN:
        _, mp = get_mountpoint(table)[0]
        base_fp = join(get_db_files_base_dir(), mp)

        sql = "SELECT filepath_id FROM qiita.filepath WHERE filepath=%s"
        TRN.add(sql, [relpath(fp, base_fp)])
        fp_id = TRN.execute_fetchindex()

        # check if the query has actually returned something
        if not fp_id:
            raise QiitaDBError("Filepath not stored in the database")

        # If there was a result it was a single row and and single value,
        # hence access to [0][0]
        return fp_id[0][0]


def filepath_id_to_rel_path(filepath_id):
    """Gets the full path, relative to the base directory

    Returns
    -------
    str
        The relative path for the given filepath id
    """
    with TRN:
        sql = """SELECT mountpoint, subdirectory, filepath
                 FROM qiita.filepath
                 JOIN qiita.data_directory USING (data_directory_id)
                 WHERE filepath_id = %s"""
        TRN.add(sql, [filepath_id])
        # It should be only one row
        return join(*TRN.execute_fetchindex()[0])


def filepath_ids_to_rel_paths(filepath_ids):
    """Gets the full paths, relative to the base directory

    Parameters
    ----------
    filepath_ids : list of int

    Returns
    -------
    dict where keys are ints and values are str
        {filepath_id: relative_path}
    """
    if not filepath_ids:
        return {}

    with TRN:
        sql = """SELECT filepath_id, mountpoint, subdirectory, filepath
                 FROM qiita.filepath
                 JOIN qiita.data_directory USING (data_directory_id)
                 WHERE filepath_id IN %s"""
        TRN.add(sql, [tuple(filepath_ids)])
        return {row[0]: join(*row[1:]) for row in TRN.execute_fetchindex()}


def convert_to_id(value, table, text_col=None):
    """Converts a string value to its corresponding table identifier

    Parameters
    ----------
    value : str
        The string value to convert
    table : str
        The table that has the conversion
    text_col : str, optional
        Column holding the string value. Defaults to same as table name.

    Returns
    -------
    int
        The id correspinding to the string

    Raises
    ------
    IncompetentQiitaDeveloperError
        The passed string has no associated id
    """
    text_col = table if text_col is None else text_col
    with TRN:
        sql = "SELECT {0}_id FROM qiita.{0} WHERE {1} = %s".format(
            table, text_col)
        TRN.add(sql, [value])
        _id = TRN.execute_fetchindex()
        if not _id:
            raise IncompetentQiitaDeveloperError("%s not valid for table %s"
                                                 % (value, table))
        # If there was a result it was a single row and and single value,
        # hence access to [0][0]
        return _id[0][0]


def convert_from_id(value, table):
    """Converts an id value to its corresponding string value

    Parameters
    ----------
    value : int
        The id value to convert
    table : str
        The table that has the conversion

    Returns
    -------
    str
        The string correspinding to the id

    Raises
    ------
    ValueError
        The passed id has no associated string
    """
    with TRN:
        sql = "SELECT {0} FROM qiita.{0} WHERE {0}_id = %s".format(table)
        TRN.add(sql, [value])
        string = TRN.execute_fetchindex()
        if not string:
            raise ValueError("%s not valid for table %s" % (value, table))
        # If there was a result it was a single row and and single value,
        # hence access to [0][0]
        return string[0][0]


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
    with TRN:
        sql = "SELECT count(1) FROM %s" % table
        TRN.add(sql)
        return TRN.execute_fetchlast()


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
    with TRN:
        sql = """SELECT table_name FROM information_schema.tables
                 WHERE table_schema = 'qiita'
                    AND SUBSTR(table_name, 1, 13) = 'preprocessed_'
                    AND table_name NOT IN ('preprocessed_data',
                                           'preprocessed_filepath',
                                           'preprocessed_processed_data')
                 ORDER BY table_name"""
        TRN.add(sql)
        return [row[0] for row in TRN.execute_fetchindex()]


def get_processed_params_tables():
    """Returns a list of all tables starting with "processed_params_"

    Returns
    -------
    list of str
    """
    with TRN:
        sql = """SELECT table_name FROM information_schema.tables
                 WHERE table_schema = 'qiita'
                    AND SUBSTR(table_name, 1, 17) = 'processed_params_'
                 ORDER BY table_name"""
        TRN.add(sql)
        return [row[0] for row in TRN.execute_fetchindex()]


def get_lat_longs():
    """Retrieve the latitude and longitude of all the samples in the DB

    Returns
    -------
    list of [float, float]
        The latitude and longitude for each sample in the database
    """
    with TRN:
        sql = """SELECT DISTINCT table_name
                 FROM information_schema.columns
                 WHERE SUBSTR(table_name, 1, 7) = 'sample_'
                    AND table_schema = 'qiita'
                    AND column_name IN ('latitude', 'longitude');"""
        TRN.add(sql)
        tables_gen = (t[0] for t in TRN.execute_fetchindex())

        sql = "SELECT latitude, longitude FROM qiita.{0}"
        idx = TRN.index
        for table in tables_gen:
            TRN.add(sql.format(table))

        return list(chain.from_iterable(TRN.execute()[idx:]))


def get_environmental_packages():
    """Get the list of available environmental packages

    Returns
    -------
    list of (str, str)
        The available environmental packages. The first string is the
        environmental package name and the second string is the table where
        the metadata for the environmental package is stored
    """
    with TRN:
        TRN.add("SELECT * FROM qiita.environmental_package")
        return TRN.execute_fetchindex()


def get_timeseries_types():
    """Get the list of available timeseries types

    Returns
    -------
    list of (int, str, str)
        The available timeseries types. Each timeseries type is defined by the
        tuple (timeseries_id, timeseries_type, intervention_type)
    """
    with TRN:
        sql = "SELECT * FROM qiita.timeseries_type ORDER BY timeseries_type_id"
        TRN.add(sql)
        return TRN.execute_fetchindex()


def check_access_to_analysis_result(user_id, requested_path):
    """Get filepath IDs for a particular requested_path, if user has access

    This function is only applicable for analysis results.

    Parameters
    ----------
    user_id : str
        The ID (email address) that identifies the user
    requested_path : str
        The path that the user requested

    Returns
    -------
    list of int
        The filepath IDs associated with the requested path
    """
    with TRN:
        # Get all filepath ids associated with analyses that the user has
        # access to where the filepath is the base_requested_fp from above.
        # There should typically be only one matching filepath ID, but for
        # safety we allow for the possibility of multiple.
        sql = """SELECT fp.filepath_id
                 FROM qiita.analysis_job aj JOIN (
                    SELECT analysis_id FROM qiita.analysis A
                    JOIN qiita.analysis_status stat
                    ON A.analysis_status_id = stat.analysis_status_id
                    WHERE stat.analysis_status_id = 6
                    UNION
                    SELECT analysis_id FROM qiita.analysis_users
                    WHERE email = %s
                    UNION
                    select analysis_id FROM qiita.analysis WHERE email = %s
                 ) ids ON aj.analysis_id = ids.analysis_id
                 JOIN qiita.job_results_filepath jrfp ON
                    aj.job_id = jrfp.job_id
                 JOIN qiita.filepath fp ON jrfp.filepath_id = fp.filepath_id
                 WHERE fp.filepath = %s"""
        TRN.add(sql, [user_id, user_id, requested_path])

        return [row[0] for row in TRN.execute_fetchindex()]


def infer_status(statuses):
    """Infers an object status from the statuses passed in

    Parameters
    ----------
    statuses : list of lists of strings or empty list
        The list of statuses used to infer the resulting status (the result
        of execute_fetchall)

    Returns
    -------
    str
        The inferred status

    Notes
    -----
    The inference is done in the following priority (high to low):
        (1) public
        (2) private
        (3) awaiting_approval
        (4) sandbox
    """
    if statuses:
        statuses = set(s[0] for s in statuses)
        if 'public' in statuses:
            return 'public'
        if 'private' in statuses:
            return 'private'
        if 'awaiting_approval' in statuses:
            return 'awaiting_approval'
    # If there are no statuses, or any of the previous ones have been found
    # then the inferred status is 'sandbox'
    return 'sandbox'
