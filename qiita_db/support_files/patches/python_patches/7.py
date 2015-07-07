# 23 Nov, 2014
# This patch creates all the qiime mapping files for the existing
# prep templates

from qiita_db.util import get_mountpoint
from qiita_db.sql_connection import TRN
from qiita_db.metadata_template import PrepTemplate

with TRN:
    _id, fp_base = get_mountpoint('templates')[0]

    TRN.add("SELECT prep_template_id FROM qiita.prep_template")
    for prep_template_id in TRN.execute_fetchflatten():
        pt = PrepTemplate(prep_template_id)
        study_id = pt.study_id

        for _, fpt in pt.get_filepaths():
            pt.create_qiime_mapping_file(fpt)
