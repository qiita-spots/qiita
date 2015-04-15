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

from __future__ import division
from future.utils import viewitems, viewvalues
from os.path import join
from functools import partial
from collections import defaultdict
from copy import deepcopy

import pandas as pd
from skbio.util import find_duplicates

from qiita_core.exceptions import IncompetentQiitaDeveloperError

from qiita_db.exceptions import (QiitaDBUnknownIDError, QiitaDBColumnError,
                                 QiitaDBNotImplementedError,
                                 QiitaDBExecutionError,
                                 QiitaDBDuplicateHeaderError)
from qiita_db.base import QiitaObject
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.util import (exists_table, get_table_cols,
                           convert_to_id,
                           get_mountpoint, insert_filepaths)
from qiita_db.logger import LogEntry
from .util import (as_python_types, get_datatypes, get_invalid_sample_names,
                   prefix_sample_names_with_id)


class BaseSample(QiitaObject):
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
    _column_table = None
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
            raise QiitaDBUnknownIDError(sample_id, self.__class__.__name__)
        # Assign private attributes
        self._id = sample_id
        self._md_template = md_template
        self._dynamic_table = "%s%d" % (self._table_prefix,
                                        self._md_template.id)

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
        cls._check_subclass()
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE sample_id=%s AND "
            "{1}=%s)".format(cls._table, cls._id_column),
            (sample_id, md_template.id))[0]

    def _get_categories(self, conn_handler):
        r"""Returns all the available metadata categories for the sample

        Parameters
        ----------
        conn_handler : SQLConnectionHandler
            The connection handler object connected to the DB

        Returns
        -------
        set of str
            The set of all available metadata categories
        """
        # Get all the required columns
        required_cols = get_table_cols(self._table, conn_handler)
        # Get all the the columns in the dynamic table
        dynamic_cols = get_table_cols(self._dynamic_table, conn_handler)
        # Get the union of the two previous lists
        cols = set(required_cols).union(dynamic_cols)
        # Remove the sample_id column and the study_id/raw_data_id columns,
        # as this columns are used internally for data storage and they don't
        # actually belong to the metadata
        cols.remove('sample_id')
        cols.remove(self._id_column)
        try:
            # study_id could be potentially removed by _id_column, so wrap
            # in a try except
            cols.remove('study_id')
        except KeyError:
            pass
        # Change the *_id columns, as this is for convenience internally,
        # and add the original categories
        for key, value in viewitems(self._md_template.translate_cols_dict):
            cols.remove(key)
            cols.add(value)

        return cols

    def _to_dict(self):
        r"""Returns the categories and their values in a dictionary

        Returns
        -------
        dict of {str: str}
            A dictionary of the form {category: value}
        """
        conn_handler = SQLConnectionHandler()
        d = dict(conn_handler.execute_fetchone(
            "SELECT * FROM qiita.{0} WHERE {1}=%s AND "
            "sample_id=%s".format(self._table, self._id_column),
            (self._md_template.id, self._id)))
        dynamic_d = dict(conn_handler.execute_fetchone(
            "SELECT * from qiita.{0} WHERE "
            "sample_id=%s".format(self._dynamic_table),
            (self._id, )))
        d.update(dynamic_d)
        del d['sample_id']
        del d[self._id_column]
        d.pop('study_id', None)

        # Modify all the *_id columns to include the string instead of the id
        for k, v in viewitems(self._md_template.translate_cols_dict):
            d[v] = self._md_template.str_cols_handlers[k][d[k]]
            del d[k]
        return d

    def __len__(self):
        r"""Returns the number of metadata categories

        Returns
        -------
        int
            The number of metadata categories
        """
        conn_handler = SQLConnectionHandler()
        # return the number of columns
        return len(self._get_categories(conn_handler))

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
        conn_handler = SQLConnectionHandler()
        key = key.lower()
        if key in self._get_categories(conn_handler):
            # It's possible that the key is asking for one of the *_id columns
            # that we have to do the translation
            def handler(x):
                return x

            # prevent flake8 from complaining about the function not being
            # used and a redefinition happening in the next few lines
            handler(None)

            if key in self._md_template.translate_cols_dict.values():
                handler = (
                    lambda x: self._md_template.str_cols_handlers[key][x])
                key = "%s_id" % key
            # Check if we have either to query the table with required columns
            # or the dynamic table
            if key in get_table_cols(self._table, conn_handler):
                result = conn_handler.execute_fetchone(
                    "SELECT {0} FROM qiita.{1} WHERE {2}=%s AND "
                    "sample_id=%s".format(key, self._table, self._id_column),
                    (self._md_template.id, self._id))[0]
                return handler(result)
            else:
                return conn_handler.execute_fetchone(
                    "SELECT {0} FROM qiita.{1} WHERE "
                    "sample_id=%s".format(key, self._dynamic_table),
                    (self._id, ))[0]
        else:
            # The key is not available for the sample, so raise a KeyError
            raise KeyError("Metadata category %s does not exists for sample %s"
                           " in template %d" %
                           (key, self._id, self._md_template.id))

    def add_setitem_queries(self, column, value, conn_handler, queue):
        """Adds the SQL queries needed to set a value to the provided queue

        Parameters
        ----------
        column : str
            The column to update
        value : str
            The value to set. This is expected to be a str on the assumption
            that psycopg2 will cast as necessary when updating.
        conn_handler : SQLConnectionHandler
            The connection handler object connected to the DB
        queue : str
            The queue where the SQL statements will be added

        Raises
        ------
        QiitaDBColumnError
            If the column does not exist in the table
        """
        # try dynamic tables
        sql = """SELECT EXISTS (
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name=%s
                        AND table_schema='qiita'
                        AND column_name=%s)"""
        exists_dynamic = conn_handler.execute_fetchone(
            sql, (self._dynamic_table, column))[0]
        # try required_sample_info
        sql = """SELECT EXISTS (
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name=%s
                        AND table_schema='qiita'
                        AND column_name=%s)"""
        exists_required = conn_handler.execute_fetchone(
            sql, (self._table, column))[0]

        if exists_dynamic:
                sql = """UPDATE qiita.{0}
                         SET {1}=%s
                         WHERE sample_id=%s""".format(self._dynamic_table,
                                                      column)
        elif exists_required:
            # here is not required the type check as the required fields have
            # an explicit type check
            sql = """UPDATE qiita.{0}
                     SET {1}=%s
                     WHERE sample_id=%s""".format(self._table, column)
        else:
            raise QiitaDBColumnError("Column %s does not exist in %s" %
                                     (column, self._dynamic_table))

        conn_handler.add_to_queue(queue, sql, (value, self._id))

    def __setitem__(self, column, value):
        r"""Sets the metadata value for the category `column`

        Parameters
        ----------
        column : str
            The column to update
        value : str
            The value to set. This is expected to be a str on the assumption
            that psycopg2 will cast as necessary when updating.

        Raises
        ------
        ValueError
            If the value type does not match the one in the DB
        """
        conn_handler = SQLConnectionHandler()
        queue_name = "set_item_%s" % self._id
        conn_handler.create_queue(queue_name)

        self.add_setitem_queries(column, value, conn_handler, queue_name)

        try:
            conn_handler.execute_queue(queue_name)
        except QiitaDBExecutionError as e:
            # catching error so we can check if the error is due to different
            # column type or something else
            type_lookup = defaultdict(lambda: 'varchar')
            type_lookup[int] = 'integer'
            type_lookup[float] = 'float8'
            type_lookup[str] = 'varchar'
            value_type = type_lookup[type(value)]

            sql = """SELECT udt_name
                     FROM information_schema.columns
                     WHERE column_name = %s
                        AND table_schema = 'qiita'
                        AND (table_name = %s OR table_name = %s)"""
            column_type = conn_handler.execute_fetchone(
                sql, (column, self._table, self._dynamic_table))

            if column_type != value_type:
                raise ValueError(
                    'The new value being added to column: "{0}" is "{1}" '
                    '(type: "{2}"). However, this column in the DB is of '
                    'type "{3}". Please change the value in your updated '
                    'template or reprocess your template.'.format(
                        column, value, value_type, column_type))

            raise e

    def __delitem__(self, key):
        r"""Removes the sample with sample id `key` from the database

        Parameters
        ----------
        key : str
            The sample id
        """
        raise QiitaDBNotImplementedError()

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
        conn_handler = SQLConnectionHandler()
        return iter(self._get_categories(conn_handler))

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
        conn_handler = SQLConnectionHandler()
        return key.lower() in self._get_categories(conn_handler)

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


