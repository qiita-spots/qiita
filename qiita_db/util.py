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
    get_db_files_base_dir
    compute_checksum
    get_files_from_uploads_folders
    get_mountpoint
    insert_filepaths
    check_table_cols
    check_required_columns
    convert_from_id
    convert_to_id
    get_environmental_packages
    get_visibilities
    purge_filepaths
    move_filepaths_to_upload_folder
    move_upload_files_to_trash
    add_message
    get_pubmed_ids_from_dois
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
from future.utils import viewitems
from random import SystemRandom
from string import ascii_letters, digits, punctuation
from binascii import crc32
from bcrypt import hashpw, gensalt
from functools import partial
from os.path import join, basename, isdir, exists
from os import walk, remove, listdir, makedirs, rename
from shutil import move, rmtree, copy as shutil_copy
from json import dumps
from datetime import datetime
from itertools import chain
from contextlib import contextmanager
from future.builtins import bytes, str
import h5py

from qiita_core.exceptions import IncompetentQiitaDeveloperError
import qiita_db as qdb


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


def get_artifact_types(key_by_id=False):
    """Gets the list of possible artifact types

    Parameters
    ----------
    key : bool, optional
        Determines the format of the returned dict. Defaults to false.

    Returns
    -------
    dict
        If key_by_id is True, dict is of the form
        {artifact_type_id: artifact_type}
        If key_by_id is False, dict is of the form
        {artifact_type: artifact_type_id}
    """
    with qdb.sql_connection.TRN:
        cols = ('artifact_type_id, artifact_type'
                if key_by_id else 'artifact_type, artifact_type_id')
        sql = "SELECT {} FROM qiita.artifact_type".format(cols)
        qdb.sql_connection.TRN.add(sql)
        return dict(qdb.sql_connection.TRN.execute_fetchindex())


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
    with qdb.sql_connection.TRN:
        if key == 'filepath_type':
            cols = 'filepath_type, filepath_type_id'
        elif key == 'filepath_type_id':
            cols = 'filepath_type_id, filepath_type'
        else:
            raise qdb.exceptions.QiitaDBColumnError(
                "Unknown key. Pass either 'filepath_type' or "
                "'filepath_type_id'.")
        sql = 'SELECT {} FROM qiita.filepath_type'.format(cols)
        qdb.sql_connection.TRN.add(sql)
        return dict(qdb.sql_connection.TRN.execute_fetchindex())


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
    with qdb.sql_connection.TRN:
        if key == 'data_type':
            cols = 'data_type, data_type_id'
        elif key == 'data_type_id':
            cols = 'data_type_id, data_type'
        else:
            raise qdb.exceptions.QiitaDBColumnError(
                "Unknown key. Pass either 'data_type_id' or 'data_type'.")
        sql = 'SELECT {} FROM qiita.data_type'.format(cols)
        qdb.sql_connection.TRN.add(sql)
        return dict(qdb.sql_connection.TRN.execute_fetchindex())


def create_rand_string(length, punct=True):
    """Returns a string of random ascii characters

    Parameters
    ----------
    length: int
        Length of string to return
    punct: bool, optional
        Include punctuation as well as letters and numbers. Default True.
    """
    chars = ascii_letters + digits
    if punct:
        chars += punctuation
    sr = SystemRandom()
    return ''.join(sr.choice(chars) for i in xrange(length))


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
    with qdb.sql_connection.TRN:
        sql = """SELECT is_nullable, column_name, column_default
                 FROM information_schema.columns WHERE table_name = %s"""
        qdb.sql_connection.TRN.add(sql, [table])
        cols = qdb.sql_connection.TRN.execute_fetchindex()
        # Test needed because a user with certain permissions can query without
        # error but be unable to get the column names
        if len(cols) == 0:
            raise RuntimeError("Unable to fetch column names for table %s"
                               % table)
        required = set(x[1] for x in cols if x[0] == 'NO' and x[2] is None)
        if len(required.difference(keys)) > 0:
            raise qdb.exceptions.QiitaDBColumnError(
                "Required keys missing: %s" % required.difference(keys))


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
    with qdb.sql_connection.TRN:
        sql = """SELECT column_name FROM information_schema.columns
                 WHERE table_name = %s"""
        qdb.sql_connection.TRN.add(sql, [table])
        cols = qdb.sql_connection.TRN.execute_fetchflatten()
        # Test needed because a user with certain permissions can query without
        # error but be unable to get the column names
        if len(cols) == 0:
            raise RuntimeError("Unable to fetch column names for table %s"
                               % table)
        if len(set(keys).difference(cols)) > 0:
            raise qdb.exceptions.QiitaDBColumnError(
                "Non-database keys found: %s" % set(keys).difference(cols))


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
    with qdb.sql_connection.TRN:
        sql = """SELECT column_name FROM information_schema.columns
                 WHERE table_name=%s AND table_schema='qiita'"""
        qdb.sql_connection.TRN.add(sql, [table])
        return qdb.sql_connection.TRN.execute_fetchflatten()


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
    with qdb.sql_connection.TRN:
        sql = """SELECT exists(
                    SELECT * FROM information_schema.tables
                    WHERE table_name=%s)"""
        qdb.sql_connection.TRN.add(sql, [table])
        return qdb.sql_connection.TRN.execute_fetchlast()


