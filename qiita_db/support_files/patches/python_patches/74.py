from os.path import getsize
from qiita_db.util import get_filepath_information, compute_checksum
from qiita_db.sql_connection import TRN


with TRN:
    sql = """SELECT filepath_id
             FROM qiita.filepath"""
    TRN.add(sql)
    fids = TRN.execute_fetchflatten()

for fid in fids:
    finfo = get_filepath_information(fid)

    try:
        size = getsize(finfo['fullpath'])
    except FileNotFoundError:
        size = 0

    try:
        checksum = compute_checksum(finfo['fullpath'])
    except FileNotFoundError:
        checksum = ''

    with TRN:
        sql = """UPDATE qiita.filepath
                SET fp_size = %s, checksum = %s
                WHERE filepath_id = %s"""
        TRN.add(sql, tuple([size, checksum, fid]))
        TRN.execute()
