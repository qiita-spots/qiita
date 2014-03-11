"""
Objects for dealing with Qiita metadata maps

This module provides the implementation for the QiitaMetadataMap base class
using an SQL backend.

Classes
-------
- `MetadataMap` -- A Qiita Metadata map class
"""

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from itertools import izip
from string import lower
from collections import namedtuple

from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError
from .sql_connection import SQLConnectionHandler
from .util import (quote_column_name, quote_data_value, get_datatypes,
                   scrub_data)

MetadataMapId = namedtuple('MetadataMapId', ('study', 'idx'))


class MetadataMap(QiitaStatusObject):
    """
    Metadata map object that accesses an SQL backend to get the information

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

    @staticmethod
    def create(md_map, md_map_id):
        """Creates a new object with a new id on the storage system

        Parameters
        ----------
        md_map : qiime.util.MetadataMap
            The mapping file contents
        md_map_id : MetadataMapId
            The metadata map identifier
        """
        if md_map_id.idx is None:
            # If idx is not defined, generate one automatically
            # from the database
            raise QiitaDBNotImplementedError()
        # Create the MetadataMap table on the SQL system
        conn_handler = SQLConnectionHandler()
        # Get the table name
        table_name = "study_%s_%s" % md_map_id
        headers = md_map.CategoryNames
        datatypes = get_datatypes(md_map)

        # Get the columns names in SQL safe
        sql_safe_column_names = [quote_column_name(h) for h in headers]

        # Get the column names paired with its datatype for SQL
        columns = []
        for column_name, datatype in izip(sql_safe_column_names, datatypes):
            columns.append('%s %s' % (column_name, datatype))
        # Get the columns in a comma-separated string
        columns = ", ".join(columns)
        # Create a table for the study
        conn_handler.execute("create table %s (sampleid varchar, %s)" %
                             (table_name, columns))

        # Add rows to the column_tables table
        lc_table_name = lower(table_name)
        quoted_lc_table_name = quote_data_value(lc_table_name)
        column_tables_sql_template = ("insert into column_tables (column_name,"
                                      " table_name, datatype) values (%s, " +
                                      quoted_lc_table_name + ", %s)")
        # The column names should be lowercase and quoted
        quoted_lc_headers = [quote_data_value(lower(h)) for h in headers]
        # Pair up the column names with its datatype
        sql_args_list = [(column_name, datatype) for column_name, datatype in
                         izip(quoted_lc_headers, datatypes)]
        conn_handler.executemany(column_tables_sql_template,
                                 sql_args_list)

        # Add rows into the study table
        columns = ', '.join(sql_safe_column_names)
        insert_sql_template = ('insert into ' + table_name + ' (sampleid, ' +
                               columns + ') values (%s' +
                               ', %s' * len(sql_safe_column_names) + ' )')

        sql_args_list = []
        for sample_id in md_map.SampleIds:
            data = md_map.getSampleMetadata(sample_id)
            values = [scrub_data(sample_id)]
            values += [scrub_data(data[header]) for header in headers]
            sql_args_list.append(values)

        conn_handler.executemany(insert_sql_template, sql_args_list)
        return MetadataMap(md_map_id)

    @staticmethod
    def delete(id_):
        """Deletes the object `id` on the storage system

        Parameters
        ----------
        id_ : MetadataMapId
            The metadata map identifier
        """
        table_name = "study_%s_%s" % id_
        conn_handler = SQLConnectionHandler()
        # Dropping table
        conn_handler.execute('drop table %s' % table_name)
        # Deleting rows from column_tables for the study
        # The query should never fail; even when there are no rows for this
        # study, the query will do nothing but complete successfully
        conn_handler.execute("delete from column_tables where "
                             "table_name = %s", (table_name,))

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
            sample_id : string
                the sample ID to retrieve metadata for
        """
        raise QiitaDBNotImplementedError()

    def get_category_value(self, sample_id, category):
        """Returns the category value associated with a sample's category.

        The returned category value will be a string.

        Parameters
        ----------
            sample_id : string
                the sample ID to retrieve category information for
            category : string
                the category name whose value will be returned
        """
        raise QiitaDBNotImplementedError()

    def get_category_values(self, sample_ids, category):
        """Returns all the values of a given category.

        The return categories will be a list.

        Parameters
        ----------
            sample_ids : list of strings
                An ordered list of sample IDs
            category : string
                the category name whose values will be returned
        """
        raise QiitaDBNotImplementedError()

    def is_numerical_category(self, category):
        """Returns True if the category is numeric and False otherwise.

        A category is numeric if all values within the category can be
        converted to a float.

        Parameters
        ----------
            category : string
                the category that will be checked
        """
        raise QiitaDBNotImplementedError()

    def has_unique_category_values(self, category):
        """Returns True if the category's values are all unique.

        Parameters
        ----------
            category : string
                the category that will be checked for uniqueness
        """
        raise QiitaDBNotImplementedError()

    def has_single_category_values(self, category):
        """Returns True if the category's values are all the same.

        For example, the category 'Treatment' only has values 'Control' for the
        entire column.

        Parameters
        ----------
            category : string
                the category that will be checked
        """
        raise QiitaDBNotImplementedError()
