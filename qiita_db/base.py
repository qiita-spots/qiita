r"""
Base objects (:mod: `qiita_db.base`)
====================================

..currentmodule:: qiita_db.base

This module provides base objects for dealing with any qiita_db object that
needs to be stored on the database.

Classes
-------

..autosummary::
    :toctree: generated/

    QiitaObject
    QiitaStatusObject
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .sql_connection import TRN
from .exceptions import QiitaDBNotImplementedError, QiitaDBUnknownIDError


class QiitaObject(object):
    r"""Base class for any qiita_db object

    Parameters
    ----------
    id_: object
        The object id on the storage system

    Attributes
    ----------
    id

    Methods
    -------
    create
    delete
    exists
    _check_subclass
    _check_id
    __eq__
    __neq__

    Raises
    ------
    IncompetentQiitaDeveloperError
        If trying to instantiate the base class directly
    """

    _table = None

    @classmethod
    def create(cls):
        r"""Creates a new object with a new id on the storage system

        Raises
        ------
        QiitaDBNotImplementedError
            If the method is not overwritten by a subclass
        """
        raise QiitaDBNotImplementedError()

    @classmethod
    def delete(cls, id_):
        r"""Deletes the object `id_` from the storage system

        Parameters
        ----------
        id_ : object
            The object identifier

        Raises
        ------
        QiitaDBNotImplementedError
            If the method is not overwritten by a subclass
        """
        raise QiitaDBNotImplementedError()

    @classmethod
    def exists(cls):
        r"""Checks if a given object info is already present on the DB

        Raises
        ------
        QiitaDBNotImplementedError
            If the method is not overwritten by a subclass
        """
        raise QiitaDBNotImplementedError()

    @classmethod
    def _check_subclass(cls):
        r"""Check that we are not calling a function that needs to access the
        database from the base class

        Raises
        ------
        IncompetentQiitaDeveloperError
            If its called directly from a base class
        """
        if cls._table is None:
            raise IncompetentQiitaDeveloperError(
                "Could not instantiate an object of the base class")

    def _check_id(self, id_):
        r"""Check that the provided ID actually exists on the database

        Parameters
        ----------
        id_ : object
            The ID to test

        Notes
        -----
        This function does not work for the User class. The problem is
        that the User sql layout doesn't follow the same conventions done in
        the other classes. However, still defining here as there is only one
        subclass that doesn't follow this convention and it can override this.
        """
        self._check_subclass()

        with TRN:
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.{0}
                        WHERE {0}_id=%s)""".format(self._table)
            TRN.add(sql, [id_])
            return TRN.execute_fetchlast()

    def __init__(self, id_):
        r"""Initializes the object

        Parameters
        ----------
        id_: the object identifier

        Raises
        ------
        QiitaDBUnknownIDError
            If `id_` does not correspond to any object
        """
        with TRN:
            if not self._check_id(id_):
                raise QiitaDBUnknownIDError(id_, self._table)

        self._id = id_

    def __eq__(self, other):
        r"""Self and other are equal based on type and database id"""
        if type(self) != type(other):
            return False
        if other._id != self._id:
            return False
        return True

    def __ne__(self, other):
        r"""Self and other are not equal based on type and database id"""
        return not self.__eq__(other)

    @property
    def id(self):
        r"""The object id on the storage system"""
        return self._id


class QiitaStatusObject(QiitaObject):
    r"""Base class for any qiita_db object with a status property

    Attributes
    ----------
    status

    Methods
    -------
    check_status
    _status_setter_checks
    """

    @property
    def status(self):
        r"""String with the current status of the analysis"""
        # Get the DB status of the object
        with TRN:
            sql = """SELECT status FROM qiita.{0}_status
                     WHERE {0}_status_id = (
                        SELECT {0}_status_id FROM qiita.{0}
                        WHERE {0}_id = %s)""".format(self._table)
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    def _status_setter_checks(self):
        r"""Perform any extra checks that needed to be done before setting the
        object status on the database. Should be overwritten by the subclasses
        """
        raise QiitaDBNotImplementedError()

    @status.setter
    def status(self, status):
        r"""Change the status of the analysis

        Parameters
        ----------
        status: str
            The new object status
        """
        with TRN:
            # Perform any extra checks needed before
            # we update the status in the DB
            self._status_setter_checks()

            # Update the status of the object
            sql = """UPDATE qiita.{0} SET {0}_status_id = (
                        SELECT {0}_status_id FROM qiita.{0}_status
                        WHERE status = %s)
                     WHERE {0}_id = %s""".format(self._table)
            TRN.add(sql, [status, self._id])
            TRN.execute()

    def check_status(self, status, exclude=False):
        r"""Checks status of object.

        Parameters
        ----------
        status: iterable
            Iterable of statuses to check against.
        exclude: bool, optional
            If True, will check that database status is NOT one of the statuses
            passed. Default False.

        Returns
        -------
        bool
            True if the object status is in the desired set of statuses. False
            otherwise.

        Notes
        -----
        This assumes the following database setup is in place: For a given
        cls._table setting, such as "table", there is a corresponding table
        with the name "table_status" holding the status entries allowed. This
        table has a column called "status" that holds the values corresponding
        to what is passed as status in this function and a column
        "table_status_id" corresponding to the column of the same name in
        "table".

        Table setup:
        foo: foo_status_id  ----> foo_status: foo_status_id, status
        """
        with TRN:
            # Get all available statuses
            sql = "SELECT DISTINCT status FROM qiita.{0}_status".format(
                self._table)
            TRN.add(sql)
            # We need to access to the results of the last SQL query,
            # hence indexing using -1
            avail_status = [x[0] for x in TRN.execute_fetchindex()]

            # Check that all the provided status are valid status
            if set(status).difference(avail_status):
                raise ValueError("%s are not valid status values"
                                 % set(status).difference(avail_status))

            # Get the DB status of the object
            dbstatus = self.status
            return dbstatus not in status if exclude else dbstatus in status
