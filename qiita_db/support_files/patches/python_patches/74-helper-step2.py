import pandas as pd
from os.path import join, dirname, abspath, exists
from qiita_db.sql_connection import TRN


with TRN:
    sql = """SELECT filepath_id
             FROM qiita.filepath"""
    TRN.add(sql)
    fids = TRN.execute_fetchflatten()

fpath = join(dirname(abspath(__file__)), 'support_files', 'patches',
             'python_patches', '74.py.cache.tsv')
if not exists(fpath):
    raise ValueError("%s doesn't exits, have you run step 1?" % fpath)
df = pd.read_csv(fpath, sep='\t', index_col=0, dtype=str,
                 names=['filepath_id', 'checksum', 'fp_size'])
cache = df.to_dict('index')

args = []
for fid in fids:
    if fid not in cache:
        print('missing: %d', fid)
    else:
        args.append([cache[fid]['fp_size'], cache[fid]['checksum'], fid])

with TRN:
    sql = """UPDATE qiita.filepath
            SET fp_size = %s, checksum = %s
            WHERE filepath_id = %s"""
    TRN.add(sql, args, many=True)
    TRN.execute()
