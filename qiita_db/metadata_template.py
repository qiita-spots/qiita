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
from future.builtins import zip
from future.utils import viewitems, PY3
from copy import deepcopy
from os.path import join
from time import strftime
from functools import partial
from os.path import basename
from itertools import izip
from future.utils.six import StringIO

import pandas as pd
import numpy as np
import warnings
from skbio.util import find_duplicates
from skbio.io.util import open_file

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .exceptions import (QiitaDBDuplicateError, QiitaDBColumnError,
                         QiitaDBUnknownIDError, QiitaDBNotImplementedError,
                         QiitaDBDuplicateHeaderError, QiitaDBError,
                         QiitaDBWarning, QiitaDBExecutionError)
from .base import QiitaObject
from .sql_connection import SQLConnectionHandler
from .ontology import Ontology
from .util import (exists_table, get_table_cols, get_emp_status,
                   get_required_sample_info_status, convert_to_id,
                   convert_from_id, get_mountpoint, insert_filepaths,
                   scrub_data, infer_status)
from .study import Study
from .data import RawData
from .logger import LogEntry

if PY3:
    from string import ascii_letters as letters, digits
else:
    from string import letters, digits


TARGET_GENE_DATA_TYPES = ['16S', '18S', 'ITS']
REQUIRED_TARGET_GENE_COLS = {'barcodesequence', 'linkerprimersequence',
                             'run_prefix', 'library_construction_protocol',
                             'experiment_design_description', 'platform'}
RENAME_COLS_DICT = {'barcode': 'barcodesequence',
                    'primer': 'linkerprimersequence'}


def _get_datatypes(metadata_map):
    r"""Returns the datatype of each metadata_map column

    Parameters
    ----------
    metadata_map : DataFrame
        The MetadataTemplate contents

    Returns
    -------
    list of str
        The SQL datatypes for each column, in column order
    """
    datatypes = []
    for dtype in metadata_map.dtypes:
        if dtype in [np.int8, np.int16, np.int32, np.int64]:
            datatypes.append('integer')
        elif dtype in [np.float16, np.float32, np.float64]:
            datatypes.append('float8')
        else:
            datatypes.append('varchar')
    return datatypes


def _as_python_types(metadata_map, headers):
    r"""Converts the values of metadata_map pointed by headers from numpy types
    to python types.

    Psycopg2 does not support the numpy types, so we should cast them to the
    closest python type

    Parameters
    ----------
    metadata_map : DataFrame
        The MetadataTemplate contents
    headers : list of str
        The headers of the columns of metadata_map that needs to be converted
        to a python type

    Returns
    -------
    list of lists
        The values of the columns in metadata_map pointed by headers cast to
        python types.
    """
    values = []
    for h in headers:
        # we explicitly check for cases when we have a datetime64 object
        # because otherwise doing the isinstance check against np.generic fails
        if isinstance(metadata_map[h].values[0], np.datetime64):
            values.append(list(map(pd.to_datetime, metadata_map[h])))
        elif isinstance(metadata_map[h].values[0], np.generic):
            values.append(list(map(np.asscalar, metadata_map[h])))
        else:
            values.append(list(metadata_map[h]))
    return values


def _prefix_sample_names_with_id(md_template, study_id):
    r"""prefix the sample_names in md_template with the study id

    Parameters
    ----------
    md_template : DataFrame
        The metadata template to modify
    study_id : int
        The study to which the metadata belongs to
    """
    # Get all the prefixes of the index, defined as any string before a '.'
    prefixes = {idx.split('.', 1)[0] for idx in md_template.index}
    # If the samples have been already prefixed with the study id, the prefixes
    # set will contain only one element and it will be the str representation
    # of the study id
    if len(prefixes) == 1 and prefixes.pop() == str(study_id):
        # The samples were already prefixed with the study id
        warnings.warn("Sample names were already prefixed with the study id.",
                      QiitaDBWarning)
    else:
        # Create a new pandas series in which all the values are the study_id
        # and it is indexed as the metadata template
        study_ids = pd.Series([str(study_id)] * len(md_template.index),
                              index=md_template.index)
        # Create a new column on the metadata template that includes the
        # metadata template indexes prefixed with the study id
        md_template['sample_name_with_id'] = (study_ids + '.' +
                                              md_template.index)
        md_template.index = md_template.sample_name_with_id
        del md_template['sample_name_with_id']
        # The original metadata template had the index column unnamed - remove
        # the name of the index for consistency
        md_template.index.name = None


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

    def __setitem__(self, key, value):
        r"""Sets the metadata value for the category `key`

        Parameters
        ----------
        key : str
            The metadata category
        value : obj
            The new value for the category
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


class PrepSample(BaseSample):
    r"""Class that models a sample present in a PrepTemplate.

    See Also
    --------
    BaseSample
    Sample
    """
    _table = "common_prep_info"
    _table_prefix = "prep_"
    _column_table = "prep_columns"
    _id_column = "prep_template_id"

    def _check_template_class(self, md_template):
        r"""Checks that md_template is of the correct type

        Parameters
        ----------
        md_template : PrepTemplate
            The metadata template

        Raises
        ------
        IncompetentQiitaDeveloperError
            If `md_template` is not a PrepTemplate object
        """
        if not isinstance(md_template, PrepTemplate):
            raise IncompetentQiitaDeveloperError()


class Sample(BaseSample):
    r"""Class that models a sample present in a SampleTemplate.

    See Also
    --------
    BaseSample
    PrepSample
    """
    _table = "required_sample_info"
    _table_prefix = "sample_"
    _column_table = "study_sample_columns"
    _id_column = "study_id"

    def _check_template_class(self, md_template):
        r"""Checks that md_template is of the correct type

        Parameters
        ----------
        md_template : SampleTemplate
            The metadata template

        Raises
        ------
        IncompetentQiitaDeveloperError
            If `md_template` is not a SampleTemplate object
        """
        if not isinstance(md_template, SampleTemplate):
            raise IncompetentQiitaDeveloperError()

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
        QiitaDBColumnError
            If the column does not exist in the table
        """
        conn_handler = SQLConnectionHandler()

        # try dynamic tables
        exists_dynamic = conn_handler.execute_fetchone("""
        SELECT EXISTS (
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='{0}'
                AND table_schema='qiita'
                AND column_name='{1}')""".format(self._dynamic_table,
                                                 column))[0]
        # try required_sample_info
        exists_required = conn_handler.execute_fetchone("""
        SELECT EXISTS (
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='required_sample_info'
                AND table_schema='qiita'
                AND column_name='{0}')""".format(column))[0]

        if exists_dynamic:
            # catching error so we can check if the error is due to different
            # column type or something else
            try:
                conn_handler.execute("""
                    UPDATE qiita.{0}
                    SET {1}=%s
                    WHERE sample_id=%s""".format(self._dynamic_table,
                                                 column), (value, self._id))
            except Exception as e:
                column_type = conn_handler.execute_fetchone("""
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE column_name=%s AND table_schema='qiita'
                    """, (column,))[0]
                value_type = type(value).__name__

                if column_type != value_type:
                    raise ValueError(
                        'The new value being added to column: "{0}" is "{1}" '
                        '(type: "{2}"). However, this column in the DB is of '
                        'type "{3}". Please change the value in your updated '
                        'template or reprocess your sample template.'.format(
                            column, value, value_type, column_type))
                else:
                    raise e
        elif exists_required:
            # here is not required the type check as the required fields have
            # an explicit type check
            conn_handler.execute("""
                UPDATE qiita.required_sample_info
                SET {0}=%s
                WHERE sample_id=%s
                """.format(column), (value, self._id))
        else:
            raise QiitaDBColumnError("Column %s does not exist in %s" %
                                     (column, self._dynamic_table))


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
        obj : Study or RawData
            The obj to which the metadata template belongs to. Study in case
            of SampleTemplate and RawData in case of PrepTemplate
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
        # Check that we are not instantiating the base class
        self._check_subclass()
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


