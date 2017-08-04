# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# Feb 11, 2015
# This changes all analysis files to be relative path instead of absolute

from os.path import basename, dirname

import qiita_db as qdb

with qdb.sql_connection.TRN:
    sql = """SELECT f.*
             FROM qiita.filepath f
                JOIN qiita.analysis_filepath afp
                    ON f.filepath_id = afp.filepath_id"""
    qdb.sql_connection.TRN.add(sql)
    filepaths = qdb.sql_connection.TRN.execute_fetchindex()

    # retrieve relative filepaths as dictionary for matching
    mountpoints = {m[1].rstrip('/\\'): m[0] for m in qdb.util.get_mountpoint(
        'analysis', retrieve_all=True)}

    sql = """UPDATE qiita.filepath SET filepath = %s, data_directory_id = %s
             WHERE filepath_id = %s"""
    for filepath in filepaths:
        filename = basename(filepath['filepath'])
        # find the ID of the analysis filepath used
        mp_id = mountpoints[dirname(filepath['filepath']).rstrip('/\\')]
        qdb.sql_connection.TRN.add(
            sql, [filename, mp_id, filepath['filepath_id']])

    qdb.sql_connection.TRN.execute()
