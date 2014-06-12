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

    MetadataTemplate
    SampleTemplate
    PrepTemplate
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

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .exceptions import QiitaDBDuplicateError
from .base import QiitaObject
# from .exceptions import QiitaDBNotImplementedError
from .sql_connection import SQLConnectionHandler
from .util import scrub_data, exists_table


def _get_datatypes(metadata_map):
    """Returns the datatype of each metadata_map column

    Parameters
    ----------
    metadata_map : DataFrame
        The MetadataTemplate contents

    Returns
    -------
    list of str
        The SQL datatypes for each column, in column order
    """
    isdigit = str.isdigit
    datatypes = []

    for header in metadata_map.CategoryNames:
        column_data = [metadata_map.getCategoryValue(sample_id, header)
                       for sample_id in metadata_map.SampleIds]

        if all([isdigit(c) for c in column_data]):
            datatypes.append('int')
        elif all([isdigit(c.replace('.', '', 1)) for c in column_data]):
            datatypes.append('float8')
        else:
            datatypes.append('varchar')

    return datatypes


class Sample(QiitaObject):
    r"""Models a sample object in the database"""
    pass


class MetadataTemplate(QiitaObject):
    r"""Metadata map object that accesses the db to get the sample/prep
    template information

    Attributes
    ----------
    sample_ids
    category_names
    metadata

    Methods
    -------
    get_sample_metadata
    get_category_value
    get_category_values
    is_numerical_category
    has_unique_category_values
    has_single_category_values

    See Also
    --------
    SampleTemplate
    PrepTemplate
    """

    # Used to find the right SQL tables - should be defined on the subclasses
    _table_prefix = None
    _column_table = None
    _id_column = None

    def _check_id(self, id_, conn_handler=None):
        r""""""
        self._check_subclass()
        conn_handler = (conn_handler if conn_handler is not None
                        else SQLConnectionHandler())
        return conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE "
            "{1}=%s)".format(self._table, self._id_column),
            (id_, ))[0]

    @classmethod
    def _table_name(cls, obj):
        r"""Returns the dynamic table name

        Parameters
        ----------
        obj : Study or RawData
            The obj to which the metadata template belongs to.

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
        return "%s%d" % (cls._table_prefix, obj.id)

    @classmethod
    def create(cls, md_template, obj):
        r"""Creates the metadata template in the database

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids
        obj : Study or RawData
            The obj to which the metadata template belongs to. Study in case
            of SampleTemplate and RawData in case of PrepTemplate
        """
        # Check that we don't have a MetadataTemplate for obj
        if cls.exists(obj):
            raise QiitaDBDuplicateError(cls.__name__, obj.id)

        # Get the table name
        table_name = cls._table_name(obj)
        # Get the column headers
        headers = md_template.keys()
        # Get the data type of each column
        datatypes = _get_datatypes(md_template)
        # Get the columns names in SQL safe
        sql_safe_column_names = ['"%s"' % h.lower() for h in headers]

        # Get the column names paired with its datatype for SQL
        columns = ['%s %s' % (cn, dt)
                   for cn, dt in zip(sql_safe_column_names, datatypes)]
        # Get the columns in a comma-separated string
        columns = ", ".join(columns)
        # Create a table for the study
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(
            "create table qiita.%s (sampleid varchar, %s)" %
            (table_name, columns))

        # Add rows to the column_table table
        column_tables_sql_template = ("insert into qiita." + cls._column_table
                                      + " (study_id, column_name, column_type)"
                                      " values ('" + str(obj.id) +
                                      "', %s, %s)")
        # The column names should be lowercase and quoted
        quoted_lc_headers = [quote_data_value(h.lower()) for h in headers]
        # Pair up the column names with its datatype
        sql_args_list = [(column_name, datatype) for column_name, datatype in
                         zip(quoted_lc_headers, datatypes)]
        conn_handler.executemany(column_tables_sql_template,
                                 sql_args_list)

        # Add rows into the study table
        columns = ', '.join(sql_safe_column_names)
        insert_sql_template = ('insert into qiita.' + table_name +
                               ' (sampleid, ' + columns + ') values (%s' +
                               ', %s' * len(sql_safe_column_names) + ' )')

        sql_args_list = []
        for sample_id in md_template.SampleIds:
            data = md_template.getSampleMetadata(sample_id)
            values = [scrub_data(sample_id)]
            values += [scrub_data(data[header]) for header in headers]
            sql_args_list.append(values)

        conn_handler.executemany(insert_sql_template, sql_args_list)
        return MetadataTemplate(study.id)

    @classmethod
    def exists(cls, obj):
        r"""Checks if already exists a MetadataTemplate for the provided object

        Parameters
        ----------
        obj : QiitaObject
            The object to test if a MetadataTemplate exists for

        Returns
        -------
        bool
            True if already exists. False otherwise.
        """
        cls._check_subclass()
        return exists_table(cls._table_name(obj), SQLConnectionHandler())

    # @property
    # def sample_ids(self):
    #     r"""Returns the IDs of all samples in the metadata map.

    #     The sample IDs are returned as a list of strings in alphabetical order.
    #     """
    #     raise QiitaDBNotImplementedError()

    # @property
    # def category_names(self):
    #     r"""Returns the names of all categories in the metadata map.

    #     The category names are returned as a list of strings in alphabetical
    #     order.
    #     """
    #     raise QiitaDBNotImplementedError()

    # @property
    # def metadata(self):
    #     r"""A python dict of dicts

    #     The top-level key is sample ID, and the inner dict maps category name
    #     to category value
    #     """
    #     raise QiitaDBNotImplementedError()

    # def get_sample_metadata(self, sample_id):
    #     r"""Returns the metadata associated with a particular sample.

    #     The metadata will be returned as a dict mapping category name to
    #     category value.

    #     Parameters
    #     ----------
    #     sample_id : str
    #         the sample ID to retrieve metadata for
    #     """
    #     raise QiitaDBNotImplementedError()

    # def get_category_value(self, sample_id, category):
    #     r"""Returns the category value associated with a sample's category.

    #     The returned category value will be a string.

    #     Parameters
    #     ----------
    #     sample_id : str
    #         the sample ID to retrieve category information for
    #     category : str
    #         the category name whose value will be returned
    #     """
    #     raise QiitaDBNotImplementedError()

    # def get_category_values(self, sample_ids, category):
    #     """Returns all the values of a given category.

    #     The return categories will be a list.

    #     Parameters
    #     ----------
    #     sample_ids : list of str
    #         An ordered list of sample IDs
    #     category : str
    #         the category name whose values will be returned
    #     """
    #     raise QiitaDBNotImplementedError()

    # def is_numerical_category(self, category):
    #     """Returns True if the category is numeric and False otherwise.

    #     A category is numeric if all values within the category can be
    #     converted to a float.

    #     Parameters
    #     ----------
    #     category : str
    #         the category that will be checked
    #     """
    #     raise QiitaDBNotImplementedError()

    # def has_unique_category_values(self, category):
    #     """Returns True if the category's values are all unique.

    #     Parameters
    #     ----------
    #     category : str
    #         the category that will be checked for uniqueness
    #     """
    #     raise QiitaDBNotImplementedError()

    # def has_single_category_values(self, category):
    #     """Returns True if the category's values are all the same.

    #     For example, the category 'Treatment' only has values 'Control' for the
    #     entire column.

    #     Parameters
    #     ----------
    #     category : str
    #         the category that will be checked
    #     """
    #     raise QiitaDBNotImplementedError()


class SampleTemplate(MetadataTemplate):
    """
    """
    _table = "required_sample_info"
    _table_prefix = "sample_"
    _column_table = "study_sample_columns"
    _id_column = "study_id"


class PrepTemplate(MetadataTemplate):
    """
    """
    _table = "common_prep_info"
    _table_prefix = "prep_"
    _column_table = "raw_data_prep_columns"
    _id_column = "raw_data_id"
