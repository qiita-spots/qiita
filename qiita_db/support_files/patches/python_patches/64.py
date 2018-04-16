# April 5, 2018
# Making sure that all parameter in the artifacts are strings

from json import dumps
from qiita_db.sql_connection import TRN

# Make sure that all validate commands have the "analysis" parameter
with TRN:
    # Get all validate commands that are missing the analysis parameter
    sql = """SELECT artifact_id, command_parameters
             FROM qiita.artifact"""
    TRN.add(sql)

    all_rows = TRN.execute_fetchindex()

sql = """UPDATE qiita.artifact
         SET command_parameters = %s
         WHERE artifact_id = %s"""
# taking the loop outside so we can have a TRN per change
for row in all_rows:
    aid, params = row

    if params is None:
        continue

    if any([isinstance(v, int) for k, v in params.items()]):
        continue

    params = {k: str(v) if isinstance(v, int) else v
              for k, v in params.items()}

    with TRN:
        TRN.add(sql, [dumps(params), aid])
        TRN.execute()