class MetadataTemplate(QiitaObject):
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

    See Also
    --------
    QiitaObject
    SampleTemplate
    PrepTemplate
    """

    # Used to find the right SQL tables - should be defined on the subclasses
    _table_prefix = None
    _column_table = None
    _id_column = None
    _sample_cls = None

    def _check_id(self, id_, conn_handler=None):
        r"""Checks that the MetadataTemplate id_ exists on the database"""
        self._check_subclass()
        conn_handler = (conn_handler if conn_handler is not None
                        else SQLConnectionHandler())
        return conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE "
            "{1}=%s)".format(self._table, self._id_column),
            (id_, ))[0]

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
                "_table_prefix should be defined in the subclasses")
        return "%s%d" % (cls._table_prefix, obj_id)

    @classmethod
    def _check_special_columns(cls, md_template, obj):
        r"""Checks for special columns based on obj type

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        obj : object
            Any extra object needed by the template to perform any extra check
        """
        # Check required columns
        missing = set(cls.translate_cols_dict.values()).difference(md_template)
        if not missing:
            # Change any *_id column to its str column
            for key, value in viewitems(cls.translate_cols_dict):
                handler = cls.id_cols_handlers[key]
                md_template[key] = pd.Series(
                    [handler[i] for i in md_template[value]],
                    index=md_template.index)
                del md_template[value]

        return missing.union(
            cls._check_template_special_columns(md_template, obj))

    @classmethod
    def _clean_validate_template(cls, md_template, study_id, obj,
                                 conn_handler=None):
        """Takes care of all validation and cleaning of metadata templates

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        study_id : int
            The study to which the metadata template belongs to.
        obj : object
            Any extra object needed by the template to perform any extra check

        Returns
        -------
        md_template : DataFrame
            Cleaned copy of the input md_template

        Raises
        ------
        QiitaDBColumnError
            If the sample names in md_template contains invalid names
        QiitaDBDuplicateHeaderError
            If md_template contains duplicate headers
        QiitaDBColumnError
            If md_template is missing a required column
        """
        cls._check_subclass()
        invalid_ids = get_invalid_sample_names(md_template.index)
        if invalid_ids:
            raise QiitaDBColumnError("The following sample names in the "
                                     "template contain invalid characters "
                                     "(only alphanumeric characters or periods"
                                     " are allowed): %s." %
                                     ", ".join(invalid_ids))
        # We are going to modify the md_template. We create a copy so
        # we don't modify the user one
        md_template = deepcopy(md_template)

        # Prefix the sample names with the study_id
        prefix_sample_names_with_id(md_template, study_id)

        # In the database, all the column headers are lowercase
        md_template.columns = [c.lower() for c in md_template.columns]

        # Check that we don't have duplicate columns
        if len(set(md_template.columns)) != len(md_template.columns):
            raise QiitaDBDuplicateHeaderError(
                find_duplicates(md_template.columns))

        # We need to check for some special columns, that are not present on
        # the database, but depending on the data type are required.
        missing = cls._check_special_columns(md_template, obj)

        conn_handler = conn_handler if conn_handler else SQLConnectionHandler()

        # Get the required columns from the DB
        db_cols = get_table_cols(cls._table, conn_handler)

        # Remove the sample_id and study_id columns
        db_cols.remove('sample_id')
        db_cols.remove(cls._id_column)

        # Retrieve the headers of the metadata template
        headers = list(md_template.keys())

        # Check that md_template has the required columns
        remaining = set(db_cols).difference(headers)
        missing = missing.union(remaining)
        missing = missing.difference(cls.translate_cols_dict)
        if missing:
            raise QiitaDBColumnError("Missing columns: %s"
                                     % ', '.join(missing))
        return md_template

    @classmethod
    def _add_common_creation_steps_to_queue(cls, md_template, obj_id,
                                            conn_handler, queue_name):
        r"""Adds the common creation steps to the queue in conn_handler

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        obj_id : int
            The id of the object being created
        conn_handler : SQLConnectionHandler
            The connection handler object connected to the DB
        queue_name : str
            The queue where the SQL statements will be added
        """
        cls._check_subclass()
        # Get some useful information from the metadata template
        sample_ids = md_template.index.tolist()
        num_samples = len(sample_ids)
        headers = list(md_template.keys())

        # Get the required columns from the DB
        db_cols = sorted(get_table_cols(cls._table, conn_handler))
        # Remove the sample_id and _id_column columns
        db_cols.remove('sample_id')
        db_cols.remove(cls._id_column)

        # Insert values on required columns
        values = as_python_types(md_template, db_cols)
        values.insert(0, sample_ids)
        values.insert(0, [obj_id] * num_samples)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} ({1}, sample_id, {2}) "
            "VALUES (%s, %s, {3})".format(cls._table, cls._id_column,
                                          ', '.join(db_cols),
                                          ', '.join(['%s'] * len(db_cols))),
            values, many=True)

        # Insert rows on *_columns table
        headers = sorted(set(headers).difference(db_cols))
        datatypes = get_datatypes(md_template.ix[:, headers])
        # psycopg2 requires a list of tuples, in which each tuple is a set
        # of values to use in the string formatting of the query. We have all
        # the values in different lists (but in the same order) so use zip
        # to create the list of tuples that psycopg2 requires.
        values = [
            v for v in zip([obj_id] * len(headers), headers, datatypes)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} ({1}, column_name, column_type) "
            "VALUES (%s, %s, %s)".format(cls._column_table, cls._id_column),
            values, many=True)

        # Create table with custom columns
        table_name = cls._table_name(obj_id)
        column_datatype = ["%s %s" % (col, dtype)
                           for col, dtype in zip(headers, datatypes)]
        conn_handler.add_to_queue(
            queue_name,
            "CREATE TABLE qiita.{0} (sample_id varchar NOT NULL, {1})".format(
                table_name, ', '.join(column_datatype)))

        # Insert values on custom table
        values = as_python_types(md_template, headers)
        values.insert(0, sample_ids)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} (sample_id, {1}) "
            "VALUES (%s, {2})".format(table_name, ", ".join(headers),
                                      ', '.join(["%s"] * len(headers))),
            values, many=True)

    @classmethod
    def delete(cls, id_):
        r"""Deletes the table from the database

        Parameters
        ----------
        id_ : obj
            The object identifier

        Raises
        ------
        QiitaDBUnknownIDError
            If no metadata_template with id id_ exists
        """
        cls._check_subclass()
        if not cls.exists(id_):
            raise QiitaDBUnknownIDError(id_, cls.__name__)

        table_name = cls._table_name(id_)
        conn_handler = SQLConnectionHandler()

        # Delete the sample template filepaths
        conn_handler.execute(
            "DELETE FROM qiita.sample_template_filepath WHERE "
            "study_id = %s", (id_, ))

        conn_handler.execute(
            "DROP TABLE qiita.{0}".format(table_name))
        conn_handler.execute(
            "DELETE FROM qiita.{0} where {1} = %s".format(cls._table,
                                                          cls._id_column),
            (id_,))
        conn_handler.execute(
            "DELETE FROM qiita.{0} where {1} = %s".format(cls._column_table,
                                                          cls._id_column),
            (id_,))

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
        return exists_table(cls._table_name(obj_id), SQLConnectionHandler())

    def _get_sample_ids(self, conn_handler):
        r"""Returns all the available samples for the metadata template

        Parameters
        ----------
        conn_handler : SQLConnectionHandler
            The connection handler object connected to the DB

        Returns
        -------
        set of str
            The set of all available sample ids
        """
        sample_ids = conn_handler.execute_fetchall(
            "SELECT sample_id FROM qiita.{0} WHERE "
            "{1}=%s".format(self._table, self._id_column),
            (self._id, ))
        return set(sample_id[0] for sample_id in sample_ids)

    def __len__(self):
        r"""Returns the number of samples in the metadata template

        Returns
        -------
        int
            The number of samples in the metadata template
        """
        conn_handler = SQLConnectionHandler()
        return len(self._get_sample_ids(conn_handler))

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
        if key in self:
            return self._sample_cls(key, self)
        else:
            raise KeyError("Sample id %s does not exists in template %d"
                           % (key, self._id))

    def __setitem__(self, key, value):
        r"""Sets the metadata values for sample id `key`

        Parameters
        ----------
        key : str
            The sample id
        value : Sample
            The sample obj holding the new sample values
        """
        raise QiitaDBNotImplementedError()

    def __delitem__(self, key):
        r"""Removes the sample with sample id `key` from the database

        Parameters
        ----------
        key : str
            The sample id
        """
        raise QiitaDBNotImplementedError()

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
        conn_handler = SQLConnectionHandler()
        return iter(self._get_sample_ids(conn_handler))

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
        conn_handler = SQLConnectionHandler()
        return key in self._get_sample_ids(conn_handler)

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
        conn_handler = SQLConnectionHandler()
        return iter(self._sample_cls(sample_id, self)
                    for sample_id in self._get_sample_ids(conn_handler))

    def items(self):
        r"""Iterator over (sample_id, values) tuples, in sample id order

        Returns
        -------
        Iterator
            Iterator over (sample_ids, values) tuples
        """
        conn_handler = SQLConnectionHandler()
        return iter((sample_id, self._sample_cls(sample_id, self))
                    for sample_id in self._get_sample_ids(conn_handler))

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
            sid = values_dict['sample_id']
            del values_dict['sample_id']
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
        raise QiitaDBNotImplementedError(
            "generate_files should be implemented in the subclass!")

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
        conn_handler = SQLConnectionHandler()
        metadata_map = self._transform_to_dict(conn_handler.execute_fetchall(
            "SELECT * FROM qiita.{0} WHERE {1}=%s".format(self._table,
                                                          self._id_column),
            (self.id,)))
        dyn_vals = self._transform_to_dict(conn_handler.execute_fetchall(
            "SELECT * FROM qiita.{0}".format(self._table_name(self.id))))

        for k in metadata_map:
            for key, value in viewitems(self.translate_cols_dict):
                id_ = metadata_map[k][key]
                metadata_map[k][value] = self.str_cols_handlers[key][id_]
                del metadata_map[k][key]
            metadata_map[k].update(dyn_vals[k])
            metadata_map[k].pop('study_id', None)

        # Remove samples that are not in the samples list, if it was supplied
        if samples is not None:
            for sid, d in metadata_map.items():
                if sid not in samples:
                    metadata_map.pop(sid)

        # Write remaining samples to file
        headers = sorted(list(metadata_map.values())[0].keys())
        with open(fp, 'w') as f:
            # First write the headers
            f.write("sample_name\t%s\n" % '\t'.join(headers))
            # Write the values for each sample id
            for sid, d in sorted(metadata_map.items()):
                values = [str(d[h]) for h in headers]
                values.insert(0, sid)
                f.write("%s\n" % '\t'.join(values))

    def to_dataframe(self):
        """Returns the metadata template as a dataframe

        Returns
        -------
        pandas DataFrame
            The metadata in the template,indexed on sample id
        """
        conn_handler = SQLConnectionHandler()
        cols = get_table_cols(self._table, conn_handler)
        if 'study_id' in cols:
            cols.remove('study_id')
        dyncols = get_table_cols(self._table_name(self._id), conn_handler)
        # remove sample_id from dyncols so not repeated
        dyncols.remove('sample_id')
        # Get all metadata for the template
        sql = """SELECT {0}, {1} FROM qiita.{2} req
            INNER JOIN qiita.{3} dyn on req.sample_id = dyn.sample_id
            WHERE req.{4} = %s""".format(
            ", ".join("req.%s" % c for c in cols),
            ", ".join("dyn.%s" % d for d in dyncols),
            self._table, self._table_name(self._id), self._id_column)
        meta = conn_handler.execute_fetchall(sql, [self._id])
        cols = cols + dyncols

        # Create the dataframe and clean it up a bit
        df = pd.DataFrame((list(x) for x in meta), columns=cols)
        df.set_index('sample_id', inplace=True, drop=True)
        # Turn id cols to value cols
        for col, value in viewitems(self.str_cols_handlers):
            df[col].replace(value, inplace=True)
        df.rename(columns=self.translate_cols_dict, inplace=True)

        return df

    def add_filepath(self, filepath, conn_handler=None):
        r"""Populates the DB tables for storing the filepath and connects the
        `self` objects with this filepath"""
        # Check that this function has been called from a subclass
        self._check_subclass()

        # Check if the connection handler has been provided. Create a new
        # one if not.
        conn_handler = conn_handler if conn_handler else SQLConnectionHandler()

        if self._table == 'required_sample_info':
            fp_id = convert_to_id("sample_template", "filepath_type",
                                  conn_handler)
            table = 'sample_template_filepath'
            column = 'study_id'
        elif self._table == 'common_prep_info':
            fp_id = convert_to_id("prep_template", "filepath_type",
                                  conn_handler)
            table = 'prep_template_filepath'
            column = 'prep_template_id'
        else:
            raise QiitaDBNotImplementedError(
                'add_filepath for %s' % self._table)

        try:
            fpp_id = insert_filepaths([(filepath, fp_id)], None, "templates",
                                      "filepath", conn_handler,
                                      move_files=False)[0]
            values = (self._id, fpp_id)
            conn_handler.execute(
                "INSERT INTO qiita.{0} ({1}, filepath_id) "
                "VALUES (%s, %s)".format(table, column), values)
        except Exception as e:
            LogEntry.create('Runtime', str(e),
                            info={self.__class__.__name__: self.id})
            raise e

    def get_filepaths(self, conn_handler=None):
        r"""Retrieves the list of (filepath_id, filepath)"""
        # Check that this function has been called from a subclass
        self._check_subclass()

        # Check if the connection handler has been provided. Create a new
        # one if not.
        conn_handler = conn_handler if conn_handler else SQLConnectionHandler()

        if self._table == 'required_sample_info':
            table = 'sample_template_filepath'
            column = 'study_id'
        elif self._table == 'common_prep_info':
            table = 'prep_template_filepath'
            column = 'prep_template_id'
        else:
            raise QiitaDBNotImplementedError(
                'get_filepath for %s' % self._table)

        try:
            filepath_ids = conn_handler.execute_fetchall(
                "SELECT filepath_id, filepath FROM qiita.filepath WHERE "
                "filepath_id IN (SELECT filepath_id FROM qiita.{0} WHERE "
                "{1}=%s) ORDER BY filepath_id DESC".format(table, column),
                (self.id, ))
        except Exception as e:
            LogEntry.create('Runtime', str(e),
                            info={self.__class__.__name__: self.id})
            raise e

        _, fb = get_mountpoint('templates', conn_handler)[0]
        base_fp = partial(join, fb)

        return [(fpid, base_fp(fp)) for fpid, fp in filepath_ids]

    def categories(self):
        """Identifies the metadata columns present in a template

        Returns
        -------
        cols : list
            The static and dynamic category fields

        """
        cols = get_table_cols(self._table_name(self._id))
        cols.extend(get_table_cols(self._table)[1:])

        for idx, c in enumerate(cols):
            if c in self.translate_cols_dict:
                cols[idx] = self.translate_cols_dict[c]

        return cols

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
        ValueError
            If one of the new values cannot be inserted in the DB due to
            different types
        """
        if not set(self.keys()).issuperset(samples_and_values):
            missing = set(self.keys()) - set(samples_and_values)
            table_name = self._table_name(self.study_id)
            raise QiitaDBUnknownIDError(missing, table_name)

        conn_handler = SQLConnectionHandler()
        queue_name = "update_category_%s_%s" % (self._id, category)
        conn_handler.create_queue(queue_name)

        for k, v in viewitems(samples_and_values):
            sample = self[k]
            sample.add_setitem_queries(category, v, conn_handler, queue_name)

        try:
            conn_handler.execute_queue(queue_name)
        except QiitaDBExecutionError as e:
            # catching error so we can check if the error is due to different
            # column type or something else
            type_lookup = defaultdict(lambda: 'varchar')
            type_lookup[int] = 'integer'
            type_lookup[float] = 'float8'
            type_lookup[str] = 'varchar'
            value_types = set(type_lookup[type(value)]
                              for value in viewvalues(samples_and_values))

            sql = """SELECT udt_name
                     FROM information_schema.columns
                     WHERE column_name = %s
                        AND table_schema = 'qiita'
                        AND (table_name = %s OR table_name = %s)"""
            column_type = conn_handler.execute_fetchone(
                sql, (category, self._table, self._table_name(self._id)))

            if any([column_type != vt for vt in value_types]):
                value_str = ', '.join(
                    [str(value) for value in viewvalues(samples_and_values)])
                value_types_str = ', '.join(value_types)

                raise ValueError(
                    'The new values being added to column: "%s" are "%s" '
                    '(types: "%s"). However, this column in the DB is of '
                    'type "%s". Please change the values in your updated '
                    'template or reprocess your template.'
                    % (category, value_str, value_types_str, column_type))

            raise e
