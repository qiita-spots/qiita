r"""
Metadata template objects (:mod: `qiita_db.metadata_template)
=============================================================

..currentmodule:: qiita_db.metadata_template

This module provides the MetadataTemplate base class and the subclasses
SampleTemplate and PrepTemplate.

Classes
-------

..autosummary::
    :toctree: generated/

    BaseSample
    Sample
    PrepSample
    MetadataTemplate
    SampleTemplate
    PrepTemplate

Methods
-------

..autosummary::
    :toctree: generated/
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
import warnings
from copy import deepcopy
from datetime import datetime
from itertools import chain
from json import dumps, loads
from string import ascii_letters, digits

import numpy as np
import pandas as pd
from iteration_utilities import duplicates

import qiita_db as qdb
from qiita_core.exceptions import IncompetentQiitaDeveloperError

# this is the name of the sample where we store all columns for a sample/prep
# information
QIITA_COLUMN_NAME = "qiita_sample_column_names"

INSDC_NULL_VALUES = {
    "not collected": "not collected",
    "not provided": "not provided",
    "restricted access": "restricted access",
    "not applicable": "not applicable",
    "unspecified": "not applicable",
    "not_collected": "not collected",
    "not_provided": "not provided",
    "restricted_access": "restricted access",
    "not_applicable": "not applicable",
    "missing: not collected": "not collected",
    "missing: not provided": "not provided",
    "missing: restricted access": "restricted access",
    "missing: not applicable": "not applicable",
}


def _helper_get_categories(table):
    """This is a helper function to avoid duplication of code"""
    with qdb.sql_connection.TRN:
        sql = """SELECT sample_values->>'columns'
                 FROM qiita.{0}
                 WHERE sample_id = '{1}'""".format(table, QIITA_COLUMN_NAME)
        qdb.sql_connection.TRN.add(sql)
        results = qdb.sql_connection.TRN.execute_fetchflatten()
        if results and results != [None]:
            results = sorted(loads(results[0]))
        else:
            results = []
        return results


class BaseSample(qdb.base.QiitaObject):
    r"""Sample object that accesses the db to get the information of a sample
    belonging to a PrepTemplate or a SampleTemplate.

    Parameters
    ----------
    sample_id : str
        The sample id
    md_template : MetadataTemplate
        The metadata template obj to which the sample belongs to

    Methods
    -------
    __eq__
    __len__
    __getitem__
    __setitem__
    __delitem__
    __iter__
    __contains__
    exists
    keys
    values
    items
    get

    See Also
    --------
    QiitaObject
    Sample
    PrepSample
    """

    # Used to find the right SQL tables - should be defined on the subclasses
    _table_prefix = None
    _id_column = None

    def _check_template_class(self, md_template):
        r"""Checks that md_template is of the correct type

        Parameters
        ----------
        md_template : MetadataTemplate
            The metadata template

        Raises
        ------
        IncompetentQiitaDeveloperError
            If its call directly from the Base class
            If `md_template` doesn't have the correct type
        """
        raise IncompetentQiitaDeveloperError()

    def __init__(self, sample_id, md_template):
        r"""Initializes the object

        Parameters
        ----------
        sample_id : str
            The sample id
        md_template : MetadataTemplate
            The metadata template in which the sample is present

        Raises
        ------
        QiitaDBUnknownIDError
            If `sample_id` does not correspond to any sample in md_template
        """
        # Check that we are not instantiating the base class
        self._check_subclass()
        # Check that the md_template is of the correct type
        self._check_template_class(md_template)
        # Check if the sample id is present on the passed metadata template
        # This test will check that the sample id is actually present on the db
        if sample_id not in md_template:
            raise qdb.exceptions.QiitaDBUnknownIDError(
                sample_id, self.__class__.__name__
            )
        # Assign private attributes
        self._id = sample_id
        self._md_template = md_template
        self._dynamic_table = "%s%d" % (self._table_prefix, self._md_template.id)

    def __hash__(self):
        r"""Defines the hash function so samples are hashable"""
        return hash(self._id)

    def __eq__(self, other):
        r"""Self and other are equal based on type and ids"""
        if not isinstance(other, type(self)):
            return False
        if other._id != self._id:
            return False
        if other._md_template != self._md_template:
            return False
        return True

    @classmethod
    def exists(cls, sample_id, md_template):
        r"""Checks if already exists a MetadataTemplate for the provided object

        Parameters
        ----------
        sample_id : str
            The sample id
        md_template : MetadataTemplate
            The metadata template to which the sample belongs to

        Returns
        -------
        bool
            True if already exists. False otherwise.
        """
        with qdb.sql_connection.TRN:
            cls._check_subclass()
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.{0}
                        WHERE sample_id=%s AND {1}=%s
                    )""".format(cls._table, cls._id_column)
            qdb.sql_connection.TRN.add(sql, [sample_id, md_template.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def _get_categories(self):
        r"""Returns all the available metadata categories for the sample

        Returns
        -------
        set of str
            The set of all available metadata categories
        """
        return set(_helper_get_categories(self._dynamic_table))

    def _to_dict(self):
        r"""Returns the categories and their values in a dictionary

        Returns
        -------
        dict of {str: str}
            A dictionary of the form {category: value}
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT sample_values
                     FROM qiita.{0}
                     WHERE sample_id=%s""".format(self._dynamic_table)
            qdb.sql_connection.TRN.add(sql, [self._id])

            result = qdb.sql_connection.TRN.execute_fetchindex()

            return result[0]["sample_values"]

    def __len__(self):
        r"""Returns the number of metadata categories

        Returns
        -------
        int
            The number of metadata categories
        """
        # return the number of columns
        return len(self._get_categories())

    def __getitem__(self, key):
        r"""Returns the value of the metadata category `key`

        Parameters
        ----------
        key : str
            The metadata category

        Returns
        -------
        obj
            The value of the metadata category `key`

        Raises
        ------
        KeyError
            If the metadata category `key` does not exists

        See Also
        --------
        get
        """
        with qdb.sql_connection.TRN:
            key = key.lower()
            if key not in self._get_categories():
                # The key is not available for the sample, so raise a KeyError
                raise KeyError(
                    "Metadata category %s does not exists for sample %s"
                    " in template %d" % (key, self._id, self._md_template.id)
                )

            sql = """SELECT sample_values->>'{0}' as {0}
                     FROM qiita.{1}
                     WHERE sample_id = %s""".format(key, self._dynamic_table)
            qdb.sql_connection.TRN.add(sql, [self._id])

            return qdb.sql_connection.TRN.execute_fetchlast()

    def setitem(self, column, value):
        """Sets `value` as value for the given `column`

        Parameters
        ----------
        column : str
            The column to update
        value : str
            The value to set. This is expected to be a str on the assumption
            that psycopg2 will cast as necessary when updating.

        Raises
        ------
        QiitaDBColumnError
            If the column does not exist in the table
        """
        # Check if the column exist in the table
        if column not in self._get_categories():
            raise qdb.exceptions.QiitaDBColumnError(
                "Column %s does not exist in %s" % (column, self._dynamic_table)
            )

        sql = """UPDATE qiita.{0}
                 SET sample_values = sample_values || %s
                 WHERE sample_id = %s""".format(self._dynamic_table)

        qdb.sql_connection.perform_as_transaction(
            sql, [dumps({column: value}), self.id]
        )

    def __setitem__(self, column, value):
        r"""Sets the metadata value for the category `column`

        Parameters
        ----------
        column : str
            The column to update
        value : str
            The value to set. This is expected to be a str on the assumption
            that psycopg2 will cast as necessary when updating.
        """
        with qdb.sql_connection.TRN:
            self.setitem(column, value)

            qdb.sql_connection.TRN.execute()

    def __delitem__(self, key):
        r"""Removes the sample with sample id `key` from the database

        Parameters
        ----------
        key : str
            The sample id
        """
        raise qdb.exceptions.QiitaDBNotImplementedError()

    def __iter__(self):
        r"""Iterator over the metadata keys

        Returns
        -------
        Iterator
            Iterator over the sample ids

        See Also
        --------
        keys
        """
        return iter(self._get_categories())

    def __contains__(self, key):
        r"""Checks if the metadata category `key` is present

        Parameters
        ----------
        key : str
            The sample id

        Returns
        -------
        bool
            True if the metadata category `key` is present, false otherwise
        """
        return key.lower() in self._get_categories()

    def keys(self):
        r"""Iterator over the metadata categories

        Returns
        -------
        Iterator
            Iterator over the sample ids

        See Also
        --------
        __iter__
        """
        return self.__iter__()

    def values(self):
        r"""Iterator over the metadata values, in metadata category order

        Returns
        -------
        Iterator
            Iterator over metadata values
        """
        d = self._to_dict()
        return d.values()

    def items(self):
        r"""Iterator over (category, value) tuples

        Returns
        -------
        Iterator
            Iterator over (category, value) tuples
        """
        d = self._to_dict()
        return d.items()

    def get(self, key):
        r"""Returns the metadata value for category `key`, or None if the
        category `key` is not present

        Parameters
        ----------
        key : str
            The metadata category

        Returns
        -------
        Obj or None
            The value object for the category `key`, or None if it is not
            present

        See Also
        --------
        __getitem__
        """
        try:
            return self[key]
        except KeyError:
            return None


class MetadataTemplate(qdb.base.QiitaObject):
    r"""Metadata map object that accesses the db to get the sample/prep
    template information

    Attributes
    ----------
    id

    Methods
    -------
    exists
    __len__
    __getitem__
    __setitem__
    __delitem__
    __iter__
    __contains__
    keys
    values
    items
    get
    to_file
    add_filepath
    update
    metadata_headers
    delete_column

    See Also
    --------
    QiitaObject
    SampleTemplate
    PrepTemplate
    """

    # Used to find the right SQL tables - should be defined on the subclasses
    _table_prefix = None
    _id_column = None
    _sample_cls = None
    # forbidden_words not defined for base class. Please redefine for
    # sub-classes.
    _forbidden_words = {}

    @classmethod
    def _check_id(cls, id_):
        r"""Checks that the MetadataTemplate id_ exists on the database"""
        return qdb.util.exists_table(f"{cls._table_prefix}{id_}")

    @classmethod
    def _table_name(cls, obj_id):
        r"""Returns the dynamic table name

        Parameters
        ----------
        obj_id : int
            The id of the metadata template

        Returns
        -------
        str
            The table name

        Raises
        ------
        IncompetentQiitaDeveloperError
            If called from the base class directly
        """
        if not cls._table_prefix:
            raise IncompetentQiitaDeveloperError(
                "_table_prefix should be defined in the subclasses"
            )
        return "%s%d" % (cls._table_prefix, obj_id)

    @classmethod
    def _clean_validate_template(cls, md_template, study_id, current_columns=None):
        """Takes care of all validation and cleaning of metadata templates

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        study_id : int
            The study to which the metadata template belongs to.
        current_columns : iterable of str, optional
            The current list of metadata columns

        Returns
        -------
        md_template : DataFrame
            Cleaned deep-copy of the input md_template:
                Removes 'qiita_study_id' and 'qiita_prep_id' columns,
                if present.

        Raises
        ------
        QiitaDBColumnError
            If the column names in md_template contains invalid characters,
            forbidden words, or PostgreSQL-reserved words.
        QiitaDBWarning
            If there are missing columns required for some functionality
        """
        cls._check_subclass()
        invalid_ids = qdb.metadata_template.util.get_invalid_sample_names(
            md_template.index
        )
        if invalid_ids:
            raise qdb.exceptions.QiitaDBColumnError(
                "The following sample names in the template contain invalid "
                "characters (only alphanumeric characters or periods are "
                "allowed): %s." % ", ".join(invalid_ids)
            )

        if len(set(md_template.index)) != len(md_template.index):
            raise qdb.exceptions.QiitaDBDuplicateSamplesError(
                set(duplicates(md_template.index))
            )

        # We are going to modify the md_template. We create a copy so
        # we don't modify the user one
        md_template = md_template.copy(deep=True)

        # In the database, all the column headers are lowercase
        md_template.columns = [c.lower() for c in md_template.columns]

        # drop these columns in the result
        if "qiita_study_id" in md_template.columns:
            del md_template["qiita_study_id"]
        if "qiita_prep_id" in md_template.columns:
            del md_template["qiita_prep_id"]

        # validating pgsql reserved words not to be column headers
        current_headers = set(md_template.columns.values)

        # testing for specific column names that are not included in the other
        # tests.

        pgsql_reserved = cls._identify_pgsql_reserved_words_in_column_names(
            current_headers
        )
        invalid = cls._identify_column_names_with_invalid_characters(current_headers)
        forbidden = cls._identify_forbidden_words_in_column_names(current_headers)
        qiime2_reserved = cls._identify_qiime2_reserved_words_in_column_names(
            current_headers
        )

        error = []
        if pgsql_reserved:
            error.append(
                "These column names are PgSQL reserved words, replace them: "
                "~~ %s ~~." % ", ".join(pgsql_reserved)
            )
        if invalid:
            error.append(
                "These column names contain invalid chars, remove or replace "
                "them: ~~ %s ~~." % ", ".join(invalid)
            )
        if forbidden:
            error.append(
                "These column names are not valid in this information file, "
                "remove them: ~~ %s ~~." % ", ".join(forbidden)
            )
        if qiime2_reserved:
            error.append(
                "These columns are QIIME2 reserved words, replace them: "
                " ~~ %s ~~." % ", ".join(pgsql_reserved)
            )

        if error:
            raise qdb.exceptions.QiitaDBColumnError(
                "%s\nYou need to modify them." % "\n".join(error)
            )

        # Prefix the sample names with the study_id
        qdb.metadata_template.util.prefix_sample_names_with_id(md_template, study_id)

        # Check that we don't have duplicate columns
        if len(set(md_template.columns)) != len(md_template.columns):
            raise qdb.exceptions.QiitaDBDuplicateHeaderError(
                set(duplicates(md_template.columns))
            )

        # validate the INSDC_NULL_VALUES
        _df = md_template.fillna("").applymap(str).applymap(str.lower)
        _ddf = _df[_df.isin(INSDC_NULL_VALUES.keys()).any(axis=1)]
        if _ddf.shape[0] != 0:
            for c in _ddf.columns:
                if set(INSDC_NULL_VALUES) & set(_ddf[c].values):
                    for s, v in _ddf[c].to_dict().items():
                        if v in INSDC_NULL_VALUES:
                            md_template[c][s] = INSDC_NULL_VALUES[v]

        return md_template

    @classmethod
    def _common_creation_steps(cls, md_template, obj_id):
        r"""Executes the common creation steps

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        obj_id : int
            The id of the object being created
        """
        with qdb.sql_connection.TRN:
            cls._check_subclass()

            # Get some useful information from the metadata template
            sample_ids = md_template.index.tolist()
            headers = sorted(md_template.keys().tolist())
            if not headers:
                raise ValueError("Your info file only has sample_name")

            # Insert values on template_sample table
            values = [[obj_id, s_id] for s_id in sample_ids]
            sql = """INSERT INTO qiita.{0} ({1}, sample_id)
                     VALUES (%s, %s)""".format(cls._table, cls._id_column)
            qdb.sql_connection.TRN.add(sql, values, many=True)

            # Create table with custom columns
            table_name = cls._table_name(obj_id)
            sql = """CREATE TABLE qiita.{0} (
                        sample_id VARCHAR NOT NULL PRIMARY KEY,
                        sample_values JSONB NOT NULL)""".format(table_name)
            qdb.sql_connection.TRN.add(sql)

            values = dumps({"columns": md_template.columns.tolist()})
            sql = """INSERT INTO qiita.{0} (sample_id, sample_values)
                     VALUES ('{1}', %s)""".format(table_name, QIITA_COLUMN_NAME)
            qdb.sql_connection.TRN.add(sql, [values])

            values = [(k, df.to_json()) for k, df in md_template.iterrows()]
            sql = """INSERT INTO qiita.{0} (sample_id, sample_values)
                     VALUES (%s, %s)""".format(table_name)
            qdb.sql_connection.TRN.add(sql, values, many=True)

            # Execute all the steps
            qdb.sql_connection.TRN.execute()

    @classmethod
    def metadata_headers(cls):
        """Returns metadata headers available

        Returns
        -------
        list
            Alphabetical list of all metadata headers available
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT DISTINCT table_name
                     FROM information_schema.columns
                     WHERE table_name LIKE '{0}%' AND
                        table_name != 'sample_template_filepath' AND
                        table_name != 'prep_template_filepath' AND
                        table_name != 'prep_template_sample' AND
                        table_name != 'prep_template_processing_job' AND
                        table_name != 'preparation_artifact' AND
                        table_name != 'prep_template'""".format(cls._table_prefix)
            qdb.sql_connection.TRN.add(sql)
            tables = qdb.sql_connection.TRN.execute_fetchflatten()
            sql = """SELECT sample_values->>'columns'
                     FROM qiita.%s WHERE sample_id = '{0}'""".format(QIITA_COLUMN_NAME)
            results = []
            for t in tables:
                qdb.sql_connection.TRN.add(sql % t)
                vals = qdb.sql_connection.TRN.execute_fetchflatten()
                if vals:
                    results.extend(loads(vals[0]))

            return list(set(results))

    def _common_delete_sample_steps(self, sample_names):
        r"""Executes the common delete sample steps

        Parameters
        ----------
        sample_names : list of str
            The sample names to be erased

        Raises
        ------
        QiitaDBUnknownIDError
            If any of the `sample_names` don't exist
        """
        keys = list(self.keys())
        missing = [sn for sn in sample_names if sn not in keys]
        if missing:
            raise qdb.exceptions.QiitaDBUnknownIDError(", ".join(missing), self._id)

        with qdb.sql_connection.TRN:
            # to simplify the sql strings, we are creating a base_sql, which
            # will be used to create sql1 and sql2. sql1 will delete the
            # sample_names from the main table ([sample | prep]_[id]), then
            # sql2 will delete the sample_names from [study | prep]_sample
            base_sql = "DELETE FROM qiita.{0} WHERE sample_id=%s"
            sql1 = base_sql.format(self._table_name(self._id))
            sql2 = "{0} AND {1}=%s".format(
                base_sql.format(self._table), self._id_column
            )
            for sn in sample_names:
                qdb.sql_connection.TRN.add(sql1, [sn])
                qdb.sql_connection.TRN.add(sql2, [sn, self.id])
            qdb.sql_connection.TRN.execute()

            # making sure we don't delete all the samples
            qdb.sql_connection.TRN.add(
                "SELECT COUNT(*) FROM qiita.{0}".format(self._table_name(self._id))
            )

            # 1 as the JSON formated tables have an extra "sample" where we
            # store the column information
            if qdb.sql_connection.TRN.execute_fetchlast() <= 1:
                raise ValueError(
                    "You cannot delete all samples from an information file"
                )

            self.generate_files(samples=sample_names)

    def delete_column(self, column_name):
        """Delete `column_name` from info file

        Parameters
        ----------
        column : str
            The column name to be deleted

        Raises
        ------
        QiitaDBColumnError
            If the `column_name` doesn't exist
        QiitaDBOperationNotPermittedError
            If a the info file can't be updated
        """
        if column_name not in self.categories:
            raise qdb.exceptions.QiitaDBColumnError(
                "'%s' not in info file %d" % (column_name, self._id)
            )
        if not self.can_be_updated(columns={column_name}):
            raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                "%s cannot be deleted" % column_name
            )

        with qdb.sql_connection.TRN:
            table_name = "qiita.{0}{1}".format(self._table_prefix, self._id)
            # deleting from all samples; note that (-) in pgsql jsonb means
            # delete that key and value
            sql = """UPDATE {0}
                     SET sample_values = sample_values - %s
                     WHERE sample_id != %s""".format(table_name)
            qdb.sql_connection.TRN.add(sql, [column_name, QIITA_COLUMN_NAME])

            # deleting from QIITA_COLUMN_NAME
            columns = self.categories
            columns.remove(column_name)
            values = '{"columns": %s}' % dumps(columns)
            sql = """UPDATE {0}
                     SET sample_values = %s
                     WHERE sample_id = '{1}'""".format(table_name, QIITA_COLUMN_NAME)
            qdb.sql_connection.TRN.add(sql, [values])

            qdb.sql_connection.TRN.execute()

            self.generate_files()

    def can_be_extended(self, new_samples, new_cols):
        """Whether the template can be updated or not

        Parameters
        ----------
        new_samples : list of str
            The new samples to be added
        new_cols : list of str
            The new columns to be added

        Returns
        -------
        bool
            Whether the template can be extended or not
        str
            The error message in case that it can't be extended

        Raises
        ------
        QiitaDBNotImplementedError
            This method should be implemented in the subclasses
        """
        raise qdb.exceptions.QiitaDBNotImplementedError(
            "The method 'can_be_extended' should be implemented in the subclasses"
        )

    def can_be_updated(self, **kwargs):
        """Whether the template can be updated or not

        Returns
        -------
        bool
            Whether the template can be updated or not

        Raises
        ------
        QiitaDBNotImplementedError
            This method should be implemented in the subclasses
        """
        raise qdb.exceptions.QiitaDBNotImplementedError(
            "The method 'can_be_updated' should be implemented in the subclasses"
        )

    def _common_extend_steps(self, md_template):
        r"""executes the common extend steps

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids

        Returns
        -------
        list of str
            The new samples being added
        list of str
            The new columns being added
        """
        with qdb.sql_connection.TRN:
            # Check if we are adding new samples
            sample_ids = md_template.index.tolist()
            curr_samples = set(self.keys())
            existing_samples = curr_samples.intersection(sample_ids)
            new_samples = set(sample_ids).difference(existing_samples)

            # check that we are within the limit of number of samples
            ms = self.max_samples()
            nsamples = len(curr_samples) + len(new_samples)
            if ms is not None and nsamples > ms:
                raise ValueError(
                    f"{nsamples} exceeds the max allowed number of samples: {ms}"
                )

            # Check if we are adding new columns
            headers = md_template.keys().tolist()
            new_cols = set(headers).difference(self.categories)

            if not new_cols and not new_samples:
                return None, None

            is_extendable, error_msg = self.can_be_extended(new_samples, new_cols)

            if not is_extendable:
                raise qdb.exceptions.QiitaDBError(error_msg)

            table_name = self._table_name(self._id)
            if new_cols:
                warnings.warn(
                    "The following columns have been added to the existing"
                    " template: %s" % ", ".join(sorted(new_cols)),
                    qdb.exceptions.QiitaDBWarning,
                )
                # If we are adding new columns, add them first (simplifies
                # code). Sorting the new columns to enforce an order
                new_cols = sorted(new_cols)

                cols = self.categories
                cols.extend(new_cols)

                values = dumps({"columns": cols})
                sql = """UPDATE qiita.{0}
                         SET sample_values = %s
                         WHERE sample_id = '{1}'""".format(
                    table_name, QIITA_COLUMN_NAME
                )
                qdb.sql_connection.TRN.add(sql, [values])

                if existing_samples:
                    # The values for the new columns are the only ones that get
                    # added to the database. None of the existing values will
                    # be modified (see update for that functionality). Remember
                    # that || is a jsonb to update or add a new key/value
                    existing_samples = list(existing_samples)
                    md_filtered = md_template[new_cols].loc[existing_samples]
                    for sid, df in md_filtered.iterrows():
                        values = dict(df.items())
                        sql = """UPDATE qiita.{0}
                                 SET sample_values = sample_values || %s
                                 WHERE sample_id = %s""".format(
                            self._table_name(self._id)
                        )
                        qdb.sql_connection.TRN.add(sql, [dumps(values), sid])

            if new_samples:
                warnings.warn(
                    "The following samples have been added to the existing"
                    " template: %s" % ", ".join(new_samples),
                    qdb.exceptions.QiitaDBWarning,
                )

                new_samples = sorted(new_samples)

                # At this point we only want the information
                # from the new samples
                md_filtered = md_template.loc[new_samples]

                # Insert new samples to the study sample table
                values = [[self._id, s_id] for s_id in new_samples]
                sql = """INSERT INTO qiita.{0} ({1}, sample_id)
                         VALUES (%s, %s)""".format(self._table, self._id_column)
                qdb.sql_connection.TRN.add(sql, values, many=True)

                # inserting new samples to the info file
                values = [(k, row.to_json()) for k, row in md_filtered.iterrows()]
                sql = """INSERT INTO qiita.{0} (sample_id, sample_values)
                         VALUES (%s, %s)""".format(table_name)
                qdb.sql_connection.TRN.add(sql, values, many=True)

            # Execute all the steps
            qdb.sql_connection.TRN.execute()

        return new_samples, new_cols

    def unique_ids(self):
        r"""Return a stable mapping of sample_name to integers

        Obtain a map from a sample_name to an integer. The association is
        unique Qiita-wide and 1-1.

        This method is idempotent.

        Returns
        ------
        dict
            {sample_name: integer_index}
        """
        raise IncompetentQiitaDeveloperError()

    @classmethod
    def exists(cls, obj_id):
        r"""Checks if already exists a MetadataTemplate for the provided object

        Parameters
        ----------
        obj_id : int
            The id to test if it exists on the database

        Returns
        -------
        bool
            True if already exists. False otherwise.
        """
        cls._check_subclass()
        return qdb.util.exists_table(cls._table_name(obj_id))

    def _get_sample_ids(self):
        r"""Returns all the available samples for the metadata template

        Returns
        -------
        set of str
            The set of all available sample ids
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT sample_id FROM qiita.{0} WHERE {1}=%s".format(
                self._table, self._id_column
            )
            qdb.sql_connection.TRN.add(sql, [self._id])
            return set(qdb.sql_connection.TRN.execute_fetchflatten())

    def __len__(self):
        r"""Returns the number of samples in the metadata template

        Returns
        -------
        int
            The number of samples in the metadata template
        """
        return len(self._get_sample_ids())

    def __getitem__(self, key):
        r"""Returns the metadata values for sample id `key`

        Parameters
        ----------
        key : str
            The sample id

        Returns
        -------
        Sample
            The sample object for the sample id `key`

        Raises
        ------
        KeyError
            If the sample id `key` is not present in the metadata template

        See Also
        --------
        get
        """
        with qdb.sql_connection.TRN:
            if key in self:
                return self._sample_cls(key, self)
            else:
                raise KeyError(
                    "Sample id %s does not exists in template %d" % (key, self._id)
                )

    def __setitem__(self, key, value):
        r"""Sets the metadata values for sample id `key`

        Parameters
        ----------
        key : str
            The sample id
        value : Sample
            The sample obj holding the new sample values
        """
        raise qdb.exceptions.QiitaDBNotImplementedError()

    def __delitem__(self, key):
        r"""Removes the sample with sample id `key` from the database

        Parameters
        ----------
        key : str
            The sample id
        """
        raise qdb.exceptions.QiitaDBNotImplementedError()

    def __iter__(self):
        r"""Iterator over the sample ids

        Returns
        -------
        Iterator
            Iterator over the sample ids

        See Also
        --------
        keys
        """
        return iter(self._get_sample_ids())

    def __contains__(self, key):
        r"""Checks if the sample id `key` is present in the metadata template

        Parameters
        ----------
        key : str
            The sample id

        Returns
        -------
        bool
            True if the sample id `key` is in the metadata template, false
            otherwise
        """
        return key in self._get_sample_ids()

    def keys(self):
        r"""Iterator over the sorted sample ids

        Returns
        -------
        Iterator
            Iterator over the sample ids

        See Also
        --------
        __iter__
        """
        return self.__iter__()

    def values(self):
        r"""Iterator over the metadata values

        Returns
        -------
        Iterator
            Iterator over Sample obj
        """
        with qdb.sql_connection.TRN:
            return iter(
                self._sample_cls(sample_id, self)
                for sample_id in self._get_sample_ids()
            )

    def items(self):
        r"""Iterator over (sample_id, values) tuples, in sample id order

        Returns
        -------
        Iterator
            Iterator over (sample_ids, values) tuples
        """
        with qdb.sql_connection.TRN:
            return iter(
                (sample_id, self._sample_cls(sample_id, self))
                for sample_id in self._get_sample_ids()
            )

    def get(self, key):
        r"""Returns the metadata values for sample id `key`, or None if the
        sample id `key` is not present in the metadata map

        Parameters
        ----------
        key : str
            The sample id

        Returns
        -------
        Sample or None
            The sample object for the sample id `key`, or None if it is not
            present

        See Also
        --------
        __getitem__
        """
        try:
            return self[key]
        except KeyError:
            return None

    def _transform_to_dict(self, values):
        r"""Transforms `values` to a dict keyed by sample id

        Parameters
        ----------
        values : object
            The object returned from a execute_fetchall call

        Returns
        -------
        dict
        """
        result = {}
        for row in values:
            # Transform the row to a dictionary
            values_dict = dict(row)
            # Get the sample id of this row
            sid = values_dict["sample_id"]
            del values_dict["sample_id"]
            # Remove _id_column from this row (if present)
            if self._id_column in values_dict:
                del values_dict[self._id_column]
            result[sid] = values_dict

        return result

    def generate_files(self):
        r"""Generates all the files that contain data from this template

        Raises
        ------
        QiitaDBNotImplementedError
            This method should be implemented by the subclasses
        """
        raise qdb.exceptions.QiitaDBNotImplementedError(
            "generate_files should be implemented in the subclass!"
        )

    def to_file(self, fp, samples=None):
        r"""Writes the MetadataTemplate to the file `fp` in tab-delimited
        format

        Parameters
        ----------
        fp : str
            Path to the output file
        samples : set, optional
            If supplied, only the specified samples will be written to the
            file
        """
        with qdb.sql_connection.TRN:
            df = self.to_dataframe()
            if samples is not None:
                df = df.loc[list(samples)]

            # Sorting the dataframe so multiple serializations of the metadata
            # template are consistent.
            df.sort_index(axis=0, inplace=True)
            df.sort_index(axis=1, inplace=True)

            # Store the template in a file
            df.to_csv(
                fp, index_label="sample_name", na_rep="", sep="\t", encoding="utf-8"
            )

    def _common_to_dataframe_steps(self, samples=None):
        """Perform the common to_dataframe steps

        Returns
        -------
        pandas DataFrame
            The metadata in the template,indexed on sample id
        samples list of string, optional
            A list of the sample names we actually want to retrieve
        """
        with qdb.sql_connection.TRN:
            # Retrieve all the information from the database
            sql = """SELECT sample_id, sample_values
                     FROM qiita.{0}
                     WHERE sample_id != '{1}'""".format(
                self._table_name(self._id), QIITA_COLUMN_NAME
            )
            if samples is None:
                qdb.sql_connection.TRN.add(sql)
            else:
                sql += " AND sample_id IN %s"
                qdb.sql_connection.TRN.add(sql, [tuple(samples)])

            data = qdb.sql_connection.TRN.execute_fetchindex()
            df = pd.DataFrame(
                [d for _, d in data], index=[i for i, _ in data], dtype=str
            )
            df.index.name = "sample_name"
            df.where((pd.notnull(df)), None)
            id_column_name = "qiita_%sid" % (self._table_prefix)
            if id_column_name == "qiita_sample_id":
                id_column_name = "qiita_study_id"
            df[id_column_name] = str(self.id)

            return df

    def add_filepath(self, filepath, fp_id=None):
        r"""Populates the DB tables for storing the filepath and connects the
        `self` objects with this filepath"""
        with qdb.sql_connection.TRN:
            fp_id = self._fp_id if fp_id is None else fp_id

            try:
                fpp_id = qdb.util.insert_filepaths(
                    [(filepath, fp_id)], None, "templates", move_files=False
                )[0]
                sql = """INSERT INTO qiita.{0} ({1}, filepath_id)
                         VALUES (%s, %s)""".format(
                    self._filepath_table, self._id_column
                )
                qdb.sql_connection.TRN.add(sql, [self._id, fpp_id])
                qdb.sql_connection.TRN.execute()
            except Exception as e:
                qdb.logger.LogEntry.create(
                    "Runtime", str(e), info={self.__class__.__name__: self.id}
                )
                raise e

    def get_filepaths(self):
        r"""Retrieves the list of (filepath_id, filepath)"""
        with qdb.sql_connection.TRN:
            return [
                (x["fp_id"], x["fp"])
                for x in qdb.util.retrieve_filepaths(
                    self._filepath_table, self._id_column, self.id, sort="descending"
                )
            ]

    @property
    def categories(self):
        """Identifies the metadata columns present in an info file

        Returns
        -------
        cols : list
            The category fields
        """
        return _helper_get_categories(self._table_name(self._id))

    def extend(self, md_template):
        """Adds the given template to the current one

        Parameters
        ----------
        md_template : DataFrame
            The metadata template contents indexed by sample ids
        """
        with qdb.sql_connection.TRN:
            md_template = self._clean_validate_template(
                md_template, self.study_id, current_columns=self.categories
            )
            new_samples, new_columns = self._common_extend_steps(md_template)
            if new_samples or new_columns:
                self.validate(self.columns_restrictions)
                self.generate_files(new_samples, new_columns)

    def _update(self, md_template):
        r"""Update values in the template

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples ids

        Returns
        -------
        set of str
            The samples that were updated
        set of str
            The columns that were updated

        Raises
        ------
        QiitaDBError
            If md_template and db do not have the same sample ids
            If md_template and db do not have the same column headers
            If self.can_be_updated is not True
        QiitaDBWarning
            If there are no differences between the contents of the DB and the
            passed md_template
        """
        with qdb.sql_connection.TRN:
            # Retrieving current metadata
            current_map = self.to_dataframe()

            # simple validations of sample ids and column names
            samples_diff = set(md_template.index).difference(current_map.index)
            if samples_diff:
                raise qdb.exceptions.QiitaDBError(
                    "The new template differs from what is stored "
                    "in database by these samples names: %s" % ", ".join(samples_diff)
                )

            if not set(current_map.columns).issuperset(md_template.columns):
                columns_diff = set(md_template.columns).difference(current_map.columns)
                raise qdb.exceptions.QiitaDBError(
                    "Some of the columns in your template are not present in "
                    'the system. Use "extend" if you want to add more columns '
                    "to the template. Missing columns: %s" % ", ".join(columns_diff)
                )

            # In order to speed up some computation, let's compare only the
            # common columns and rows. current_map.columns and
            # current_map.index are supersets of md_template.columns and
            # md_template.index, respectivelly, so this will not fail
            current_map = current_map[md_template.columns].loc[md_template.index]

            # Get the values that we need to change
            # diff_map is a DataFrame that hold boolean values. If a cell is
            # True, means that the md_template is different from the
            # current_map while False means that the cell has the same value
            diff_map = current_map != md_template
            # ne_stacked holds a MultiIndexed DataFrame in which the first
            # level of indexing is the sample_name and the second one is the
            # columns. We only have 1 column, which holds if that
            # (sample, column) pair has been modified or not (i.e. cell)
            ne_stacked = diff_map.stack()
            # by using ne_stacked to index itself, we get only the columns
            # that did change (see boolean indexing in pandas docs)
            changed = ne_stacked[ne_stacked]
            if changed.empty:
                warnings.warn(
                    "There are no differences between the data stored in the "
                    "DB and the new data provided",
                    qdb.exceptions.QiitaDBWarning,
                )
                return None, None

            changed.index.names = ["sample_name", "column"]
            # the combination of np.where and boolean indexing produces
            # a numpy array with only the values that actually changed
            # between the current_map and md_template
            changed_to = md_template.values[np.where(diff_map)]
            # now we are going to take that map and create a new DataFrame
            # which is going to have a double level index (sample_id /
            # column_name) with a single column 'to'; this will looks something
            # like:
            #                                               to
            # sample_name column
            # XX.Sample1  sample_type                            6
            # XX.Sample2  sample_type                            5
            #             host_subject_id             the only one
            # XX.Sample3  sample_type                           10
            #             physical_specimen_location  new location
            to_update = pd.DataFrame({"to": changed_to}, index=changed.index)
            # reset_index will expand the multi-index and convert the example
            # to:
            #    sample_name            column                 to
            # 0  XX.Sample1                 sample_type             6
            # 1  XX.Sample2                 sample_type             5
            # 2  XX.Sample2             host_subject_id  the only one
            # 3  XX.Sample3                 sample_type            10
            # 4  XX.Sample3  physical_specimen_location  new location
            to_update.reset_index(inplace=True)
            new_columns = []
            samples_updated = []
            for sid, df in to_update.groupby("sample_name"):
                samples_updated.append(sid)
                # getting just columns: column and to, and then using column
                # as index will generate this for XX.Sample2:
                #                        to
                # column
                # sample_type                 5
                # host_subject_id  the only one
                df = df[["column", "to"]].set_index("column")
                # finally to_dict in XX.Sample2:
                # {'to': {'host_subject_id': 'the only one',
                #         'sample_type': '5'}}
                values = df.to_dict()["to"]
                new_columns.extend(values.keys())
                sql = """UPDATE qiita.{0}
                         SET sample_values = sample_values || %s
                         WHERE sample_id = %s""".format(self._table_name(self._id))
                qdb.sql_connection.TRN.add(sql, [dumps(values), sid])

            nc = list(set(new_columns).union(set(self.categories)))
            table_name = self._table_name(self.id)
            values = dumps({"columns": nc})
            sql = """UPDATE qiita.{0}
                     SET sample_values = %s
                     WHERE sample_id = '{1}'""".format(table_name, QIITA_COLUMN_NAME)
            qdb.sql_connection.TRN.add(sql, [values])

            qdb.sql_connection.TRN.execute()

        return set(samples_updated), set(new_columns)

    def update(self, md_template):
        r"""Update values in the template

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples ids

        Raises
        ------
        QiitaDBError
            If md_template and db do not have the same sample ids
            If md_template and db do not have the same column headers
            If self.can_be_updated is not True
        QiitaDBWarning
            If there are no differences between the contents of the DB and the
            passed md_template
        """
        with qdb.sql_connection.TRN:
            # Clean and validate the metadata template given
            new_map = self._clean_validate_template(
                md_template, self.study_id, current_columns=self.categories
            )
            samples, columns = self._update(new_map)
            self.validate(self.columns_restrictions)
            self.generate_files(samples, columns)

    def extend_and_update(self, md_template):
        """Performs the update and extend operations at once

        Parameters
        ----------
        md_template : DataFrame
            The metadata template contents indexed by sample ids

        See Also
        --------
        update
        extend
        """
        with qdb.sql_connection.TRN:
            md_template = self._clean_validate_template(
                md_template, self.study_id, current_columns=self.categories
            )
            new_samples, new_columns = self._common_extend_steps(md_template)
            samples, columns = self._update(md_template)
            if samples is None:
                samples = new_samples
            elif new_samples is not None:
                samples.update(new_samples)
            if columns is None:
                columns = new_columns
            elif new_columns is not None:
                columns.update(new_columns)

            self.validate(self.columns_restrictions)
            self.generate_files(samples, columns)

    def update_category(self, category, samples_and_values):
        """Update an existing column

        Parameters
        ----------
        category : str
            The category to update
        samples_and_values : dict
            A mapping of {sample_id: value}

        Raises
        ------
        QiitaDBUnknownIDError
            If a sample_id is included in values that is not in the template
        QiitaDBColumnError
            If the column does not exist in the table. This is implicit, and
            can be thrown by the contained Samples.
        """
        with qdb.sql_connection.TRN:
            if not set(self.keys()).issuperset(samples_and_values):
                missing = set(self.keys()) - set(samples_and_values)
                table_name = self._table_name(self._id)
                raise qdb.exceptions.QiitaDBUnknownIDError(missing, table_name)

            for k, v in samples_and_values.items():
                sample = self[k]
                if isinstance(v, np.generic):
                    v = np.asscalar(v)
                sample.setitem(category, v)

            qdb.sql_connection.TRN.execute()

    def get_category(self, category):
        """Returns the values of all samples for the given category

        Parameters
        ----------
        category : str
            Metadata category to get information for

        Returns
        -------
        dict
            Sample metadata for the category in the form {sample_id: value}

        Raises
        ------
        QiitaDBColumnError
            If category is not part of the template
        """
        with qdb.sql_connection.TRN:
            if category not in self.categories:
                raise qdb.exceptions.QiitaDBColumnError(category)
            sql = """SELECT sample_id,
                        COALESCE(sample_values->>'{0}', 'None') AS {0}
                     FROM qiita.{1}
                     WHERE sample_id != '{2}'""".format(
                category, self._table_name(self._id), QIITA_COLUMN_NAME
            )
            qdb.sql_connection.TRN.add(sql)
            return dict(qdb.sql_connection.TRN.execute_fetchindex())

    def check_restrictions(self, restrictions):
        """Checks if the template fulfills the restrictions

        Parameters
        ----------
        restrictions : list of Restriction
            The restrictions to test if the template fulfills

        Returns
        -------
        set of str
            The missing columns
        """
        cols = {col for restriction in restrictions for col in restriction.columns}

        return cols.difference(self.categories)

    def _get_accession_numbers(self, column):
        """Return the accession numbers stored in `column`

        Parameters
        ----------
        column : str
            The column name where the accession number is stored

        Returns
        -------
        dict of {str: str}
            The accession numbers keyed by sample id
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT sample_id, {0}
                     FROM qiita.{1}
                     WHERE {2}=%s""".format(column, self._table, self._id_column)
            qdb.sql_connection.TRN.add(sql, [self.id])
            dbresult = qdb.sql_connection.TRN.execute_fetchindex()
            result = {sample_id: accession for sample_id, accession in dbresult}
        return result

    def _update_accession_numbers(self, column, values):
        """Update accession numbers stored in `column` with `values`

        Parameters
        ----------
        column : str
            The column name where the accession number are stored
        values : dict of {str: str}
            The accession numbers keyed by sample id

        Raises
        ------
        QiitaDBError
            If a sample in `values` already has an accession number
        QiitaDBWarning
            If `values` is not updating any accesion number
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT sample_id, {0}
                     FROM qiita.{1}
                     WHERE {2}=%s
                        AND {0} IS NOT NULL""".format(
                column, self._table, self._id_column
            )
            qdb.sql_connection.TRN.add(sql, [self.id])
            dbresult = qdb.sql_connection.TRN.execute_fetchindex()
            db_vals = {sample_id: accession for sample_id, accession in dbresult}
            common_samples = set(db_vals) & set(values)
            diff = [
                sample for sample in common_samples if db_vals[sample] != values[sample]
            ]
            if diff:
                raise qdb.exceptions.QiitaDBError(
                    "The following samples already have an accession number: "
                    "%s" % ", ".join(diff)
                )

            # Remove the common samples form the values dictionary
            values = deepcopy(values)
            for sample in common_samples:
                del values[sample]

            if values:
                sql_vals = ", ".join(["(%s, %s)"] * len(values))
                sql = """UPDATE qiita.{0} AS t
                         SET {1}=c.{1}
                         FROM (VALUES {2}) AS c(sample_id, {1})
                         WHERE c.sample_id = t.sample_id
                            AND t.{3} = %s
                         """.format(self._table, column, sql_vals, self._id_column)
                sql_vals = list(chain.from_iterable(values.items()))
                sql_vals.append(self.id)
                qdb.sql_connection.TRN.add(sql, sql_vals)
                qdb.sql_connection.TRN.execute()
            else:
                warnings.warn(
                    "No new accession numbers to update", qdb.exceptions.QiitaDBWarning
                )

    def validate(self, restriction_dict):
        """Validate the values in the restricted fields in info files

        Parameters
        ----------
        restriction_dict : dict of {str: Restriction}
            A dictionary with the restrictions that apply to the metadata

        Raises
        ------
        QiitaDBWarning
            If the values aren't castable
        """
        warning_msg = []
        columns = self.categories
        wrong_msg = 'Sample "%s", column "%s", wrong value "%s"'
        for label, restriction in restriction_dict.items():
            missing = set(restriction.columns).difference(columns)
            if missing:
                warning_msg.append(
                    "%s: %s" % (restriction.error_msg, ", ".join(sorted(missing)))
                )
            else:
                valid_null = qdb.metadata_template.constants.EBI_NULL_VALUES
                for column, datatype in restriction.columns.items():
                    # sorting by key (sample id) so we always check in the
                    # same order, helpful for testing
                    cats_by_column = self.get_category(column)
                    for sample in sorted(cats_by_column):
                        val = cats_by_column[sample]
                        # ignore if valid null value
                        if val in valid_null:
                            continue
                        # test values
                        if datatype == datetime:
                            val = str(val)
                            formats = [
                                # 4 digits year
                                "%Y-%m-%d %H:%M:%S",
                                "%Y-%m-%d %H:%M",
                                "%Y-%m-%d %H",
                                "%Y-%m-%d",
                                "%Y-%m",
                                "%Y",
                            ]
                            date = None
                            for fmt in formats:
                                try:
                                    date = datetime.strptime(val, fmt)
                                    break
                                except ValueError:
                                    pass
                            if date is None:
                                warning_msg.append(wrong_msg % (sample, column, val))
                        else:
                            try:
                                datatype(val)
                            except (ValueError, TypeError):
                                warning_msg.append(wrong_msg % (sample, column, val))

        if warning_msg:
            warnings.warn(
                "Some functionality will be disabled due to missing "
                "columns:\n\t%s.\nSee the Templates tutorial for a description"
                " of these fields." % ";\n\t".join(warning_msg),
                qdb.exceptions.QiitaDBWarning,
            )

    @classmethod
    def _identify_forbidden_words_in_column_names(cls, column_names):
        """Return a list of forbidden words found in column_names.

        Parameters
        ----------
        column_names : iterable
            Iterable containing the column names to check.

        Returns
        ------
            set of forbidden words present in the column_names iterable.
        """
        return set(cls._forbidden_words) & set(column_names)

    @classmethod
    def _identify_pgsql_reserved_words_in_column_names(cls, column_names):
        """Return a list of PostgreSQL-reserved words found in column_names.

        Parameters
        ----------
        column_names : iterable
            Iterable containing the column names to check.

        Returns
        ------
            set of reserved words present in the column_names iterable.

        References
        ----------
        .. [1] postgresql SQL-SYNTAX-IDENTIFIERS: https://goo.gl/EF0cUV.
        """
        return qdb.metadata_template.util.get_pgsql_reserved_words() & set(column_names)

    @classmethod
    def _identify_column_names_with_invalid_characters(cls, column_names):
        """Return a list of invalid words found in column_names.

        Parameters
        ----------
        column_names : iterable
            Iterable containing the column names to check.

        Returns
        ------
            set of words containing invalid (illegal) characters.
        """
        valid_initial_char = ascii_letters
        valid_rest = set(ascii_letters + digits + "_:|")
        invalid = []
        for s in column_names:
            if s[0] not in valid_initial_char:
                invalid.append(s)
            elif set(s) - valid_rest:
                invalid.append(s)
        return set(invalid)

    @classmethod
    def _identify_qiime2_reserved_words_in_column_names(cls, column_names):
        """Return a list of QIIME2-reserved words found in column_names.

        Parameters
        ----------
        column_names : iterable
            Iterable containing the column names to check.

        Returns
        ------
            set of words containing QIIME2-reserved words.
        """
        return qdb.metadata_template.util.get_qiime2_reserved_words() & set(
            column_names
        )

    @property
    def restrictions(cls):
        r"""Retrieves the restrictions based on the class._table

        Returns
        -------
        dict
            {restriction: values, ...}
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT name, valid_values
                     FROM qiita.restrictions
                     WHERE table_name = %s"""
            qdb.sql_connection.TRN.add(sql, [cls._table])
            return dict(qdb.sql_connection.TRN.execute_fetchindex())

    def validate_restrictions(self):
        r"""Validates the restrictions

        Returns
        -------
        success, boolean
            If the validation was successful
        message, string
            Message if success is not True
        """
        with qdb.sql_connection.TRN:
            # [:-1] removing last _
            name = "%s %d" % (self._table_prefix[:-1], self.id)
            success = True
            message = []
            restrictions = self.restrictions
            categories = self.categories

            difference = sorted(set(restrictions.keys()) - set(categories))
            if difference:
                success = False
                message.append(
                    '%s is missing columns "%s"' % (name, ", ".join(difference))
                )

            to_review = set(restrictions.keys()) & set(categories)
            for key in to_review:
                info_vals = set(self.get_category(key).values())
                msg = []
                for v in info_vals:
                    if v not in restrictions[key]:
                        msg.append(v)
                if msg:
                    success = False
                    message.append(
                        '%s has invalid values: "%s", valid values are: '
                        '"%s"' % (name, ", ".join(msg), ", ".join(restrictions[key]))
                    )

            return success, "\n".join(message)
