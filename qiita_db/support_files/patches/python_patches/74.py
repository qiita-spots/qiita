import pandas as pd
from os.path import getsize, join, dirname, abspath, exists
from qiita_db.util import get_filepath_information, compute_checksum
from qiita_db.sql_connection import TRN


with TRN:
    sql = """SELECT filepath_id
             FROM qiita.filepath"""
    TRN.add(sql)
    fids = TRN.execute_fetchflatten()


fpath = join(dirname(abspath(__file__)), 'support_files', 'patches',
             'python_patches', '74.py.cache.tsv')
cache = dict()
if exists(fpath):
    df = pd.read_csv(fpath, sep='\t', index_col=0, dtype=str,
                     names=['filepath_id', 'checksum', 'fp_size'])
    cache = df.to_dict('index')

for fid in fids:
    if fid not in cache:
        finfo = get_filepath_information(fid)
        try:
            size = getsize(finfo['fullpath'])
        except FileNotFoundError:
            size = 0

        try:
            checksum = compute_checksum(finfo['fullpath'])
        except FileNotFoundError:
            checksum = ''
    else:
        checksum = cache[fid]['checksum']
        size = cache[fid]['fp_size']

    with TRN:
        sql = """UPDATE qiita.filepath
                SET fp_size = %s, checksum = %s
                WHERE filepath_id = %s"""
        TRN.add(sql, tuple([size, checksum, fid]))
        TRN.execute()
