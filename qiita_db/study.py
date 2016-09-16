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
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb


_VALID_EBI_STATUS = ('not submitted', 'submitting', 'submitted')


class Study(qdb.base.QiitaObject):
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
    _portal_table = "study_portal"
    # The following columns are considered not part of the study info
    _non_info = frozenset(["email", "study_title", "ebi_submission_status",
                           "ebi_study_accession"])

    def _lock_non_sandbox(self):
        """Raises QiitaDBStatusError if study is non-sandboxed"""
        if self.status != 'sandbox':
            raise qdb.exceptions.QiitaDBStatusError(
                "Illegal operation on non-sandbox study!")

    @property
    def status(self):
        r"""The status is inferred by the status of its artifacts"""
        with qdb.sql_connection.TRN:
            # Get the status of all its artifacts
            sql = """SELECT DISTINCT visibility
                     FROM qiita.visibility
                        JOIN qiita.artifact USING (visibility_id)
                        JOIN qiita.study_artifact USING (artifact_id)
                     WHERE study_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.util.infer_status(
                qdb.sql_connection.TRN.execute_fetchindex())

    @staticmethod
    def all_data_types():
        """Returns list of all the data types available in the system

        Returns
        -------
        list of str
            All the data types available in the system
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT DISTINCT data_type FROM qiita.data_type"
            qdb.sql_connection.TRN.add(sql)
            return qdb.sql_connection.TRN.execute_fetchflatten()

    @classmethod
    def get_by_status(cls, status):
        """Returns study id for all Studies with given status

        Parameters
        ----------
        status : str
            Status setting to search for

        Returns
        -------
        set of qiita_db.study.Study
            All studies in the database that match the given status
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT DISTINCT study_id
                     FROM qiita.study_artifact
                        JOIN qiita.artifact USING (artifact_id)
                        JOIN qiita.visibility USING (visibility_id)
                        JOIN qiita.study_portal USING (study_id)
                        JOIN qiita.portal_type USING (portal_type_id)
                      WHERE visibility = %s AND portal = %s"""
            qdb.sql_connection.TRN.add(sql, [status, qiita_config.portal])
            studies = set(qdb.sql_connection.TRN.execute_fetchflatten())
            # If status is sandbox, all the studies that are not present in the
            # study_artifact table are also sandbox
            if status == 'sandbox':
                sql = """SELECT study_id
                         FROM qiita.study
                            JOIN qiita.study_portal USING (study_id)
                            JOIN qiita.portal_type USING (portal_type_id)
                         WHERE portal = %s AND study_id NOT IN (
                                SELECT study_id
                                FROM qiita.study_artifact)"""
                qdb.sql_connection.TRN.add(sql, [qiita_config.portal])
                studies = studies.union(
                    qdb.sql_connection.TRN.execute_fetchflatten())

            return set(cls(sid) for sid in studies)

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
        # The following tables are considered part of info
        _info_cols = frozenset(chain(
            qdb.util.get_table_cols('study'),
            qdb.util.get_table_cols('study_status'),
            qdb.util.get_table_cols('timeseries_type'),
            qdb.util.get_table_cols('study_publication')))

        if info_cols is None:
            info_cols = _info_cols
        elif not _info_cols.issuperset(info_cols):
            warnings.warn("Non-info columns passed: %s" % ", ".join(
                set(info_cols) - _info_cols))

        search_cols = ",".join(sorted(_info_cols.intersection(info_cols)))

        with qdb.sql_connection.TRN:
            sql = """SELECT {0}
                     FROM (
                        qiita.study
                        JOIN qiita.timeseries_type  USING (timeseries_type_id)
                        LEFT JOIN (
                            SELECT study_id, array_agg(
                                    publication_doi ORDER BY publication_doi)
                                AS publication_doi
                            FROM qiita.study_publication
                            GROUP BY study_id) sp USING (study_id)
                        JOIN qiita.study_portal USING (study_id)
                        JOIN qiita.portal_type USING (portal_type_id))
                    WHERE portal = %s""".format(search_cols)

            args = [qiita_config.portal]
            if study_ids is not None:
                sql = "{0} AND study_id IN %s".format(sql)
                args.append(tuple(study_ids))

            qdb.sql_connection.TRN.add(sql, args)
            res = qdb.sql_connection.TRN.execute_fetchindex()
            if study_ids is not None and len(res) != len(study_ids):
                raise qdb.exceptions.QiitaDBError(
                    'Non-portal-accessible studies asked for!')
            return res

    @classmethod
    def exists(cls, study_title):
        """Check if a study exists based on study_title, which is unique

        Parameters
        ----------
        study_title : str
            The title of the study to search for in the database

        Returns
        -------
        bool
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT study_id
                        FROM qiita.{}
                        WHERE study_title = %s)""".format(cls._table)
            qdb.sql_connection.TRN.add(sql, [study_title])
            return qdb.sql_connection.TRN.execute_fetchlast()

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
        QiitaDBColumnError
            Non-db columns in info dictionary
            All required keys not passed
        IncompetentQiitaDeveloperError
            email, study_id, study_status_id, or study_title passed as a key
            empty efo list passed
        QiitaDBDuplicateError
            If a study with the given title already exists

        Notes
        -----
        All keys in info, except the efo, must be equal to columns in
        qiita.study table in the database.
        """
        # make sure not passing non-info columns in the info dict
        if cls._non_info.intersection(info):
            raise qdb.exceptions.QiitaDBColumnError(
                "non info keys passed: %s" % cls._non_info.intersection(info))

        # make sure efo info passed
        if not efo:
            raise IncompetentQiitaDeveloperError("Need EFO information!")

        with qdb.sql_connection.TRN:
            if cls.exists(title):
                raise qdb.exceptions.QiitaDBDuplicateError(
                    "Study", "title: %s" % title)

            # add default values to info
            insertdict = deepcopy(info)
            insertdict['email'] = owner.id
            insertdict['study_title'] = title
            if "reprocess" not in insertdict:
                insertdict['reprocess'] = False

            # No nuns allowed
            insertdict = {k: v for k, v in viewitems(insertdict)
                          if v is not None}

            # make sure dictionary only has keys for available columns in db
            qdb.util.check_table_cols(insertdict, cls._table)
            # make sure reqired columns in dictionary
            qdb.util.check_required_columns(insertdict, cls._table)

            # Insert study into database
            sql = """INSERT INTO qiita.{0} ({1})
                     VALUES ({2}) RETURNING study_id""".format(
                cls._table, ','.join(insertdict),
                ','.join(['%s'] * len(insertdict)))

            # make sure data in same order as sql column names,
            # and ids are used
            data = []
            for col in insertdict:
                if isinstance(insertdict[col], qdb.base.QiitaObject):
                    data.append(insertdict[col].id)
                else:
                    data.append(insertdict[col])

            qdb.sql_connection.TRN.add(sql, data)
            study_id = qdb.sql_connection.TRN.execute_fetchlast()

            # insert efo information into database
            sql = """INSERT INTO qiita.{0}_experimental_factor
                        (study_id, efo_id)
                     VALUES (%s, %s)""".format(cls._table)
            qdb.sql_connection.TRN.add(
                sql, [[study_id, e] for e in efo], many=True)

            # Add to both QIITA and given portal (if not QIITA)
            portal_id = qdb.util.convert_to_id(
                qiita_config.portal, 'portal_type', 'portal')
            sql = """INSERT INTO qiita.study_portal (study_id, portal_type_id)
                     VALUES (%s, %s)"""
            args = [[study_id, portal_id]]
            if qiita_config.portal != 'QIITA':
                qp_id = qdb.util.convert_to_id(
                    'QIITA', 'portal_type', 'portal')
                args.append([study_id, qp_id])
            qdb.sql_connection.TRN.add(sql, args, many=True)
            qdb.sql_connection.TRN.execute()

            # add study to investigation if necessary
            if investigation:
                sql = """INSERT INTO qiita.investigation_study
                            (investigation_id, study_id)
                         VALUES (%s, %s)"""
                qdb.sql_connection.TRN.add(sql, [investigation.id, study_id])

            qdb.sql_connection.TRN.execute()

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
        with qdb.sql_connection.TRN:
            # checking that the id_ exists
            cls(id_)

            if qdb.util.exists_table('sample_%d' % id_):
                raise qdb.exceptions.QiitaDBError(
                    'Study "%s" cannot be erased because it has a '
                    'sample template' % cls(id_).title)

            args = [id_]

            sql = "DELETE FROM qiita.study_portal WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            sql = """DELETE FROM qiita.study_experimental_factor
                     WHERE study_id = %s"""
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.study_publication WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            sql = """DELETE FROM qiita.study_environmental_package
                     WHERE study_id = %s"""
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.study_users WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.investigation_study WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.study WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            qdb.sql_connection.TRN.execute()


# --- Attributes ---
    @property
    def title(self):
        """Returns the title of the study

        Returns
        -------
        str
            Title of study
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT study_title FROM qiita.{0}
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @title.setter
    def title(self, title):
        """Sets the title of the study

        Parameters
        ----------
        title : str
            The new study title
        """
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.{0} SET study_title = %s
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [title, self._id])
            return qdb.sql_connection.TRN.execute()

    @property
    def info(self):
        """Dict with all information attached to the study

        Returns
        -------
        dict
            info of study keyed to column names
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.{0} WHERE study_id = %s".format(
                self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            info = dict(qdb.sql_connection.TRN.execute_fetchindex()[0])
            # remove non-info items from info
            for item in self._non_info:
                info.pop(item)
            # removed because redundant to the id already stored in the object
            info.pop('study_id')

            if info['principal_investigator_id']:
                info['principal_investigator'] = qdb.study.StudyPerson(
                    info["principal_investigator_id"])
            else:
                info['principal_investigator'] = None
            del info['principal_investigator_id']

            if info['lab_person_id']:
                info['lab_person'] = qdb.study.StudyPerson(
                    info["lab_person_id"])
            else:
                info['lab_person'] = None
            del info['lab_person_id']

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
        if not info:
            raise IncompetentQiitaDeveloperError("Need entries in info dict!")

        if 'study_id' in info:
            raise qdb.exceptions.QiitaDBColumnError("Cannot set study_id!")

        if self._non_info.intersection(info):
            raise qdb.exceptions.QiitaDBColumnError(
                "non info keys passed: %s" % self._non_info.intersection(info))

        with qdb.sql_connection.TRN:
            if 'timeseries_type_id' in info:
                # We only lock if the timeseries type changes
                self._lock_non_sandbox()

            # make sure dictionary only has keys for available columns in db
            qdb.util.check_table_cols(info, self._table)

            sql_vals = []
            data = []
            # build query with data values in correct order for SQL statement
            for key, val in viewitems(info):
                sql_vals.append("{0} = %s".format(key))
                if isinstance(val, qdb.base.QiitaObject):
                    data.append(val.id)
                else:
                    data.append(val)
            data.append(self._id)

            sql = "UPDATE qiita.{0} SET {1} WHERE study_id = %s".format(
                self._table, ','.join(sql_vals))
            qdb.sql_connection.TRN.add(sql, data)
            qdb.sql_connection.TRN.execute()

    @property
    def efo(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT efo_id FROM qiita.{0}_experimental_factor
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchflatten()

    @efo.setter
    def efo(self, efo_vals):
        """Sets the efo for the study

        Parameters
        ----------
        efo_vals : list
            Id(s) for the new efo values

        Raises
        ------
        IncompetentQiitaDeveloperError
            Empty efo list passed
        """
        if not efo_vals:
            raise IncompetentQiitaDeveloperError("Need EFO information!")
        with qdb.sql_connection.TRN:
            self._lock_non_sandbox()
            # wipe out any EFOs currently attached to study
            sql = """DELETE FROM qiita.{0}_experimental_factor
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            # insert new EFO information into database
            sql = """INSERT INTO qiita.{0}_experimental_factor
                        (study_id, efo_id)
                     VALUES (%s, %s)""".format(self._table)
            qdb.sql_connection.TRN.add(
                sql, [[self._id, efo] for efo in efo_vals], many=True)
            qdb.sql_connection.TRN.execute()

    @property
    def shared_with(self):
        """list of users the study is shared with

        Returns
        -------
        list of qiita_db.user.User
            Users the study is shared with
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT email FROM qiita.{0}_users
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return [qdb.user.User(uid)
                    for uid in qdb.sql_connection.TRN.execute_fetchflatten()]

    @property
    def publications(self):
        """ Returns list of publications from this study

        Returns
        -------
        list of (str, str)
            list of all the DOI and pubmed ids
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT doi, pubmed_id
                     FROM qiita.publication p
                        JOIN qiita.study_publication sp
                            ON sp.publication_doi = p.doi
                     WHERE sp.study_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchindex()

    @publications.setter
    def publications(self, values):
        """Sets the pmids for the study

        Parameters
        ----------
        values : list of (str, str)
            The list of (DOI, pubmed id) to associate with the study

        Raises
        ------
        TypeError
            If values is not a list
        """
        # Check that a list is actually passed
        if not isinstance(values, list):
            raise TypeError('publications should be a list')

        with qdb.sql_connection.TRN:
            # Delete the previous pmids associated with the study
            sql = "DELETE FROM qiita.study_publication WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, [self._id])

            # Set the new ones
            sql = """INSERT INTO qiita.publication (doi, pubmed_id)
                     SELECT %s, %s
                     WHERE NOT EXISTS(
                        SELECT doi FROM qiita.publication WHERE doi = %s)"""
            sql_args = [(doi, pmid, doi) for doi, pmid in values]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)

            sql = """INSERT INTO qiita.study_publication
                            (study_id, publication_doi)
                     VALUES (%s, %s)"""
            sql_args = [[self._id, doi] for doi, _ in values]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

    def add_publications(self, publications):
        """Add publications to study

        Parameters
        ----------
        publications : list of (str, str)
            A list with the (DOI, pubmed id) to associate with the study
        """
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.publication (doi, pubmed_id)
                        VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, publications, many=True)

            sql = """INSERT INTO qiita.study_publication
                            (study_id, publication_doi)
                        VALUES (%s, %s)"""
            sql_args = [[self.id, doi] for doi, _ in publications]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

    @property
    def investigation(self):
        """ Returns Investigation this study is part of

        If the study doesn't have an investigation associated with it, it will
        return None

        Returns
        -------
        qiita_db.investigation.Investigation or None
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT investigation_id FROM qiita.investigation_study
                     WHERE study_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            inv = qdb.sql_connection.TRN.execute_fetchindex()
            # If this study belongs to an investigation it will be in
            # the first value of the first row [0][0]
            return qdb.investigation.Investigation(inv[0][0]) if inv else None

    @property
    def sample_template(self):
        """Returns sample_template information

        If the study doesn't have a sample template associated with it, it will
        return None

        Returns
        -------
        qiita_db.metadata_template.sample_template.SampleTemplate or None
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.study_sample
                                   WHERE study_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            exists = qdb.sql_connection.TRN.execute_fetchlast()
        return (qdb.metadata_template.sample_template.SampleTemplate(self._id)
                if exists else None)

    @property
    def data_types(self):
        """Returns list of the data types for this study

        Returns
        -------
        list of str
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT DISTINCT data_type
                     FROM qiita.study_prep_template
                        JOIN qiita.prep_template USING (prep_template_id)
                        JOIN qiita.data_type USING (data_type_id)
                     WHERE study_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchflatten()

    @property
    def owner(self):
        """Gets the owner of the study

        Returns
        -------
        qiita_db.user.User
            The user that owns this study
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT email FROM qiita.{} WHERE study_id = %s""".format(
                self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.user.User(qdb.sql_connection.TRN.execute_fetchlast())

    @property
    def environmental_packages(self):
        """Gets the environmental packages associated with the study

        Returns
        -------
        list of str
            The environmental package names associated with the study
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT environmental_package_name
                     FROM qiita.study_environmental_package
                     WHERE study_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchflatten()

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
        with qdb.sql_connection.TRN:
            # The environmental packages can be changed only if the study is
            # sandboxed
            self._lock_non_sandbox()

            # Check that a list is actually passed
            if not isinstance(values, list):
                raise TypeError('Environmental packages should be a list')

            # Get all the environmental packages
            env_pkgs = [pkg[0]
                        for pkg in qdb.util.get_environmental_packages()]

            # Check that all the passed values are valid environmental packages
            missing = set(values).difference(env_pkgs)
            if missing:
                raise ValueError('Environmetal package(s) not recognized: %s'
                                 % ', '.join(missing))

            # Delete the previous environmental packages associated with
            # the study
            sql = """DELETE FROM qiita.study_environmental_package
                     WHERE study_id=%s"""
            qdb.sql_connection.TRN.add(sql, [self._id])

            # Set the new ones
            sql = """INSERT INTO qiita.study_environmental_package
                        (study_id, environmental_package_name)
                     VALUES (%s, %s)"""
            sql_args = [[self._id, val] for val in values]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)

            qdb.sql_connection.TRN.execute()

    @property
    def _portals(self):
        """Portals this study is associated with

        Returns
        -------
        list of str
            Portal names study is associated with
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT portal
                     FROM qiita.portal_type
                        JOIN qiita.study_portal USING (portal_type_id)
                     WHERE study_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchflatten()

    @property
    def ebi_study_accession(self):
        """The EBI study accession for this study

        Returns
        -------
        str
            The study EBI accession
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT ebi_study_accession
                     FROM qiita.{0}
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @ebi_study_accession.setter
    def ebi_study_accession(self, value):
        """Sets the study's EBI study accession

        Parameters
        ----------
        value : str
            The new EBI study accession

        Raises
        ------
        QiitDBError
            If the study already has an EBI study accession
        """
        with qdb.sql_connection.TRN:
            if self.ebi_study_accession is not None:
                raise qdb.exceptions.QiitaDBError(
                    "Study %s already has an EBI study accession"
                    % self.id)
            sql = """UPDATE qiita.{}
                     SET ebi_study_accession = %s
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [value, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def ebi_submission_status(self):
        """The EBI submission status of this study

        Returns
        -------
        str
            The study EBI submission status
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT ebi_submission_status
                     FROM qiita.{0}
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @ebi_submission_status.setter
    def ebi_submission_status(self, value):
        """Sets the study's EBI submission status

        Parameters
        ----------
        value : str {%s}
            The new EBI submission status

        Raises
        ------
        ValueError
            If the status is not known
        """
        if not (value in _VALID_EBI_STATUS or
                value.startswith('failed')):
            raise ValueError("Unknown status: %s" % value)
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.{}
                     SET ebi_submission_status = %s
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [value, self.id])
            qdb.sql_connection.TRN.execute()

    ebi_submission_status.__doc__.format(', '.join(_VALID_EBI_STATUS))

    # --- methods ---
    def artifacts(self, dtype=None, artifact_type=None):
        """Returns the list of artifacts associated with the study

        Parameters
        ----------
        dtype : str, optional
            If given, retrieve only artifacts for given data type. Default,
            return all artifacts associated with the study.
        artifact_type : str, optional
            If given, retrieve only artifacts of given data type. Default,
            return all artifacts associated with the study

        Returns
        -------
        list of qiita_db.artifact.Artifact
        """
        with qdb.sql_connection.TRN:
            sql_args = [self._id]
            sql_where = ""
            if dtype:
                sql_args.append(dtype)
                sql_where = " AND data_type = %s"

            if artifact_type:
                sql_args.append(artifact_type)
                sql_where += "AND artifact_type = %s"

            sql = """SELECT artifact_id
                     FROM qiita.artifact
                        JOIN qiita.data_type USING (data_type_id)
                        JOIN qiita.study_artifact USING (artifact_id)
                        JOIN qiita.artifact_type USING (artifact_type_id)
                     WHERE study_id = %s{0}
                     ORDER BY artifact_id""".format(sql_where)

            qdb.sql_connection.TRN.add(sql, sql_args)
            return [qdb.artifact.Artifact(aid)
                    for aid in qdb.sql_connection.TRN.execute_fetchflatten()]

    def prep_templates(self, data_type=None):
        """Return list of prep template ids

        Parameters
        ----------
        data_type : str, optional
            If given, retrieve only prep templates for given datatype.
            Default None.

        Returns
        -------
        list of qiita_db.metadata_template.prep_template.PrepTemplate
        """
        with qdb.sql_connection.TRN:
            spec_data = ""
            args = [self._id]
            if data_type:
                spec_data = " AND data_type_id = %s"
                args.append(qdb.util.convert_to_id(data_type, "data_type"))

            sql = """SELECT prep_template_id
                     FROM qiita.study_prep_template
                        JOIN qiita.prep_template USING (prep_template_id)
                     WHERE study_id = %s{0}""".format(spec_data)
            qdb.sql_connection.TRN.add(sql, args)
            return [qdb.metadata_template.prep_template.PrepTemplate(ptid)
                    for ptid in qdb.sql_connection.TRN.execute_fetchflatten()]

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
        with qdb.sql_connection.TRN:
            # if admin or superuser, just return true
            if user.level in {'superuser', 'admin'}:
                return True

            if no_public:
                study_set = user.user_studies | user.shared_studies
            else:
                study_set = user.user_studies | user.shared_studies | \
                    self.get_by_status('public')

            return self in study_set

    def can_edit(self, user):
        """Returns whether the given user can edit the study

        Parameters
        ----------
        user : User object
            User we are checking edit permissions for

        Returns
        -------
        bool
            Whether user can edit the study or not
        """
        # The study is editable only if the user is the owner, is in the shared
        # list or the user is an admin
        return (user.level in {'superuser', 'admin'} or self.owner == user or
                user in self.shared_with)

    def share(self, user):
        """Share the study with another user

        Parameters
        ----------
        user: User object
            The user to share the study with
        """
        with qdb.sql_connection.TRN:
            # Make sure the study is not already shared with the given user
            if user in self.shared_with:
                return
            # Do not allow the study to be shared with the owner
            if user == self.owner:
                return

            sql = """INSERT INTO qiita.study_users (study_id, email)
                     VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, [self._id, user.id])
            qdb.sql_connection.TRN.execute()

    def unshare(self, user):
        """Unshare the study with another user

        Parameters
        ----------
        user: User object
            The user to unshare the study with
        """
        with qdb.sql_connection.TRN:
            sql = """DELETE FROM qiita.study_users
                     WHERE study_id = %s AND email = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id, user.id])
            qdb.sql_connection.TRN.execute()