def get_db_files_base_dir():
    r"""Returns the path to the base directory of all db files

    Returns
    -------
    str
        The path to the base directory of all db files
    """
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add("SELECT base_data_dir FROM settings")
        return qdb.sql_connection.TRN.execute_fetchlast()


def get_work_base_dir():
    r"""Returns the path to the base directory of all db files

    Returns
    -------
    str
        The path to the base directory of all db files
    """
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add("SELECT base_work_dir FROM settings")
        return qdb.sql_connection.TRN.execute_fetchlast()


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
    study_id = str(study_id)
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
            raise qdb.exceptions.QiitaDBError(
                "You can not erase the trash folder: %s" % trash_folder)

        if fid not in folders:
            raise qdb.exceptions.QiitaDBError(
                "The filepath id: %d doesn't exist in the database" % fid)

        foldername = join(folders[fid], str(study_id))
        if not exists(foldername):
            raise qdb.exceptions.QiitaDBError(
                "The upload folder for study id: %d doesn't exist" % study_id)

        trashpath = join(foldername, trash_folder)
        if not exists(trashpath):
            makedirs(trashpath)

        fullpath = join(foldername, filename)
        new_fullpath = join(foldername, trash_folder, filename)

        if not exists(fullpath):
            raise qdb.exceptions.QiitaDBError(
                "The filepath %s doesn't exist in the system" % fullpath)

        rename(fullpath, new_fullpath)


def get_mountpoint(mount_type, retrieve_all=False, retrieve_subdir=False):
    r""" Returns the most recent values from data directory for the given type

    Parameters
    ----------
    mount_type : str
        The data mount type
    retrieve_all : bool, optional
        Retrieve all the available mount points or just the active one.
        Default: False.
    retrieve_subdir : bool, optional
        Retrieve the subdirectory column. Default: False.

    Returns
    -------
    list
        List of tuple, where: [(id_mountpoint, filepath_of_mountpoint)]
    """
    with qdb.sql_connection.TRN:
        if retrieve_all:
            sql = """SELECT data_directory_id, mountpoint, subdirectory
                     FROM qiita.data_directory
                     WHERE data_type=%s ORDER BY active DESC"""
        else:
            sql = """SELECT data_directory_id, mountpoint, subdirectory
                     FROM qiita.data_directory
                     WHERE data_type=%s AND active=true"""
        qdb.sql_connection.TRN.add(sql, [mount_type])
        db_result = qdb.sql_connection.TRN.execute_fetchindex()
        basedir = get_db_files_base_dir()
        if retrieve_subdir:
            result = [(d, join(basedir, m), s) for d, m, s in db_result]
        else:
            result = [(d, join(basedir, m)) for d, m, _ in db_result]
        return result


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
    with qdb.sql_connection.TRN:
        sql = """SELECT mountpoint FROM qiita.data_directory
                 WHERE data_directory_id=%s"""
        qdb.sql_connection.TRN.add(sql, [mount_id])
        mountpoint = qdb.sql_connection.TRN.execute_fetchlast()
        return join(get_db_files_base_dir(), mountpoint)


