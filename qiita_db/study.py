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
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from datetime import date

from .base import QiitaStatusObject
from .util import check_required, check_table_cols, clean_sql_result
from .exceptions import QiitaDBNotImplementedError
from .sql_connection import SQLConnectionHandler


REQUIRED_KEYS = {"timeseries_type_id", "lab_person_id", "mixs_compliant",
                 "metadata_complete", "number_samples_collected",
                 "number_samples_promised", "portal_type",
                 "principal_investigator_id", "study_title", "study_alias",
                 "study_description", "study_abstract"}


class Study(QiitaStatusObject):
    """
    Study object to access to the Qiita Study information

    Attributes
    ----------
    name: str
        name of the study
    info: dict
        Major information about the study, keyed by db column name
    status: int
        Status of the study
    sample_ids: list of str
        All sample_ids associated with the study
    shared_with: list of str
        Emails of users the study is shared with
    pmids: list of str
        PMIDs assiciated with the study
    investigations: list of int
        Investigation ids of all investigations study is part of
    metadata: list of str
        Metadata column names available from study
    raw_data: list of data objects
    preprocessed_data: list of data objects
    processed_data: list of data objects

    Methods
    -------
    share_with(email)
        Shares the study with given user

     def add_raw_data(raw_data_id):
        Associates raw data with the study

    add_pmid(self, pmid):
        Adds PMID to study
    """

    @staticmethod
    def create(owner, info, investigation_id=None):
        """Creates a new study on the database

        Parameters
        ----------
        owner : str
            the user id of the study' owner
        info: dict
            the information attached to the study
        investigation_id: int
            if the study is part of an investigation, the id to associate with

        Raises
        ------
        QiitaDBExecutionError
            All required keys not passed or non-db columns in info dictionary

        Notes
        -----
        If investigation_id passed in investigation database, will assume that
        study is part of that investigation. Otherwise need to pass the
        following keys in investigation: "name", "description",
        "contact_person_id"
        """
        # make sure required keys are in the info dict
        check_required(info, REQUIRED_KEYS)

        conn_handler = SQLConnectionHandler()
        # make sure dictionary only has keys for available columns in db
        check_table_cols(conn_handler, info, "study")

        # Insert study into database
        sql = ("INSERT INTO qiita.study (email,study_status_id,first_contact,"
               "%s) VALUES (%s) RETURNING study_id" % (','.join(info.keys()),
                                                       '%s' * (len(info)+3)))
        # make sure data in same order as sql column names
        data = [owner, 1, date.today().strftime("%B %d, %Y")]
        for col in info.keys():
            data.append(info[col])
        study_id = conn_handler.execute_fetchone(sql, data)[0]
                
        # add study to investigation if necessary
        if investigation_id:
            sql = ("INSERT INTO qiita.investigation_study (investigation_id, "
                   "study_id) VALUES (%s, %s)")
            conn_handler.execute(sql, (investigation_id, study_id))

        return Study(study_id)

    @staticmethod
    def delete(id_):
        """Deletes the study `id_` from the database

        Parameters
        ----------
        id_ :
            The object identifier
        """
        raise QiitaDBNotImplementedError()