class StudyPerson(qdb.base.QiitaObject):
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
        with qdb.sql_connection.TRN:
            sql = """SELECT study_person_id FROM qiita.{}
                     ORDER BY study_person_id""".format(cls._table)
            qdb.sql_connection.TRN.add(sql)

            for id_ in qdb.sql_connection.TRN.execute_fetchflatten():
                yield StudyPerson(id_)

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
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.{0}
                        WHERE name = %s
                            AND affiliation = %s)""".format(cls._table)
            qdb.sql_connection.TRN.add(sql, [name, affiliation])
            return qdb.sql_connection.TRN.execute_fetchlast()

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
        with qdb.sql_connection.TRN:
            if cls.exists(name, affiliation):
                sql = """SELECT study_person_id
                         FROM qiita.{0}
                         WHERE name = %s
                            AND affiliation = %s""".format(cls._table)
                args = [name, affiliation]
            else:
                sql = """INSERT INTO qiita.{0} (name, email, affiliation,
                                                address, phone)
                         VALUES (%s, %s, %s, %s, %s)
                         RETURNING study_person_id""".format(cls._table)
                args = [name, email, affiliation, address, phone]

            qdb.sql_connection.TRN.add(sql, args)
            return cls(qdb.sql_connection.TRN.execute_fetchlast())

    @classmethod
    def delete(cls, id_):
        r"""Deletes the StudyPerson from the database

        Parameters
        ----------
        id_ : integer
            The object identifier

        Raises
        ------
        QiitaDBError
            If the StudyPerson with the given id is attached to studies
        """
        with qdb.sql_connection.TRN:
            # checking that the id_ exists
            cls(id_)

            # Check if the person is attached to any study
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.study
                        WHERE lab_person_id = %s OR
                            principal_investigator_id = %s OR
                            emp_person_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [id_, id_, id_])
            if qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBError(
                    'StudyPerson "%s" cannot be deleted because there are '
                    'studies referencing it' % id_)

            sql = "DELETE FROM qiita.study_person WHERE study_person_id = %s"
            qdb.sql_connection.TRN.add(sql, [id_])
            qdb.sql_connection.TRN.execute()

    # Properties
    @property
    def name(self):
        """Returns the name of the person

        Returns
        -------
        str
            Name of person
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT name FROM qiita.{0}
                     WHERE study_person_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def email(self):
        """Returns the email of the person

        Returns
        -------
        str
            Email of person
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT email FROM qiita.{0}
                     WHERE study_person_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def affiliation(self):
        """Returns the affiliation of the person

        Returns
        -------
        str
            Affiliation of person
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT affiliation FROM qiita.{0}
                     WHERE study_person_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def address(self):
        """Returns the address of the person

        Returns
        -------
        str or None
            address or None if no address in database
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT address FROM qiita.{0}
                     WHERE study_person_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @address.setter
    def address(self, value):
        """Set/update the address of the person

        Parameters
        ----------
        value : str
            New address for person
        """
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.{0} SET address = %s
                     WHERE study_person_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [value, self._id])
            qdb.sql_connection.TRN.execute()

    @property
    def phone(self):
        """Returns the phone number of the person

        Returns
        -------
         str or None
            phone or None if no address in database
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT phone FROM qiita.{0}
                     WHERE study_person_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @phone.setter
    def phone(self, value):
        """Set/update the phone number of the person

        Parameters
        ----------
        value : str
            New phone number for person
        """
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.{0} SET phone = %s
                     WHERE study_person_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [value, self._id])
            qdb.sql_connection.TRN.execute()
