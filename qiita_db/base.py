#!/usr/bin/env python
from __future__ import division

from .sql_connection import SQLConnectionHandler

"""
Objects for dealing with qiita_db objects

This module provides base objects for dealing with any qiita_db object that
needs to be stored.

Classes
-------
- `QiitaObject` -- A Qiita object class with a storage id
- `QiitaStatusObject` -- A Qiita object class with a storage id and status
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .exceptions import QiitaDBNotImplementedError


class QiitaObject(object):
    """Base class for any qiita_db object

    Parameters
    ----------
    id_: object
        The object id on the storage system

    Attributes
    ----------
    id_

    Methods
    -------
    create()
        Creates a new object with a new id on the storage system

    delete(id_)
        Deletes the object `id_` from the storage system
    """

    _table = None

    @staticmethod
    def create():
        """Creates a new object with a new id on the storage system"""
        raise QiitaDBNotImplementedError()

    @staticmethod
    def delete(id_):
        """Deletes the object `id_` from the storage system

        Parameters
        ----------
        id_ :
            The object identifier
        """
        raise QiitaDBNotImplementedError()

    def __init__(self, id_):
        """Initializes the object

        Parameters
        ----------
        id_: the object identifier
        """
        self._id = id_

    @property
    def id(self):
        """The object id on the storage system"""
        return self._id


class QiitaStatusObject(QiitaObject):
    """Base class for any qiita_db object with a status property

    Attributes
    ----------
    status :
        The current status of the object
    """

    @property
    def status(self):
        """String with the current status of the analysis"""
        raise QiitaDBNotImplementedError()

    @status.setter
    def status(self, status):
        """Change the status of the analysis

        Parameters
        ----------
        status: str
            The new object status
        """
        raise QiitaDBNotImplementedError()

    def check_status(self, status, not_state=False):
        """Decorator: checks status of object, allowing function to run if
        conditions met.

        Parameters
        ----------
        status: str
            Status to check against
        not_state: bool, optional
            If True, will check that status is NOT equal to the one in the db.
            Default False.

        Notes
        -----
        This assumes the following database setup is in place: For a given
        cls._table setting, such as "table", there is a corresponding table
        with the name "table_status" holding the status entries allowed. This
        table has a column called "status" that holds the values corresponding
        to what is passed as status in this function and a column
        "table_status_id" corresponding to the column of the same name in
        "table".

        Example:
        foo: foo_status_id  ----> foo_status: foo_status_id, status
        """
        def wrap(f):
            sql = ("SELECT status FROM qiita.{0}_status WHERE {0}_status_id = "
                       "(SELECT {0}_status_id FROM qiita.{0} WHERE "
                       "{0}_id = %s)").format(self._table)
            conn = SQLConnectionHandler()
            dbstatus = conn.execute_fetchone(sql, (self._id, ))[0]
            def wrapped_f(*args):
                if not_state and dbstatus != status:
                    return f(*args)
                elif dbstatus == status:
                    return f(*args)
                else:
                    raise ValueError("Trying to run function with disallowed "
                                     "status: %s" % status)
            return wrapped_f
        return wrap
