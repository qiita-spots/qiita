from qiita_db.sql_connection import TRN
from qiita_db.metadata_template.constants import (NA_VALUES, TRUE_VALUES,
                                                  FALSE_VALUES)
from qiita_db.metadata_template import SampleTemplate, PrepTemplate
from qiita_db.study import Study
from qiita_db.data import RawData

bool_vals = set(TRUE_VALUES + FALSE_VALUES + [None])
na_vals = set(NA_VALUES)

nans = tuple(NA_VALUES)
false_vals = tuple(FALSE_VALUES)
true_vals = tuple(TRUE_VALUES)

st_update = set()
pr_update = set()

with TRN:
    sql = """SELECT table_name
             FROM information_schema.tables
             WHERE table_schema='qiita'
                AND (table_name SIMILAR TO 'sample\_[0-9]+'
                     OR table_name SIMILAR TO 'prep\_[0-9]+')"""
    TRN.add(sql)
    tables = TRN.execute_fetchflatten()

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
        TRN.add(cols_sql, [table])
        cols = TRN.execute_fetchflatten()
        for col in cols:
                TRN.add(null_sql.format(table, col), [nans])
        TRN.execute()

        # Update now boolean columns to bool in database
        TRN.add("SELECT {0} FROM qiita.{1}".format(','.join(cols), table))
        col_vals = zip(*TRN.execute_fetchindex())
        for col, vals in zip(cols, col_vals):
            if set(vals) == {None}:
                # Ignore columns that are all NULL
                continue
            if all([v in bool_vals for v in vals]):
                # Every value in the column should be bool, so do it
                TRN.add(alter_sql.format(table, col),
                        [false_vals, true_vals])
                if "sample" in table:
                    st_update.add(table_id)
                    TRN.add(ssc_update_sql, [table_id, col])
                else:
                    pr_update.add(table_id)
                    TRN.add(pc_update_sql, [table_id, col])

        TRN.execute()
        for stid in st_update:
            SampleTemplate(int(stid)).generate_files()
            for rd_id in Study(int(stid)).raw_data():
                for pt_id in RawData(rd_id).prep_templates:
                    pr_update.discard(pt_id)
        for prid in pr_update:
            PrepTemplate(int(prid)).generate_files()
