# 23 Nov, 2014
# This patch creates all the qiime mapping files for the existing
# prep templates

import qiita_db as qdb

with qdb.sql_connection.TRN:
    _id, fp_base = qdb.util.get_mountpoint('templates')[0]

    qdb.sql_connection.TRN.add(
        "SELECT prep_template_id FROM qiita.prep_template")
    for prep_template_id in qdb.sql_connection.TRN.execute_fetchflatten():
        pt = qdb.metadata_template.prep_template.PrepTemplate(prep_template_id)
        study_id = pt.study_id

        for _, fpt in pt.get_filepaths():
            pt.create_qiime_mapping_file(fpt)
