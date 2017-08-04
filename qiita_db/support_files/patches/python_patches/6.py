# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# Nov 22, 2014
# This patch is to create all the prep/sample template files and link them in
# the database so they are present for download

from os.path import join
from time import strftime

import qiita_db as qdb

with qdb.sql_connection.TRN:
    _id, fp_base = qdb.util.get_mountpoint('templates')[0]

    qdb.sql_connection.TRN.add("SELECT study_id FROM qiita.study")
    for study_id in qdb.sql_connection.TRN.execute_fetchflatten():
        if qdb.metadata_template.sample_template.SampleTemplate.exists(
                study_id):
            st = qdb.metadata_template.sample_template.SampleTemplate(study_id)
            fp = join(fp_base,
                      '%d_%s.txt' % (study_id, strftime("%Y%m%d-%H%M%S")))
            st.to_file(fp)
            st.add_filepath(fp)

    qdb.sql_connection.TRN.add(
        "SELECT prep_template_id FROM qiita.prep_template")
    for prep_template_id in qdb.sql_connection.TRN.execute_fetchflatten():
        pt = qdb.metadata_template.prep_template.PrepTemplate(prep_template_id)
        study_id = pt.study_id

        fp = join(fp_base,
                  '%d_prep_%d_%s.txt' % (pt.study_id, prep_template_id,
                                         strftime("%Y%m%d-%H%M%S")))
        pt.to_file(fp)
        pt.add_filepath(fp)
