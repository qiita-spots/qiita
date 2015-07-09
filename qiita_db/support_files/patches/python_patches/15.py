# Feb 11, 2015
# This changes all analysis files to be relative path instead of absolute

from os.path import basename, dirname

from qiita_db.util import get_mountpoint
from qiita_db.sql_connection import TRN

with TRN:
    sql = """SELECT f.*
             FROM qiita.filepath f
                JOIN qiita.analysis_filepath afp
                    ON f.filepath_id = afp.filepath_id"""
    TRN.add(sql)
    filepaths = TRN.execute_fetchindex()

    # retrieve relative filepaths as dictionary for matching
    mountpoints = {m[1].rstrip('/\\'): m[0] for m in get_mountpoint(
        'analysis', retrieve_all=True)}

    sql = """UPDATE qiita.filepath SET filepath = %s, data_directory_id = %s
             WHERE filepath_id = %s"""
    for filepath in filepaths:
        filename = basename(filepath['filepath'])
        # find the ID of the analysis filepath used
        mp_id = mountpoints[dirname(filepath['filepath']).rstrip('/\\')]
        TRN.add(sql, [filename, mp_id, filepath['filepath_id']])

    TRN.execute()
