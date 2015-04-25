# Mar 27, 2015
# Need to re-generate the files, given that some headers have changed

from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.metadata_template import SampleTemplate, PrepTemplate

conn_handler = SQLConnectionHandler()

# Get all the sample templates
sql = """SELECT DISTINCT study_id from qiita.study_sample"""
study_ids = {s[0] for s in conn_handler.execute_fetchall(sql)}

for s_id in study_ids:
    SampleTemplate(s_id).generate_files()

# Get all the prep templates
sql = """SELECT prep_template_id from qiita.prep_template"""
prep_ids = {p[0] for p in conn_handler.execute_fetchall(sql)}
for prep_id in prep_ids:
    PrepTemplate(prep_id).generate_files()
