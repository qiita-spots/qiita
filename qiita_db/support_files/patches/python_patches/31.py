from os.path import realpath
from qiita_db.sql_connection import TRN

with TRN:
    TRN.add('SELECT base_data_dir FROM settings')
    path = TRN.execute_fetchlast()

    # if the path is non-canonical (it contains .. or other redundant symbols)
    # this will update it, else it will leave as is
    TRN.add("UPDATE settings SET base_data_dir = %s", (realpath(path),))
    TRN.execute()
