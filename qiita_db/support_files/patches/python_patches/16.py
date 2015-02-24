# Feb 23, 2015
# This corrects the value in processed_data_status_id to have the same as
# the study has

from qiita_db.sql_connection import SQLConnectionHandler

conn_handler = SQLConnectionHandler()

# Retrieve all the processed data ids with its study
ids = conn_handler.execute_fetchall(
    "SELECT processed_data_id, study_id FROM qiita.study_processed_data")

sql = """UPDATE qiita.processed_data
         SET processed_data_status_id = (
            SELECT study_status_id FROM qiita.study WHERE study_id=1)
         WHERE processed_data_id = 1"""

for vals in ids:
    conn_handler.execute(sql, tuple(vals))
