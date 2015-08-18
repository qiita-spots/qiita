from qiita_db.sql_connection import TRN
from qiita_db.metadata_template.constants import (NA_VALUES, TRUE_VALUES,
                                                  FALSE_VALUES)

with TRN:
    bool_vals = set(TRUE_VALUES + FALSE_VALUES + [None])
    nans = tuple(NA_VALUES)
    false_vals = tuple(FALSE_VALUES)
    true_vals = tuple(TRUE_VALUES)

    sql = """SELECT table_name
             FROM information_schema.tables
             WHERE table_schema='qiita'
                AND table_name SIMILAR TO 'sample\_[0-9]+'"""
    TRN.add(sql)
    tables = [x[0] for x in TRN.execute_fetchindex()]

    cols_sql = """SELECT column_name, data_type
                  FROM information_schema.columns
                  WHERE table_name = %s"""
    alter_sql = """ALTER TABLE qiita.{0}
                   ALTER COLUMN {1} TYPE bool
                   USING CASE
                       WHEN {1} IN %s THEN FALSE
                       WHEN {1} IN %s THEN TRUE
                   END"""
    null_sql = "UPDATE qiita.{0} SET {1} = NULL WHERE {1} IN %s"

    for table in tables:
        # Change NaN values to NULL in database
        TRN.add(cols_sql, [table])
        colinfo = TRN.execute_fetchindex()
        for col, ctype in colinfo:
            if ctype == 'character varying':
                TRN.add(null_sql.format(table, col), [nans])
        TRN.execute()

        # Update now boolean columns to bool in database
        TRN.add("SELECT * FROM qiita.{}".format(table))
        col_vals = zip(*TRN.execute_fetchindex())
        cols = [x[0] for x in colinfo]
        for col, vals in zip(cols, col_vals):
            if all(v in bool_vals for v in vals):
                # Every value in the column should be bool, so do it
                TRN.add(alter_sql.format(table, col),
                        [false_vals, true_vals])