def insert_filepaths(filepaths, obj_id, table, move_files=True, copy=False):
    r"""Inserts `filepaths` in the database.

    Since the files live outside the database, the directory in which the files
    lives is controlled by the database, so it moves the filepaths from
    its original location to the controlled directory.

    Parameters
    ----------
    filepaths : iterable of tuples (str, int)
        The list of paths to the raw files and its filepath type identifier
    obj_id : int
        Id of the object calling the functions. Disregarded if move_files
        is False
    table : str
        Table that holds the file data
    move_files : bool, optional
        Whether or not to move the given filepaths to the db filepaths
        default: True
    copy : bool, optional
        If `move_files` is true, whether to actually move the files or just
        copy them

    Returns
    -------
    list of int
        List of the filepath_id in the database for each added filepath
    """
    with qdb.sql_connection.TRN:
        new_filepaths = filepaths

        dd_id, mp, subdir = get_mountpoint(table, retrieve_subdir=True)[0]
        base_fp = join(get_db_files_base_dir(), mp)

        if move_files:
            db_path = partial(join, base_fp)
            if subdir:
                # Generate the new filepaths, format:
                # mountpoint/obj_id/original_name
                dirname = db_path(str(obj_id))
                if not exists(dirname):
                    makedirs(dirname)
                new_filepaths = [
                    (join(dirname, basename(path)), id_)
                    for path, id_ in filepaths]
            else:
                # Generate the new fileapths. format:
                # mountpoint/DataId_OriginalName
                new_filepaths = [
                    (db_path("%s_%s" % (obj_id, basename(path))), id_)
                    for path, id_ in filepaths]
            # Move the original files to the controlled DB directory
            transfer_function = shutil_copy if copy else move
            for old_fp, new_fp in zip(filepaths, new_filepaths):
                    transfer_function(old_fp[0], new_fp[0])
                    # In case the transaction executes a rollback, we need to
                    # make sure the files have not been moved
                    qdb.sql_connection.TRN.add_post_rollback_func(
                        move, new_fp[0], old_fp[0])

        def str_to_id(x):
            return (x if isinstance(x, (int, long))
                    else convert_to_id(x, "filepath_type"))
        paths_w_checksum = [(basename(path), str_to_id(id_),
                            compute_checksum(path))
                            for path, id_ in new_filepaths]
        # Create the list of SQL values to add
        values = [[path, pid, checksum, 1, dd_id]
                  for path, pid, checksum in paths_w_checksum]
        # Insert all the filepaths at once and get the filepath_id back
        sql = """INSERT INTO qiita.filepath
                    (filepath, filepath_type_id, checksum,
                     checksum_algorithm_id, data_directory_id)
                 VALUES (%s, %s, %s, %s, %s)
                 RETURNING filepath_id"""
        idx = qdb.sql_connection.TRN.index
        qdb.sql_connection.TRN.add(sql, values, many=True)
        # Since we added the query with many=True, we've added len(values)
        # queries to the transaction, so the ids are in the last idx queries
        return list(chain.from_iterable(
            chain.from_iterable(qdb.sql_connection.TRN.execute()[idx:])))


def retrieve_filepaths(obj_fp_table, obj_id_column, obj_id, sort=None,
                       fp_type=None):
    """Retrieves the filepaths for the given object id

    Parameters
    ----------
    obj_fp_table : str
        The name of the table that links the object and the filepath
    obj_id_column : str
        The name of the column that represents the object id
    obj_id : int
        The object id
    sort : {'ascending', 'descending'}, optional
        The direction in which the results are sorted, using the filepath id
        as sorting key. Default: None, no sorting is applied
    fp_type: str, optional
        Retrieve only the filepaths of the matching filepath type

    Returns
    -------
    list of (int, str, str)
        The list of (filepath id, filepath, filepath_type) attached to the
        object id
    """

    def path_builder(db_dir, filepath, mountpoint, subdirectory, obj_id):
        if subdirectory:
            return join(db_dir, mountpoint, str(obj_id), filepath)
        else:
            return join(db_dir, mountpoint, filepath)

    sql_sort = ""
    if sort == 'ascending':
        sql_sort = " ORDER BY filepath_id"
    elif sort == 'descending':
        sql_sort = " ORDER BY filepath_id DESC"
    elif sort is not None:
        raise qdb.exceptions.QiitaDBError(
            "Unknown sorting direction: %s. Please choose from 'ascending' or "
            "'descending'" % sort)

    sql_args = [obj_id]

    sql_type = ""
    if fp_type:
        sql_type = " AND filepath_type=%s"
        sql_args.append(fp_type)

    with qdb.sql_connection.TRN:
        sql = """SELECT filepath_id, filepath, filepath_type, mountpoint,
                        subdirectory
                 FROM qiita.filepath
                    JOIN qiita.filepath_type USING (filepath_type_id)
                    JOIN qiita.data_directory USING (data_directory_id)
                    JOIN qiita.{0} USING (filepath_id)
                 WHERE {1} = %s{2}{3}""".format(obj_fp_table, obj_id_column,
                                                sql_type, sql_sort)
        qdb.sql_connection.TRN.add(sql, sql_args)
        results = qdb.sql_connection.TRN.execute_fetchindex()
        db_dir = get_db_files_base_dir()

        return [(fpid, path_builder(db_dir, fp, m, s, obj_id), fp_type_)
                for fpid, fp, fp_type_, m, s in results]


def _rm_files(TRN, fp):
    # Remove the data
    if exists(fp):
        if isdir(fp):
            func = rmtree
        else:
            func = remove
        TRN.add_post_commit_func(func, fp)


