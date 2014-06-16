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
from __future__ import division

from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError


class Analysis(QiitaStatusObject):
    """
    Analysis object to access to the Qiita Analysis information

    Attributes
    ----------
    name
    description
    biom_table
    jobs
    pmid
    parent
    children

    Methods
    -------
    add_jobs
    """

    _table = "analysis"

    @classmethod
    def create(owner, title, description, sample_processed_ids, parent=None):
        """Creates a new analysis on the database

        Parameters
        ----------
        owner : str
            The user id of the analysis' owner
        title : str
            Title of the analysis
        description : str
            Description of the analysis
        sample_processed_ids : list of tuples
            samples and the processed data id they come from in form
            (sample_id, processed_data_id)
        parent : Analysis object, optional
            The analysis this one was forked from
        """
        raise QiitaDBNotImplementedError()

    # ---- Properties ----
    @property
    def name(self):
        """The name of the analysis

        Returns
        -------
        str
            Name of the Analysis
        """
        raise QiitaDBNotImplementedError()

    @property
    def description(self):
        """Returns the description of the analysis"""
        raise QiitaDBNotImplementedError()

    @description.setter
    def description(self, description):
        """Changes the description of the analysis

        Parameters
        ----------
        description : str
            New description for the analysis

        Raises
        ------
        QiitaDBStatusError
            Analysis is public
        """
        raise QiitaDBNotImplementedError()

    @property
    def biom_table(self):
        """The biom table of the analysis

        Returns
        -------
        int
            ProcessedData id of the biom table
        """
        raise QiitaDBNotImplementedError()

    @property
    def jobs(self):
        """A list of jobs included in the analysis

        Returns
        -------
        list of ints
            Job ids for jobs in analysis
        """
        raise QiitaDBNotImplementedError()

    @property
    def pmid(self):
        """Returns pmid attached to the analysis

        Returns
        -------
        str
        """
        raise QiitaDBNotImplementedError()

    @pmid.setter
    def pmid(self, pmid):
        """adds pmid to the analysis

        Parameters
        ----------
        pmid: str
            pmid to set for study

        Raises
        ------
        QiitaDBStatusError
            Analysis is public

        Notes
        -----
        An analysis should only ever have one PMID attached to it.
        """
        raise QiitaDBNotImplementedError()

    # ---- Functions ----

    def add_jobs(self, jobs):
        """Adds a list of jobs to the analysis

        Parameters
        ----------
            jobs : list of Job objects
        """
        raise QiitaDBNotImplementedError()
