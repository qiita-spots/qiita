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

from .base import QiitaStatusObject, QiitaObject
# from .data import RawData, PreprocessedData, ProcessedData
from .util import check_required, check_table_cols, clean_sql_result
from .exceptions import QiitaDBNotImplementedError
from .sql_connection import SQLConnectionHandler
from qiita_core.exceptions import QiitaStudyError


REQUIRED_KEYS = {"timeseries_type_id", "lab_person_id", "mixs_compliant",
                 "metadata_complete", "number_samples_collected",
                 "number_samples_promised", "portal_type_id",
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

    @classmethod
    def create(cls, owner, info, investigation_id=None):
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

        # Save study_experimental_factor data for insertion
        efo = None
        if "study_experimental_factor" in info:
            efo = info["study_experimental_factor"]
            if isinstance(efo, str):
                efo = [efo]
            info.pop("study_experimental_factor")

        conn_handler = SQLConnectionHandler()
        # make sure dictionary only has keys for available columns in db
        check_table_cols(conn_handler, info, "study")

        # Insert study into database
        sql = ("INSERT INTO qiita.study (email,study_status_id,first_contact,"
               "reprocess, %s) VALUES (%s) RETURNING study_id" %
               (','.join(info.keys()), ','.join(['%s'] * (len(info)+4))))
        # make sure data in same order as sql column names, and ids are used
        data = [owner, 1, date.today().strftime("%B %d, %Y"), 'FALSE']
        for col, val in info.items():
            if isinstance(val, QiitaObject):
                data.append(val.id_)
            else:
                data.append(val)
        study_id = conn_handler.execute_fetchone(sql, data)[0]

        if efo:
            # insert efo information into database
            sql = ("INSERT INTO qiita.study_experimental_factor (study_id, "
                   "efo_id) VALUES (%s, %s)")
            conn_handler.executemany(sql, zip([study_id] * len(efo), efo))
        else:
            raise QiitaStudyError("EFO information is required!")

        # add study to investigation if necessary
        if investigation_id:
            sql = ("INSERT INTO qiita.investigation_study (investigation_id, "
                   "study_id) VALUES (%s, %s)")
            conn_handler.execute(sql, (investigation_id, study_id))

        cls._table = "study"
        return cls(study_id)

    @classmethod
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
    def title(self):
        """Returns the title of the study"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT study_title FROM qiita.study WHERE study_id = %s"
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @title.setter
    def title(self, title):
        """Sets the title of the study

        Parameters
        ----------
        title : str
            The new study title
        """
        conn_handler = SQLConnectionHandler()
        sql = "UPDATE qiita.study SET study_title = %s WHERE study_id = %s"
        return conn_handler.execute(sql, (title, self._id))

    @property
    def info(self):
        """Dict with all information attached to the study"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT * FROM qiita.study WHERE study_id = %s"
        info = dict(conn_handler.execute_fetchone(sql, (self._id, )))
        efo = clean_sql_result(conn_handler.execute_fetchall(sql, (self._id,)))
        info["study_experimental_factor"] = efo

        #TODO: Convert everythin from ids to objects
        return info

    @info.setter
    def info(self, info):
        """Updates the information attached to the study

        Parameters
        ----------
        info : dict
        """
        conn_handler = SQLConnectionHandler()
        check_table_cols(conn_handler, info, "study")

        # Save study_experimental_factor data for insertion
        efo = None
        if "study_experimental_factor" in info:
            efo = info["study_experimental_factor"]
            if not isinstance(efo, list) and not isinstance(efo, tuple):
                efo = [efo]
            info.pop("study_experimental_factor")

        data = []
        sql = "UPDATE qiita.study SET "
        # items() used for py3 compatability
        # build query with data values in correct order for SQL statement
        for key, val in info.items():
            sql = ' '.join((sql, key, "=", "%s,"))
            if isinstance(val, QiitaObject):
                data.append(val.id_)
            else:
                data.append(val)
        sql = ' '.join((sql[-1], "WHERE study_id = %s"))
        data.append(self._id)

        if efo:
            # insert efo information into database
            sql = ("INSERT INTO qiita.study_experimental_factor (study_id, "
                   "efo_id) VALUES (%s, %s)")
            conn_handler.executemany(sql, zip([self._id] * len(efo), efo))
        conn_handler.execute(sql, data)

    @property
    def status(self):
        """Returns the study_status_id for the study"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT study_status_id FROM qiita.study WHERE study_id = %s "
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @status.setter
    def status(self, status_id):
        """Sets the study_status_id for the study"""
        conn_handler = SQLConnectionHandler()
        sql = "UPDATE qiita.study SET study_status_id = %s WHERE study_id = %s"
        conn_handler.execute(sql, (status_id, self._id))

    @property
    def sample_ids(self):
        """Returns the IDs of all samples in study

        The sample IDs are returned as a list of strings in alphabetical order.
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT sample_id FROM qiita.required_sample_info WHERE "
               "study_id = %s ORDER BY sample_id")
        return clean_sql_result(conn_handler.execute_fetchall(sql,
                                                              (self._id, )))

    @property
    def shared_with(self):
        """list of users the study is shared with"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT email FROM qiita.study_users WHERE study_id = %s"
        return clean_sql_result(conn_handler.execute_fetchall(sql,
                                                              (self._id, )))

    @property
    def pmids(self):
        """ Returns list of paper PMIDs from this study """
        conn_handler = SQLConnectionHandler()
        sql = "SELECT pmid FROM qiita.study_pmid WHERE study_id = %s"
        return clean_sql_result(conn_handler.execute_fetchall(sql,
                                                              (self._id, )))

    @property
    def investigations(self):
        """ Returns list of investigation_id this study is part of """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT investigation_id FROM qiita.investigation_study WHERE "
               "study_id = %s")
        return clean_sql_result(conn_handler.execute_fetchall(sql,
                                                              (self._id, )))

    @property
    def metadata(self):
        """ Returns list of metadata columns """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT column_name FROM qiita.study_sample_columns WHERE "
               "study_id = %s")
        return clean_sql_result(conn_handler.execute_fetchall(sql,
                                                              (self._id, )))

    @property
    def raw_data(self):
        """ Returns list of data objects with raw data info """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT raw_data_id FROM qiita.study_raw_data WHERE "
               "study_id = %s")
        raw_ids = clean_sql_result(conn_handler.execute_fetchall(sql,
                                                                 (self._id, )))
        raw_data = []
        for rid in raw_ids:
            raw_data.append(RawData(rid))
        return raw_data

    @property
    def preprocessed_data(self):
        """ Returns list of data objects with preprocessed data info """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT preprocessed_data_id FROM qiita.study_preprocessed_data"
               " WHERE study_id = %s")
        pre_ids = clean_sql_result(conn_handler.execute_fetchall(sql,
                                                                 (self._id, )))
        preprocessed_data = []
        for pid in pre_ids:
            preprocessed_data.append(PreprocessedData(pid))
        return preprocessed_data

    @property
    def processed_data(self):
        """ Returns list of data objects with processed data info """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT processed_data_id FROM qiita.study_processed_data"
               " WHERE study_id = %s")
        pro_ids = clean_sql_result(conn_handler.execute_fetchall(sql,
                                                                 (self._id, )))
        processed_data = []
        for pid in pro_ids:
            processed_data.append(ProcessedData(pid))
        return processed_data

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
        conn_handler.execute(sql, (self._id, email))

    def add_pmid(self, pmid):
        """Adds PMID to study

        Parameters
        ----------
        pmid: int
            pmid to associate with study
        """
        conn_handler = SQLConnectionHandler()
        sql = "INSERT INTO qiita.study_pmid (study_id, pmid) VALUES (%s, %s)"
        conn_handler.execute(sql, (self._id, pmid))


class StudyPerson(QiitaObject):
    """Object handling information pertaining to people involved in a study

    Attributes
    ----------
    name: str
        name of the person
    email: str
        email of the person
    address: str, optional
        address of the person
    phone: str, optional
        phone number of the person
    """
    @classmethod
    def create(cls, name, email, address=None, phone=None):
        # Make sure person doesn't already exist
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT study_person_id FROM qiita.study WHERE name = %s AND "
               "email = %s")
        spid = conn_handler.execute_fetchone(sql, (name, email))[0]
        if spid:
            return StudyPerson(spid)

        # Doesn't exist so insert new person
        sql = ("INSERT INTO qiita.study_person (name, email, address, phone) "
               "VALUES (%s, %s, %s, %s) RETURNING study_person_id")
        spid = conn_handler.execute_fetchone(sql, (name, email, address,
                                                   phone))[0]
        return StudyPerson(spid)

    @classmethod
    def delete(self):
        raise NotImplementedError()

    # Properties
    @property
    def name(self):
        conn_handler = SQLConnectionHandler()
        sql = "SELECT name FROM qiita.study_person WHERE study_person_id = %s"
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @name.setter
    def name(self, value):
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.study_person SET name = %s WHERE "
               "study_person_id = %s")
        conn_handler.execute(sql, (value, self._id))

    @property
    def email(self):
        conn_handler = SQLConnectionHandler()
        sql = "SELECT email FROM qiita.study_person WHERE study_person_id = %s"
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @email.setter
    def email(self, value):
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.study_person SET email = %s WHERE "
               "study_person_id = %s")
        conn_handler.execute(sql, (value, self._id))

    @property
    def address(self):
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT address FROM qiita.study_person WHERE study_person_id ="
               " %s")
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @address.setter
    def address(self, value):
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.study_person SET address = %s WHERE "
               "study_person_id = %s")
        conn_handler.execute(sql, (value, self._id))

    @property
    def phone(self):
        conn_handler = SQLConnectionHandler()
        sql = "SELECT phone FROM qiita.study_person WHERE study_person_id = %s"
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @phone.setter
    def phone(self, value):
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.study_person SET phone = %s WHERE "
               "study_person_id = %s")
        conn_handler.execute(sql, (value, self._id))
