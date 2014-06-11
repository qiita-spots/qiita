r"""
Study and StudyPerson objects (:mod:`qiita_db.study`)
=====================================================

.. currentmodule:: qiita_db.study

This module provides the implementation of the Study and StudyPerson classes.
The study class allows access to all basic information including name and
pmids associated with the study, as well as returning objects for the data,
metadata, owner, and shared users. It is the central hub for creating,
deleting, and accessing a study in the database.

Contacts are taken care of by the StudyPerson class. This holds the contact's
name, email, address, and phone of the various persons in a study, e.g. The PI
or lab contact.

Classes
-------

.. autosummary::
   :toctree: generated/

   Study
   StudyPerson

Examples
--------
Studies contain contact people (PIs, Lab members, and EBI contacts). These
people have names, emails, addresses, and phone numbers. The email and name are
the minimum required information.

>>> from qiita_db.study import StudyPerson # doctest: +SKIP
>>> person = StudyPerson.create('Some Dude', 'somedude@foo.bar',
...                             address='111 fake street',
...                             phone='111-121-1313') # doctest: +SKIP
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

>>> from qiita_db.study import Study # doctest: +SKIP
>>> from qiita_db.user import User # doctest: +SKIP
>>> info = {
...     "timeseries_type_id": 1,
...     "metadata_complete": True,
...     "mixs_compliant": True,
...     "number_samples_collected": 25,
...     "number_samples_promised": 28,
...     "portal_type_id": 3,
...     "study_title": "Study Title",
...     "study_alias": "TST",
...     "study_description": "Some description of the study goes here",
...     "study_abstract": "Some abstract goes here",
...     "emp_person_id": StudyPerson(2),
...     "principal_investigator_id": StudyPerson(3),
...     "lab_person_id": StudyPerson(1)} # doctest: +SKIP
>>> owner = User('owner@foo.bar') # doctest: +SKIP
>>> Study(owner, 1, info) # doctest: +SKIP

You can also add a study to an investigation by passing the investigation
object while creating the study.

>>> from qiita_db.study import Study # doctest: +SKIP
>>> from qiita_db.user import User # doctest: +SKIP
>>> from qiita_db.study import Investigation # doctest: +SKIP
>>> info = {
...     "timeseries_type_id": 1,
...     "metadata_complete": True,
...     "mixs_compliant": True,
...     "number_samples_collected": 25,
...     "number_samples_promised": 28,
...     "portal_type_id": 3,
...     "study_title": "Study Title",
...     "study_alias": "TST",
...     "study_description": "Some description of the study goes here",
...     "study_abstract": "Some abstract goes here",
...     "emp_person_id": StudyPerson(2),
...     "principal_investigator_id": StudyPerson(3),
...     "lab_person_id": StudyPerson(1)} # doctest: +SKIP
>>> owner = User('owner@foo.bar') # doctest: +SKIP
>>> investigation = Investigation(1) # doctest: +SKIP
>>> Study(owner, 1, info, investigation) # doctest: +SKIP
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from future.builtins import zip
from datetime import date

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .base import QiitaStatusObject, QiitaObject
from .exceptions import (QiitaDBDuplicateError, QiitaDBNotImplementedError,
                         QiitaDBStatusError)
from .data import RawData, PreprocessedData, ProcessedData
from .user import User
from .investigation import Investigation
from .util import check_required_columns, check_table_cols
from .metadata_template import SampleTemplate
from .sql_connection import SQLConnectionHandler


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
    efo: list of int
        list of Experimental Factor Ontology ids for the study
    shared_with: list of User objects
        Emails of users the study is shared with
    pmids: list of str
        PMIDs assiciated with the study
    investigation: Investigation object
        Investigation the study is part of
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
    share
    unshare
    add_pmid

    Notes
    -----
    All setters raise QiitaDBStatusError if trying to change a public study.
    You should not be doing that.
    """
    _table = "study"

    def _lock_public(self, conn_handler):
        """Raises QiitaDBStatusError if study is public"""
        sql = ("SELECT study_status_id FROM qiita.{0} WHERE "
               "{0}_id = %s".format(self._table))
        if conn_handler.execute_fetchone(sql, (self._id, ))[0] == 2:
            raise QiitaDBStatusError("Can't change status of public study!")

    def _status_setter_checks(self, conn_handler):
        r"""Perform any extra checks that needed to be done before setting the
        object status on the database. Should be overwritten by the subclasses
        """
        self._lock_public(conn_handler)

    @classmethod
    def create(cls, owner, efo, info, investigation=None):
        """Creates a new study on the database

        Parameters
        ----------
        owner : User object
            the user id of the study' owner
        info: dict
            the information attached to the study.
        efo: int or list
            Experimental Factor Ontology or -ies for the study
        investigation: Investigation object
            if the study is part of an investigation, the id to associate with

        Raises
        ------
        QiitaDBColumnError
            Non-db columns in info dictionary
            All required keys not passed
        IncompetentQiitaDeveloperError
            study_id or study_status_id passed as a key

        Notes
        -----
        All keys in info, except the efo, must be equal to columns in
        qiita.study table in the database. EFO information is stored as a list
        under the key 'study_experimental_factor', the name of the table it is
        stored in.
        """
        # make sure not passing a study id in the info dict
        if "study_id" in info:
            raise IncompetentQiitaDeveloperError("Can't pass study_id in info "
                                                 "dict!")
        if "study_status_id" in info:
            raise IncompetentQiitaDeveloperError("Can't pass status in info "
                                                 "dict!")

        # add default values to info
        info['email'] = owner.id
        info['reprocess'] = False
        info['first_contact'] = date.today().strftime("%B %d, %Y")
        # default to waiting_approval status
        info['study_status_id'] = 1

        conn_handler = SQLConnectionHandler()
        # make sure dictionary only has keys for available columns in db
        check_table_cols(conn_handler, info, cls._table)
        # make sure reqired columns in dictionary
        check_required_columns(conn_handler, info, cls._table)

        # Insert study into database
        keys = info.keys()
        sql = ("INSERT INTO qiita.{0} ({1}) VALUES ({2}) RETURNING "
               "study_id".format(cls._table, ','.join(keys),
                                 ','.join(['%s'] * len(info))))
        # make sure data in same order as sql column names, and ids are used
        data = []
        for col in keys:
            if isinstance(info[col], QiitaObject):
                data.append(info[col].id)
            else:
                data.append(info[col])
        study_id = conn_handler.execute_fetchone(sql, data)[0]

        # insert efo information into database
        if isinstance(efo, int):
                efo = [efo]
        sql = ("INSERT INTO qiita.{0}_experimental_factor (study_id, "
               "efo_id) VALUES (%s, %s)".format(cls._table))
        conn_handler.executemany(sql, list(zip([study_id] * len(efo), efo)))

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
        raise QiitaDBNotImplementedError()