def purge_filepaths(delete_files=True):
    r"""Goes over the filepath table and remove all the filepaths that are not
    used in any place

    Parameters
    ----------
    delete_files : bool
        if True it will actually delete the files, if False print
    """
    with qdb.sql_connection.TRN:
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
        qdb.sql_connection.TRN.add(sql)

        union_str = " UNION ".join(
            ["SELECT %s FROM qiita.%s WHERE %s IS NOT NULL" % (col, table, col)
             for table, col in qdb.sql_connection.TRN.execute_fetchindex()])
        if union_str:
            # Get all the filepaths from the filepath table that are not
            # referenced from any place in the database
            sql = """SELECT filepath_id, filepath, filepath_type, data_directory_id
                FROM qiita.filepath FP JOIN qiita.filepath_type FPT
                    ON FP.filepath_type_id = FPT.filepath_type_id
                WHERE filepath_id NOT IN (%s)""" % union_str
            qdb.sql_connection.TRN.add(sql)

        # We can now go over and remove all the filepaths
        sql = "DELETE FROM qiita.filepath WHERE filepath_id=%s"
        db_results = qdb.sql_connection.TRN.execute_fetchindex()
        for fp_id, fp, fp_type, dd_id in db_results:
            if delete_files:
                qdb.sql_connection.TRN.add(sql, [fp_id])
                fp = join(get_mountpoint_path_by_id(dd_id), fp)
                _rm_files(qdb.sql_connection.TRN, fp)
            else:
                print fp, fp_type

        if delete_files:
            qdb.sql_connection.TRN.execute()


def empty_trash_upload_folder(delete_files=True):
    r"""Delete all files in the trash folder inside each of the upload
    folders

    Parameters
    ----------
    delete_files : bool
        if True it will actually delete the files, if False print
    """
    gfp = partial(join, get_db_files_base_dir())
    with qdb.sql_connection.TRN:
        sql = """SELECT mountpoint
                 FROM qiita.data_directory
                 WHERE data_type = 'uploads'"""
        qdb.sql_connection.TRN.add(sql)

        for mp in qdb.sql_connection.TRN.execute_fetchflatten():
            for path, dirs, files in walk(gfp(mp)):
                if path.endswith('/trash'):
                    if delete_files:
                        for f in files:
                            fp = join(path, f)
                            _rm_files(qdb.sql_connection.TRN, fp)
                    else:
                        print files

        if delete_files:
            qdb.sql_connection.TRN.execute()


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
    with qdb.sql_connection.TRN:
        uploads_fp = join(get_mountpoint("uploads")[0][1], str(study_id))

        if not exists(uploads_fp):
            makedirs(uploads_fp)

        path_builder = partial(join, uploads_fp)

        # We can now go over and remove all the filepaths
        sql = """DELETE FROM qiita.filepath WHERE filepath_id=%s"""
        for fp_id, fp, fp_type in filepaths:
            qdb.sql_connection.TRN.add(sql, [fp_id])

            if fp_type == 'html_summary':
                qdb.sql_connection.TRN.add_post_commit_func(
                    remove, fp)
            else:
                destination = path_builder(basename(fp))

                qdb.sql_connection.TRN.add_post_rollback_func(
                    move, destination, fp)
                move(fp, destination)

        qdb.sql_connection.TRN.execute()


def filepath_id_to_rel_path(filepath_id):
    """Gets the relative to the base directory of filepath_id

    Returns
    -------
    str
        The relative path for the given filepath id
    """
    with qdb.sql_connection.TRN:
        sql = """SELECT mountpoint, filepath, subdirectory, artifact_id
                 FROM qiita.filepath
                    JOIN qiita.data_directory USING (data_directory_id)
                    LEFT JOIN qiita.artifact_filepath USING (filepath_id)
                 WHERE filepath_id = %s"""
        qdb.sql_connection.TRN.add(sql, [filepath_id])
        # It should be only one row
        mp, fp, sd, a_id = qdb.sql_connection.TRN.execute_fetchindex()[0]
        if sd:
            result = join(mp, str(a_id), fp)
        else:
            result = join(mp, fp)
        return result


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

    with qdb.sql_connection.TRN:
        sql = """SELECT filepath_id, mountpoint, filepath, subdirectory,
                        artifact_id
                 FROM qiita.filepath
                    JOIN qiita.data_directory USING (data_directory_id)
                    LEFT JOIN qiita.artifact_filepath USING (filepath_id)
                 WHERE filepath_id IN %s"""
        qdb.sql_connection.TRN.add(sql, [tuple(filepath_ids)])
        res = {}
        for row in qdb.sql_connection.TRN.execute_fetchindex():
            if row[3]:
                res[row[0]] = join(row[1], str(row[4]), row[2])
            else:
                res[row[0]] = join(row[1], row[2])
        return res


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
    QiitaDBLookupError
        The passed string has no associated id
    """
    text_col = table if text_col is None else text_col
    with qdb.sql_connection.TRN:
        sql = "SELECT {0}_id FROM qiita.{0} WHERE {1} = %s".format(
            table, text_col)
        qdb.sql_connection.TRN.add(sql, [value])
        _id = qdb.sql_connection.TRN.execute_fetchindex()
        if not _id:
            raise qdb.exceptions.QiitaDBLookupError(
                "%s not valid for table %s" % (value, table))
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
    QiitaDBLookupError
        The passed id has no associated string
    """
    with qdb.sql_connection.TRN:
        sql = "SELECT {0} FROM qiita.{0} WHERE {0}_id = %s".format(table)
        qdb.sql_connection.TRN.add(sql, [value])
        string = qdb.sql_connection.TRN.execute_fetchindex()
        if not string:
            raise qdb.exceptions.QiitaDBLookupError(
                "%s not valid for table %s" % (value, table))
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
    with qdb.sql_connection.TRN:
        sql = "SELECT count(1) FROM %s" % table
        qdb.sql_connection.TRN.add(sql)
        return qdb.sql_connection.TRN.execute_fetchlast()


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


