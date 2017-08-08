# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_db.sql_connection import TRN


# Due to the size of these changes we will
with TRN:
    # select all table and column names from all sample template
    sql = """SELECT DISTINCT table_name FROM information_schema.columns
                WHERE (table_name LIKE 'sample_%'
                       OR table_name LIKE 'prep_%')
                    AND table_name NOT LIKE '%template%'"""
    TRN.add(sql)

    all_tables = TRN.execute_fetchflatten()

for table in all_tables:
    with TRN:
        sql = """SELECT column_name FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY column_name"""
        TRN.add(sql, [table])

        for column in TRN.execute_fetchflatten():
            sql = "ALTER TABLE qiita.%s ALTER COLUMN %s TYPE VARCHAR" % (
                table, column)
            TRN.add(sql)

        TRN.execute()
