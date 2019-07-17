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
    filepath_id_to_rel_path
    filepath_id_to_object_id
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
    generate_analysis_list
    human_merging_scheme
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
from random import SystemRandom
from string import ascii_letters, digits, punctuation
from binascii import crc32
from bcrypt import hashpw, gensalt
from functools import partial
from os.path import join, basename, isdir, exists, getsize
from os import walk, remove, listdir, rename
from glob import glob
from shutil import move, rmtree, copy as shutil_copy
from openpyxl import load_workbook
from tempfile import mkstemp
from csv import writer as csv_writer
from datetime import datetime
from itertools import chain
from contextlib import contextmanager
from future.builtins import bytes, str
import h5py
from humanize import naturalsize
import hashlib
from smtplib import SMTP, SMTP_SSL, SMTPException

from os import makedirs
from errno import EEXIST
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb

from future import standard_library

with standard_library.hooks():
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText


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
    return ''.join(sr.choice(chars) for i in range(length))


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
    filepaths = []
    if isdir(path):
        for name, dirs, files in walk(path):
            join_f = partial(join, name)
            filepaths.extend(list(map(join_f, files)))
    else:
        filepaths.append(path)

    buffersize = 65536
    crcvalue = 0
    for fp in filepaths:
        with open(fp, 'rb') as f:
            buffr = f.read(buffersize)
            while len(buffr) > 0:
                crcvalue = crc32(buffr, crcvalue)
                buffr = f.read(buffersize)
    # We need the & 0xFFFFFFFF in order to get the same numeric value across
    # all python versions and platforms
    return crcvalue & 0xFFFFFFFF


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
            for f in listdir(t):
                d = join(t, f)
                if not f.startswith('.') and not isdir(d):
                    fp.append((pid, f, naturalsize(getsize(d))))

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
        create_nested_path(trashpath)

        fullpath = join(foldername, filename)
        new_fullpath = join(foldername, trash_folder, filename)

        if exists(fullpath):
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
                create_nested_path(dirname)
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
            return (x if isinstance(x, int)
                    else convert_to_id(x, "filepath_type"))
        # 1 is the checksum algorithm, which we only have one implemented
        values = [[basename(path), str_to_id(id_), compute_checksum(path),
                   getsize(path), 1, dd_id] for path, id_ in new_filepaths]
        # Insert all the filepaths at once and get the filepath_id back
        sql = """INSERT INTO qiita.filepath
                    (filepath, filepath_type_id, checksum, fp_size,
                     checksum_algorithm_id, data_directory_id)
                 VALUES (%s, %s, %s, %s, %s, %s)
                 RETURNING filepath_id"""
        idx = qdb.sql_connection.TRN.index
        qdb.sql_connection.TRN.add(sql, values, many=True)
        # Since we added the query with many=True, we've added len(values)
        # queries to the transaction, so the ids are in the last idx queries
        return list(chain.from_iterable(
            chain.from_iterable(qdb.sql_connection.TRN.execute()[idx:])))


def _path_builder(db_dir, filepath, mountpoint, subdirectory, obj_id):
    """Builds the path of a DB stored file

    Parameters
    ----------
    db_dir : str
        The DB base dir
    filepath : str
        The path stored in the DB
    mountpoint : str
        The mountpoint of the given file
    subdirectory : bool
        Whether the file is stored in a subdirectory in the mountpoint or not
    obj_id : int
        The id of the object to which the file is attached

    Returns
    -------
    str
        The full path of the given file
    """
    if subdirectory:
        return join(db_dir, mountpoint, str(obj_id), filepath)
    else:
        return join(db_dir, mountpoint, filepath)


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
    list of dict {fp_id, fp, ft_type, checksum, fp_size}
        The list of dict with the properties of the filepaths
    """

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
                        subdirectory, checksum, fp_size
                 FROM qiita.filepath
                    JOIN qiita.filepath_type USING (filepath_type_id)
                    JOIN qiita.data_directory USING (data_directory_id)
                    JOIN qiita.{0} USING (filepath_id)
                 WHERE {1} = %s{2}{3}""".format(obj_fp_table, obj_id_column,
                                                sql_type, sql_sort)
        qdb.sql_connection.TRN.add(sql, sql_args)
        results = qdb.sql_connection.TRN.execute_fetchindex()
        db_dir = get_db_files_base_dir()

        return [{'fp_id': fpid, 'fp': _path_builder(db_dir, fp, m, s, obj_id),
                 'fp_type': fp_type_, 'checksum': c, 'fp_size': fpsize}
                for fpid, fp, fp_type_, m, s, c, fpsize in results]