def get_environmental_packages():
    """Get the list of available environmental packages

    Returns
    -------
    list of (str, str)
        The available environmental packages. The first string is the
        environmental package name and the second string is the table where
        the metadata for the environmental package is stored
    """
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add("SELECT * FROM qiita.environmental_package")
        return qdb.sql_connection.TRN.execute_fetchindex()


def get_visibilities():
    """Get the list of available visibilities for artifacts

    Returns
    -------
    list of str
        The available visibilities
    """
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add("SELECT visibility FROM qiita.visibility")
        return qdb.sql_connection.TRN.execute_fetchflatten()


def get_timeseries_types():
    """Get the list of available timeseries types

    Returns
    -------
    list of (int, str, str)
        The available timeseries types. Each timeseries type is defined by the
        tuple (timeseries_id, timeseries_type, intervention_type)
    """
    with qdb.sql_connection.TRN:
        sql = "SELECT * FROM qiita.timeseries_type ORDER BY timeseries_type_id"
        qdb.sql_connection.TRN.add(sql)
        return qdb.sql_connection.TRN.execute_fetchindex()


def get_pubmed_ids_from_dois(doi_ids):
    """Get the dict of pubmed ids from a list of doi ids

    Parameters
    ----------
    doi_ids : list of str
        The list of doi ids

    Returns
    -------
    dict of {doi: pubmed_id}
        Return dict of doi and pubmed ids

    Notes
    -----
    If doi doesn't exist it will not return that {key: value} pair
    """
    with qdb.sql_connection.TRN:
        sql = "SELECT doi, pubmed_id FROM qiita.publication WHERE doi IN %s"
        qdb.sql_connection.TRN.add(sql, [tuple(doi_ids)])
        return {row[0]: row[1]
                for row in qdb.sql_connection.TRN.execute_fetchindex()}


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


def add_message(message, users):
    """Adds a message to the messages table, attaching it to given users

    Parameters
    ----------
    message : str
        Message to add
    users : list of User objects
        Users to connect the message to
    """
    with qdb.sql_connection.TRN:
        sql = """INSERT INTO qiita.message (message) VALUES (%s)
                 RETURNING message_id"""
        qdb.sql_connection.TRN.add(sql, [message])
        msg_id = qdb.sql_connection.TRN.execute_fetchlast()
        sql = """INSERT INTO qiita.message_user (email, message_id)
                 VALUES (%s, %s)"""
        sql_args = [[user.id, msg_id] for user in users]
        qdb.sql_connection.TRN.add(sql, sql_args, many=True)
        qdb.sql_connection.TRN.execute()


def add_system_message(message, expires):
    """Adds a system message to the messages table, attaching it to asl users

    Parameters
    ----------
    message : str
        Message to add
    expires : datetime object
        Expiration for the message
    """
    with qdb.sql_connection.TRN:
        sql = """INSERT INTO qiita.message (message, expiration)
                 VALUES (%s, %s)
                 RETURNING message_id"""
        qdb.sql_connection.TRN.add(sql, [message, expires])
        msg_id = qdb.sql_connection.TRN.execute_fetchlast()
        sql = """INSERT INTO qiita.message_user (email, message_id)
                 SELECT email, %s FROM qiita.qiita_user"""
        qdb.sql_connection.TRN.add(sql, [msg_id])
        qdb.sql_connection.TRN.execute()


def clear_system_messages():
    with qdb.sql_connection.TRN:
        sql = "SELECT message_id FROM qiita.message WHERE expiration < %s"
        qdb.sql_connection.TRN.add(sql, [datetime.now()])
        msg_ids = qdb.sql_connection.TRN.execute_fetchflatten()
        if msg_ids:
            msg_ids = tuple(msg_ids)
            sql = "DELETE FROM qiita.message_user WHERE message_id IN %s"
            qdb.sql_connection.TRN.add(sql, [msg_ids])
            sql = "DELETE FROM qiita.message WHERE message_id IN %s"
            qdb.sql_connection.TRN.add(sql, [msg_ids])
            qdb.sql_connection.TRN.execute()


