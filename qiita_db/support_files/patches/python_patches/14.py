from qiita_db.sql_connection import SQLConnectionHandler
from os.path import basename

# This changes all analysis files to be relative path instead of absolute

conn_handler = SQLConnectionHandler()

filepaths = conn_handler.execute_fetchall(
    'SELECT f.* from qiita.filepath f JOIN qiita.analysis_filepath afp ON '
    'f.filepath_id = afp.filepath_id')
for filepath in filepaths:
    filename = basename(filepath['filepath'])
    conn_handler.execute(
        'UPDATE qiita.filepath SET filepath = %s WHERE filepath_id = %s',
        [filename, filepath['filepath_id']])