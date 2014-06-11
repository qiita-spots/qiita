#!/usr/bin/env python
from __future__ import division
from random import choice
from string import ascii_letters, digits, punctuation

from bcrypt import hashpw, gensalt

from .exceptions import QiitaDBColumnError

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


def create_rand_string(length, punct=True):
        """Returns a string of random ascii characters

        Parameters:
        length: int
            Length of string to return
        punct: bool, optional
            Include punctiation as well as letters and numbers. Default True.
        """
        chars = ''.join((ascii_letters, digits))
        if punct:
            chars = ''.join((chars, punctuation))
        return ''.join(choice(chars) for i in xrange(length))


def hash_pw(password, hashedpw=None):
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
        if hashedpw is None:
            hashedpw = gensalt()
            #python 3 workaround for bcrypt
        if isinstance(password, bytes):
            password = password.decode('utf-8')
        if isinstance(hashedpw, bytes):
            hashedpw = hashedpw.decode('utf-8')
        return hashpw(password, hashedpw)


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
