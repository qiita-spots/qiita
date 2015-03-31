# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from future.utils import viewitems
from os.path import join
from functools import partial
from copy import deepcopy
import warnings

import pandas as pd
from skbio.util import find_duplicates

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import (QiitaDBUnknownIDError, QiitaDBColumnError,
                                 QiitaDBNotImplementedError, QiitaDBWarning,
                                 QiitaDBDuplicateHeaderError)
from qiita_db.base import QiitaObject
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.util import (exists_table, get_table_cols, get_mountpoint,
                           insert_filepaths)
from qiita_db.logger import LogEntry
from .util import (get_invalid_sample_names, prefix_sample_names_with_id,
                   get_datatypes, as_python_types)


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
        # Get all the columns
        cols = set(get_table_cols(self._dynamic_table, conn_handler))
        # Remove the sample_id column as this column is used internally for
        # data storage and they don't actually belong to the metadata
        cols.remove('sample_id')

        return cols

    def _to_dict(self):
        r"""Returns the categories and their values in a dictionary

        Returns
        -------
        dict of {str: str}
            A dictionary of the form {category: value}
        """
        conn_handler = SQLConnectionHandler()
        sql = "SELECT * from qiita.{0} WHERE sample_id=%s".format(
            self._dynamic_table)
        d = dict(conn_handler.execute_fetchone(sql, (self._id, )))
        # Remove the sample_id column as this column is used internally for
        # data storage and they don't actually belong to the metadata
        del d['sample_id']
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
        if key not in self._get_categories(conn_handler):
            # The key is not available for the sample, so raise a KeyError
            raise KeyError("Metadata category %s does not exists for sample %s"
                           " in template %d" %
                           (key, self._id, self._md_template.id))
        sql = "SELECT {0} FROM qiita.{1} WHERE sample_id=%s".format(
            key, self._dynamic_table)
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    def __setitem__(self, key, value):
        r"""Sets the metadata value for the category `key`

        Parameters
        ----------
        key : str
            The metadata category
        value : obj
            The new value for the category
        """
        conn_handler = SQLConnectionHandler()

        # try dynamic tables
        sql = """SELECT EXISTS (
            SELECT column_name
                FROM information_schema.columns
                WHERE table_name=%s
                    AND table_schema=%s
                    AND column_name=%s)"""
        exists = conn_handler.execute_fetchone(
            sql, (self._dynamic_table, 'qiita', key))[0]

        if not exists:
            raise QiitaDBColumnError("Column %s does not exist in %s" %
                                     (key, self._dynamic_table))

        # catching error so we can check if the error is due to different
        # column type or something else
        try:
            sql = """UPDATE qiita.{0} SET {1}=%s
                    WHERE sample_id=%s""".format(self._dynamic_table, key)
            conn_handler.execute(sql, (value, self._id))
        except Exception as e:
            sql = """SELECT data_type
                        FROM information_schema.columns
                        WHERE table_name=%s
                            AND table_schema=%s
                            AND column_name=%s"""
            column_type = conn_handler.execute_fetchone(
                sql, (self._dynamic_table, 'qiita', key))[0]
            value_type = type(value).__name__

            if value_type == "bool_":
                value_type = "boolean"

            if column_type != value_type:
                raise ValueError(
                    'The new value being added to column: "{0}" is "{1}" '
                    '(type: "{2}"). However, this column in the DB is of '
                    'type "{3}". Please change the value in your updated '
                    'template or reprocess your sample template.'.format(
                        key, value, value_type, column_type))
            else:
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
    create
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
    _filepath_table = None
    _filepath_type = None

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
    def metadata_headers(cls):
        """Returns metadata headers available

        Returns
        -------
        list
            Alphabetical list of all metadata headers available
        """
        cls._check_subclass()
        conn_handler = SQLConnectionHandler()
        sql = """SELECT DISTINCT column_name FROM qiita.{0}
                 ORDER BY column_name""".format(cls._column_table)
        return [x[0] for x in conn_handler.execute_fetchall(sql)]

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
        cls._check_subclass()
        if not cls._table_prefix:
            raise IncompetentQiitaDeveloperError(
                "_table_prefix should be defined in the subclasses")
        return "%s%d" % (cls._table_prefix, obj_id)

    @classmethod
    def _clean_validate_template(cls, md_template, study_id, restriction_dict):
        """Takes care of all validation and cleaning of templates

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        study_id : int
            The study to which the template belongs to.
        restriction_dict : dict of {str: Restriction}
            A dictionary with the restrictions that apply to the metadata

        Returns
        -------
        md_template : DataFrame
            Cleaned copy of the input md_template
        """
        cls._check_subclass()
        invalid_ids = get_invalid_sample_names(md_template.index)
        if invalid_ids:
            raise QiitaDBColumnError(
                "The following sample names in the %s contain invalid "
                "characters (only alphanumeric characters or periods are "
                "allowed): %s." % (cls.__name__, ", ".join(invalid_ids)))

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

        # Check if we have the columns needed for some functionality
        warning_msg = []
        for key, restriction in viewitems(restriction_dict):
            missing = [col for col in restriction.columns
                       if col not in md_template]
            if missing:
                warning_msg.append(
                    "%s: %s" % (restriction.error_msg, ', '.join(missing)))

        if warning_msg:
            warnings.warn(
                "Some functionality will be disabled due to missing "
                "columns:\n\t%s" % "\n\t".join(warning_msg),
                QiitaDBWarning)

        return md_template

    @classmethod
    def _add_common_creation_steps(cls, obj_id, md_template, conn_handler,
                                   queue):
        cls._check_subclass()
        # Get some useful information from the metadata template
        sample_ids = md_template.index.tolist()
        headers = list(md_template.keys())
        # Insert values on required columns
        values = [(obj_id, s_id) for s_id in sample_ids]
        sql = "INSERT INTO qiita.{0} ({1}, sample_id) VALUES (%s, %s)".format(
            cls._table, cls._id_column)
        conn_handler.add_to_queue(queue, sql, values, many=True)

        # Insert rows on *_columns table
        datatypes = get_datatypes(md_template.ix[:, headers])
        # psycopg2 requires a list of tuples, in which each tuple contains
        # the values to use in the string formatting of the query. We have all
        # the values in different lists (but in the same order) so use zip
        # to create the list of tuples that psycopg2 requires.
        values = [(obj_id, h, d) for h, d in zip(headers, datatypes)]
        sql = """INSERT INTO qiita.{0} ({1}, column_name, column_type)
                 VALUES (%s, %s, %s)""".format(cls._column_table,
                                               cls._id_column)
        conn_handler.add_to_queue(queue, sql, values, many=True)

        # Create table with custom columns
        table_name = cls._table_name(obj_id)
        column_datatype = ["%s %s" % (col, dtype)
                           for col, dtype in zip(headers, datatypes)]
        conn_handler.add_to_queue(
            queue,
            "CREATE TABLE qiita.{0} (sample_id varchar NOT NULL, {1})".format(
                table_name, ', '.join(column_datatype)))

        # Insert values on custom table
        values = as_python_types(md_template, headers)
        values.insert(0, sample_ids)
        values = [v for v in zip(*values)]
        sql = "INSERT INTO qiita.{0} (sample_id, {1}) VALUES (%s, {2})".format(
            table_name, ", ".join(headers), ', '.join(["%s"] * len(headers)))
        conn_handler.add_to_queue(queue, sql, values, many=True)

    @classmethod
    def _delete_checks(cls, id_, conn_handler=None):
        r"""Performs the checks to know if a MetadataTemplate can be deleted

        Parameters
        ----------
        id_ : obj id
            The object identifier
        conn_handler : SQLConnectionHandler, optional
            The connection handler connected to the DB

        Raises
        ------
        IncompetentQiitaDeveloperError
            Should be implemented in the subclasses
        """
        raise IncompetentQiitaDeveloperError(
            "_delete_checks should be implemtented in the subclasses")

    @classmethod
    def _add_delete_extra_cleanup(cls, id_, conn_handler, queue):
        r"""Adds any extra needed clean up to the queue

        Parameters
        ----------
        id_ : obj id
            The object identifier
        conn_handler : SQLConnectionHandler
            The connection handler connected to the DB
        queue : str
            The queue from conn_handler to add the extra clean up sql commands
        """
        pass

    @classmethod
    def delete(cls, id_):
        r"""Deletes the metadata template from the database

        Parameters
        ----------
        id_ : int
            The object identifier

        Raises
        ------
        QiitaDBUnknownIDError
            If no metadata_template with id id_ exists
        """
        cls._check_subclass()
        if not cls.exists(id_):
            raise QiitaDBUnknownIDError(id_, cls.__name__)

        conn_handler = SQLConnectionHandler()

        # Let each type of template to handle their checks. If they fail,
        # they will raise a useful error.
        cls._delete_checks(id_, conn_handler)
        table_name = cls._table_name(id_)

        queue = "DELETE_%s_%d" % (cls.__name__, id_)
        conn_handler.create_queue(queue)

        # Delete the connection between the metadata template and its filepath
        sql = "DELETE FROM qiita.{0} WHERE {1} = %s".format(
            cls._filepath_table, cls._id_column)
        conn_handler.add_to_queue(queue, sql, (id_,))

        # Drop the dynamic table
        sql = "DROP TABLE qiita.{0}".format(table_name)
        conn_handler.add_to_queue(queue, sql)

        # Drop the rows from table with required values
        sql = "DELETE FROM qiita.{0} where {1} = %s".format(cls._table,
                                                            cls._id_column)
        conn_handler.add_to_queue(queue, sql, (id_,))

        # Drop the rows from the table with the column type information
        sql = "DELETE FROM qiita.{0} where {1} = %s".format(cls._column_table,
                                                            cls._id_column)
        conn_handler.add_to_queue(queue, sql, (id_,))

        cls._add_delete_extra_cleanup(id_, conn_handler, queue)

        conn_handler.execute_queue(queue)

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
            result[sid] = values_dict

        return result

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
        df = self.to_dataframe(samples)
        df.sort_index(axis=0, inplace=True)
        df.sort_index(axis=1, inplace=True)
        df.to_csv(fp, index_label='sample_name', na_rep='', sep='\t')

    def to_dataframe(self, samples=None):
        """Returns the metadata template as a dataframe

        Parameters
        ----------
        samples : set, optional
            If supplied, only the specified samples will be written to the
            file

        Returns
        -------
        pandas DataFrame
            The metadata in the template,indexed on sample id
        """
        conn_handler = SQLConnectionHandler()
        cols = get_table_cols(self._table_name(self._id), conn_handler)
        # Get all metadata for the template. This is technically a SELECT *
        # but passing the columns will ensure the column order
        sql = "SELECT {0} FROM qiita.{1}".format(
            ','.join(cols), self._table_name(self.id))
        sql_args = None

        if samples is not None:
            sql = sql + " WHERE sample_id IN ({0})".format(
                ', '.join(['%s'] * len(samples)))
            sql_args = list(samples)

        meta = conn_handler.execute_fetchall(sql, sql_args)

        # Create the dataframe and clean it up a bit
        df = pd.DataFrame((list(x) for x in meta), columns=cols)
        df.set_index('sample_id', inplace=True, drop=True)
        return df

    def add_filepath(self, filepath, conn_handler=None):
        r"""Populates the DB tables for storing the filepath and connects the
        `self` objects with this filepath"""
        # Check that this function has been called from a subclass
        self._check_subclass()

        # Check if the connection handler has been provided. Create a new
        # one if not.
        conn_handler = conn_handler if conn_handler else SQLConnectionHandler()

        try:
            fpp_id = insert_filepaths([(filepath, self._filepath_type)], None,
                                      "templates", "filepath", conn_handler,
                                      move_files=False)[0]
            values = (self._id, fpp_id)
            sql = """INSERT INTO qiita.{0} ({1}, filepath_id)
                     VALUES (%s, %s)""".format(self._filepath_table,
                                               self._id_column)
            # If this call fails, filepaths will have been added to the DB,
            # but they're not linked to anything. However, this is not a
            # problem, as any subsequent call to purge_filepaths will remove
            # those filepaths
            conn_handler.execute(sql, values)
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

        sql = """SELECT filepath_id, filepath
                 FROM qiita.filepath
                 WHERE filepath_id IN (
                    SELECT filepath_id
                    FROM qiita.{0}
                    WHERE {1}=%s)
                ORDER BY filepath_id DESC""".format(self._filepath_table,
                                                    self._id_column)
        try:
            filepath_ids = conn_handler.execute_fetchall(sql, (self.id, ))
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
        return get_table_cols(self._table_name(self._id))
