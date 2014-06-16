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

from .sql_connection import SQLConnectionHandler
from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError, QiitaDBStatusError
from .util import convert_to_id


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
    add_samples
    remove_samples
    add_jobs
    """

    _table = "analysis"

    def _lock_public(self, conn_handler):
        """Raises QiitaDBStatusError if analysis is public"""
        sql = ("SELECT qiita.{0}_status_id FROM qiita.{0} WHERE "
               "analysis_id = %s".format(self._table))
        dbid = conn_handler.execute(sql, (self._id, ))
        if convert_to_id("public", "%s_status" % self._table,
                         conn_handler) == dbid:
            raise QiitaDBStatusError("Cannot edit public sanalysis!")

    def _status_setter_checks(self, conn_handler):
        r"""Perform a check to make sure not setting status away from public
        """
        self._lock_public(conn_handler)

    @classmethod
    def create(cls, owner, name, description, parent=None):
        """Creates a new analysis on the database

        Parameters
        ----------
        owner : User object
            The analysis' owner
        name : str
            Name of the analysis
        description : str
            Description of the analysis
        parent : Analysis object, optional
            The analysis this one was forked from
        """
        conn_handler = SQLConnectionHandler()
        # TODO after demo: if exists()

        # insert analysis information into table with "in construction" status
        sql = ("INSERT INTO qiita.{0} (email, name, description, "
               "analysis_status_id) VALUES (%s, %s, %s, 1) "
               "RETURNING analysis_id".format(cls._table))
        a_id = conn_handler.execute_fetchone(
            sql, (owner.id, name, description))[0]

        # add parent if necessary
        if parent:
            sql = ("INSERT INTO qiita.analysis_chain (parent, child) VALUES "
                   "(%s, %s)")
            conn_handler.execute(sql, (parent, a_id))

        return cls(a_id)

    # ---- Properties ----
    @property
    def name(self):
        """The name of the analysis

        Returns
        -------
        str
            Name of the Analysis
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT name FROM qiita.{0} WHERE "
               "analysis_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @property
    def description(self):
        """Returns the description of the analysis"""
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT description FROM qiita.{0} WHERE "
               "analysis_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

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
        conn_handler = SQLConnectionHandler()
        self._lock_public(conn_handler)
        sql = ("UPDATE qiita.{0} SET description = %s WHERE "
               "analysis_id = %s".format(self._table))
        conn_handler.execute(sql, (description, self._id))

    @property
    def biom_table(self):
        """The biom table of the analysis

        Returns
        -------
        int
            ProcessedData id of the biom table
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT filepath_id FROM qiita.analysis_filepath WHERE "
               "analysis_id = %s")
        return [file_id[0] for file_id in
                conn_handler.execute_fetchall(sql, (self._id, ))]

    @property
    def jobs(self):
        """A list of jobs included in the analysis

        Returns
        -------
        list of ints
            Job ids for jobs in analysis
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT job_id FROM qiita.analysis_job WHERE "
               "analysis_id = %s".format(self._table))
        return [job_id[0] for job_id in
                conn_handler.execute_fetchall(sql, (self._id, ))]

    @property
    def pmid(self):
        """Returns pmid attached to the analysis

        Returns
        -------
        str or None
            returns the PMID or None if none is attached
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT pmid FROM qiita.{0} WHERE "
               "analysis_id = %s".format(self._table))
        pmid = conn_handler.execute_fetchone(sql, (self._id, ))
        if pmid is None:
            return None
        return pmid[0]

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
        conn_handler = SQLConnectionHandler()
        self._lock_public(conn_handler)
        sql = ("UPDATE qiita.{0} SET pmid = %s WHERE "
               "analysis_id = %s".format(self._table))
        conn_handler.execute(sql, (pmid, self._id))

    @property
    def parent(self):
        """Returns the id of the parent analysis this was forked from"""
        return QiitaDBNotImplementedError()

    @property
    def children(self):
        return QiitaDBNotImplementedError()

    # ---- Functions ----

    def add_samples(self, samples):
        """Adds samples to the analysis

        Parameters
        ----------
        samples : list of tuples
            samples and the processed data id they come from in form
            [(processed_data_id, sample_id), ...]
        """
        conn_handler = SQLConnectionHandler()
        self._lock_public(conn_handler)

        sql = ("INSERT INTO qiita.study_samples (analysis_id, sample_id, "
               "processed_data_id) VALUES (%s, %s, %s)")
        conn_handler.executemany(sql, [(self._id, s[1], s[0])
                                       for s in samples])

    def remove_samples(self, samples):
        """Removes samples from the analysis

        Parameters
        ----------
        samples : list of tuples
            samples and the processed data id they come from in form
            [(processed_data_id, sample_id), ...]
        """
        conn_handler = SQLConnectionHandler()
        self._lock_public(conn_handler)

        sql = ("DELETE FROM qiita.study_samples WHERE (analysis_id =%s AND "
               "sample_id = %s AND processed_data_id = %s ")
        conn_handler.executemany(sql, [(self._id, s[1], s[0])
                                       for s in samples])

    def add_jobs(self, jobs):
        """Adds a list of jobs to the analysis

        Parameters
        ----------
            jobs : list of Job objects
        """
        conn_handler = SQLConnectionHandler()
        self._lock_public(conn_handler)
        sql = ("INSERT INTO qiita.analysis_job (analysis_id, job_id) "
               "VALUES (%s, %s)")
        conn_handler.executemany(sql, [(self._id, job.id) for job in jobs])