def _rm_files(TRN, fp):
    # Remove the data
    if exists(fp):
        if isdir(fp):
            func = rmtree
        else:
            func = remove
        TRN.add_post_commit_func(func, fp)


def purge_filepaths(delete_files=True):
    r"""Goes over the filepath table and removes all the filepaths that are not
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
                print(fp, fp_type)

        if delete_files:
            qdb.sql_connection.TRN.execute()


def _rm_exists(fp, obj, _id, delete_files):
    try:
        _id = int(_id)
        obj(_id)
    except Exception:
        _id = str(_id)
        if delete_files:
            with qdb.sql_connection.TRN:
                _rm_files(qdb.sql_connection.TRN, fp)
                qdb.sql_connection.TRN.execute()
        else:
            print("Remove %s" % fp)


def purge_files_from_filesystem(delete_files=True):
    r"""Goes over the filesystem and removes all the filepaths that are not
    used in any place

    Parameters
    ----------
    delete_files : bool
        if True it will actually delete the files, if False print
    """
    # Step 1, check which mounts actually exists, we'll just report the
    #         discrepancies
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add(
            "SELECT DISTINCT data_type FROM qiita.data_directory")
        mount_types = qdb.sql_connection.TRN.execute_fetchflatten()

    fbd = qdb.util.get_db_files_base_dir()
    actual_paths = {join(fbd, x) for x in listdir(fbd)}
    db_paths = {fp for mt in mount_types
                for x, fp in qdb.util.get_mountpoint(mt, retrieve_all=True)}

    missing_db = actual_paths - db_paths
    if missing_db:
        print('\n\npaths without db entries: %s\n\n' % ', '.join(missing_db))
    missing_paths = [x for x in db_paths - actual_paths if not isdir(x)]
    if missing_paths:
        print('\n\npaths without actual mounts: %s\n\n' % ', '.join(
            missing_paths))

    # Step 2, clean based on the 2 main group: True/False subdirectory
    # subdirectory True, the artifacts are stored within their own folders
    paths = {fp for mt in mount_types
             for x, fp, sp in get_mountpoint(mt, True, True) if sp}
    for pt in paths:
        if isdir(pt):
            for aid in listdir(pt):
                _rm_exists(
                    join(pt, aid), qdb.artifact.Artifact, aid, delete_files)
    # subdirectory False - this are the legacy folders, the files are stored
    # in the base folder prepended with the element id, which are:
    #  *** ignored or not in use anymore ***
    # - job
    # - preprocessed_data
    # - processed_data
    # - raw_data
    # - reference
    # - working_dir
    #  *** dealing ***
    # - analysis
    # - templates
    # - uploads
    data_types = {
        'analysis': qdb.analysis.Analysis,
        'templates': qdb.study.Study,
        'uploads': qdb.study.Study
    }
    for dt, obj in data_types.items():
        for _, pt in get_mountpoint(dt, True):
            if isdir(pt):
                for ppt in listdir(pt):
                    obj_id = ppt.split('_')[0]
                    _rm_exists(join(pt, ppt), obj, obj_id, delete_files)


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
                        print(files)

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

        create_nested_path(uploads_fp)

        path_builder = partial(join, uploads_fp)

        # We can now go over and remove all the filepaths
        sql = """DELETE FROM qiita.filepath WHERE filepath_id = %s"""
        for x in filepaths:
            qdb.sql_connection.TRN.add(sql, [x['fp_id']])

            if x['fp_type'] == 'html_summary':
                _rm_files(qdb.sql_connection.TRN, x['fp'])
            else:
                destination = path_builder(basename(x['fp']))

                qdb.sql_connection.TRN.add_post_rollback_func(
                    move, destination, x['fp'])
                move(x['fp'], destination)

        qdb.sql_connection.TRN.execute()


def get_filepath_information(filepath_id):
    """Gets the filepath information of filepath_id

    Parameters
    ----------
    filepath_id : int
        The filepath id

    Returns
    -------
    dict
        The filepath information
    """
    with qdb.sql_connection.TRN:
        sql = """SELECT filepath_id, filepath, filepath_type, checksum,
                        data_type, mountpoint, subdirectory, active,
                        artifact_id
                 FROM qiita.filepath
                    JOIN qiita.filepath_type USING (filepath_type_id)
                    JOIN qiita.data_directory USING (data_directory_id)
                    LEFT JOIN qiita.artifact_filepath USING (filepath_id)
                 WHERE filepath_id = %s"""
        qdb.sql_connection.TRN.add(sql, [filepath_id])
        res = dict(qdb.sql_connection.TRN.execute_fetchindex()[0])

        obj_id = res.pop('artifact_id')
        res['fullpath'] = _path_builder(get_db_files_base_dir(),
                                        res['filepath'], res['mountpoint'],
                                        res['subdirectory'], obj_id)
        return res


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


def filepath_id_to_object_id(filepath_id):
    """Gets the object id to which the filepath id belongs to

    Returns
    -------
    int
        The object id the filepath id belongs to or None if not found

    Notes
    -----
    This helper function is intended to be used with the download handler so
    we can prepend downloads with the artifact id; thus, we will only look for
    filepath ids in qiita.analysis_filepath and qiita.artifact_filepath as
    search in qiita.reference, qiita.prep_template_filepath and
    qiita.sample_template_filepath will make the naming redundat (those already
    have the study_id in their filename)
    """
    with qdb.sql_connection.TRN:
        sql = """
            SELECT analysis_id FROM qiita.analysis_filepath
                WHERE filepath_id = %s UNION
            SELECT artifact_id FROM qiita.artifact_filepath
                WHERE filepath_id = %s"""
        qdb.sql_connection.TRN.add(sql, [filepath_id, filepath_id])
        fids = sorted(qdb.sql_connection.TRN.execute_fetchflatten())
        if fids:
            return fids[0]
        return None


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


def generate_study_list(user, visibility):
    """Get general study information

    Parameters
    ----------
    user : qiita_db.user.User
        The user of which we are requesting studies from
    visibility : string
        The visibility to get studies {'public', 'user'}

    Returns
    -------
    list of dict
        The list of studies and their information

    Notes
    -----
    The main select might look scary but it's pretty simple:
    - We select the requiered fields from qiita.study and qiita.study_person
        SELECT metadata_complete, study_abstract, study_id, study_alias,
            study_title, ebi_study_accession,
            qiita.study_person.name AS pi_name,
            qiita.study_person.email AS pi_email,
    - the total number of samples collected by counting sample_ids
            (SELECT COUNT(sample_id) FROM qiita.study_sample
                WHERE study_id=qiita.study.study_id)
                AS number_samples_collected]
    - retrieve all the prep data types for all the artifacts depending on their
      visibility
            (SELECT array_agg(DISTINCT data_type)
             FROM qiita.study_prep_template
             LEFT JOIN qiita.prep_template USING (prep_template_id)
             LEFT JOIN qiita.data_type USING (data_type_id)
             LEFT JOIN qiita.artifact USING (artifact_id)
             LEFT JOIN qiita.visibility USING (visibility_id)
             LEFT JOIN qiita.artifact_type USING (artifact_type_id)
             WHERE {0} study_id = qiita.study.study_id)
                 AS preparation_data_types,
    - all the BIOM artifact_ids sorted by artifact_id that belong to the study,
      including their software deprecated value and their prep info file data
      type values
            (SELECT array_agg(row_to_json(
             (m_aid.artifact_id, qs.deprecated), true)
                 ORDER BY artifact_id)
             FROM qiita.study_artifact
             LEFT JOIN qiita.artifact AS m_aid USING (artifact_id)
             LEFT JOIN qiita.visibility USING (visibility_id)
             LEFT JOIN qiita.artifact_type USING (artifact_type_id)
             LEFT JOIN qiita.software_command USING (command_id)
             LEFT JOIN qiita.software qs USING (software_id)
             WHERE artifact_type='BIOM' AND {0}
                 study_id = qiita.study.study_id) AS aids_with_deprecation,
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

    visibility_sql = ''
    sids = set(s.id for s in user.user_studies.union(user.shared_studies))
    if visibility == 'user':
        if user.level == 'admin':
            sids = (sids |
                    qdb.study.Study.get_ids_by_status('sandbox') |
                    qdb.study.Study.get_ids_by_status('private') |
                    qdb.study.Study.get_ids_by_status('awaiting_approval'))
    elif visibility == 'public':
        sids = qdb.study.Study.get_ids_by_status('public') - sids
        visibility_sql = "visibility = 'public' AND"
    else:
        raise ValueError('Not a valid visibility: %s' % visibility)

    sql = """
        SELECT metadata_complete, study_abstract, study_id, study_alias,
            study_title, ebi_study_accession,
            qiita.study_person.name AS pi_name,
            qiita.study_person.email AS pi_email,
            (SELECT COUNT(sample_id) FROM qiita.study_sample
                WHERE study_id=qiita.study.study_id)
                AS number_samples_collected,
            (SELECT array_agg(DISTINCT data_type)
                FROM qiita.study_prep_template
                LEFT JOIN qiita.prep_template USING (prep_template_id)
                LEFT JOIN qiita.data_type USING (data_type_id)
                LEFT JOIN qiita.artifact USING (artifact_id)
                LEFT JOIN qiita.visibility USING (visibility_id)
                LEFT JOIN qiita.artifact_type USING (artifact_type_id)
                WHERE {0} study_id = qiita.study.study_id)
                    AS preparation_data_types,
            (SELECT array_agg(row_to_json(
                (m_aid.artifact_id, qs.deprecated), true)
                    ORDER BY artifact_id)
                FROM qiita.study_artifact
                LEFT JOIN qiita.artifact AS m_aid USING (artifact_id)
                LEFT JOIN qiita.visibility USING (visibility_id)
                LEFT JOIN qiita.artifact_type USING (artifact_type_id)
                LEFT JOIN qiita.software_command USING (command_id)
                LEFT JOIN qiita.software qs USING (software_id)
                WHERE artifact_type='BIOM' AND {0}
                    study_id = qiita.study.study_id) AS aids_with_deprecation,
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
                WHERE email=qiita.study.email) AS owner,
            qiita.study.email AS owner_email
            FROM qiita.study
            LEFT JOIN qiita.study_person ON (
                study_person_id=principal_investigator_id)
            WHERE study_id IN %s
            ORDER BY study_id""".format(visibility_sql)

    infolist = []
    if sids:
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql, [tuple(sids)])
            for info in qdb.sql_connection.TRN.execute_fetchindex():
                info = dict(info)

                # cleaning owners name
                if info['owner'] in (None, ''):
                    info['owner'] = info['owner_email']
                del info['owner_email']

                # cleaning aids_with_deprecation
                info['artifact_biom_ids'] = []
                if info['aids_with_deprecation'] is not None:
                    for x in info['aids_with_deprecation']:
                        # f1-2 are the default names given by pgsql
                        if not x['f2']:
                            info['artifact_biom_ids'].append(x['f1'])
                del info['aids_with_deprecation']

                if info['preparation_data_types'] is None:
                    info['preparation_data_types'] = []

                # publication info
                info['publication_doi'] = []
                info['publication_pid'] = []
                if info['publications'] is not None:
                    for p in info['publications']:
                        # f1-2 are the default names given by pgsql
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

                study = qdb.study.Study(info['study_id'])
                info['status'] = study.status
                info['ebi_submission_status'] = study.ebi_submission_status
                infolist.append(info)
    return infolist


