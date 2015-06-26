r"""
Study and StudyPerson objects (:mod:`qiita_db.study`)
=====================================================

.. currentmodule:: qiita_db.study

This module provides the implementation of the Study and StudyPerson classes.
The study class allows access to all basic information including name and
pmids associated with the study, as well as returning ids for the data,
sample template, owner, and shared users. It is the central hub for creating,
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
...     "study_alias": "TST",
...     "study_description": "Some description of the study goes here",
...     "study_abstract": "Some abstract goes here",
...     "emp_person_id": StudyPerson(2),
...     "principal_investigator_id": StudyPerson(3),
...     "lab_person_id": StudyPerson(1)} # doctest: +SKIP
>>> owner = User('owner@foo.bar') # doctest: +SKIP
>>> Study(owner, "New Study Title", 1, info) # doctest: +SKIP

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
...     "study_alias": "TST",
...     "study_description": "Some description of the study goes here",
...     "study_abstract": "Some abstract goes here",
...     "emp_person_id": StudyPerson(2),
...     "principal_investigator_id": StudyPerson(3),
...     "lab_person_id": StudyPerson(1)} # doctest: +SKIP
>>> owner = User('owner@foo.bar') # doctest: +SKIP
>>> investigation = Investigation(1) # doctest: +SKIP
>>> Study(owner, "New Study Title", 1, info, investigation) # doctest: +SKIP
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from future.utils import viewitems
from copy import deepcopy
from itertools import chain
import warnings

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .base import QiitaObject
from .exceptions import (QiitaDBStatusError, QiitaDBColumnError, QiitaDBError,
                         QiitaDBDuplicateError)
from .util import (check_required_columns, check_table_cols, convert_to_id,
                   get_environmental_packages, get_table_cols, infer_status)
from .sql_connection import SQLConnectionHandler, Transaction
from .util import exists_table


class Study(QiitaObject):
    r"""Study object to access to the Qiita Study information

    Attributes
    ----------
    data_types
    efo
    info
    investigation
    name
    pmids
    shared_with
    sample_template
    status
    title
    owner

    Methods
    -------
    raw_data
    preprocessed_data
    processed_data
    add_pmid
    exists
    has_access
    share
    unshare

    Notes
    -----
    All setters raise QiitaDBStatusError if trying to change a public study.
    You should not be doing that.
    """
    _table = "study"
    # The following columns are considered not part of the study info
    _non_info = frozenset(["email", "study_title"])
    # The following tables are considered part of info
    _info_cols = frozenset(chain(
        get_table_cols('study'), get_table_cols('study_status'),
        get_table_cols('timeseries_type'), get_table_cols('portal_type'),
        get_table_cols('study_pmid')))

    def _lock_non_sandbox(self, trans):
        """Raises QiitaDBStatusError if study is non-sandboxed"""
        if self.status(trans) != 'sandbox':
            raise QiitaDBStatusError("Illegal operation on non-sandbox study!")

    def status(self, trans=None):
        r"""The status is inferred by the status of its processed data

        Parameters
        ----------
        trans: Transaction, optional
            Transaction in which this method should be executed
        """
        trans = trans if trans is not None else Transaction("study_status_%s"
                                                            % self._id)
        with trans:
            # Get the status of all its processed data
            sql = """SELECT processed_data_status
                     FROM qiita.processed_data_status pds
                        JOIN qiita.processed_data pd
                            USING (processed_data_status_id)
                        JOIN qiita.study_processed_data spd
                            USING (processed_data_id)
                     WHERE spd.study_id = %s"""
            trans.add(sql, [self._id])
            pd_statuses = trans.execute()[-1]

            return infer_status(pd_statuses)

    @classmethod
    def get_by_status(cls, status, trans=None):
        """Returns study id for all Studies with given status

        Parameters
        ----------
        status : str
            Status setting to search for
        trans: Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        set of int
            All study ids in the database that match the given status
        """
        trans = trans if trans is not None else Transaction(
            "get_study_by_status")
        with trans:
            sql = """SELECT study_id FROM qiita.study_processed_data spd
                    JOIN qiita.processed_data pd
                    ON spd.processed_data_id=pd.processed_data_id
                    JOIN qiita.processed_data_status pds
                    ON pds.processed_data_status_id=pd.processed_data_status_id
                    WHERE pds.processed_data_status=%s"""
            trans.add(sql, [status])
            studies = {x[0] for x in trans.execute()}
            # If status is sandbox, all the studies that are not present in the
            # study_processed_data are also sandbox
            if status == 'sandbox':
                sql = """SELECT study_id FROM qiita.study WHERE study_id NOT IN (
                         SELECT study_id FROM qiita.study_processed_data)"""
                trans.add(sql)
                extra_studies = {x[0] for x in trans.execute()}
                studies = studies.union(extra_studies)

        return studies

    @classmethod
    def get_info(cls, study_ids=None, info_cols=None):
        """Returns study data for a set of study_ids

        Parameters
        ----------
        study_ids : list of ints, optional
            Studies to get information for. Defauls to all studies
        info_cols: list of str, optional
            Information columns to retrieve. Defaults to all study data

        Returns
        -------
        list of DictCursor
            Table-like structure of metadata, one study per row. Can be
            accessed as a list of dictionaries, keyed on column name.
        """
        if info_cols is None:
            info_cols = cls._info_cols
        elif not cls._info_cols.issuperset(info_cols):
            warnings.warn("Non-info columns passed: %s" % ", ".join(
                set(info_cols) - cls._info_cols))

        search_cols = ",".join(sorted(cls._info_cols.intersection(info_cols)))

        sql = """SELECT {0} FROM (
            qiita.study
            JOIN qiita.timeseries_type  USING (timeseries_type_id)
            JOIN qiita.portal_type USING (portal_type_id)
            LEFT JOIN (SELECT study_id, array_agg(pmid ORDER BY pmid) as
            pmid FROM qiita.study_pmid GROUP BY study_id) sp USING (study_id)
            )""".format(search_cols)
        if study_ids is not None:
            sql = "{0} WHERE study_id in ({1})".format(
                sql, ','.join(str(s) for s in study_ids))

        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchall(sql)

    @classmethod
    def exists(cls, study_title, trans=None):
        """Check if a study exists based on study_title, which is unique

        Parameters
        ----------
        study_title : str
            The title of the study to search for in the database
        trans: Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        bool
        """
        trans = trans if trans is not None else Transaction("exists_%s"
                                                            % study_title)
        with trans:
            sql = ("SELECT exists(select study_id from qiita.{} WHERE "
                   "study_title = %s)").format(cls._table)
            trans.add(sql, [study_title])
            return trans.execute()[-1][0][0]

    @classmethod
    def create(cls, owner, title, efo, info, investigation=None):
        """Creates a new study on the database

        Parameters
        ----------
        owner : User object
            the study's owner
        title : str
            Title of the study
        efo : list
            Experimental Factor Ontology id(s) for the study
        info : dict
            the information attached to the study. All "*_id" keys must pass
            the objects associated with them.
        investigation : Investigation object, optional
            If passed, the investigation to associate with. Defaults to None.

        Raises
        ------
        QiitaDBDuplicateError
            If another study with the same title already exists in the DB
        QiitaDBColumnError
            Non-db columns in info dictionary
            All required keys not passed
        IncompetentQiitaDeveloperError
            email, study_id, study_status_id, or study_title passed as a key
            empty efo list passed

        Notes
        -----
        All keys in info, except the efo, must be equal to columns in
        qiita.study table in the database.
        """
        # make sure not passing non-info columns in the info dict
        if cls._non_info.intersection(info):
            raise QiitaDBColumnError("non info keys passed: %s" %
                                     cls._non_info.intersection(info))

        # make sure efo info passed
        if not efo:
            raise IncompetentQiitaDeveloperError("Need EFO information!")

        with Transaction("create_%s" % title) as trans:
            if cls.exists(title, trans=trans):
                raise QiitaDBDuplicateError("Study", "title: %s" % title)

            # add default values to info
            insertdict = deepcopy(info)
            insertdict['email'] = owner.id
            insertdict['study_title'] = title
            if "reprocess" not in insertdict:
                insertdict['reprocess'] = False

            # No Nones allowed
            insertdict = {k: v for k, v in viewitems(insertdict)
                          if v is not None}

            # make sure dictionary only has keys for available columns in db
            check_table_cols(trans, insertdict, cls._table)
            # make sure reqired columns in dictionary
            check_required_columns(trans, insertdict, cls._table)

            # Insert study into database
            sql = ("INSERT INTO qiita.{0} ({1}) VALUES ({2}) RETURNING "
                   "study_id".format(cls._table, ','.join(insertdict),
                                     ','.join(['%s'] * len(insertdict))))
            # make sure data in same order as sql column names,
            # and ids are used
            data = []
            for col in insertdict:
                if isinstance(insertdict[col], QiitaObject):
                    data.append(insertdict[col].id)
                else:
                    data.append(insertdict[col])

            trans.add(sql, data)
            study_id = trans.execute()[-1][0][0]

            # insert efo information into database
            sql = ("INSERT INTO qiita.{0}_experimental_factor (study_id, "
                   "efo_id) VALUES (%s, %s)".format(cls._table))
            trans.add(sql, [[study_id, e] for e in efo], many=True)

            # add study to investigation if necessary
            if investigation:
                sql = ("INSERT INTO qiita.investigation_study "
                       "(investigation_id, study_id) VALUES (%s, %s)")
                trans.add(sql, [investigation.id, study_id])
            trans.execute()

        return cls(study_id)

    @classmethod
    def delete(cls, id_):
        r"""Deletes the study from the database

        Parameters
        ----------
        id_ : integer
            The object identifier

        Raises
        ------
        QiitaDBError
            If the sample_(id_) table exists means a sample template exists
        """
        with Transaction("delete_study_%d" % id_) as trans:
            # checking that the id_ exists
            st = cls(id_, trans=trans)

            if exists_table('sample_%d' % id_, trans):
                raise QiitaDBError(
                    'Study "%s" cannot be erased because it has a '
                    'sample template' % st.title(trans))

            sql = "DELETE FROM qiita.study_sample_columns WHERE study_id = %s"
            args = [id_]
            trans.add(sql, args)

            sql = """DELETE FROM qiita.study_experimental_factor
                     WHERE study_id = %s"""
            trans.add(sql, args)

            sql = "DELETE FROM qiita.study_pmid WHERE study_id = %s"
            trans.add(sql, args)

            sql = """DELETE FROM qiita.study_environmental_package
                     WHERE study_id = %s"""
            trans.add(sql, args)

            sql = "DELETE FROM qiita.study_users WHERE study_id = %s"
            trans.add(sql, args)

            sql = "DELETE FROM qiita.investigation_study WHERE study_id = %s"
            trans.add(sql, args)

            sql = "DELETE FROM qiita.study WHERE study_id = %s"
            trans.add(sql, args)

            trans.execute()


# --- Attributes ---
    def title(self, trans=None):
        """Returns the title of the study

        Parameters
        ----------
        trans: Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        str
            Title of study
        """
        trans = trans if trans is not None else Transaction("title_%s"
                                                            % self._id)
        with trans:
            sql = ("SELECT study_title FROM qiita.{0} WHERE "
                   "study_id = %s".format(self._table))
            trans.add(sql, [self._id])
            return trans.execute()[-1][0][0]

    def set_title(self, title, trans=None):
        """Sets the title of the study

        Parameters
        ----------
        title : str
            The new study title
        trans: Transaction, optional
            Transaction in which this method should be executed
        """
        trans = trans if trans is not None else Transaction("set_title_%s"
                                                            % self._id)
        with trans:
            sql = ("UPDATE qiita.{0} SET study_title = %s WHERE "
                   "study_id = %s".format(self._table))
            trans.add(sql, [title, self._id])
            return trans.execute()

    def info(self, trans=None):
        """Dict with all information attached to the study

        Parameters
        ----------
        trans: Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        dict
            info of study keyed to column names
        """
        trans = trans if trans is not None else Transaction("study_info_%s"
                                                            % (self._id))
        with trans:
            sql = "SELECT * FROM qiita.{0} WHERE study_id = %s".format(
                self._table)
            trans.add(sql, [self._id])
            info = dict(trans.execute()[-1][0])
            # remove non-info items from info
            for item in self._non_info:
                info.pop(item)
            # This is an optional column, but should not be considered part
            # of the info
            info.pop('study_id')
        return info

    def set_info(self, info, trans=None):
        """Updates the information attached to the study

        Parameters
        ----------
        info : dict
            information to change/update for the study, keyed to column name
        trans: Transaction, optional
            Transaction in which this method should be executed

        Raises
        ------
        IncompetentQiitaDeveloperError
            Empty dict passed
        QiitaDBColumnError
            Unknown column names passed
        """
        if not info:
            raise IncompetentQiitaDeveloperError("Need entries in info dict!")

        if 'study_id' in info:
            raise QiitaDBColumnError("Cannot set study_id!")

        if self._non_info.intersection(info):
            raise QiitaDBColumnError("non info keys passed: %s" %
                                     self._non_info.intersection(info))

        trans = trans if trans is not None else Transaction("set_study_info_%s"
                                                            % (self._id))
        with trans:
            if 'timeseries_type_id' in info:
                # We only lock if the timeseries type changes
                self._lock_non_sandbox(trans)

            # make sure dictionary only has keys for available columns in db
            check_table_cols(trans, info, self._table)

            sql_vals = []
            data = []
            # build query with data values in correct order for SQL statement
            for key, val in viewitems(info):
                sql_vals.append("{0} = %s".format(key))
                if isinstance(val, QiitaObject):
                    data.append(val.id)
                else:
                    data.append(val)
            data.append(self._id)

            sql = ("UPDATE qiita.{0} SET {1} WHERE "
                   "study_id = %s".format(self._table, ','.join(sql_vals)))
            trans.add(sql, data)
            trans.execute()

    def efo(self, trans=None):
        """Gets the efo for the study

        Parameters
        ----------
        trans: Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        list of str
            The efos associated with the study
        """
        trans = trans if trans is not None else Transaction("efo_%s"
                                                            % (self._id))
        with trans:
            sql = ("SELECT efo_id FROM qiita.{0}_experimental_factor WHERE "
                   "study_id = %s".format(self._table))
            trans.add(sql, [self._id])
            return [x[0] for x in trans.execute()[-1]]

    def set_efo(self, efo_vals, trans=None):
        """Sets the efo for the study

        Parameters
        ----------
        efo_vals : list
            Id(s) for the new efo values
        trans: Transaction, optional
            Transaction in which this method should be executed

        Raises
        ------
        IncompetentQiitaDeveloperError
            Empty efo list passed
        """
        if not efo_vals:
            raise IncompetentQiitaDeveloperError("Need EFO information!")

        trans = trans if trans is not None else Transaction("set_efo_%s"
                                                            % (self._id))
        with trans:
            self._lock_non_sandbox(trans)
            # wipe out any EFOs currently attached to study
            sql = ("DELETE FROM qiita.{0}_experimental_factor WHERE "
                   "study_id = %s".format(self._table))
            trans.add(sql, [self._id])
            # insert new EFO information into database
            sql = ("INSERT INTO qiita.{0}_experimental_factor (study_id, "
                   "efo_id) VALUES (%s, %s)".format(self._table))
            trans.add(sql, [[self._id, efo] for efo in efo_vals], many=True)
            trans.execute()

    def shared_with(self, trans=None):
        """list of users the study is shared with

        Parameters
        ----------
        trans: Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        list of User ids
            Users the study is shared with
        """
        trans = trans if trans is not None else Transaction("shared_with_%s"
                                                            % self._id)
        with trans:
            sql = ("SELECT email FROM qiita.{0}_users WHERE "
                   "study_id = %s".format(self._table))
            trans.add(sql, [self._id])
            return [x[0] for x in trans.execute()[-1]]

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

    @pmids.setter
    def pmids(self, values):
        """Sets the pmids for the study

        Parameters
        ----------
        values : list of str
            The list of pmids to associate with the study

        Raises
        ------
        TypeError
            If values is not a list
        """
        # Check that a list is actually passed
        if not isinstance(values, list):
            raise TypeError('pmids should be a list')

        # Get the connection to the database
        conn_handler = SQLConnectionHandler()

        # Create a queue for the operations that we need to do
        queue = "%d_pmid_setter" % self._id
        conn_handler.create_queue(queue)

        # Delete the previous pmids associated with the study
        sql = "DELETE FROM qiita.study_pmid WHERE study_id=%s"
        sql_args = (self._id,)
        conn_handler.add_to_queue(queue, sql, sql_args)

        # Set the new ones
        sql = "INSERT INTO qiita.study_pmid (study_id, pmid) VALUES (%s, %s)"
        sql_args = [(self._id, val) for val in values]
        conn_handler.add_to_queue(queue, sql, sql_args, many=True)

        # Execute the queue
        conn_handler.execute_queue(queue)

    @property
    def investigation(self):
        """ Returns Investigation this study is part of

        Returns
        -------
        Investigation id
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT investigation_id FROM qiita.investigation_study WHERE "
               "study_id = %s")
        inv = conn_handler.execute_fetchone(sql, (self._id, ))
        return inv[0] if inv is not None else inv

    @property
    def sample_template(self):
        """ Returns sample_template information id

        Returns
        -------
        SampleTemplate id
        """
        return self._id

    @property
    def data_types(self):
        """Returns list of the data types for this study

        Returns
        -------
        list of str
        """
        conn_handler = SQLConnectionHandler()
        sql = """SELECT DISTINCT data_type
                 FROM qiita.study_prep_template
                    JOIN qiita.prep_template USING (prep_template_id)
                    JOIN qiita.data_type USING (data_type_id)
                 WHERE study_id = %s"""
        return [x[0] for x in conn_handler.execute_fetchall(sql, (self._id,))]

    @property
    def owner(self):
        """Gets the owner of the study

        Returns
        -------
        str
            The email (id) of the user that owns this study
        """
        conn_handler = SQLConnectionHandler()
        sql = """select email from qiita.{} where study_id = %s""".format(
            self._table)

        return conn_handler.execute_fetchone(sql, [self._id])[0]

    @property
    def environmental_packages(self):
        """Gets the environmental packages associated with the study

        Returns
        -------
        list of str
            The environmental package names associated with the study
        """
        conn_handler = SQLConnectionHandler()
        env_pkgs = conn_handler.execute_fetchall(
            "SELECT environmental_package_name FROM "
            "qiita.study_environmental_package WHERE study_id = %s",
            (self._id,))
        return [pkg[0] for pkg in env_pkgs]

    @environmental_packages.setter
    def environmental_packages(self, values):
        """Sets the environmental packages for the study

        Parameters
        ----------
        values : list of str
            The list of environmental package names to associate with the study

        Raises
        ------
        TypeError
            If values is not a list
        ValueError
            If any environmental packages listed on values is not recognized
        """
        # Get the connection to the database
        conn_handler = SQLConnectionHandler()

        # The environmental packages can be changed only if the study is
        # sandboxed
        self._lock_non_sandbox(conn_handler)

        # Check that a list is actually passed
        if not isinstance(values, list):
            raise TypeError('Environmental packages should be a list')

        # Get all the environmental packages
        env_pkgs = [pkg[0] for pkg in get_environmental_packages()]

        # Check that all the passed values are valid environmental packages
        missing = set(values).difference(env_pkgs)
        if missing:
            raise ValueError('Environmetal package(s) not recognized: %s'
                             % ', '.join(missing))

        # Create a queue for the operations that we need to do
        queue = "%d_env_pkgs_setter" % self._id
        conn_handler.create_queue(queue)

        # Delete the previous environmental packages associated with the study
        sql = "DELETE FROM qiita.study_environmental_package WHERE study_id=%s"
        sql_args = (self._id,)
        conn_handler.add_to_queue(queue, sql, sql_args)

        # Set the new ones
        sql = ("INSERT INTO qiita.study_environmental_package "
               "(study_id, environmental_package_name) VALUES (%s, %s)")
        sql_args = [(self._id, val) for val in values]
        conn_handler.add_to_queue(queue, sql, sql_args, many=True)

        # Execute the queue
        conn_handler.execute_queue(queue)

    # --- methods ---
    def raw_data(self, data_type=None):
        """ Returns list of data ids for raw data info

        Parameters
        ----------
        data_type : str, optional
            If given, retrieve only raw_data for given datatype. Default None.

        Returns
        -------
        list of RawData ids
        """
        spec_data = ""
        if data_type:
            spec_data = " AND data_type_id = %d" % convert_to_id(data_type,
                                                                 "data_type")
        conn_handler = SQLConnectionHandler()
        sql = """SELECT raw_data_id
                 FROM qiita.study_prep_template
                    JOIN qiita.prep_template USING (prep_template_id)
                    JOIN qiita.raw_data USING (raw_data_id)
                 WHERE study_id = %s{0}""".format(spec_data)

        return [x[0] for x in conn_handler.execute_fetchall(sql, (self._id,))]

    def prep_templates(self, data_type=None):
        """Return list of prep template ids

        Parameters
        ----------
        data_type : str, optional
            If given, retrieve only prep templates for given datatype.
            Default None.

        Returns
        -------
        list of PrepTemplate ids
        """
        spec_data = ""
        if data_type:
            spec_data = " AND data_type_id = %s" % convert_to_id(data_type,
                                                                 "data_type")

        conn_handler = SQLConnectionHandler()
        sql = """SELECT prep_template_id
                 FROM qiita.study_prep_template
                    JOIN qiita.prep_template USING (prep_template_id)
                 WHERE study_id = %s{0}""".format(spec_data)
        return [x[0] for x in conn_handler.execute_fetchall(sql, (self._id,))]

    def preprocessed_data(self, data_type=None):
        """ Returns list of data ids for preprocessed data info

        Parameters
        ----------
        data_type : str, optional
            If given, retrieve only raw_data for given datatype. Default None.

        Returns
        -------
        list of PreprocessedData ids
        """
        spec_data = ""
        if data_type:
            spec_data = " AND data_type_id = %d" % convert_to_id(data_type,
                                                                 "data_type")
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT preprocessed_data_id FROM qiita.study_preprocessed_data"
               " WHERE study_id = %s{0}".format(spec_data))
        return [x[0] for x in conn_handler.execute_fetchall(sql, (self._id,))]

    def processed_data(self, data_type=None):
        """ Returns list of data ids for processed data info

        Parameters
        ----------
        data_type : str, optional
            If given, retrieve only for given datatype. Default None.

        Returns
        -------
        list of ProcessedData ids
        """
        spec_data = ""
        if data_type:
            spec_data = " AND p.data_type_id = %d" % convert_to_id(data_type,
                                                                   "data_type")
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT p.processed_data_id FROM qiita.processed_data p JOIN "
               "qiita.study_processed_data sp ON p.processed_data_id = "
               "sp.processed_data_id WHERE "
               "sp.study_id = %s{0}".format(spec_data))
        return [x[0] for x in conn_handler.execute_fetchall(sql, (self._id,))]

    def add_pmid(self, pmid):
        """Adds PMID to study

        Parameters
        ----------
        pmid : str
            pmid to associate with study
        """
        conn_handler = SQLConnectionHandler()
        sql = ("INSERT INTO qiita.{0}_pmid (study_id, pmid) "
               "VALUES (%s, %s)".format(self._table))
        conn_handler.execute(sql, (self._id, pmid))

    def has_access(self, user, no_public=False):
        """Returns whether the given user has access to the study

        Parameters
        ----------
        user : User object
            User we are checking access for
        no_public: bool
            If we should ignore those studies shared with the user. Defaults
            to False

        Returns
        -------
        bool
            Whether user has access to study or not
        """
        # if admin or superuser, just return true
        if user.level in {'superuser', 'admin'}:
            return True

        if no_public:
            return self._id in user.user_studies | user.shared_studies
        else:
            return self._id in user.user_studies | user.shared_studies \
                | self.get_by_status('public')

    def share(self, user):
        """Share the study with another user

        Parameters
        ----------
        user: User object
            The user to share the study with
        """
        conn_handler = SQLConnectionHandler()

        # Make sure the study is not already shared with the given user
        if user.id in self.shared_with:
            return
        # Do not allow the study to be shared with the owner
        if user.id == self.owner:
            return

        sql = ("INSERT INTO qiita.study_users (study_id, email) VALUES "
               "(%s, %s)")

        conn_handler.execute(sql, (self._id, user.id))

    def unshare(self, user):
        """Unshare the study with another user

        Parameters
        ----------
        user: User object
            The user to unshare the study with
        """
        conn_handler = SQLConnectionHandler()

        sql = ("DELETE FROM qiita.study_users WHERE study_id = %s AND "
               "email = %s")

        conn_handler.execute(sql, (self._id, user.id))


