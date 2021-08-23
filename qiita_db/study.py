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
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from collections import defaultdict
from copy import deepcopy
from itertools import chain
import warnings

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb


class Study(qdb.base.QiitaObject):
    r"""Study object to access to the Qiita Study information

    Attributes
    ----------
    data_types
    info
    investigation
    name
    pmids
    shared_with
    sample_template
    status
    title
    owner
    specimen_id_column
    autoloaded

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
    _non_info = frozenset(["email", "study_title", "ebi_study_accession",
                           "autoloaded"])

    def _lock_non_sandbox(self):
        """Raises QiitaDBStatusError if study is non-sandboxed"""
        if self.status != 'sandbox':
            raise qdb.exceptions.QiitaDBStatusError(
                "Illegal operation on non-sandbox study!")

    @classmethod
    def iter(cls):
        """Iterate over all studies in the database

        Returns
        -------
        generator
            Yields a `Study` object for each study in the database,
            in order of ascending study_id
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT study_id FROM qiita.{}
                     ORDER BY study_id""".format(cls._table)
            qdb.sql_connection.TRN.add(sql)

            ids = qdb.sql_connection.TRN.execute_fetchflatten()

        for id_ in ids:
            yield Study(id_)

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
    def get_ids_by_status(cls, status):
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
            sids = set(qdb.sql_connection.TRN.execute_fetchflatten())
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
                sids = sids.union(
                    qdb.sql_connection.TRN.execute_fetchflatten())

            return sids

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
        return set(cls(sid) for sid in cls.get_ids_by_status(status))

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
            # placeholder for table study_publication
            ['publications']))

        if info_cols is None:
            info_cols = _info_cols
        elif not _info_cols.issuperset(info_cols):
            warnings.warn("Non-info columns passed: %s" % ", ".join(
                set(info_cols) - _info_cols))

        search_cols = ",".join(sorted(_info_cols.intersection(info_cols)))

        with qdb.sql_connection.TRN:
            sql = """SELECT {0}
                     FROM qiita.study
                     LEFT JOIN (
                            SELECT study_id,
                            array_agg(row_to_json((publication, is_doi), true))
                                AS publications
                            FROM qiita.study_publication
                            GROUP BY study_id)
                                AS full_publications
                        USING (study_id)
                     JOIN qiita.timeseries_type  USING (timeseries_type_id)
                     JOIN qiita.study_portal USING (study_id)
                     JOIN qiita.portal_type USING (portal_type_id)
                    WHERE portal = %s""".format(search_cols)
            args = [qiita_config.portal]
            if study_ids is not None:
                sql = "{0} AND study_id IN %s".format(sql)
                args.append(tuple(study_ids))

            qdb.sql_connection.TRN.add(sql, args)
            rows = qdb.sql_connection.TRN.execute_fetchindex()
            if study_ids is not None and len(rows) != len(study_ids):
                raise qdb.exceptions.QiitaDBError(
                    'Non-portal-accessible studies asked for!')

            res = []
            for r in rows:
                r = dict(r)
                if 'ebi_study_accession' in info_cols:
                    r['ebi_submission_status'] = cls(
                        r['study_id']).ebi_submission_status
                res.append(r)

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
    def create(cls, owner, title, info, investigation=None):
        """Creates a new study on the database

        Parameters
        ----------
        owner : User object
            the study's owner
        title : str
            Title of the study
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
        QiitaDBDuplicateError
            If a study with the given title already exists

        Notes
        -----
        All keys in info, must be equal to columns in qiita.study table in the
        database.
        """
        # make sure not passing non-info columns in the info dict
        if cls._non_info.intersection(info):
            raise qdb.exceptions.QiitaDBColumnError(
                "non info keys passed: %s" % cls._non_info.intersection(info))

        # cleaning up title, this is also done in JS for the GUI but rather
        # be safe than sorry
        title = ' '.join(title.split()).strip()

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
            insertdict = {k: v for k, v in insertdict.items()
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

            sql = "DELETE FROM qiita.study_publication WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            sql = """DELETE FROM qiita.study_environmental_package
                     WHERE study_id = %s"""
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.study_users WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.investigation_study WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.per_study_tags WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.study WHERE study_id = %s"
            qdb.sql_connection.TRN.add(sql, args)

            qdb.sql_connection.TRN.execute()

    @classmethod
    def get_tags(cls):
        """Returns the available study tags

        Returns
        -------
        list of DictCursor
            Table-like structure of metadata, one tag per row. Can be
            accessed as a list of dictionaries, keyed on column name.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT qiita.user_level.name AS user_level,
                        array_agg(study_tag ORDER BY study_tag)
                    FROM qiita.study_tags
                    LEFT JOIN qiita.qiita_user USING (email)
                    LEFT JOIN qiita.user_level USING (user_level_id)
                    GROUP BY qiita.user_level.name"""

            qdb.sql_connection.TRN.add(sql)
            results = dict(qdb.sql_connection.TRN.execute_fetchindex())
            # when the system is empty,
            # it's possible to get an empty dict, fixing
            if 'admin' not in results:
                results['admin'] = []
            if 'user' not in results:
                results['user'] = []

            return results

    @classmethod
    def insert_tags(cls, user, tags):
        """Insert available study tags

        Parameters
        ----------
        user : qiita_db.user.User
            The user adding the tags
        tags : list of str
            The list of tags to add
        """
        with qdb.sql_connection.TRN:
            email = user.email
            sql = """INSERT INTO qiita.study_tags (email, study_tag)
                     SELECT %s, %s WHERE NOT EXISTS (
                        SELECT 1 FROM qiita.study_tags WHERE study_tag = %s)"""
            sql_args = [[email, tag, tag] for tag in tags]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

# --- Attributes ---
    @property
    def autoloaded(self):
        """Returns if the study was autoloaded

        Returns
        -------
        bool
            If the study was autoloaded or not
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT autoloaded FROM qiita.{0}
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @autoloaded.setter
    def autoloaded(self, value):
        """Sets the autoloaded status of the study

        Parameters
        ----------
        value : bool
            Whether the study was autoloaded
        """
        sql = """UPDATE qiita.{0} SET autoloaded = %s
                 WHERE study_id = %s""".format(self._table)
        qdb.sql_connection.perform_as_transaction(sql, [value, self._id])

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
            The study title
        """
        sql = """UPDATE qiita.{0} SET study_title = %s
                 WHERE study_id = %s""".format(self._table)
        qdb.sql_connection.perform_as_transaction(sql, [title, self._id])

    @property
    def notes(self):
        """Returns the notes of the study

        Returns
        -------
        str
            Study notes
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT notes FROM qiita.{0}
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @notes.setter
    def notes(self, notes):
        """Sets the notes of the study

        Parameters
        ----------
        notes : str
            The study notes
        """
        sql = """UPDATE qiita.{0} SET notes = %s
                 WHERE study_id = %s""".format(self._table)
        qdb.sql_connection.perform_as_transaction(sql, [notes, self._id])

    @property
    def public_raw_download(self):
        """Returns if the study's raw data is available for download

        Returns
        -------
        str
            public_raw_download of study
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT public_raw_download FROM qiita.{0}
                     WHERE study_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @public_raw_download.setter
    def public_raw_download(self, public_raw_download):
        """Sets if the study's raw data is available for download

        Parameters
        ----------
        public_raw_download : bool
            The study public_raw_download
        """
        sql = """UPDATE qiita.{0} SET public_raw_download = %s
                 WHERE study_id = %s""".format(self._table)
        qdb.sql_connection.perform_as_transaction(
            sql, [public_raw_download, self._id])

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
            for key, val in info.items():
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
            sql = """SELECT publication, is_doi
                     FROM qiita.study_publication
                     WHERE study_id = %s"""
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
            sql = """INSERT INTO qiita.study_publication
                            (study_id, publication, is_doi)
                     VALUES (%s, %s, %s)"""
            sql_args = [[self._id, pub, is_doi] for pub, is_doi in values]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

    @property
    def specimen_id_column(self):
        """Returns the specimen identifier column

        Returns
        -------
        str
            The name of the specimen id column
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT specimen_id_column
                     FROM qiita.study
                     WHERE study_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @specimen_id_column.setter
    def specimen_id_column(self, value):
        """Sets the specimen identifier column

        Parameters
        ----------
        value : str
            The name of the column with the specimen identifiers.

        Raises
        ------
        QiitaDBLookupError
            If value is not in the sample information for this study.
            If the study does not have sample information.
        QiitaDBColumnError
            Category is not unique.
        """
        st = self.sample_template
        if st is None:
            raise qdb.exceptions.QiitaDBLookupError("Study does not have a "
                                                    "sample information.")

        if value is not None:
            if value not in st.categories:
                raise qdb.exceptions.QiitaDBLookupError("Category '%s' is not "
                                                        "present in the sample"
                                                        " information."
                                                        % value)

            observed_values = st.get_category(value)
            if len(observed_values) != len(set(observed_values.values())):
                raise qdb.exceptions.QiitaDBColumnError("The category does not"
                                                        " contain unique "
                                                        "values.")

        sql = """UPDATE qiita.study SET
                 specimen_id_column = %s
                 WHERE study_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [value, self._id])

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
        if self.ebi_study_accession is not None:
            raise qdb.exceptions.QiitaDBError(
                "Study %s already has an EBI study accession"
                % self.id)
        sql = """UPDATE qiita.{}
                 SET ebi_study_accession = %s
                 WHERE study_id = %s""".format(self._table)
        qdb.sql_connection.perform_as_transaction(sql, [value, self.id])

    def _ebi_submission_jobs(self):
        """Helper code to avoid duplication"""
        plugin = qdb.software.Software.from_name_and_version(
            'Qiita', 'alpha')
        cmd = plugin.get_command('submit_to_EBI')

        sql = """SELECT processing_job_id,
                    pj.command_parameters->>'artifact' as aid,
                    processing_job_status, can_be_submitted_to_ebi,
                    array_agg(ebi_run_accession)
                 FROM qiita.processing_job pj
                 LEFT JOIN qiita.processing_job_status
                    USING (processing_job_status_id)
                 LEFT JOIN qiita.artifact ON (
                    artifact_id = (
                        pj.command_parameters->>'artifact')::INT)
                 LEFT JOIN qiita.ebi_run_accession era USING (artifact_id)
                 LEFT JOIN qiita.artifact_type USING (artifact_type_id)
                 WHERE pj.command_parameters->>'artifact' IN (
                    SELECT artifact_id::text
                    FROM qiita.study_artifact WHERE study_id = {0})
                    AND pj.command_id = {1}
                 GROUP BY processing_job_id, aid, processing_job_status,
                    can_be_submitted_to_ebi""".format(self._id, cmd.id)
        qdb.sql_connection.TRN.add(sql)

        return qdb.sql_connection.TRN.execute_fetchindex()

    @property
    def ebi_submission_status(self):
        """The EBI submission status of this study

        Returns
        -------
        str
            The study EBI submission status

        Notes
        -----
        There are 4 possible states: 'not submitted', 'submitting',
        'submitted' & 'failed'. We are going to assume 'not submitted' if the
        study doesn't have an accession, 'submitted' if it has an accession,
        'submitting' if there are submit_to_EBI jobs running using the study
        artifacts, & 'failed' if there are artifacts with failed jobs without
        successful ones.
        """
        status = 'not submitted'
        with qdb.sql_connection.TRN:
            if self.ebi_study_accession:
                status = 'submitted'

            jobs = defaultdict(dict)
            for info in self._ebi_submission_jobs():
                jid, aid, js, cbste, era = info
                if not cbste or era != [None]:
                    continue
                jobs[js][aid] = jid

            if 'queued' in jobs or 'running' in jobs:
                status = 'submitting'
            elif 'error' in jobs:
                aids_error = []
                aids_other = []
                for s, aids in jobs.items():
                    for aid in aids.keys():
                        if s == 'error':
                            aids_error.append(aid)
                        else:
                            aids_other.append(aid)
                difference = set(aids_error) - set(aids_other)
                if difference:
                    status = ('Some artifact submissions failed: %s' %
                              ', '.join(map(str, list(difference))))

        return status

    @property
    def tags(self):
        """Returns the tags of the study

        Returns
        -------
        list of str
            The study tags
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT study_tag
                        FROM qiita.study_tags
                        LEFT JOIN qiita.per_study_tags USING (study_tag)
                        WHERE study_id = {0}
                        ORDER BY study_tag""".format(self._id)
            qdb.sql_connection.TRN.add(sql)
            return [t[0] for t in qdb.sql_connection.TRN.execute_fetchindex()]

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

    def analyses(self):
        """Get all analyses where samples from this study have been used

        Returns
        -------
        list of qiita_db.analysis.Analysis
        """
        with qdb.sql_connection.TRN:
            if self.sample_template is not None:
                sids = self.sample_template.keys()
                if sids:
                    sql = """SELECT DISTINCT analysis_id
                             FROM qiita.analysis_sample
                             WHERE sample_id IN %s
                             ORDER BY analysis_id"""
                    qdb.sql_connection.TRN.add(
                        sql, [tuple(self.sample_template.keys())])

                    return [qdb.analysis.Analysis(_id) for _id in
                            qdb.sql_connection.TRN.execute_fetchflatten()]
            return []

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
        # Make sure the study is not already shared with the given user
        if user in self.shared_with:
            return
        # Do not allow the study to be shared with the owner
        if user == self.owner:
            return

        sql = """INSERT INTO qiita.study_users (study_id, email)
                 VALUES (%s, %s)"""
        qdb.sql_connection.perform_as_transaction(sql, [self._id, user.id])

    def unshare(self, user):
        """Unshare the study with another user

        Parameters
        ----------
        user: User object
            The user to unshare the study with
        """
        sql = """DELETE FROM qiita.study_users
                 WHERE study_id = %s AND email = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [self._id, user.id])

    def update_tags(self, user, tags):
        """Sets the tags of the study

        Parameters
        ----------
        user: User object
            The user reqesting the study tags update
        tags : list of str
            The tags to update within the study

        Returns
        -------
        str
            Warnings during insertion
        """
        message = ''
        # converting to set just to facilitate operations
        system_tags_admin = set(self.get_tags()['admin'])
        user_level = user.level
        current_tags = set(self.tags)
        to_delete = current_tags - set(tags)
        to_add = set(tags) - current_tags

        if to_delete or to_add:
            with qdb.sql_connection.TRN:
                if to_delete:
                    if user_level != 'admin':
                        admin_tags = to_delete & system_tags_admin
                        if admin_tags:
                            message += 'You cannot remove: %s' % ', '.join(
                                admin_tags)
                        to_delete = to_delete - admin_tags

                    if to_delete:
                        sql = """DELETE FROM qiita.per_study_tags
                                     WHERE study_id = %s AND study_tag IN %s"""
                        qdb.sql_connection.TRN.add(
                            sql, [self._id, tuple(to_delete)])

                if to_add:
                    if user_level != 'admin':
                        admin_tags = to_add & system_tags_admin
                        if admin_tags:
                            message += ('Only admins can assign: '
                                        '%s' % ', '.join(admin_tags))
                        to_add = to_add - admin_tags

                    if to_add:
                        self.insert_tags(user, to_add)

                        sql = """INSERT INTO qiita.per_study_tags
                                    (study_tag, study_id)
                                 SELECT %s, %s
                                    WHERE
                                        NOT EXISTS (
                                            SELECT study_tag, study_id
                                            FROM qiita.per_study_tags
                                            WHERE study_tag = %s
                                                AND study_id = %s
                                        )"""
                        sql_args = [[t, self._id, t, self._id] for t in to_add]
                        qdb.sql_connection.TRN.add(sql, sql_args, many=True)

                qdb.sql_connection.TRN.execute()
        else:
            message = 'No changes in the tags.'

        return message


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
    def from_name_and_affiliation(cls, name, affiliation):
        """Gets a StudyPerson object based on the name and affiliation

        Parameters
        ----------
        name: str
            Name of the person
        affiliation : str
            institution with which the person is affiliated

        Returns
        -------
        StudyPerson
            The StudyPerson for the name and affiliation
        """
        with qdb.sql_connection.TRN:
            if not cls.exists(name, affiliation):
                raise qdb.exceptions.QiitaDBLookupError(
                        'Study person does not exist')

            sql = """SELECT study_person_id FROM qiita.{0}
                        WHERE name = %s
                     AND affiliation = %s""".format(cls._table)
            qdb.sql_connection.TRN.add(sql, [name, affiliation])
            return cls(qdb.sql_connection.TRN.execute_fetchlast())

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
            If the StudyPerson with the given id is attached to any study
        """
        with qdb.sql_connection.TRN:
            # checking that the id_ exists
            cls(id_)

            # Check if the person is attached to any study
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.study
                        WHERE lab_person_id = %s OR
                            principal_investigator_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [id_, id_])
            if qdb.sql_connection.TRN.execute_fetchlast():
                sql = """SELECT study_id
                         FROM qiita.study
                         WHERE {} = %s"""
                cols = ['lab_person_id', 'principal_investigator_id']
                rel = {}
                for c in cols:
                    qdb.sql_connection.TRN.add(sql.format(c), [id_])
                    rel[c] = qdb.sql_connection.TRN.execute_fetchindex()
                raise qdb.exceptions.QiitaDBError(
                    'StudyPerson "%s" cannot be deleted because there are '
                    'studies referencing it: %s' % (id_, str(rel)))

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
        sql = """UPDATE qiita.{0} SET address = %s
                 WHERE study_person_id = %s""".format(self._table)
        qdb.sql_connection.perform_as_transaction(sql, [value, self._id])

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
        sql = """UPDATE qiita.{0} SET phone = %s
                 WHERE study_person_id = %s""".format(self._table)
        qdb.sql_connection.perform_as_transaction(sql, [value, self._id])
