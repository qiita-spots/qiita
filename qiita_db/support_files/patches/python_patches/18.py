# March 18, 2015
# This removes study_id and processed_data_id columns from prep and sample
# template dynamic tables, if they exist
from psycopg2 import Error as PostgresError
from qiita_db.sql_connection import SQLConnectionHandler

conn_handler = SQLConnectionHandler()

# Get all sample and prep templates with offending columns
sql = """SELECT DISTINCT table_name from information_schema.columns where
    table_schema = 'qiita' AND
    (table_name SIMILAR TO '%%sample[_][0-9,]%%' OR
    table_name SIMILAR TO '%%prep[_][0-9,]%%') AND
    (column_name = 'study_id' OR column_name = 'processed_data_id')"""

tables = [c[0] for c in conn_handler.execute_fetchall(sql)]
for t in tables:
    # we know it has at least one of the columns, so drop both, and ignore
    # error if dropping non-existant column
    try:
        conn_handler.execute("ALTER TABLE qiita.%s RENAME COLUMN study_id TO "
                             "study_id_template" % t)
    except PostgresError:
        pass
    try:
        conn_handler.execute("ALTER TABLE qiita.%s RENAME COLUMN "
                             "processed_data_id TO "
                             "processed_data_id_template" % t)
    except PostgresError:
        pass