def supported_filepath_types(artifact_type):
    """Returns the list of supported filepath types for the given artifact type

    Parameters
    ----------
    artifact_type : str
        The artifact type to check the supported filepath types

    Returns
    -------
    list of [str, bool]
        The list of supported filepath types and whether it is required by the
        artifact type or not
    """
    with qdb.sql_connection.TRN:
        sql = """SELECT DISTINCT filepath_type, required
                 FROM qiita.artifact_type_filepath_type
                    JOIN qiita.artifact_type USING (artifact_type_id)
                    JOIN qiita.filepath_type USING (filepath_type_id)
                 WHERE artifact_type = %s"""
        qdb.sql_connection.TRN.add(sql, [artifact_type])
        return qdb.sql_connection.TRN.execute_fetchindex()


def generate_study_list(study_ids, public_only=False):
    """Get general study information

    Parameters
    ----------
    study_ids : list of ints
        The study ids to look for. Non-existing ids will be ignored
    public_only : bool, optional
        If true, return only public BIOM artifacts. Default: false.

    Returns
    -------
    list of dict
        The list of studies and their information

    Notes
    -----
    The main select might look scary but it's pretty simple:
    - We select the requiered fields from qiita.study and qiita.study_person
        SELECT metadata_complete, study_abstract, study_id, study_alias,
            study_title, ebi_study_accession, ebi_submission_status,
            qiita.study_person.name AS pi_name,
            qiita.study_person.email AS pi_email,
    - the total number of samples collected by counting sample_ids
            (SELECT COUNT(sample_id) FROM qiita.study_sample
                WHERE study_id=qiita.study.study_id)
                AS number_samples_collected]
    - all the BIOM artifact_ids sorted by artifact_id that belong to the study
            (SELECT array_agg(artifact_id ORDER BY artifact_id)
                FROM qiita.study_artifact
                LEFT JOIN qiita.artifact USING (artifact_id)
                LEFT JOIN qiita.artifact_type USING (artifact_type_id)
                WHERE artifact_type='BIOM' AND
                study_id = qiita.study.study_id) AS artifact_biom_ids,
    - all the publications that belong to the study
            (SELECT array_agg((publication, is_doi)))
                FROM qiita.study_publication
                WHERE study_id=qiita.study.study_id) AS publications,
    - all names sorted by email of users that have access to the study
            (SELECT array_agg(name ORDER BY email) FROM qiita.study_users
                LEFT JOIN qiita.qiita_user USING (email)
                WHERE study_id=qiita.study.study_id) AS shared_with_name,
    - all emails sorted by email of users that have access to the study
            (SELECT array_agg(email ORDER BY email) FROM qiita.study_users
                LEFT JOIN qiita.qiita_user USING (email)
                WHERE study_id=qiita.study.study_id) AS shared_with_email
    - all study tags
            (SELECT array_agg(study_tag) FROM qiita.per_study_tags
                WHERE study_id=qiita.study.study_id) AS study_tags
    - study owner
            (SELECT name FROM qiita.qiita_user
                WHERE email=qiita.study.email) AS owner
    """
    with qdb.sql_connection.TRN:
        sql = """
            SELECT metadata_complete, study_abstract, study_id, study_alias,
                study_title, ebi_study_accession, ebi_submission_status,
                qiita.study_person.name AS pi_name,
                qiita.study_person.email AS pi_email,
                (SELECT COUNT(sample_id) FROM qiita.study_sample
                    WHERE study_id=qiita.study.study_id)
                    AS number_samples_collected,
                (SELECT array_agg(artifact_id ORDER BY artifact_id)
                    FROM qiita.study_artifact
                    LEFT JOIN qiita.artifact USING (artifact_id)
                    LEFT JOIN qiita.artifact_type USING (artifact_type_id)
                    WHERE artifact_type='BIOM' AND
                        study_id = qiita.study.study_id) AS artifact_biom_ids,
                (SELECT array_agg(row_to_json((publication, is_doi), true))
                    FROM qiita.study_publication
                    WHERE study_id=qiita.study.study_id) AS publications,
                (SELECT array_agg(name ORDER BY email) FROM qiita.study_users
                    LEFT JOIN qiita.qiita_user USING (email)
                    WHERE study_id=qiita.study.study_id) AS shared_with_name,
                (SELECT array_agg(email ORDER BY email) FROM qiita.study_users
                    LEFT JOIN qiita.qiita_user USING (email)
                    WHERE study_id=qiita.study.study_id) AS shared_with_email,
                (SELECT array_agg(study_tag) FROM qiita.per_study_tags
                    WHERE study_id=qiita.study.study_id) AS study_tags,
                (SELECT name FROM qiita.qiita_user
                    WHERE email=qiita.study.email) AS owner
                FROM qiita.study
                LEFT JOIN qiita.study_person ON (
                    study_person_id=principal_investigator_id)
                WHERE study_id IN %s
                ORDER BY study_id"""
        qdb.sql_connection.TRN.add(sql, [tuple(study_ids)])
        infolist = []
        for info in qdb.sql_connection.TRN.execute_fetchindex():
            info = dict(info)

            # publication info
            info['publication_doi'] = []
            info['publication_pid'] = []
            if info['publications'] is not None:
                for p in info['publications']:
                    # f1-2 are the default names given
                    pub = p['f1']
                    is_doi = p['f2']
                    if is_doi:
                        info['publication_doi'].append(pub)
                    else:
                        info['publication_pid'].append(pub)
            del info['publications']

            # pi info
            info["pi"] = (info['pi_email'], info['pi_name'])
            del info["pi_email"]
            del info["pi_name"]

            # shared with
            info['shared'] = []
            if info['shared_with_name'] and info['shared_with_email']:
                for name, email in zip(info['shared_with_name'],
                                       info['shared_with_email']):
                    if not name:
                        name = email
                    info['shared'].append((email, name))
            del info["shared_with_name"]
            del info["shared_with_email"]

            infolist.append({
                'owner': info['owner'],
                'study_alias': info['study_alias'],
                'metadata_complete': info['metadata_complete'],
                'publication_pid': info['publication_pid'],
                'ebi_submission_status': info['ebi_submission_status'],
                'shared': info['shared'],
                'study_abstract': info['study_abstract'], 'pi': info['pi'],
                'status': qdb.study.Study(info['study_id']).status,
                'study_tags': info['study_tags'],
                'publication_doi': info['publication_doi'],
                'study_id': info['study_id'],
                'ebi_study_accession': info['ebi_study_accession'],
                'study_title': info['study_title'],
                'number_samples_collected': info['number_samples_collected'],
                'artifact_biom_ids': info['artifact_biom_ids']
            })

    return infolist


