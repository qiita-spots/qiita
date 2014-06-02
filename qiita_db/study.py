from __future__ import division

r"""
Study and StudyPerson objects (:mod:`qiita_db.study`)
================================================================

.. currentmodule:: qiita_db.study

This module provides the implementation of the Study class. It allows access to
all basic information including name and pmids associated with the study, as
well as returning objects for the data, metadata, owner, and shared users. It
is the central hub for creating, deleting, and accessing a study in the
database.


Classes
-------

.. autosummary::
   :toctree: generated/

   Study
   StudyPerson

Examples
--------
Studdies are attached to people. These people have names, emails, addresses,
and phone numbers. The email and name are the minimum required information.
>>> person = StudyPerson.create('Some Dude', 'somedude@foo.bar',
                                address='111 fake street',
                                phone='111-121-1313') # doctest: +SKIP
>>> person.name # doctest: +SKIP
Some dude
>>> person.email # doctest: +SKIP
somedude@foobar
>>> person.address # doctest: +SKIP
111 fake street
>>> person.phone # doctest: +SKIP
111-121-1313

A study requres a minimum of information to be created. Note that the people
must be passed as StudyPerson objects and the owner as a User object.
>>> info = {
...     "timeseries_type_id": 1,
...     "study_experimental_factor": 1,
...     "metadata_complete": True,
...     "mixs_compliant": True,
...     "number_samples_collected": 25,
...     "number_samples_promised": 28,
...     "portal_type_id": 3,
...     "study_title": "Study Title",
...     "study_alias": "TST",
...     "study_description": ("Some description of the study goes here"),
...     "study_abstract": ("Some abstract goes here"),
...     "emp_person_id": StudyPerson(2),
...     "principal_investigator_id": StudyPerson(3),
...     "lab_person_id": StudyPerson(1)} # doctest: +SKIP
>>> owner = User('owner@foo.bar') # doctest: +SKIP
>>> Study(owner, info) # doctest: +SKIP

You can also add a study to an investigation by passing the investigation
object while creating the study.
>>> investigation = Investigation(1) # doctest: +SKIP
>>> Study(owner, info, investigation) # doctest: +SKIP
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
from .data import RawData, PreprocessedData, ProcessedData
from .user import User
from .investigation import Investigation
from .util import check_required, check_table_cols
from .metadata_template import SampleTemplate
from .sql_connection import SQLConnectionHandler
from qiita_core.exceptions import QiitaStudyError


REQUIRED_KEYS = {"timeseries_type_id", "lab_person_id", "mixs_compliant",
                 "metadata_complete", "number_samples_collected",
                 "number_samples_promised", "portal_type_id",
                 "principal_investigator_id", "study_title", "study_alias",
                 "study_description", "study_abstract"}


class Study(QiitaStatusObject):
    r"""Study object to access to the Qiita Study information

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
    shared_with: list of User objects
        Emails of users the study is shared with
    pmids: list of str
        PMIDs assiciated with the study
    investigations: list of Investigation objects
        All investigations study is part of
    metadata: Metadata object
        Metadata object tied to this study
    raw_data: list of RawData objects
        All raw data attached to the study
    preprocessed_data: list of PreprocessedData objects
        All preprocessed data attached to the study
    processed_data: list of ProcessedData objects
        All processed data attached to the study

    Methods
    -------
    share_with(User_obj)
        Shares the study with given user

    add_pmid(self, pmid):
        Adds PMID to study
    """
    _table = "study"

    @classmethod
    def create(cls, owner, info, investigation=None):
        """Creates a new study on the database

        Parameters
        ----------
        owner : User object
            the user id of the study' owner
        info: dict
            the information attached to the study.
        investigation_id: Investigation object
            if the study is part of an investigation, the id to associate with

        Raises
        ------
        QiitaDBExecutionError
            All required keys not passed or non-db columns in info dictionary

        Notes
        -----
        All keys in info, except the efo, must be equal to columns in the
        forge.study table in the database. EFO information is stored as a list
        under the key 'study_experimental_factor', the name of the table it is
        stored in.
        """
        # make sure not passing a study id in the info dict
        if "study_id" in info:
            raise QiitaStudyError("Can't pass study_id in info dict!")

        # make sure required keys are in the info dict
        check_required(info, REQUIRED_KEYS)

        # Save study_experimental_factor data for insertion
        efo = None
        if "study_experimental_factor" in info:
            efo = info["study_experimental_factor"]
            if isinstance(efo, int):
                efo = [efo]
            info.pop("study_experimental_factor")
        else:
            raise QiitaStudyError("EFO information is required!")

        conn_handler = SQLConnectionHandler()
        # make sure dictionary only has keys for available columns in db
        check_table_cols(conn_handler, info, "study")

        # Insert study into database
        sql = ("INSERT INTO qiita.{0} (email,study_status_id,first_contact,"
               "reprocess, %s) VALUES (%s) RETURNING "
               "study_id".format(cls._table) %
               (','.join(info.keys()), ','.join(['%s'] * (len(info)+4))))
        # make sure data in same order as sql column names, and ids are used
        data = [owner.id, 1, date.today().strftime("%B %d, %Y"), 'FALSE']
        for col, val in info.items():
            if isinstance(val, QiitaObject):
                data.append(val.id)
            else:
                data.append(val)
        study_id = conn_handler.execute_fetchone(sql, data)[0]

        # insert efo information into database
        sql = ("INSERT INTO qiita.{0}_experimental_factor (study_id, "
               "efo_id) VALUES (%s, %s)".format(cls._table))
        conn_handler.executemany(sql, zip([study_id] * len(efo), efo))

        # add study to investigation if necessary
        if investigation:
            sql = ("INSERT INTO qiita.investigation_study (investigation_id, "
                   "study_id) VALUES (%s, %s)")
            conn_handler.execute(sql, (investigation.id, study_id))

        return cls(study_id)

    @classmethod
    def delete(cls, id_):
        """Deletes the study `id_` from the database

        Parameters
        ----------
        id_ :
            The object identifier
        """
        # delete raw data
        # drop sample_x dynamic table
        # delete study row from study table (and cascade to satelite tables)
        raise NotImplementedError()

# --- Attributes ---
    @property
    def title(self):
        """Returns the title of the study

        Returns
        -------
        str: title of study
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT study_title FROM qiita.{0} WHERE "
               "study_id = %s".format(self._table))
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
        sql = ("UPDATE qiita.{0} SET study_title = %s WHERE "
               "study_id = %s".format(self._table))
        return conn_handler.execute(sql, (title, self._id))

    @property
    def info(self):
        """Dict with all information attached to the study

        Returns
        -------
        dict: info of study keyed to column names
        """
        conn_handler = SQLConnectionHandler()
        sql = "SELECT * FROM qiita.{0} WHERE study_id = %s".format(self._table)
        info = dict(conn_handler.execute_fetchone(sql, (self._id, )))
        efo = [x[0] for x in conn_handler.execute_fetchall(sql, (self._id,))]
        info["study_experimental_factor"] = efo

        # Convert everything from ids to objects
        info['email'] = User(info['email'])
        if info['principal_investigator_id'] is not None:
            info['principal_investigator_id'] = StudyPerson(
                info['principal_investigator_id'])
        if info['lab_person_id'] is not None:
            info['lab_person_id'] = StudyPerson(
                info['lab_person_id'])
        if info['emp_person_id'] is not None:
            info['emp_person_id'] = StudyPerson(
                info['emp_person_id'])
        # remove id since not needed
        info.pop("study_id")
        return info

    @info.setter
    def info(self, info):
        """Updates the information attached to the study

        Parameters
        ----------
        info : dict
            information to change/update for the study, keyed to column name
        """
        conn_handler = SQLConnectionHandler()

        # Save study_experimental_factor data for insertion
        efo = None
        if "study_experimental_factor" in info:
            efo = info["study_experimental_factor"]
            if isinstance(efo, int):
                efo = [efo]
            info.pop("study_experimental_factor")

        check_table_cols(conn_handler, info, "study")

        data = []
        sql = "UPDATE qiita.{0} SET ".format(self._table)
        # items() used for py3 compatability
        # build query with data values in correct order for SQL statement
        for key, val in info.items():
            sql = ' '.join((sql, key, "=", "%s,"))
            if isinstance(val, QiitaObject):
                data.append(val.id)
            else:
                data.append(val)
        sql = ' '.join((sql[:-1], "WHERE study_id = %s"))
        data.append(self._id)
        conn_handler.execute(sql, data)

        if efo:
            # insert efo information into database
            sql = ("INSERT INTO qiita.{0}_experimental_factor (study_id, "
                   "efo_id) VALUES (%s, %s)".format(self._table))
            conn_handler.executemany(sql, zip([self._id] * len(efo), efo))

    @property
    def status(self):
        """Returns the study_status_id for the study

        Returns
        -------
        int: status of study
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT study_status_id FROM qiita.{0} WHERE "
               "study_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @status.setter
    def status(self, status_id):
        """Sets the study_status_id for the study

        Parameters
        ----------
        status_id: int
            ID for the new status
        """
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.{0} SET study_status_id = %s WHERE "
               "study_id = %s".format(self._table))
        conn_handler.execute(sql, (status_id, self._id))

    @property
    def sample_ids(self):
        """Returns the IDs of all samples in study

        Returns
        -------
        list of str
            The sample IDs in alphabetical order.
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT sample_id FROM qiita.required_sample_info WHERE "
               "study_id = %s ORDER BY sample_id".format(self._table))
        return [x[0] for x in conn_handler.execute_fetchall(sql, (self._id, ))]

    @property
    def shared_with(self):
        """list of users the study is shared with

        Returns
        -------
        list of User objects
            Users the study is shared with
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT email FROM qiita.{0}_users WHERE "
               "study_id = %s".format(self._table))
        users = [x[0] for x in conn_handler.execute_fetchall(sql, (self._id,))]
        return [User(email) for email in users]

    @property
    def pmids(self):
        """ Returns list of paper PMIDs from this study

        Returns
        -------
        list of str
            list of all the PMIDs
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT pmid FROM qiita.{0}_pmid WHERE "
               "study_id = %s".format(self._table))
        return [x[0] for x in conn_handler.execute_fetchall(sql, (self._id, ))]

    @property
    def investigations(self):
        """ Returns list of investigations this study is part of 

        Returns
        -------
        list of Investigation objects
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT investigation_id FROM qiita.investigation_study WHERE "
               "study_id = %s")
        invs = conn_handler.execute_fetchall(sql, (self._id, ))
        return [Investigation(inv[0]) for inv in invs]

    @property
    def metadata(self):
        """ Returns list of metadata columns

        Returns
        -------
        SampleTemplate object
        """
        return SampleTemplate(self._id)

    @property
    def raw_data(self):
        """ Returns list of data objects with raw data info 

        Returns
        -------
        list of RawData objects
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT raw_data_id FROM qiita.study_raw_data WHERE "
               "study_id = %s")
        raw_ids = [x[0] for x in conn_handler.execute_fetchall(sql,
                                                               (self._id, ))]
        return [RawData(rid) for rid in raw_ids]

    @property
    def preprocessed_data(self):
        """ Returns list of data objects with preprocessed data info 

        Returns
        -------
        list of PreprocessedData objects
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT preprocessed_data_id FROM qiita.study_preprocessed_data"
               " WHERE study_id = %s")
        pre_ids = [x[0] for x in conn_handler.execute_fetchall(sql,
                                                               (self._id,))]
        return [PreprocessedData(pid) for pid in pre_ids]

    @property
    def processed_data(self):
        """ Returns list of data objects with processed data info

        Returns
        -------
        list of ProcessedData objects
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT processed_data_id FROM qiita.processed_data WHERE "
               "preprocessed_data_id IN (SELECT preprocessed_data_id FROM "
               "qiita.study_preprocessed_data where study_id = %s)")
        pro_ids = [x[0] for x in conn_handler.execute_fetchall(sql,
                                                               (self._id,))]
        return [ProcessedData(pid) for pid in pro_ids]

