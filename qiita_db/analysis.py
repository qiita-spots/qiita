#!/usr/bin/env python
from __future__ import division

"""
Objects for dealing with Qiita analyses

This module provides the implementation of the Analysis class.

Classes
-------
- `Analysis` -- A Qiita Analysis class
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError


class Analysis(QiitaStatusObject):
    """
    Analysis object to access to the Qiita Analysis information

    Attributes
    ----------
    biom_table
    jobs
    info

    Methods
    -------
    add_jobs(jobs)
        Adds a list of jobs to the analysis

    remove_jobs(jobs)
        Removes a list of jobs from the analysis

    """

    @staticmethod
    def create(owner):
        """Creates a new analysis on the database

        Parameters
        ----------
        owner : string
            the user id of the analysis' owner
        """
        raise QiitaDBNotImplementedError()

    @staticmethod
    def delete(id_):
        """Deletes the analysis `id` from the database

        Parameters
        ----------
        id_ :
            The analysis identifier
        """
        raise QiitaDBNotImplementedError()

    @property
    def biom_table(self):
        """The biom table of the analysis"""
        raise QiitaDBNotImplementedError()

    @biom_table.setter
    def biom_table(self, biom_table):
        """Updates the biom table used in the analysis

        Parameters
        ----------
            biom_table :
        """
        raise QiitaDBNotImplementedError()

    @property
    def jobs(self):
        """A list of jobs included in the analysis"""
        raise QiitaDBNotImplementedError()

    @property
    def info(self):
        """Dict with any other information attached to the analysis"""
        raise QiitaDBNotImplementedError()

    @info.setter
    def info(self, info):
        """Updates the information attached to the analysis

        Parameters
        ----------
            info : dict
        """
        raise QiitaDBNotImplementedError()

    def add_jobs(self, jobs):
        """Adds a list of jobs to the analysis

        Parameters
        ----------
            jobs : list of Job objects
        """
        raise QiitaDBNotImplementedError()

    def remove_jobs(self, jobs):
        """Removes a list of jobs from the analysis

        Parameters
        ----------
            jobs : list of Job objects
        """
        raise QiitaDBNotImplementedError()
