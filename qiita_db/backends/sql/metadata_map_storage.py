#!/usr/bin/env python
from __future__ import division

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from itertools import izip
from string import lower

from .base_sql import BaseSQLStorageAPI
from .util import quote_column_name, quote_data_value, get_datatypes


class MetadataMapStorage(BaseSQLStorageAPI):
    """"""

    def insert(self, metadata_map):
        """Inserts the MetadataMap in the backend storage"""
        # Get the table name
        table_name = "study_%s_%s" % metadata_map.get_id()
        headers = metadata_map.CategoryNames()
        datatypes = get_datatypes(metadata_map)

        # Get the columns names in SQL safe
        sql_safe_column_names = [quote_column_name(h) for h in headers]

        # Get the column names paired with its datatype for SQL
        columns = []
        for column_name, datatype in izip(sql_safe_column_names, datatypes):
            columns.append('%s %s' % (column_name, datatype))
        # Get the columns in a comma-separated string
        columns = ", ".join(columns)
        # Create a table for the study
        self.conn_handler.execute("create table %s (sampleid varchar, %s)" %
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
        self.conn_handler.executemany(column_tables_sql_template,
                                      sql_args_list)

        # Add rows into the study table
        columns = ', '.join(sql_safe_column_names)
        insert_sql_template = ('insert into ' + table_name + ' (sampleid, ' +
                               columns + ') values (%s' +
                               ', %s' * len(sql_safe_column_names) + ' )')

        sql_args_list = []
        for sample_id in metadata_map.SampleIds():
            data = metadata_map.getSampleMetadata(sample_id)
            values = [scrub_data(sample_id)]
            values += [scrub_data(data[header]) for header in headers]
            sql_args_list.append(values)

        sql_executemany(insert_sql_template, sql_args_list)

    def update(self, metadata_map):
        """Updates the MetadataMap attributes in the backend storage"""
        raise NotImplementedError("MetadataMapStorage.update not implemented")

    def delete(self, md_id):
        """Deletes the MetadataMap with id=md_id from the SQL db"""
        table_name = "study_%s_%s" % md_id
        # Dropping table
        self.conn_handler.execute('drop table %s' % table_name)
        # Deleting rows from column_tables for the study
        # The query should never fail; even when there are no rows for this
        # study, the query will do nothing but complete successfully
        self.conn_handler.execute("delete from column_tables where "
                                  "table_name = %s", (table_name,))

    def search(self, searchObject):
        """Retrieves all the objects that match searchObject queries"""
        raise NotImplementedError("MetadataMapStorage.search not implemented")
