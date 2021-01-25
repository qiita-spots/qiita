from os.path import basename

from qiita_db.sql_connection import TRN
from qiita_db.study import Study


for study in Study.iter():
    for pt in study.prep_templates():
        filepaths = pt.get_filepaths()
        if filepaths:
            # filepaths are returned in order so we can take the
            # oldest and newest; then we get the filename and parse the
            # creation time. Note that the filename comes in one of these
            # formats: 1_prep_1_qiime_19700101-000000.txt or
            # 1_prep_1_19700101-000000.txt
            oldest = basename(filepaths[-1][1])[-19:-4].replace('-', ' ')
            newest = basename(filepaths[0][1])[-19:-4].replace('-', ' ')

            with TRN:
                sql = """UPDATE qiita.prep_template
                         SET creation_timestamp = %s,
                             modification_timestamp = %s
                         WHERE prep_template_id = %s"""
                TRN.add(sql, [oldest, newest, pt.id])
                TRN.execute()