# --- Attributes ---
    @property
    def title(self):
        """Returns the title of the study

        Returns
        -------
        str
            Title of study
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
        self._lock_public(conn_handler)
        sql = ("UPDATE qiita.{0} SET study_title = %s WHERE "
               "study_id = %s".format(self._table))
        return conn_handler.execute(sql, (title, self._id))

    @property
    def info(self):
        """Dict with all information attached to the study

        Returns
        -------
        dict
            info of study keyed to column names
        """
        conn_handler = SQLConnectionHandler()
        sql = "SELECT * FROM qiita.{0} WHERE study_id = %s".format(self._table)
        info = dict(conn_handler.execute_fetchone(sql, (self._id, )))

        # Convert everything from ids to objects
        info['email'] = User(info['email'])
        info.update({k: StudyPerson(info[k]) for k in
                    ['principal_investigator_id', 'lab_person_id',
                    'emp_person_id'] if info[k] is not None})
        # remove id and status since not needed
        info.pop("study_id")
        info.pop("study_status_id")
        return info

    @info.setter
    def info(self, info):
        """Updates the information attached to the study

        Parameters
        ----------
        info : dict
            information to change/update for the study, keyed to column name

        Raises
        ------
        IncompetentQiitaDeveloperError
            Empty dict passed
        QiitaDBColumnError
            Unknown column names passed
        """
        conn_handler = SQLConnectionHandler()
        self._lock_public(conn_handler)
        if not info:
            raise IncompetentQiitaDeveloperError("Need entries in info dict!")

        # make sure dictionary only has keys for available columns in db
        check_table_cols(conn_handler, info, self._table)

        sql_vals = []
        data = []
        # items() used for py3 compatability
        # build query with data values in correct order for SQL statement
        for key, val in info.items():
            sql_vals.append("{0} = %s".format(key))
            if isinstance(val, QiitaObject):
                data.append(val.id)
            else:
                data.append(val)
        data.append(self._id)

        sql = ("UPDATE qiita.{0} SET {1} WHERE "
               "study_id = %s".format(self._table, ','.join(sql_vals)))
        conn_handler.execute(sql, data)

    @property
    def efo(self):
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT efo_id FROM qiita.{0}_experimental_factor WHERE "
               "study_id = %s".format(self._table))
        return [x[0] for x in conn_handler.execute_fetchall(sql, (self._id, ))]

    @efo.setter
    def efo(self, efo_vals):
        """Sets the efo for the study

        Parameters
        ----------
        status_id: int
            ID for the new status
        """
        conn_handler = SQLConnectionHandler()
        self._lock_public(conn_handler)
        if isinstance(efo_vals, int):
                efo_vals = [efo_vals]
        # wipe out any EFOs currently attached to study
        sql = ("DELETE FROM qiita.{0}_experimental_factor WHERE "
               "study_id = %s".format(self._table))
        conn_handler.execute(sql, (self._id, ))
        # insert new EFO information into database
        sql = ("INSERT INTO qiita.{0}_experimental_factor (study_id, "
               "efo_id) VALUES (%s, %s)".format(self._table))
        conn_handler.executemany(sql, list(zip([self._id] * len(efo_vals),
                                           efo_vals)))

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
        return [User(x[0]) for x in conn_handler.execute_fetchall(sql,
                                                                  (self._id,))]

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
    def investigation(self):
        """ Returns Investigation this study is part of

        Returns
        -------
        Investigation object
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT investigation_id FROM qiita.investigation_study WHERE "
               "study_id = %s")
        inv = conn_handler.execute_fetchone(sql, (self._id, ))
        return Investigation(inv[0]) if inv is not None else inv

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
        return [RawData(x[0]) for x in
                conn_handler.execute_fetchall(sql, (self._id,))]

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
        return [PreprocessedData(x[0]) for x in
                conn_handler.execute_fetchall(sql, (self._id,))]

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
        return [ProcessedData(x[0]) for x in
                conn_handler.execute_fetchall(sql, (self._id,))]