# --- methods ---
    def share_with(self, user):
        """Shares the study with given user

        Parameters
        ----------
        email: str
            email of the user to share with
        """
        conn_handler = SQLConnectionHandler()
        sql = ("INSERT INTO qiita.study_users (study_id, email) VALUES "
               "(%s, %s)")
        conn_handler.execute(sql, (self._id, user.id))

    def add_pmid(self, pmid):
        """Adds PMID to study

        Parameters
        ----------
        pmid: int
            pmid to associate with study
        """
        conn_handler = SQLConnectionHandler()
        sql = ("INSERT INTO qiita.{0}_pmid (study_id, pmid) "
               "VALUES (%s, %s)".format(self._table))
        conn_handler.execute(sql, (self._id, pmid))


class StudyPerson(QiitaObject):
    r"""Object handling information pertaining to people involved in a study

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
    _table = "study_person"

    @classmethod
    def create(cls, name, email, address=None, phone=None):
        """Create a StudyPerson object, checking if person already exists.

        Parameters
        ----------
        name: str
            name of person
        email: str
            email of person
        address: str, optional
            address of person
        phone: str, optional
            phone number of person

        Returns
        -------
        New StudyPerson object
        """
        # Make sure person doesn't already exist
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT study_person_id FROM qiita.{0} WHERE name = %s AND "
               "email = %s".format(cls._table))
        spid = conn_handler.execute_fetchone(sql, (name, email))
        if spid is None:
            # Doesn't exist so insert new person
            sql = ("INSERT INTO qiita.{0} (name, email, address, phone) VALUES"
                   " (%s, %s, %s, %s) RETURNING "
                   "study_person_id".format(cls._table))
            spid = conn_handler.execute_fetchone(sql, (name, email, address,
                                                       phone))
        return cls(spid[0])

    # Properties
    @property
    def name(self):
        """Returns the name of the person

        Returns
        -------
        str: name of person
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT name FROM qiita.{0} WHERE "
               "study_person_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @name.setter
    def name(self, value):
        """Changes the name of the person

        Parameters
        ----------
        value: str
            New name for person
        """
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.{0} SET name = %s WHERE "
               "study_person_id = %s".format(self._table))
        conn_handler.execute(sql, (value, self._id))

    @property
    def email(self):
        """Returns the email of the person

        Returns
        -------
        str: email of person
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT email FROM qiita.{0} WHERE "
               "study_person_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @email.setter
    def email(self, value):
        """Changes the name of the person

        Parameters
        ----------
        value: str
            New email for person
        """
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.{0} SET email = %s WHERE "
               "study_person_id = %s".format(self._table))
        conn_handler.execute(sql, (value, self._id))

    @property
    def address(self):
        """Returns the address of the person

        Returns
        -------
        str or None
            address or None if no address in database
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT address FROM qiita.{0} WHERE study_person_id ="
               " %s".format(self._table))
        address = conn_handler.execute_fetchone(sql, (self._id, ))
        if address is not None:
            return address[0]
        return None

    @address.setter
    def address(self, value):
        """Set/update the address of the person

        Parameters
        ----------
        value: str
            New address for person
        """
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.{0} SET address = %s WHERE "
               "study_person_id = %s".format(self._table))
        conn_handler.execute(sql, (value, self._id))

    @property
    def phone(self):
        """Returns the phone number of the person

        Returns
        -------
         str or None
            phone or None if no address in database
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT phone FROM qiita.{0} WHERE "
               "study_person_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @phone.setter
    def phone(self, value):
        """Set/update the phone number of the person

        Parameters
        ----------
        value: str
            New phone number for person
        """
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.{0} SET phone = %s WHERE "
               "study_person_id = %s".format(self._table))
        conn_handler.execute(sql, (value, self._id))
