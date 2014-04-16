#!/usr/bin/env python
from __future__ import division

"""
Objects for dealing with Qiita studies

This module provides the implementation of the Study class.


Classes
-------
- `QittaStudy` -- A Qiita study class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError


class Study(QiitaStatusObject):
    """
    Study object to access to the Qiita Study information

    Attributes
    ----------
    name
    sample_ids
    info

    Methods
    -------
    add_samples(samples)
        Adds the samples listed in `samples` to the study

    remove_samples(samples)
        Removes the samples listed in `samples` from the study
    """

    @staticmethod
    def create(owner):
        """Creates a new study on the storage system

        Parameters
        ----------
        owner : string
            the user id of the study' owner
        """
        raise QiitaDBNotImplementedError()

    @staticmethod
    def delete(id_):
        """Deletes the study `id_` from the storage system

        Parameters
        ----------
        id_ :
            The object identifier
        """
        raise QiitaDBNotImplementedError()

    @property
    def name(self):
        """Returns the name of the study"""
        raise QiitaDBNotImplementedError()

    @name.setter
    def name(self, name):
        """Sets the name of the study

        Parameters
        ----------
            name : string
                The new study name
        """
        raise QiitaDBNotImplementedError()

    @property
    def sample_ids(self):
        """Returns the IDs of all samples in study

        The sample IDs are returned as a list of strings in alphabetical order.
        """
        raise QiitaDBNotImplementedError()

    @property
    def info(self):
        """Dict with any other information attached to the study"""
        raise QiitaDBNotImplementedError()

    @info.setter
    def info(self, info):
        """Updates the information attached to the study

        Parameters
        ----------
            info : dict
        """
        raise QiitaDBNotImplementedError()

    def add_samples(self, samples):
        """Adds the samples listed in `samples` to the study
        Parameters
        ----------
            samples : list of strings
                The sample Ids to be added to the study
        """
        raise QiitaDBNotImplementedError()

    def remove_samples(self, samples):
        """Removes the samples listed in `samples` from the study
        Parameters
        ----------
            samples : list of strings
                The sample Ids to be removed from the study
        """
        raise QiitaDBNotImplementedError()