def get_artifacts_information(artifact_ids, only_biom=True):
        """Returns processing information about the artifact ids

        Parameters
        ----------
        artifact_ids : list of ints
            The artifact ids to look for. Non-existing ids will be ignored
        only_biom : bool
            If true only the biom artifacts are retrieved

        Returns
        -------
        dict
            The info of the artifacts
        """
        if not artifact_ids:
            return {}

        sql = """
            WITH main_query AS (
                SELECT a.artifact_id, a.name, a.command_id,
                       a.generated_timestamp, array_agg(a.command_parameters),
                       dt.data_type, parent_id,
                       array_agg(parent_info.command_parameters),
                       array_agg(filepaths.filepath),
                       qiita.find_artifact_roots(a.artifact_id) AS root_id
                FROM qiita.artifact a"""
        if only_biom:
            sql += """
                JOIN qiita.artifact_type at ON (
                    a.artifact_type_id = at .artifact_type_id
                        AND artifact_type = 'BIOM')"""
        sql += """
                LEFT JOIN qiita.parent_artifact pa ON (
                    a.artifact_id = pa.artifact_id)
                LEFT JOIN qiita.data_type dt USING (data_type_id)
                LEFT OUTER JOIN LATERAL (
                    SELECT command_parameters FROM qiita.artifact ap
                    WHERE ap.artifact_id = pa.parent_id) parent_info ON true
                LEFT OUTER JOIN LATERAL (
                    SELECT filepath
                    FROM qiita.artifact_filepath af
                    JOIN qiita.filepath USING (filepath_id)
                    WHERE af.artifact_id = a.artifact_id) filepaths ON true
                WHERE a.artifact_id IN %s
                GROUP BY a.artifact_id, a.name, a.command_id,
                         a.generated_timestamp, dt.data_type, parent_id
                ORDER BY command_id, artifact_id),
              has_target_subfragment AS (
                SELECT main_query.*, CASE WHEN (
                        SELECT true FROM information_schema.columns
                        WHERE table_name = 'prep_' || CAST(
                            prep_template_id AS TEXT)
                        AND column_name='target_subfragment')
                    THEN prep_template_id ELSE NULL END, prep_template_id
                FROM main_query
                LEFT JOIN qiita.prep_template pt ON (
                    main_query.root_id = pt.artifact_id)
            )
            SELECT * FROM has_target_subfragment
            ORDER BY command_id, data_type, artifact_id
            """

        sql_params = """
            SELECT parameter_set_name, array_agg(parameter_set) AS param_set
            FROM qiita.default_parameter_set
            GROUP BY parameter_set_name"""

        sql_ts = """SELECT DISTINCT target_subfragment FROM qiita.prep_%s"""

        with qdb.sql_connection.TRN:
            results = []
            commands = {}
            # obtaining all existing parameters, note that
            # they are not that many (~40) and we don't expect
            # to have a huge growth in the near future
            qdb.sql_connection.TRN.add(sql_params)
            params = {name: set(params[0].iteritems()) for name, params in
                      qdb.sql_connection.TRN.execute_fetchindex()}

            # now let's get the actual artifacts
            ts = {}
            ps = {}
            PT = qdb.metadata_template.prep_template.PrepTemplate
            qdb.sql_connection.TRN.add(sql, [tuple(artifact_ids)])
            for row in qdb.sql_connection.TRN.execute_fetchindex():
                aid, name, cid, gt, aparams, dt, pid, pparams, filepaths, _, \
                    target, prep_template_id = row

                # cleaning fields:
                # - [0] due to the array_agg
                pparams = pparams[0]
                if pparams is not None:
                    # [-1] taking the last cause it's sorted by
                    #      the number of overlapping parameters
                    # [0] then taking the first element that is
                    # the name of the parameter set
                    pparams = sorted([
                        [k, len(v & set(pparams.iteritems()))]
                        for k, v in viewitems(params)],
                        key=lambda x: x[1])[-1][0]
                else:
                    pparams = 'N/A'
                # - [0] due to the array_agg
                aparams = aparams[0]
                if aparams is None:
                    aparams = {}
                # - ignoring empty filepaths
                if filepaths == [None]:
                    filepaths = []
                # - ignoring empty target
                if target == [None]:
                    target = []

                algorithm = ''
                if cid is not None:
                    if cid not in commands:
                        c = qdb.software.Command(cid)
                        s = c.software
                        commands[cid] = '%s, %sv%s' % (
                            c.name, s.name, s.version)

                    algorithm = '%s | %s' % (commands[cid], pparams)

                if target is None:
                    target = []
                else:
                    if target not in ts:
                        qdb.sql_connection.TRN.add(sql_ts, [target])
                        ts[target] = \
                            qdb.sql_connection.TRN.execute_fetchflatten()
                    target = ts[target]

                if prep_template_id is None:
                    prep_samples = 0
                else:
                    if prep_template_id not in ps:
                        ps[prep_template_id] = len(list(
                            PT(prep_template_id).keys()))
                    prep_samples = ps[prep_template_id]

                results.append({
                    'artifact_id': aid,
                    'target_subfragment': target,
                    'prep_samples': prep_samples,
                    'name': name,
                    'data_type': dt,
                    'timestamp': str(gt),
                    'parameters': aparams,
                    'algorithm': algorithm,
                    'files': filepaths})

            return results


