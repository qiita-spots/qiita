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
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb


class QiitaObject(object):
    r"""Base class for any qiita_db object

    Parameters
    ----------
    id_: int, long, str, or unicode
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
    _portal_table = None

    @classmethod
    def create(cls):
        r"""Creates a new object with a new id on the storage system

        Raises
        ------
        QiitaDBNotImplementedError
            If the method is not overwritten by a subclass
        """
        raise qdb.exceptions.QiitaDBNotImplementedError()

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
        raise qdb.exceptions.QiitaDBNotImplementedError()

    @classmethod
    def exists(cls):
        r"""Checks if a given object info is already present on the DB

        Raises
        ------
        QiitaDBNotImplementedError
            If the method is not overwritten by a subclass
        """
        raise qdb.exceptions.QiitaDBNotImplementedError()

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
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.{0}
                        WHERE {0}_id=%s)""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [id_])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def _check_portal(self, id_):
        """Checks that object is accessible in current portal

        Parameters
        ----------
        id_ : object
            The ID to test
        """
        if self._portal_table is None:
            # assume not portal limited object
            return True

        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.{0}
                            JOIN qiita.portal_type USING (portal_type_id)
                        WHERE {1}_id = %s AND portal = %s
                    )""".format(self._portal_table, self._table)
            qdb.sql_connection.TRN.add(sql, [id_, qiita_config.portal])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def __init__(self, id_):
        r"""Initializes the object

        Parameters
        ----------
        id_: int, long, str, or unicode
            the object identifier

        Raises
        ------
        QiitaDBUnknownIDError
            If `id_` does not correspond to any object
        """
        # Most IDs in the database are numerical, but some (e.g., IDs used for
        # the User object) are strings. Moreover, some integer IDs are passed
        # as strings (e.g., '5'). Therefore, explicit type-checking is needed
        # here to accommodate these possibilities.
        if not isinstance(id_, (int, long, str, unicode)):
            raise TypeError("id_ must be a numerical or text type (not %s) "
                            "when instantiating "
                            "%s" % (id_.__class__.__name__,
                                    self.__class__.__name__))

        if isinstance(id_, (str, unicode)):
            if id_.isdigit():
                id_ = int(id_)
        elif isinstance(id_, long):
            id_ = int(id_)

        with qdb.sql_connection.TRN:
            self._check_subclass()
            if not self._check_id(id_):
                raise qdb.exceptions.QiitaDBUnknownIDError(id_, self._table)

            if not self._check_portal(id_):
                raise qdb.exceptions.QiitaDBError(
                    "%s with id %d inaccessible in current portal: %s"
                    % (self.__class__.__name__, id_, qiita_config.portal))

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

    def __hash__(self):
        r"""The hash of an object is based on the id"""
        return hash(str(self.id))

    @property
    def id(self):
        r"""The object id on the storage system"""
        return self._id