# --- methods ---
    def share(self, user):
        """Shares the study with given user

        Parameters
        ----------
        user: User object
            The user to share with
        """
        conn_handler = SQLConnectionHandler()
        sql = ("INSERT INTO qiita.study_users (study_id, email) VALUES "
               "(%s, %s)")
        conn_handler.execute(sql, (self._id, user.id))

    def add_pmid(self, pmid):
        """Adds PMID to study

        Parameters
        ----------
        pmid: str
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
    address: str or None
        address of the person
    phone: str or None
        phone number of the person
    """
    _table = "study_person"

    @classmethod
    def exists(cls, name, email):
        """Checks if a person exists

        Parameters
        ----------
        name: str
            Name of the person
        email: str
            Email of the person

        Returns
        -------
        bool
            True if person exists else false
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT exists(SELECT * FROM qiita.{0} WHERE "
               "name = %s AND email = %s)".format(cls._table))
        return conn_handler.execute_fetchone(sql, (name, email))[0]

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

        Raises
        ------
        QiitaDBExecutionError
            Person already exists
        """
        if cls.exists(name, email):
            raise QiitaDBDuplicateError("StudyPerson already exists!")

        # Doesn't exist so insert new person
        sql = ("INSERT INTO qiita.{0} (name, email, address, phone) VALUES"
               " (%s, %s, %s, %s) RETURNING "
               "study_person_id".format(cls._table))
        conn_handler = SQLConnectionHandler()
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
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

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
