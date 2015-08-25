from os.path import realpath
from qiita_db.sql_connection import SQLConnectionHandler

conn = SQLConnectionHandler()
path = conn.execute_fetchone('SELECT base_data_dir FROM settings')[0]
conn.execute("UPDATE settings SET base_data_dir = %s", (realpath(path),))