class SampleTemplate(MetadataTemplate):
    r"""Represent the SampleTemplate of a study. Provides access to the
    tables in the DB that holds the sample metadata information.

    See Also
    --------
    MetadataTemplate
    PrepTemplate
    """
    _table = "required_sample_info"
    _table_prefix = "sample_"
    _column_table = "study_sample_columns"
    _id_column = "study_id"
    translate_cols_dict = {
        'required_sample_info_status_id': 'required_sample_info_status'}
    id_cols_handlers = {
        'required_sample_info_status_id': get_required_sample_info_status()}
    str_cols_handlers = {
        'required_sample_info_status_id': get_required_sample_info_status(
            key='required_sample_info_status_id')}
    _sample_cls = Sample

    @staticmethod
    def metadata_headers():
        """Returns metadata headers available

        Returns
        -------
        list
            Alphabetical list of all metadata headers available
        """
        conn_handler = SQLConnectionHandler()
        return [x[0] for x in
                conn_handler.execute_fetchall(
                "SELECT DISTINCT column_name FROM qiita.study_sample_columns "
                "UNION SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'required_sample_info' "
                "ORDER BY column_name")]

    @classmethod
    def _check_template_special_columns(cls, md_template, study_id):
        r"""Checks for special columns based on obj type

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        study_id : int
            The study to which the sample template belongs to.
        """
        return set()

    @classmethod
    def _clean_validate_template(cls, md_template, study_id,
                                 conn_handler=None):
        """Takes care of all validation and cleaning of sample templates

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        study_id : int
            The study to which the sample template belongs to.

        Returns
        -------
        md_template : DataFrame
            Cleaned copy of the input md_template
        """
        invalid_ids = get_invalid_sample_names(md_template.index)
        if invalid_ids:
            raise QiitaDBColumnError("The following sample names in the sample"
                                     " template contain invalid characters "
                                     "(only alphanumeric characters or periods"
                                     " are allowed): %s." %
                                     ", ".join(invalid_ids))
        # We are going to modify the md_template. We create a copy so
        # we don't modify the user one
        md_template = deepcopy(md_template)

        # Prefix the sample names with the study_id
        _prefix_sample_names_with_id(md_template, study_id)

        # In the database, all the column headers are lowercase
        md_template.columns = [c.lower() for c in md_template.columns]

        # Check that we don't have duplicate columns
        if len(set(md_template.columns)) != len(md_template.columns):
            raise QiitaDBDuplicateHeaderError(
                find_duplicates(md_template.columns))

        # We need to check for some special columns, that are not present on
        # the database, but depending on the data type are required.
        missing = cls._check_special_columns(md_template, study_id)

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
    def create(cls, md_template, study):
        r"""Creates the sample template in the database

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids
        study : Study
            The study to which the sample template belongs to.
        """
        cls._check_subclass()

        # Check that we don't have a MetadataTemplate for study
        if cls.exists(study.id):
            raise QiitaDBDuplicateError(cls.__name__, 'id: %d' % study.id)

        conn_handler = SQLConnectionHandler()
        queue_name = "CREATE_SAMPLE_TEMPLATE_%d" % study.id
        conn_handler.create_queue(queue_name)

        # Clean and validate the metadata template given
        md_template = cls._clean_validate_template(md_template, study.id,
                                                   conn_handler)

        # Get some useful information from the metadata template
        sample_ids = md_template.index.tolist()
        num_samples = len(sample_ids)
        headers = list(md_template.keys())

        # Get the required columns from the DB
        db_cols = get_table_cols(cls._table, conn_handler)
        # Remove the sample_id and study_id columns
        db_cols.remove('sample_id')
        db_cols.remove(cls._id_column)

        # Insert values on required columns
        values = _as_python_types(md_template, db_cols)
        values.insert(0, sample_ids)
        values.insert(0, [study.id] * num_samples)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} ({1}, sample_id, {2}) "
            "VALUES (%s, %s, {3})".format(cls._table, cls._id_column,
                                          ', '.join(db_cols),
                                          ', '.join(['%s'] * len(db_cols))),
            values, many=True)

        # Insert rows on *_columns table
        headers = list(set(headers).difference(db_cols))
        datatypes = _get_datatypes(md_template.ix[:, headers])
        # psycopg2 requires a list of tuples, in which each tuple is a set
        # of values to use in the string formatting of the query. We have all
        # the values in different lists (but in the same order) so use zip
        # to create the list of tuples that psycopg2 requires.
        values = [
            v for v in zip([study.id] * len(headers), headers, datatypes)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} ({1}, column_name, column_type) "
            "VALUES (%s, %s, %s)".format(cls._column_table, cls._id_column),
            values, many=True)

        # Create table with custom columns
        table_name = cls._table_name(study.id)
        column_datatype = ["%s %s" % (col, dtype)
                           for col, dtype in zip(headers, datatypes)]
        conn_handler.add_to_queue(
            queue_name,
            "CREATE TABLE qiita.{0} (sample_id varchar NOT NULL, {1})".format(
                table_name, ', '.join(column_datatype)))

        # Insert values on custom table
        values = _as_python_types(md_template, headers)
        values.insert(0, sample_ids)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} (sample_id, {1}) "
            "VALUES (%s, {2})".format(table_name, ", ".join(headers),
                                      ', '.join(["%s"] * len(headers))),
            values, many=True)
        conn_handler.execute_queue(queue_name)

        # figuring out the filepath of the backup
        _id, fp = get_mountpoint('templates')[0]
        fp = join(fp, '%d_%s.txt' % (study.id, strftime("%Y%m%d-%H%M%S")))
        # storing the backup
        st = cls(study.id)
        st.to_file(fp)

        # adding the fp to the object
        st.add_filepath(fp)

        return st

    @property
    def study_id(self):
        """Gets the study id with which this sample template is associated

        Returns
        -------
        int
            The ID of the study with which this sample template is associated
        """
        return self._id

    def extend(self, md_template):
        """Adds the given sample template to the current one

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids
        """
        conn_handler = SQLConnectionHandler()
        queue_name = "EXTEND_SAMPLE_TEMPLATE_%d" % self.id
        conn_handler.create_queue(queue_name)

        md_template = self._clean_validate_template(md_template, self.study_id,
                                                    conn_handler)

        # Raise warning and filter out existing samples
        sample_ids = md_template.index.tolist()
        sql = ("SELECT sample_id FROM qiita.required_sample_info WHERE "
               "study_id = %d" % self.id)
        curr_samples = set(s[0] for s in conn_handler.execute_fetchall(sql))
        existing_samples = curr_samples.intersection(sample_ids)
        if existing_samples:
            warnings.warn(
                "The following samples already exist and will be ignored: "
                "%s" % ", ".join(curr_samples.intersection(
                                 sorted(existing_samples))), QiitaDBWarning)
            md_template.drop(existing_samples, inplace=True)

        # Get some useful information from the metadata template
        sample_ids = md_template.index.tolist()
        num_samples = len(sample_ids)
        headers = list(md_template.keys())

        # Get the required columns from the DB
        db_cols = get_table_cols(self._table, conn_handler)
        # Remove the sample_id and study_id columns
        db_cols.remove('sample_id')
        db_cols.remove(self._id_column)

        # Insert values on required columns
        values = _as_python_types(md_template, db_cols)
        values.insert(0, sample_ids)
        values.insert(0, [self.study_id] * num_samples)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} ({1}, sample_id, {2}) "
            "VALUES (%s, %s, {3})".format(self._table, self._id_column,
                                          ', '.join(db_cols),
                                          ', '.join(['%s'] * len(db_cols))),
            values, many=True)

        # Add missing columns to the sample template dynamic table
        headers = list(set(headers).difference(db_cols))
        datatypes = _get_datatypes(md_template.ix[:, headers])
        table_name = self._table_name(self.study_id)
        new_cols = set(md_template.columns).difference(
            set(self.metadata_headers()))
        dtypes_dict = dict(zip(md_template.ix[:, headers], datatypes))
        for category in new_cols:
            # Insert row on *_columns table
            conn_handler.add_to_queue(
                queue_name,
                "INSERT INTO qiita.{0} ({1}, column_name, column_type) "
                "VALUES (%s, %s, %s)".format(self._column_table,
                                             self._id_column),
                (self.study_id, category, dtypes_dict[category]))
            # Insert row on dynamic table
            conn_handler.add_to_queue(
                queue_name,
                "ALTER TABLE qiita.{0} ADD COLUMN {1} {2}".format(
                    table_name, scrub_data(category), dtypes_dict[category]))

        # Insert values on custom table
        values = _as_python_types(md_template, headers)
        values.insert(0, sample_ids)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} (sample_id, {1}) "
            "VALUES (%s, {2})".format(table_name, ", ".join(headers),
                                      ', '.join(["%s"] * len(headers))),
            values, many=True)
        conn_handler.execute_queue(queue_name)

        # figuring out the filepath of the backup
        _id, fp = get_mountpoint('templates')[0]
        fp = join(fp, '%d_%s.txt' % (self.id, strftime("%Y%m%d-%H%M%S")))
        # storing the backup
        self.to_file(fp)

        # adding the fp to the object
        self.add_filepath(fp)

    def update(self, md_template):
        r"""Update values in the sample template

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids

        Raises
        ------
        QiitaDBError
            If md_template and db do not have the same sample ids
        """
        conn_handler = SQLConnectionHandler()

        # Clean and validate the metadata template given
        new_map = self._clean_validate_template(md_template, self.id,
                                                conn_handler)
        # Retrieving current metadata
        current_map = self._transform_to_dict(conn_handler.execute_fetchall(
            "SELECT * FROM qiita.{0} WHERE {1}=%s".format(self._table,
                                                          self._id_column),
            (self.id,)))
        dyn_vals = self._transform_to_dict(conn_handler.execute_fetchall(
            "SELECT * FROM qiita.{0}".format(self._table_name(self.id))))

        for k in current_map:
            current_map[k].update(dyn_vals[k])
            current_map[k].pop('study_id', None)

        # converting sql results to dataframe
        current_map = pd.DataFrame.from_dict(current_map, orient='index')

        # simple validations of sample ids
        samples_diff = set(
            new_map.index.tolist()) - set(current_map.index.tolist())
        if samples_diff:
            raise QiitaDBError('The new sample template differs from what is '
                               'stored in database by these samples names: %s'
                               % ', '.join(samples_diff))
        columns_diff = set(new_map.columns) - set(current_map.columns)
        if columns_diff:
            queue = 'add_cols_%d' % self._id
            datatypes = dict(izip(new_map.columns, _get_datatypes(new_map)))
            conn_handler.create_queue(queue)

            for col in columns_diff:
                self.add_category(col, new_map[col].to_dict(), datatypes[col])
                new_map.drop(col, axis=1, inplace=True)

            warnings.warn('Added the following metadata columns: %s' %
                          ', '.join(columns_diff))

        # here we are comparing two dataframes following:
        # http://stackoverflow.com/a/17095620/4228285
        current_map.sort(axis=0, inplace=True)
        current_map.sort(axis=1, inplace=True)
        new_map.sort(axis=0, inplace=True)
        new_map.sort(axis=1, inplace=True)
        map_diff = (current_map != new_map).stack()
        map_diff = map_diff[map_diff]
        map_diff.index.names = ['id', 'column']
        changed_cols = map_diff.index.get_level_values('column').unique()

        for col in changed_cols:
            self.update_category(col, new_map[col].to_dict())

        # figuring out the filepath of the backup
        _id, fp = get_mountpoint('templates')[0]
        fp = join(fp, '%d_%s.txt' % (self.id, strftime("%Y%m%d-%H%M%S")))
        # storing the backup
        self.to_file(fp)

        # adding the fp to the object
        self.add_filepath(fp)

        # generating all new QIIME mapping files
        for rd_id in Study(self.id).raw_data():
            for pt_id in RawData(rd_id).prep_templates:
                pt = PrepTemplate(pt_id)
                for _, fp in pt.get_filepaths():
                    # the difference between a prep and a qiime template is the
                    # word qiime within the name of the file
                    if '_qiime_' not in basename(fp):
                        pt.create_qiime_mapping_file(fp)

    def remove_category(self, category):
        """Remove a category from the sample template

        Parameters
        ----------
        category : str
            The category to remove

        Raises
        ------
        QiitaDBColumnError
            If the column does not exist in the table
        """
        table_name = self._table_name(self.study_id)

        if category not in self.categories():
            raise QiitaDBColumnError("Column %s does not exist in %s" %
                                     (category, table_name))
        conn_handler = SQLConnectionHandler()
        queue = 'rem_col_%d' % self._id
        conn_handler.create_queue(queue)
        # This operation may invalidate another user's perspective on the
        # table
        conn_handler.add_to_queue(queue, """
            ALTER TABLE qiita.{0} DROP COLUMN {1}""".format(table_name,
                                                            category))
        conn_handler.add_to_queue(queue, """
            DELETE FROM qiita.{0} WHERE
            {1} = %s AND column_name = %s""".format(
            self._column_table, self._id_column),
            (self.study_id, category))
        conn_handler.execute_queue(queue)

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
        if not set(self.keys()).issuperset(samples_and_values):
            missing = set(self.keys()) - set(samples_and_values)
            table_name = self._table_name(self.study_id)
            raise QiitaDBUnknownIDError(missing, table_name)

        for k, v in viewitems(samples_and_values):
            sample = self[k]
            sample[category] = v

    def add_category(self, category, samples_and_values, dtype, default=None):
        """Add a metadata category

        Parameters
        ----------
        category : str
            The category to add
        samples_and_values : dict
            A mapping of {sample_id: value}
        dtype : str
            The datatype of the column
        default : object, optional
            The default value associated with the column. If given, the column
            will be added as "NOT NULL".

        Raises
        ------
        QiitaDBDuplicateError
            If the column already exists
        """
        table_name = self._table_name(self.study_id)

        if category in self.categories():
            raise QiitaDBDuplicateError(category, "N/A")
        conn_handler = SQLConnectionHandler()
        queue = 'add_col_%d' % self._id
        conn_handler.create_queue(queue)

        # add the column to the sample template
        sql = """ALTER TABLE qiita.{0}
            ADD COLUMN {1} {2}""".format(table_name, category, dtype)
        sql_args = None
        if default is not None:
                sql = sql + " NOT NULL DEFAULT %s"
                sql_args = [default]
        conn_handler.add_to_queue(queue, sql, sql_args)

        # add the column to the column listings table
        conn_handler.add_to_queue(
            queue,
            "INSERT INTO qiita.{0} ({1}, column_name, column_type) "
            "VALUES (%s, %s, %s)".format(self._column_table, self._id_column),
            (self.study_id, category, dtype))
        conn_handler.execute_queue(queue)

        self.update_category(category, samples_and_values)


