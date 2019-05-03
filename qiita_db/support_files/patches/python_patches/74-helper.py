from joblib import Parallel, delayed

from os.path import getsize, exists, dirname, abspath, join
from qiita_db.util import get_filepath_information, compute_checksum
from qiita_db.sql_connection import TRN


# helper function to calculate checksum and file size
def calculate(finfo):
    try:
        size = getsize(finfo['fullpath'])
    except FileNotFoundError:
        size = 0

    try:
        checksum = compute_checksum(finfo['fullpath'])
    except FileNotFoundError:
        checksum = ''

    return finfo['filepath_id'], checksum, size


# get all filepaths and their filepath information; takes ~10 min
with TRN:
    TRN.add("SELECT filepath_id FROM qiita.filepath")
    files = []
    for fid in TRN.execute_fetchflatten():
        files.append(get_filepath_information(fid))


# just get the filepath ids that haven't been processed, the file format
# of this file is filepath_id[tab]checksum[tab]filesize
fpath = join(dirname(abspath(__file__)), '74.py.cache.tsv')
processed = []
if exists(fpath):
    with open(fpath, 'r') as f:
        processed = [int(line.split('\t')[0])
                     for line in f.read().split('\n') if line != '']
files_curr = [f for f in files if f['filepath_id'] not in processed]

# let's use 20 processor and in each iteration use 120 files
fids = 120
processors = 20
files_len = len(files_curr)
files_chunks = [files_curr[i * fids:(i + 1) * fids]
                for i in range((files_len + fids - 1) // fids)]

with Parallel(n_jobs=processors, verbose=100) as parallel:
    for fc in files_chunks:
        results = parallel(delayed(calculate)(finfo) for finfo in fc)
        with open(fpath, 'a') as f:
            f.write(
                '%s\n' % '\n'.join(['\t'.join(map(str, r)) for r in results]))
