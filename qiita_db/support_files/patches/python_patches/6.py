# Nov 22, 2014
# This patch is to create all the prep/sample template files and link them in
# the database so they are present for download

from os.path import join
from time import strftime

from qiita_db.util import get_mountpoint
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.metadata_template import SampleTemplate, PrepTemplate

conn_handler = SQLConnectionHandler()

_id, fp_base = get_mountpoint('templates')[0]

for study_id in conn_handler.execute_fetchall(
        "SELECT study_id FROM qiita.study"):
    study_id = study_id[0]
    if SampleTemplate.exists(study_id):
        st = SampleTemplate(study_id)
        fp = join(fp_base, '%d_%s.txt' % (study_id, strftime("%Y%m%d-%H%M%S")))
        st.to_file(fp)
        st.add_filepath(fp)

for prep_template_id in conn_handler.execute_fetchall(
        "SELECT prep_template_id FROM qiita.prep_template"):
    prep_template_id = prep_template_id[0]
    pt = PrepTemplate(prep_template_id)
    study_id = pt.study_id

    fp = join(fp_base, '%d_prep_%d_%s.txt' % (pt.study_id, prep_template_id,
              strftime("%Y%m%d-%H%M%S")))
    pt.to_file(fp)
    pt.add_filepath(fp)