# --- Attributes ---
    @property
    def name(self):
        """Returns the name of the study"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT name FROM qiita.study WHERE study_id = %s"
        return conn_handler.execute_fetchone(sql, self.id_)[0]

    @name.setter
    def name(self, name):
        """Sets the name of the study

        Parameters
        ----------
        name : str
            The new study name
        """
        conn_handler = SQLConnectionHandler()
        sql = "UPDATE qiita.study SET name = %s WHERE study_id = %s"
        return conn_handler.execute(sql, (name, self.id_))

    @property
    def info(self):
        """Dict with any other information attached to the study"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT * FROM qiita.study WHERE study_id = %s"
        return dict(conn_handler.execute_fetchone(sql, self.id_))

    @info.setter
    def info(self, info):
        """Updates the information attached to the study

        Parameters
        ----------
        info : dict
        """
        conn_handler = SQLConnectionHandler()
        check_table_cols(conn_handler, info, "study")

        data = []
        sql = "UPDATE qiita.study SET "
        # items() used for py3 compatability
        # build query with data values in correct order for SQL statement
        for key, val in info.items():
            sql = ' '.join((sql, key, "=", "%s,"))
            data.append(val)
        sql = ' '.join((sql[-1], "WHERE study_id = %s"))
        data.append(self.id_)

        conn_handler.execute(sql, data)

    @property
    def status(self):
        """Returns the study_status_id for the study"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT study_status_id FROM qiita.study WHERE study_id = %s "
        return conn_handler.execute_fetchone(sql, self.id_)[0]

    @status.setter
    def status(self, status_id):
        """Sets the study_status_id for the study"""
        conn_handler = SQLConnectionHandler()
        sql = "UPDATE qiita.study SET study_status_id = %s WHERE study_id = %s"
        return conn_handler.execute_fetchone(sql, (status_id, self.id_))[0]

    @property
    def sample_ids(self):
        """Returns the IDs of all samples in study

        The sample IDs are returned as a list of strings in alphabetical order.
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT sample_id FROM qiita.required_sample_info WHERE "
               "study_id = %s ORDER BY sample_id")
        return conn_handler.execute_fetchone(sql, self.id_)

    @property
    def shared_with(self):
        """list of users the study is shared with"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT * FROM qiita.study_users WHERE study_id = %s"
        return list(conn_handler.execute_fetchone(sql, self.id_))

    @property
    def pmids(self):
        """ Returns list of paper PMIDs from this study """
        conn_handler = SQLConnectionHandler()
        sql = "SELECT pmid FROM qiita.study_pmid WHERE study_id = %s"
        return clean_sql_result(conn_handler.execute_fetchall(sql, self.id_))

    @property
    def investigations(self):
        """ Returns list of investigation_id this study is part of """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT investigation_id FROM qiita.investigation_study WHERE "
               "study_id = %s")
        return clean_sql_result(conn_handler.execute_fetchall(sql, self.id_))

    @property
    def metadata(self):
        """ Returns list of metadata columns """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT column_name FROM qiita.study_sample_columns WHERE "
               "study_id = %s")
        return clean_sql_result(conn_handler.execute_fetchall(sql, self.id_))

    @property
    def raw_data(self):
        """ Returns list of data objects with raw data info """
        raise NotImplementedError(Study.raw_data)

    @property
    def preprocessed_data(self):
        """ Returns list of data objects with preprocessed data info """
        raise NotImplementedError(Study.preprocessed_data)

    @property
    def processed_data(self):
        """ Returns list of data objects with processed data info """
        raise NotImplementedError(Study.processed_data)

# --- methods ---
    def share_with(self, email):
        """Shares the study with given user

        Parameters
        ----------
        email: str
            email of the user to share with
        """
        conn_handler = SQLConnectionHandler()
        sql = ("INSERT INTO qiita.study_users (study_id, email) VALUES "
               "(%s, %s)")
        conn_handler.execute_fetchone(sql, (self.id_, email))

    def add_raw_data(self, raw_data_id):
        """Associates raw data with the study

        Parameters
        ----------
        raw_data_id: int
            ID of the raw data to associate with study
        """
        conn_handler = SQLConnectionHandler()
        sql = ("INSERT INTO qiita.study_raw_data (study_id, raw_data_id) "
               "VALUES (%s, %s)")
        conn_handler.execute_fetchone(sql, (self.id_, raw_data_id))

    def add_pmid(self, pmid):
        """Adds PMID to study

        Parameters
        ----------
        pmid: int
            pmid to associate with study
        """
        conn_handler = SQLConnectionHandler()
        sql = "INSERT INTO qiita.study_pmid (study_id, pmid) VALUES (%s, %s)"
        conn_handler.execute_fetchone(sql, (self.id_, pmid))
