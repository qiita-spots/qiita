# Nov 22, 2014
# This patch is to create all the prep/sample template files and link them in
# the database so they are present for download

from os.path import join
from time import strftime

from qiita_db.util import get_mountpoint
from qiita_db.sql_connection import TRN
from qiita_db.metadata_template import SampleTemplate, PrepTemplate

with TRN:
    _id, fp_base = get_mountpoint('templates')[0]

    TRN.add("SELECT study_id FROM qiita.study")
    for study_id in TRN.execute_fetchflatten():
        if SampleTemplate.exists(study_id):
            st = SampleTemplate(study_id)
            fp = join(fp_base,
                      '%d_%s.txt' % (study_id, strftime("%Y%m%d-%H%M%S")))
            st.to_file(fp)
            st.add_filepath(fp)

    TRN.add("SELECT prep_template_id FROM qiita.prep_template")
    for prep_template_id in TRN.execute_fetchflatten():
        pt = PrepTemplate(prep_template_id)
        study_id = pt.study_id

        fp = join(fp_base,
                  '%d_prep_%d_%s.txt' % (pt.study_id, prep_template_id,
                                         strftime("%Y%m%d-%H%M%S")))
        pt.to_file(fp)
        pt.add_filepath(fp)