class StudyPerson(QiitaObject):
    r"""Object handling information pertaining to people involved in a study

    Attributes
    ----------
    name : str
        name of the person
    email : str
        email of the person
    affiliation : str
        institution with which the person is affiliated
    address : str or None
        address of the person
    phone : str or None
        phone number of the person
    """
    _table = "study_person"

    @classmethod
    def iter(cls):
        """Iterate over all study people in the database

        Returns
        -------
        generator
            Yields a `StudyPerson` object for each person in the database,
            in order of ascending study_person_id
        """
        conn = SQLConnectionHandler()
        sql = "select study_person_id from qiita.{} order by study_person_id"
        results = conn.execute_fetchall(sql.format(cls._table))

        for result in results:
            ID = result[0]
            yield StudyPerson(ID)

    @classmethod
    def exists(cls, name, affiliation):
        """Checks if a person exists

        Parameters
        ----------
        name: str
            Name of the person
        affiliation : str
            institution with which the person is affiliated

        Returns
        -------
        bool
            True if person exists else false
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT exists(SELECT * FROM qiita.{0} WHERE "
               "name = %s AND affiliation = %s)".format(cls._table))
        return conn_handler.execute_fetchone(sql, (name, affiliation))[0]

    @classmethod
    def create(cls, name, email, affiliation, address=None, phone=None):
        """Create a StudyPerson object, checking if person already exists.

        Parameters
        ----------
        name : str
            name of person
        email : str
            email of person
        affiliation : str
            institution with which the person is affiliated
        address : str, optional
            address of person
        phone : str, optional
            phone number of person

        Returns
        -------
        New StudyPerson object

        """
        if cls.exists(name, affiliation):
            sql = ("SELECT study_person_id from qiita.{0} WHERE name = %s and"
                   " affiliation = %s".format(cls._table))
            conn_handler = SQLConnectionHandler()
            spid = conn_handler.execute_fetchone(sql, (name, affiliation))

        # Doesn't exist so insert new person
        else:
            sql = ("INSERT INTO qiita.{0} (name, email, affiliation, address, "
                   "phone) VALUES"
                   " (%s, %s, %s, %s, %s) RETURNING "
                   "study_person_id".format(cls._table))
            conn_handler = SQLConnectionHandler()
            spid = conn_handler.execute_fetchone(sql, (name, email,
                                                       affiliation, address,
                                                       phone))
        return cls(spid[0])

    # Properties
    @property
    def name(self):
        """Returns the name of the person

        Returns
        -------
        str
            Name of person
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
        str
            Email of person
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT email FROM qiita.{0} WHERE "
               "study_person_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @property
    def affiliation(self):
        """Returns the affiliation of the person

        Returns
        -------
        str
            Affiliation of person
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT affiliation FROM qiita.{0} WHERE "
               "study_person_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, [self._id])[0]

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
        value : str
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
        value : str
            New phone number for person
        """
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.{0} SET phone = %s WHERE "
               "study_person_id = %s".format(self._table))
        conn_handler.execute(sql, (value, self._id))
