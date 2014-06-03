#!/usr/bin/env python
from __future__ import division

"""
Objects for dealing with Qiita metadata templates

This module provides the MetadataTemplate base class and the classes
SampleTemplate and PrepTemplate that implement MetadataTemplate.

Classes
-------
- `MetadataTemplate` -- A Qiita Metadata template base class
- `SampleTemplate` -- A Qiita Sample template class
- `PrepTemplate` -- A Qiita Prep template class
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from future.builtins import zip
from string import lower

from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError
from .sql_connection import SQLConnectionHandler
from .util import (quote_column_name, quote_data_value, get_datatypes,
                   scrub_data)


class MetadataTemplate(QiitaStatusObject):
    """
    Metadata map object that accesses the db to get the information

    Attributes
    ----------
    sample_ids
    category_names
    metadata

    Methods
    -------
    get_sample_metadata(sample_id):
        Returns the metadata associated with a particular sample

    get_category_value(sample_id, category)
        Returns the category value associated with a sample's category

    get_category_values(sample_ids, category)
        Returns all the values of a given category.

    is_numerical_category(category)
        Returns True if the category is numeric and False otherwise

    has_unique_category_values(category)
        Returns True if the category's values are all unique

    has_single_category_values(category)
        Returns True if the category's values are all the same
    """

    # Used to find the right SQL tables - should be defined on the classes that
    # instantiate this base class
    _table_prefix = None
    _column_table = None

    @classmethod
    def _get_table_name(cls, study_id):
        """"""
        if not cls._table_prefix:
            raise QiitaDBNotImplementedError('_table_prefix should be defined '
                                             'in the classes that implement '
                                             'MetadataTemplate!')
        return "%s%d" % (cls._table_prefix, study_id)

    @classmethod
    def create(cls, md_template, study_id):
        """Creates a new object with a new id on the database

        Parameters
        ----------
        md_template : qiime.util.MetadataMap
            The template file contents
        study_id : int
            The study identifier to which the metadata template belongs to
        """
        # Create the MetadataTemplate table on the SQL system
        conn_handler = SQLConnectionHandler()
        # Get the table name
        table_name = cls._get_table_name(study_id)
        headers = md_template.CategoryNames
        datatypes = get_datatypes(md_template)

        # Get the columns names in SQL safe
        sql_safe_column_names = [quote_column_name(h) for h in headers]

        # Get the column names paired with its datatype for SQL
        columns = []
        for column_name, datatype in zip(sql_safe_column_names, datatypes):
            columns.append('%s %s' % (column_name, datatype))
        # Get the columns in a comma-separated string
        columns = ", ".join(columns)
        # Create a table for the study
        conn_handler.execute("create table qiita.%s (sampleid varchar, %s)" %
                             (table_name, columns))

        # Add rows to the column_table table
        column_tables_sql_template = ("insert into qiita." + cls._column_table
                                      + " (study_id, column_name, column_type)"
                                      " values ('" + str(study_id) +
                                      "', %s, %s)")
        # The column names should be lowercase and quoted
        quoted_lc_headers = [quote_data_value(lower(h)) for h in headers]
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
        return MetadataTemplate(study_id)

    @classmethod
    def delete(cls, study_id):
        """Deletes the metadata template attached to the study `id` from the
        database

        Parameters
        ----------
        study_id : int
            The study identifier
        """
        table_name = cls._get_table_name(study_id)
        conn_handler = SQLConnectionHandler()
        # Dropping table
        conn_handler.execute('drop table qiita.%s' % table_name)
        # Deleting rows from column_tables for the study
        # The query should never fail; even when there are no rows for this
        # study, the query will do nothing but complete successfully
        conn_handler.execute("delete from qiita." + cls._column_table +
                             " where study_id = %s", (study_id,))

    @property
    def sample_ids(self):
        """Returns the IDs of all samples in the metadata map.

        The sample IDs are returned as a list of strings in alphabetical order.
        """
        raise QiitaDBNotImplementedError()

    @property
    def category_names(self):
        """Returns the names of all categories in the metadata map.

        The category names are returned as a list of strings in alphabetical
        order.
        """
        raise QiitaDBNotImplementedError()

    @property
    def metadata(self):
        """A python dict of dicts

        The top-level key is sample ID, and the inner dict maps category name
        to category value
        """
        raise QiitaDBNotImplementedError()

    def get_sample_metadata(self, sample_id):
        """Returns the metadata associated with a particular sample.

        The metadata will be returned as a dict mapping category name to
        category value.

        Parameters
        ----------
        sample_id : str
            the sample ID to retrieve metadata for
        """
        raise QiitaDBNotImplementedError()

    def get_category_value(self, sample_id, category):
        """Returns the category value associated with a sample's category.

        The returned category value will be a string.

        Parameters
        ----------
        sample_id : str
            the sample ID to retrieve category information for
        category : str
            the category name whose value will be returned
        """
        raise QiitaDBNotImplementedError()

    def get_category_values(self, sample_ids, category):
        """Returns all the values of a given category.

        The return categories will be a list.

        Parameters
        ----------
        sample_ids : list of str
            An ordered list of sample IDs
        category : str
            the category name whose values will be returned
        """
        raise QiitaDBNotImplementedError()

    def is_numerical_category(self, category):
        """Returns True if the category is numeric and False otherwise.

        A category is numeric if all values within the category can be
        converted to a float.

        Parameters
        ----------
        category : str
            the category that will be checked
        """
        raise QiitaDBNotImplementedError()

    def has_unique_category_values(self, category):
        """Returns True if the category's values are all unique.

        Parameters
        ----------
        category : str
            the category that will be checked for uniqueness
        """
        raise QiitaDBNotImplementedError()

    def has_single_category_values(self, category):
        """Returns True if the category's values are all the same.

        For example, the category 'Treatment' only has values 'Control' for the
        entire column.

        Parameters
        ----------
        category : str
            the category that will be checked
        """
        raise QiitaDBNotImplementedError()


class SampleTemplate(MetadataTemplate):
    """"""
    _table_prefix = "sample_"
    _column_table = "study_sample_columns"


class PrepTemplate(MetadataTemplate):
    """"""
    _table_prefix = "prep_"
    _column_table = "raw_data_prep_columns"
