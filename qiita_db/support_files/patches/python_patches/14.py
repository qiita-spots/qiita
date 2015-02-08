# Feberuary 7, 2015
# This patch recreates all the QIIME mapping files to avoid lower-upper case
# problems. See https://github.com/biocore/qiita/issues/799

from qiita_db.util import get_mountpoint
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.metadata_template import PrepTemplate

conn_handler = SQLConnectionHandler()

_id, fp_base = get_mountpoint('templates')[0]

for prep_template_id in conn_handler.execute_fetchall(
        "SELECT prep_template_id FROM qiita.prep_template"):
    prep_template_id = prep_template_id[0]
    pt = PrepTemplate(prep_template_id)
    study_id = pt.study_id

    for _, fpt in pt.get_filepaths():
        pt.create_qiime_mapping_file(fpt)