def _is_string_or_bytes(s):
    """Returns True if input argument is string (unicode or not) or bytes.
    """
    return isinstance(s, str) or isinstance(s, bytes)


def _get_filehandle(filepath_or, *args, **kwargs):
    """Open file if `filepath_or` looks like a string/unicode/bytes, else
    pass through.
    """
    if _is_string_or_bytes(filepath_or):
        if h5py.is_hdf5(filepath_or):
            fh, own_fh = h5py.File(filepath_or, *args, **kwargs), True
        else:
            fh, own_fh = open(filepath_or, *args, **kwargs), True
    else:
        fh, own_fh = filepath_or, False
    return fh, own_fh


@contextmanager
def open_file(filepath_or, *args, **kwargs):
    """Context manager, like ``open``, but lets file handles and file like
    objects pass untouched.

    It is useful when implementing a function that can accept both
    strings and file-like objects (like numpy.loadtxt, etc).

    This method differs slightly from scikit-bio's implementation in that it
    handles HDF5 files appropriately.

    Parameters
    ----------
    filepath_or : str/bytes/unicode string or file-like
         If string, file to be opened using ``h5py.File`` if the file is an
         HDF5 file, otherwise builtin ``open`` will be used. If it is not a
         string, the object is just returned untouched.

    Other parameters
    ----------------
    args, kwargs : tuple, dict
        When `filepath_or` is a string, any extra arguments are passed
        on to the ``open`` builtin.

    Examples
    --------
    >>> with open_file('filename') as f:  # doctest: +SKIP
    ...     pass
    >>> fh = open('filename')             # doctest: +SKIP
    >>> with open_file(fh) as f:          # doctest: +SKIP
    ...     pass
    >>> fh.closed                         # doctest: +SKIP
    False
    >>> fh.close()                        # doctest: +SKIP

    """
    fh, own_fh = _get_filehandle(filepath_or, *args, **kwargs)
    try:
        yield fh
    finally:
        if own_fh:
            fh.close()
