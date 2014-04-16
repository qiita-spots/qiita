#!/usr/bin/env python
from __future__ import division

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
# Copyright (c) 2014, The Qiita Development Team.
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
    id_:
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

    @staticmethod
    def create():
        """Creates a new object with a new id on the storage system"""
        raise QiitaDBNotImplementedError()

    @staticmethod
    def delete(id_):
        """Deletes the object `id` from the storage system

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