class PrepTemplate(MetadataTemplate):
    r"""Represent the PrepTemplate of a raw data. Provides access to the
    tables in the DB that holds the sample preparation information.

    See Also
    --------
    MetadataTemplate
    SampleTemplate
    """
    _table = "common_prep_info"
    _table_prefix = "prep_"
    _column_table = "prep_columns"
    _id_column = "prep_template_id"
    translate_cols_dict = {'emp_status_id': 'emp_status'}
    id_cols_handlers = {'emp_status_id': get_emp_status()}
    str_cols_handlers = {'emp_status_id': get_emp_status(key='emp_status_id')}
    _sample_cls = PrepSample

    @classmethod
    def create(cls, md_template, raw_data, study, data_type,
               investigation_type=None):
        r"""Creates the metadata template in the database

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids
        raw_data : RawData
            The raw_data to which the prep template belongs to.
        study : Study
            The study to which the prep template belongs to.
        data_type : str or int
            The data_type of the prep template
        investigation_type : str, optional
            The investigation type, if relevant

        Returns
        -------
        A new instance of `cls` to access to the PrepTemplate stored in the DB

        Raises
        ------
        QiitaDBColumnError
            If the investigation_type is not valid
            If a required column is missing in md_template
        """
        # If the investigation_type is supplied, make sure it is one of
        # the recognized investigation types
        if investigation_type is not None:
            cls.validate_investigation_type(investigation_type)

        invalid_ids = get_invalid_sample_names(md_template.index)
        if invalid_ids:
            raise QiitaDBColumnError("The following sample names in the prep"
                                     " template contain invalid characters "
                                     "(only alphanumeric characters or periods"
                                     " are allowed): %s." %
                                     ", ".join(invalid_ids))

        # We are going to modify the md_template. We create a copy so
        # we don't modify the user one
        md_template = deepcopy(md_template)

        # Prefix the sample names with the study_id
        _prefix_sample_names_with_id(md_template, study.id)

        # In the database, all the column headers are lowercase
        md_template.columns = [c.lower() for c in md_template.columns]

        # Check that we don't have duplicate columns
        if len(set(md_template.columns)) != len(md_template.columns):
            raise QiitaDBDuplicateHeaderError(
                find_duplicates(md_template.columns))

        # Get a connection handler
        conn_handler = SQLConnectionHandler()
        queue_name = "CREATE_PREP_TEMPLATE_%d" % raw_data.id
        conn_handler.create_queue(queue_name)

        # Check if the data_type is the id or the string
        if isinstance(data_type, (int, long)):
            data_type_id = data_type
            data_type_str = convert_from_id(data_type, "data_type",
                                            conn_handler)
        else:
            data_type_id = convert_to_id(data_type, "data_type", conn_handler)
            data_type_str = data_type

        # We need to check for some special columns, that are not present on
        # the database, but depending on the data type are required.
        missing = cls._check_special_columns(md_template, data_type_str)

        # Get some useful information from the metadata template
        sample_ids = md_template.index.tolist()
        num_samples = len(sample_ids)

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

        # Insert the metadata template
        # We need the prep_id for multiple calls below, which currently is not
        # supported by the queue system. Thus, executing this outside the queue
        prep_id = conn_handler.execute_fetchone(
            "INSERT INTO qiita.prep_template (data_type_id, raw_data_id, "
            "investigation_type) VALUES (%s, %s, %s) RETURNING "
            "prep_template_id", (data_type_id, raw_data.id,
                                 investigation_type))[0]

        # Insert values on required columns
        values = _as_python_types(md_template, db_cols)
        values.insert(0, sample_ids)
        values.insert(0, [prep_id] * num_samples)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} ({1}, sample_id, {2}) "
            "VALUES (%s, %s, {3})".format(
                cls._table, cls._id_column, ', '.join(db_cols),
                ', '.join(['%s'] * len(db_cols))),
            values, many=True)

        # Insert rows on *_columns table
        headers = list(set(headers).difference(db_cols))
        datatypes = _get_datatypes(md_template.ix[:, headers])
        # psycopg2 requires a list of tuples, in which each tuple is a set
        # of values to use in the string formatting of the query. We have all
        # the values in different lists (but in the same order) so use zip
        # to create the list of tuples that psycopg2 requires.
        values = [
            v for v in zip([prep_id] * len(headers), headers, datatypes)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} ({1}, column_name, column_type) "
            "VALUES (%s, %s, %s)".format(cls._column_table, cls._id_column),
            values, many=True)

        # Create table with custom columns
        table_name = cls._table_name(prep_id)
        column_datatype = ["%s %s" % (col, dtype)
                           for col, dtype in zip(headers, datatypes)]
        conn_handler.add_to_queue(
            queue_name,
            "CREATE TABLE qiita.{0} (sample_id varchar, "
            "{1})".format(table_name, ', '.join(column_datatype)))

        # Insert values on custom table
        values = _as_python_types(md_template, headers)
        values.insert(0, sample_ids)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} (sample_id, {1}) "
            "VALUES (%s, {2})".format(table_name, ", ".join(headers),
                                      ', '.join(["%s"] * len(headers))),
            values, many=True)

        try:
            conn_handler.execute_queue(queue_name)
        except Exception:
            # Clean up row from qiita.prep_template
            conn_handler.execute(
                "DELETE FROM qiita.prep_template where "
                "{0} = %s".format(cls._id_column), (prep_id,))

            # Check if sample IDs present here but not in sample template
            sql = ("SELECT sample_id from qiita.required_sample_info WHERE "
                   "study_id = %s")
            # Get list of study sample IDs, prep template study IDs,
            # and their intersection
            prep_samples = set(md_template.index.values)
            unknown_samples = prep_samples.difference(
                s[0] for s in conn_handler.execute_fetchall(sql, [study.id]))
            if unknown_samples:
                raise QiitaDBExecutionError(
                    'Samples found in prep template but not sample template: '
                    '%s' % ', '.join(unknown_samples))

            # some other error we haven't seen before so raise it
            raise

        # figuring out the filepath of the backup
        _id, fp = get_mountpoint('templates')[0]
        fp = join(fp, '%d_prep_%d_%s.txt' % (study.id, prep_id,
                  strftime("%Y%m%d-%H%M%S")))
        # storing the backup
        pt = cls(prep_id)
        pt.to_file(fp)

        # adding the fp to the object
        pt.add_filepath(fp)

        # creating QIIME mapping file
        pt.create_qiime_mapping_file(fp)

        return pt

    @classmethod
    def validate_investigation_type(self, investigation_type):
        """Simple investigation validation to avoid code duplication

        Parameters
        ----------
        investigation_type : str
            The investigation type, should be part of the ENA ontology

        Raises
        -------
        QiitaDBColumnError
            The investigation type is not in the ENA ontology
        """
        ontology = Ontology(convert_to_id('ENA', 'ontology'))
        terms = ontology.terms + ontology.user_defined_terms
        if investigation_type not in terms:
            raise QiitaDBColumnError("'%s' is Not a valid investigation_type. "
                                     "Choose from: %s" % (investigation_type,
                                                          ', '.join(terms)))

    @classmethod
    def _check_template_special_columns(cls, md_template, data_type):
        r"""Checks for special columns based on obj type

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        data_type : str
            The data_type of the template.

        Returns
        -------
        set
            The set of missing columns

        Notes
        -----
        Sometimes people use different names for the same columns. We just
        rename them to use the naming that we expect, so this is normalized
        across studies.
        """
        # We only have column requirements if the data type of the raw data
        # is one of the target gene types
        missing_cols = set()
        if data_type in TARGET_GENE_DATA_TYPES:
            md_template.rename(columns=RENAME_COLS_DICT, inplace=True)

            # Check for all required columns for target genes studies
            missing_cols = REQUIRED_TARGET_GENE_COLS.difference(
                md_template.columns)

        return missing_cols

    @classmethod
    def delete(cls, id_):
        r"""Deletes the table from the database

        Parameters
        ----------
        id_ : obj
            The object identifier

        Raises
        ------
        QiitaDBExecutionError
            If the prep template already has a preprocessed data
        QiitaDBUnknownIDError
            If no prep template with id = id_ exists
        """
        table_name = cls._table_name(id_)
        conn_handler = SQLConnectionHandler()

        if not cls.exists(id_):
            raise QiitaDBUnknownIDError(id_, cls.__name__)

        preprocessed_data_exists = conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.prep_template_preprocessed_data"
            " WHERE prep_template_id=%s)", (id_,))[0]

        if preprocessed_data_exists:
            raise QiitaDBExecutionError("Cannot remove prep template %d "
                                        "because a preprocessed data has been"
                                        " already generated using it." % id_)

        # Delete the prep template filepaths
        conn_handler.execute(
            "DELETE FROM qiita.prep_template_filepath WHERE "
            "prep_template_id = %s", (id_, ))

        # Drop the prep_X table
        conn_handler.execute(
            "DROP TABLE qiita.{0}".format(table_name))

        # Remove the rows from common_prep_info
        conn_handler.execute(
            "DELETE FROM qiita.{0} where {1} = %s".format(cls._table,
                                                          cls._id_column),
            (id_,))

        # Remove the rows from prep_columns
        conn_handler.execute(
            "DELETE FROM qiita.{0} where {1} = %s".format(cls._column_table,
                                                          cls._id_column),
            (id_,))

        # Remove the row from prep_template
        conn_handler.execute(
            "DELETE FROM qiita.prep_template where "
            "{0} = %s".format(cls._id_column), (id_,))

    def data_type(self, ret_id=False):
        """Returns the data_type or the data_type id

        Parameters
        ----------
        ret_id : bool, optional
            If true, return the id instead of the string, default false.

        Returns
        -------
        str or int
            string value of data_type or data_type_id if ret_id is True
        """
        ret = "_id" if ret_id else ""
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT d.data_type{0} FROM qiita.data_type d JOIN "
            "qiita.prep_template p ON p.data_type_id = d.data_type_id WHERE "
            "p.prep_template_id=%s".format(ret), (self.id,))[0]

    @property
    def raw_data(self):
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT raw_data_id FROM qiita.prep_template "
            "WHERE prep_template_id=%s", (self.id,))[0]

    @property
    def preprocessed_data(self):
        conn_handler = SQLConnectionHandler()
        prep_datas = conn_handler.execute_fetchall(
            "SELECT preprocessed_data_id FROM "
            "qiita.prep_template_preprocessed_data WHERE prep_template_id=%s",
            (self.id,))
        return [x[0] for x in prep_datas]

    @property
    def preprocessing_status(self):
        r"""Tells if the data has been preprocessed or not

        Returns
        -------
        str
            One of {'not_preprocessed', 'preprocessing', 'success', 'failed'}
        """
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT preprocessing_status FROM qiita.prep_template "
            "WHERE {0}=%s".format(self._id_column), (self.id,))[0]

    @preprocessing_status.setter
    def preprocessing_status(self, state):
        r"""Update the preprocessing status

        Parameters
        ----------
        state : str, {'not_preprocessed', 'preprocessing', 'success', 'failed'}
            The current status of preprocessing

        Raises
        ------
        ValueError
            If the state is not known.
        """
        if (state not in ('not_preprocessed', 'preprocessing', 'success') and
                not state.startswith('failed:')):
            raise ValueError('Unknown state: %s' % state)

        conn_handler = SQLConnectionHandler()

        conn_handler.execute(
            "UPDATE qiita.prep_template SET preprocessing_status = %s "
            "WHERE {0} = %s".format(self._id_column),
            (state, self.id))

    @property
    def investigation_type(self):
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT investigation_type FROM qiita.prep_template "
               "WHERE {0} = %s".format(self._id_column))
        return conn_handler.execute_fetchone(sql, [self._id])[0]

    @investigation_type.setter
    def investigation_type(self, investigation_type):
        r"""Update the investigation type

        Parameters
        ----------
        investigation_type : str
            The investigation type to set, should be part of the ENA ontology

        Raises
        ------
        QiitaDBColumnError
            If the investigation type is not a valid ENA ontology
        """
        if investigation_type is not None:
            self.validate_investigation_type(investigation_type)

        conn_handler = SQLConnectionHandler()

        conn_handler.execute(
            "UPDATE qiita.prep_template SET investigation_type = %s "
            "WHERE {0} = %s".format(self._id_column),
            (investigation_type, self.id))

    @property
    def study_id(self):
        """Gets the study id with which this prep template is associated

        Returns
        -------
        int
            The ID of the study with which this prep template is associated
        """
        conn = SQLConnectionHandler()
        sql = ("SELECT srd.study_id FROM qiita.prep_template pt JOIN "
               "qiita.study_raw_data srd ON pt.raw_data_id = srd.raw_data_id "
               "WHERE prep_template_id = %d" % self.id)
        study_id = conn.execute_fetchone(sql)
        if study_id:
            return study_id[0]
        else:
            raise QiitaDBError("No studies found associated with prep "
                               "template ID %d" % self._id)

    def create_qiime_mapping_file(self, prep_template_fp):
        """This creates the QIIME mapping file and links it in the db.

        Parameters
        ----------
        prep_template_fp : str
            The prep template filepath that should be concatenated to the
            sample template go used to generate a new  QIIME mapping file

        Returns
        -------
        filepath : str
            The filepath of the created QIIME mapping file

        Raises
        ------
        ValueError
            If the prep template is not a subset of the sample template
        """
        rename_cols = {
            'barcode': 'BarcodeSequence',
            'barcodesequence': 'BarcodeSequence',
            'primer': 'LinkerPrimerSequence',
            'linkerprimersequence': 'LinkerPrimerSequence',
            'description': 'Description',
        }

        # getting the latest sample template
        _, sample_template_fp = SampleTemplate(
            self.study_id).get_filepaths()[0]

        # reading files via pandas
        st = load_template_to_dataframe(sample_template_fp)
        pt = load_template_to_dataframe(prep_template_fp)
        st_sample_names = set(st.index)
        pt_sample_names = set(pt.index)

        if not pt_sample_names.issubset(st_sample_names):
            raise ValueError(
                "Prep template is not a sub set of the sample template, files:"
                "%s %s - samples: %s" % (sample_template_fp, prep_template_fp,
                                         str(pt_sample_names-st_sample_names)))

        mapping = pt.join(st, lsuffix="_prep")
        mapping.rename(columns=rename_cols, inplace=True)

        # Gets the orginal mapping columns and readjust the order to comply
        # with QIIME requirements
        cols = mapping.columns.values.tolist()
        cols.remove('BarcodeSequence')
        cols.remove('LinkerPrimerSequence')
        cols.remove('Description')
        new_cols = ['BarcodeSequence', 'LinkerPrimerSequence']
        new_cols.extend(cols)
        new_cols.append('Description')
        mapping = mapping[new_cols]

        # figuring out the filepath for the QIIME map file
        _id, fp = get_mountpoint('templates')[0]
        filepath = join(fp, '%d_prep_%d_qiime_%s.txt' % (self.study_id,
                        self.id, strftime("%Y%m%d-%H%M%S")))

        # Save the mapping file
        mapping.to_csv(filepath, index_label='#SampleID', na_rep='unknown',
                       sep='\t')

        # adding the fp to the object
        self.add_filepath(filepath)

        return filepath

    @property
    def status(self):
        """The status of the prep template

        Returns
        -------
        str
            The status of the prep template

        Notes
        -----
        The status of a prep template is inferred by the status of the
        processed data generated from this prep template. If no processed
        data has been generated with this prep template; then the status
        is 'sandbox'.
        """
        conn_handler = SQLConnectionHandler()
        sql = """SELECT processed_data_status
                FROM qiita.processed_data_status pds
                  JOIN qiita.processed_data pd
                    USING (processed_data_status_id)
                  JOIN qiita.preprocessed_processed_data ppd_pd
                    USING (processed_data_id)
                  JOIN qiita.prep_template_preprocessed_data pt_ppd
                    USING (preprocessed_data_id)
                WHERE pt_ppd.prep_template_id=%s"""
        pd_statuses = conn_handler.execute_fetchall(sql, (self._id,))

        return infer_status(pd_statuses)