def generate_study_list_without_artifacts(study_ids, portal=None):
    """Get general study information without artifacts

    Parameters
    ----------
    study_ids : list of ints
        The study ids to look for. Non-existing ids will be ignored
    portal : str
        Portal to use, if None take it from configuration. Mainly for tests.

    Returns
    -------
    list of dict
        The list of studies and their information

    Notes
    -----
    The main select might look scary but it's pretty simple:
    - We select the requiered fields from qiita.study and qiita.study_person
        SELECT metadata_complete, study_abstract, study_id, study_alias,
            study_title, ebi_study_accession,
            qiita.study_person.name AS pi_name,
            qiita.study_person.email AS pi_email,
    - the total number of samples collected by counting sample_ids
            (SELECT COUNT(sample_id) FROM qiita.study_sample
                WHERE study_id=qiita.study.study_id)
                AS number_samples_collected]
    - all the publications that belong to the study
            (SELECT array_agg((publication, is_doi)))
                FROM qiita.study_publication
                WHERE study_id=qiita.study.study_id) AS publications
    """
    if portal is None:
        portal = qiita_config.portal
    with qdb.sql_connection.TRN:
        sql = """
            SELECT metadata_complete, study_abstract, study_id, study_alias,
                study_title, ebi_study_accession,
                qiita.study_person.name AS pi_name,
                qiita.study_person.email AS pi_email,
                (SELECT COUNT(sample_id) FROM qiita.study_sample
                    WHERE study_id=qiita.study.study_id)
                    AS number_samples_collected,
                (SELECT array_agg(row_to_json((publication, is_doi), true))
                    FROM qiita.study_publication
                    WHERE study_id=qiita.study.study_id) AS publications
                FROM qiita.study
                LEFT JOIN qiita.study_portal USING (study_id)
                LEFT JOIN qiita.portal_type USING (portal_type_id)
                LEFT JOIN qiita.study_person ON (
                    study_person_id=principal_investigator_id)
                WHERE study_id IN %s AND portal = %s
                ORDER BY study_id"""
        qdb.sql_connection.TRN.add(sql, [tuple(study_ids), portal])
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

            study = qdb.study.Study(info['study_id'])
            info['status'] = study.status
            info['ebi_submission_status'] = study.ebi_submission_status
            infolist.append(info)
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
            SELECT a.artifact_id, a.name, a.command_id as cid, sc.name,
                   a.generated_timestamp, array_agg(a.command_parameters),
                   dt.data_type, parent_id,
                   parent_info.command_id, parent_info.name,
                   array_agg(parent_info.command_parameters),
                   array_agg(filepaths.filepath),
                   qiita.find_artifact_roots(a.artifact_id) AS root_id
            FROM qiita.artifact a
            LEFT JOIN qiita.software_command sc USING (command_id)"""
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
                SELECT command_id, sc.name, command_parameters
                FROM qiita.artifact ap
                LEFT JOIN qiita.software_command sc USING (command_id)
                WHERE ap.artifact_id = pa.parent_id) parent_info ON true
            LEFT OUTER JOIN LATERAL (
                SELECT filepath
                FROM qiita.artifact_filepath af
                JOIN qiita.filepath USING (filepath_id)
                WHERE af.artifact_id = a.artifact_id) filepaths ON true
            WHERE a.artifact_id IN %s
            GROUP BY a.artifact_id, a.name, a.command_id, sc.name,
                     a.generated_timestamp, dt.data_type, parent_id,
                     parent_info.command_id, parent_info.name
            ORDER BY a.command_id, artifact_id),
          has_target_subfragment AS (
            SELECT main_query.*, prep_template_id
            FROM main_query
            LEFT JOIN qiita.prep_template pt ON (
                main_query.root_id = pt.artifact_id)
        )
        SELECT * FROM has_target_subfragment
        ORDER BY cid, data_type, artifact_id
        """

    sql_params = """SELECT command_id, array_agg(parameter_name)
                    FROM qiita.command_parameter
                    WHERE parameter_type = 'artifact'
                    GROUP BY command_id"""

    QCN = qdb.metadata_template.base_metadata_template.QIITA_COLUMN_NAME
    sql_ts = """SELECT DISTINCT sample_values->>'target_subfragment'
                FROM qiita.prep_%s
                WHERE sample_id != '{0}'""".format(QCN)

    with qdb.sql_connection.TRN:
        results = []

        # getting all commands and their artifact parameters so we can
        # delete from the results below
        commands = {}
        qdb.sql_connection.TRN.add(sql_params)
        for cid, params in qdb.sql_connection.TRN.execute_fetchindex():
            cmd = qdb.software.Command(cid)
            commands[cid] = {
                'params': params,
                'merging_scheme': cmd.merging_scheme,
                'active': cmd.active,
                'deprecated': cmd.software.deprecated}

        # Now let's get the actual artifacts. Note that ts is a cache
        # (prep id : target subfragment) so we don't have to query
        # multiple times the target subfragment for a prep info file.
        # However, some artifacts (like analysis) do not have a prep info
        # file; thus we can have a None prep id (key)
        ts = {None: []}
        ps = {}
        algorithm_az = {'': ''}
        PT = qdb.metadata_template.prep_template.PrepTemplate
        qdb.sql_connection.TRN.add(sql, [tuple(artifact_ids)])
        for row in qdb.sql_connection.TRN.execute_fetchindex():
            aid, name, cid, cname, gt, aparams, dt, pid, pcid, pname, \
                pparams, filepaths, _, prep_template_id = row

            # cleaning up aparams & pparams
            # - [0] due to the array_agg
            aparams = aparams[0]
            pparams = pparams[0]
            if aparams is None:
                aparams = {}
            else:
                # we are going to remove any artifacts from the parameters
                for ti in commands[cid]['params']:
                    del aparams[ti]

            # - ignoring empty filepaths
            if filepaths == [None]:
                filepaths = []
            else:
                filepaths = [fp for fp in filepaths if fp.endswith('biom')]

            # generating algorithm, by default is ''
            algorithm = ''
            # set to False because if there is no cid, it means that it
            # was a direct upload
            deprecated = None
            active = None
            if cid is not None:
                deprecated = commands[cid]['deprecated']
                active = commands[cid]['active']
                if pcid is None:
                    parent_merging_scheme = None
                else:
                    parent_merging_scheme = commands[pcid][
                        'merging_scheme']

                algorithm = human_merging_scheme(
                    cname, commands[cid]['merging_scheme'],
                    pname, parent_merging_scheme,
                    aparams, filepaths, pparams)

                if algorithm not in algorithm_az:
                    algorithm_az[algorithm] = hashlib.md5(
                        algorithm.encode('utf-8')).hexdigest()

            if prep_template_id not in ts:
                qdb.sql_connection.TRN.add(sql_ts, [prep_template_id])
                ts[prep_template_id] = \
                    qdb.sql_connection.TRN.execute_fetchflatten()
            target = ts[prep_template_id]

            prep_samples = 0
            platform = 'not provided'
            target_gene = 'not provided'
            if prep_template_id is not None:
                if prep_template_id not in ps:
                    pt = PT(prep_template_id)
                    categories = pt.categories()
                    if 'platform' in categories:
                        platform = ', '.join(
                            set(pt.get_category('platform').values()))
                    if 'target_gene' in categories:
                        target_gene = ', '.join(
                            set(pt.get_category('target_gene').values()))

                    ps[prep_template_id] = [
                        len(list(pt.keys())), platform, target_gene]

                prep_samples, patform, target_gene = ps[prep_template_id]

            results.append({
                'artifact_id': aid,
                'target_subfragment': target,
                'prep_samples': prep_samples,
                'platform': platform,
                'target_gene': target_gene,
                'name': name,
                'data_type': dt,
                'timestamp': str(gt),
                'parameters': aparams,
                'algorithm': algorithm,
                'algorithm_az': algorithm_az[algorithm],
                'deprecated': deprecated,
                'active': active,
                'files': filepaths})

        return results


