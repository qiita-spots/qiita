from os.path import realpath
import qiita_db as qdb

with qdb.sql_connection.TRN:
    qdb.sql_connection.TRN.add('SELECT base_data_dir FROM settings')
    path = qdb.sql_connection.TRN.execute_fetchlast()

    # if the path is non-canonical (it contains .. or other redundant symbols)
    # this will update it, else it will leave as is
    qdb.sql_connection.TRN.add(
        "UPDATE settings SET base_data_dir = %s", (realpath(path),))
    qdb.sql_connection.TRN.execute()