def load_template_to_dataframe(fn, strip_whitespace=True):
    """Load a sample or a prep template into a data frame

    Parameters
    ----------
    fn : str or file-like object
        filename of the template to load, or an already open template file
    strip_whitespace : bool, optional
        Defaults to True. Whether or not to strip whitespace from values in the
        input file

    Returns
    -------
    DataFrame
        Pandas dataframe with the loaded information

    Raises
    ------
    ValueError
        Empty file passed
    QiitaDBColumnError
        If the sample_name column is not present in the template.
        If there's a value in one of the reserved columns that cannot be cast
        to the needed type.
    QiitaDBWarning
        When columns are dropped because they have no content for any sample.

    Notes
    -----
    The index attribute of the DataFrame will be forced to be 'sample_name'
    and will be cast to a string. Additionally rows that start with a '\t'
    character will be ignored and columns that are empty will be removed. Empty
    sample names will be removed from the DataFrame.

    The following table describes the data type per column that will be
    enforced in `fn`. Column names are case-insensitive but will be lowercased
    on addition to the database.

    +-----------------------+--------------+
    |      Column Name      |  Python Type |
    +=======================+==============+
    |           sample_name |          str |
    +-----------------------+--------------+
    |     physical_location |          str |
    +-----------------------+--------------+
    | has_physical_specimen |         bool |
    +-----------------------+--------------+
    |    has_extracted_data |         bool |
    +-----------------------+--------------+
    |           sample_type |          str |
    +-----------------------+--------------+
    |       host_subject_id |          str |
    +-----------------------+--------------+
    |           description |          str |
    +-----------------------+--------------+
    |              latitude |        float |
    +-----------------------+--------------+
    |             longitude |        float |
    +-----------------------+--------------+
    """
    # Load in file lines
    holdfile = None
    with open_file(fn) as f:
        holdfile = f.readlines()
    if not holdfile:
        raise ValueError('Empty file passed!')

    # Strip all values in the cells in the input file, if requested
    if strip_whitespace:
        for pos, line in enumerate(holdfile):
            holdfile[pos] = '\t'.join(d.strip(" \r\x0b\x0c")
                                      for d in line.split('\t'))

    # get and clean the required columns
    reqcols = set(get_table_cols("required_sample_info"))
    reqcols.add('sample_name')
    reqcols.add('required_sample_info_status')
    reqcols.discard('required_sample_info_status_id')
    # clean all the column names
    cols = holdfile[0].split('\t')
    holdfile[0] = '\t'.join(c.lower() if c.lower() in reqcols else c
                            for c in cols)
    # index_col:
    #   is set as False, otherwise it is cast as a float and we want a string
    # keep_default:
    #   is set as False, to avoid inferring empty/NA values with the defaults
    #   that Pandas has.
    # na_values:
    #   the values that should be considered as empty, in this case only empty
    #   strings.
    # converters:
    #   ensure that sample names are not converted into any other types but
    #   strings and remove any trailing spaces. Don't let pandas try to guess
    #   the dtype of the other columns, force them to be a str.
    # comment:
    #   using the tab character as "comment" we remove rows that are
    #   constituted only by delimiters i. e. empty rows.
    template = pd.read_csv(StringIO(''.join(holdfile)), sep='\t',
                           infer_datetime_format=True,
                           keep_default_na=False, na_values=[''],
                           parse_dates=True, index_col=False, comment='\t',
                           mangle_dupe_cols=False, converters={
                               'sample_name': lambda x: str(x).strip(),
                               # required_sample_info
                               'physical_location': str,
                               'sample_type': str,
                               # collection_timestamp is not added here
                               'host_subject_id': str,
                               'description': str,
                               # common_prep_info
                               'center_name': str,
                               'center_projct_name': str})

    # let pandas infer the dtypes of these columns, if the inference is
    # not correct, then we have to raise an error
    columns_to_dtype = [(['latitude', 'longitude'], (np.int, np.float),
                         'integer or decimal'),
                        (['has_physical_specimen', 'has_extracted_data'],
                         np.bool_, 'boolean')]
    for columns, c_dtype, english_desc in columns_to_dtype:
        for n in columns:
            if n in template.columns and not all([isinstance(val, c_dtype)
                                                  for val in template[n]]):
                raise QiitaDBColumnError("The '%s' column includes values "
                                         "that cannot be cast into a %s "
                                         "value " % (n, english_desc))

    initial_columns = set(template.columns)

    if 'sample_name' not in template.columns:
        raise QiitaDBColumnError("The 'sample_name' column is missing from "
                                 "your template, this file cannot be parsed.")

    # remove rows that have no sample identifier but that may have other data
    # in the rest of the columns
    template.dropna(subset=['sample_name'], how='all', inplace=True)

    # set the sample name as the index
    template.set_index('sample_name', inplace=True)

    # it is not uncommon to find templates that have empty columns
    template.dropna(how='all', axis=1, inplace=True)

    initial_columns.remove('sample_name')
    dropped_cols = initial_columns - set(template.columns)
    if dropped_cols:
        warnings.warn('The following column(s) were removed from the template '
                      'because all their values are empty: '
                      '%s' % ', '.join(dropped_cols), QiitaDBWarning)

    return template


def get_invalid_sample_names(sample_names):
    """Get a list of sample names that are not QIIME compliant

    Parameters
    ----------
    sample_names : iterable
        Iterable containing the sample names to check.

    Returns
    -------
    list
        List of str objects where each object is an invalid sample name.

    References
    ----------
    .. [1] QIIME File Types documentaiton:
    http://qiime.org/documentation/file_formats.html#mapping-file-overview.
    """

    # from the QIIME mapping file documentation
    valid = set(letters+digits+'.')
    inv = []

    for s in sample_names:
        if set(s) - valid:
            inv.append(s)

    return inv