def _is_string_or_bytes(s):
    """Returns True if input argument is string (unicode or not) or bytes.
    """
    return isinstance(s, str) or isinstance(s, bytes)


def _get_filehandle(filepath_or, *args, **kwargs):
    """Open file if `filepath_or` looks like a string/unicode/bytes/Excel, else
    pass through.

    Notes
    -----
    If Excel, the code will write a temporary txt file with the contents. Also,
    it will check if the file is a Qiimp file or a regular Excel file.
    """
    if _is_string_or_bytes(filepath_or):
        if h5py.is_hdf5(filepath_or):
            fh, own_fh = h5py.File(filepath_or, *args, **kwargs), True
        elif filepath_or.endswith('.xlsx'):
            # due to extension, let's assume Excel file
            wb = load_workbook(filename=filepath_or, data_only=True)
            sheetnames = wb.sheetnames
            # let's check if Qiimp, they must be in same order
            first_cell_index = 0
            is_qiimp_wb = False
            if sheetnames == ["Metadata", "Validation", "Data Dictionary",
                              "metadata_schema", "metadata_form",
                              "Instructions"]:
                first_cell_index = 1
                is_qiimp_wb = True
            first_sheet = wb[sheetnames[0]]
            cell_range = range(first_cell_index, first_sheet.max_column)
            _, fp = mkstemp(suffix='.txt')
            with open(fp, 'w') as fh:
                cfh = csv_writer(fh, delimiter='\t')
                for r in first_sheet.rows:
                    if is_qiimp_wb:
                        # check contents of first column; if they are a zero
                        # (not a valid QIIMP sample_id) or a "No more than
                        # max samples" message, there are no more valid rows,
                        # so don't examine any more rows.
                        fcv = str(r[cell_range[0]].value)
                        if fcv == "0" or fcv.startswith("No more than"):
                            break
                    cfh.writerow([r[x].value for x in cell_range])
            fh, own_fh = open(fp, *args, **kwargs), True
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
    """
    fh, own_fh = _get_filehandle(filepath_or, *args, **kwargs)
    try:
        yield fh
    finally:
        if own_fh:
            fh.close()


def generate_analysis_list(analysis_ids, public_only=False):
    """Get general analysis information

    Parameters
    ----------
    analysis_ids : list of ints
        The analysis ids to look for. Non-existing ids will be ignored
    public_only : bool, optional
        If true, return only public analyses. Default: false.

    Returns
    -------
    list of dict
        The list of studies and their information
    """
    if not analysis_ids:
        return []

    sql = """
        SELECT analysis_id, a.name, a.description, a.timestamp,
            array_agg(DISTINCT CASE WHEN command_id IS NOT NULL
                      THEN artifact_id END),
            array_agg(DISTINCT visibility),
            array_agg(DISTINCT CASE WHEN filepath_type = 'plain_text'
                      THEN filepath_id END)
        FROM qiita.analysis a
        LEFT JOIN qiita.analysis_artifact USING (analysis_id)
        LEFT JOIN qiita.artifact USING (artifact_id)
        LEFT JOIN qiita.visibility USING (visibility_id)
        LEFT JOIN qiita.analysis_filepath USING (analysis_id)
        LEFT JOIN qiita.filepath USING (filepath_id)
        LEFT JOIN qiita.filepath_type USING (filepath_type_id)
        WHERE dflt = false AND analysis_id IN %s
        GROUP BY analysis_id
        ORDER BY analysis_id"""

    with qdb.sql_connection.TRN:
        results = []

        qdb.sql_connection.TRN.add(sql, [tuple(analysis_ids)])
        for row in qdb.sql_connection.TRN.execute_fetchindex():
            aid, name, description, ts, artifacts, av, mapping_files = row

            av = 'public' if set(av) == {'public'} else 'private'
            if av != 'public' and public_only:
                continue

            if mapping_files == [None]:
                mapping_files = []
            else:
                mapping_files = [
                    (mid, get_filepath_information(mid)['fullpath'])
                    for mid in mapping_files if mid is not None]
            if artifacts == [None]:
                artifacts = []
            else:
                # making sure they are int so they don't break the GUI
                artifacts = [int(a) for a in artifacts if a is not None]

            results.append({
                'analysis_id': aid, 'name': name, 'description': description,
                'timestamp': ts.strftime("%m/%d/%y %H:%M:%S"),
                'visibility': av, 'artifacts': artifacts,
                'mapping_files': mapping_files})

    return results


def create_nested_path(path):
    """Wraps makedirs() to make it safe to use across multiple concurrent calls.
    Returns successfully if the path was created, or if it already exists.
    (Note, this alters the normal makedirs() behavior, where False is returned
    if the full path already exists.)

    Parameters
    ----------
    path : str
        The path to be created. The path can contain multiple levels that do
        not currently exist on the filesystem.

    Raises
    ------
    OSError
        If the operation failed for whatever reason (likely because the caller
        does not have permission to create new directories in the part of the
        filesystem requested
    """
    # TODO: catching errno=EEXIST (17 usually) will suffice for now, to avoid
    # stomping when multiple artifacts are being manipulated within a study.
    # In the future, employ a process-spanning mutex to serialize.
    # With Python3, the try/except wrapper can be replaced with a call to
    # makedirs with exist_ok=True
    try:
        # try creating the directory specified. if the directory already exists
        # , or if qiita does not have permissions to create/modify the path, an
        # exception will be thrown.
        makedirs(path)
    except OSError as e:
        # if the directory already exists, treat as success (idempotent)
        if e.errno != EEXIST:
            raise


def human_merging_scheme(cname, merging_scheme,
                         pname, parent_merging_scheme,
                         artifact_parameters, artifact_filepaths,
                         parent_parameters):
    """From the artifact and its parent features format the merging scheme

    Parameters
    ----------
    cname : str
        The artifact command name
    merging_scheme : dict, from qdb.artifact.Artifact.merging_scheme
        The artifact merging scheme
    pname : str
        The artifact parent command name
    parent_merging_scheme : dict, from qdb.artifact.Artifact.merging_scheme
        The artifact parent merging scheme
    artifact_parameters : dict
        The artfiact processing parameters
    artifact_filepaths : list of str
        The artifact filepaths
    parent_parameters :
        The artifact parents processing parameters

    Returns
    -------
    str
        The merging scheme
    """
    eparams = []
    if merging_scheme['parameters']:
        eparams.append(','.join(['%s: %s' % (k, artifact_parameters[k])
                                 for k in merging_scheme['parameters']]))
    if (merging_scheme['outputs'] and
            artifact_filepaths is not None and
            artifact_filepaths):
        eparams.append('BIOM: %s' % ', '.join(artifact_filepaths))
    if eparams:
        cname = "%s (%s)" % (cname, ', '.join(eparams))

    if merging_scheme['ignore_parent_command']:
        algorithm = cname
    else:
        palgorithm = 'N/A'
        if pname is not None:
            palgorithm = pname
            if parent_merging_scheme['parameters']:
                params = ','.join(
                    ['%s: %s' % (k, parent_parameters[k])
                     for k in parent_merging_scheme['parameters']])
                palgorithm = "%s (%s)" % (palgorithm, params)

        algorithm = '%s | %s' % (cname, palgorithm)

    return algorithm


def activate_or_update_plugins(update=False):
    """Activates/updates the plugins

    Parameters
    ----------
    update : bool, optional
        If True will update the plugins. Otherwise will activate them.
        Default: False.
    """
    conf_files = sorted(glob(join(qiita_config.plugin_dir, "*.conf")))
    label = "{} plugin (%s/{}): %s... ".format(
        "Updating" if update else "\tLoading", len(conf_files))
    for i, fp in enumerate(conf_files):
        print(label % (i + 1, basename(fp)), end=None)
        s = qdb.software.Software.from_file(fp, update=update)
        if not update:
            s.activate()
        print("Ok")


def send_email(to, subject, body):
    # create email
    msg = MIMEMultipart()
    msg['From'] = qiita_config.smtp_email
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # connect to smtp server, using ssl if needed
    if qiita_config.smtp_ssl:
        smtp = SMTP_SSL()
    else:
        smtp = SMTP()
    smtp.set_debuglevel(False)
    smtp.connect(qiita_config.smtp_host, qiita_config.smtp_port)
    # try tls, if not available on server just ignore error
    try:
        smtp.starttls()
    except SMTPException:
        pass
    smtp.ehlo_or_helo_if_needed()

    if qiita_config.smtp_user:
        smtp.login(qiita_config.smtp_user, qiita_config.smtp_password)

    # send email
    try:
        smtp.sendmail(qiita_config.smtp_email, to, msg.as_string())
    except Exception:
        raise RuntimeError("Can't send email!")
    finally:
        smtp.close()
