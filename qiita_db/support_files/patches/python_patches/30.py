# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import qiita_db as qdb

st_update = set()
pr_update = set()

with qdb.sql_connection.TRN:
    sql = """SELECT table_name
             FROM information_schema.tables
             WHERE table_schema='qiita'
                AND (table_name SIMILAR TO 'sample\_[0-9]+'
                     OR table_name SIMILAR TO 'prep\_[0-9]+')"""
    qdb.sql_connection.TRN.add(sql)
    tables = qdb.sql_connection.TRN.execute_fetchflatten()

    cols_sql = """SELECT column_name
                  FROM information_schema.columns
                  WHERE table_name = %s
                  AND data_type = 'character varying'"""
    alter_sql = """ALTER TABLE qiita.{0}
                   ALTER COLUMN {1} TYPE bool
                   USING CASE
                       WHEN {1} IN %s THEN FALSE
                       WHEN {1} IN %s THEN TRUE
                   END"""
    null_sql = "UPDATE qiita.{0} SET {1} = NULL WHERE {1} IN %s"
    ssc_update_sql = """UPDATE qiita.study_sample_columns
                        SET column_type = 'bool'
                        WHERE study_id = %s AND column_name = %s"""
    pc_update_sql = """UPDATE qiita.prep_columns
                        SET column_type = 'bool'
                        WHERE prep_template_id = %s AND column_name = %s"""

    for table in tables:
        table_id = table.split("_")[1]
        # Change NaN values to NULL in database
        qdb.sql_connection.TRN.add(cols_sql, [table])
        cols = qdb.sql_connection.TRN.execute_fetchflatten()
        qdb.sql_connection.TRN.execute()

        # Update now boolean columns to bool in database
        qdb.sql_connection.TRN.add(
            "SELECT {0} FROM qiita.{1}".format(','.join(cols), table))
        col_vals = zip(*qdb.sql_connection.TRN.execute_fetchindex())
        for col, vals in zip(cols, col_vals):
            if set(vals) == {None}:
                # Ignore columns that are all NULL
                continue

    qdb.sql_connection.TRN.execute()
    for stid in st_update:
        stid = int(stid)
        qdb.metadata_template.sample_template.SampleTemplate(
            stid).generate_files()
        for pt_id in qdb.study.Study(stid).prep_templates():
            pr_update.discard(pt_id)
    for prid in pr_update:
        qdb.metadata_template.prep_template.PrepTemplate(
            int(prid)).generate_files()
