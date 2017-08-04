# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# Mar 27, 2015
# Need to re-generate the files, given that some headers have changed

import qiita_db as qdb

with qdb.sql_connection.TRN:
    # Get all the sample templates
    qdb.sql_connection.TRN.add(
        "SELECT DISTINCT study_id from qiita.study_sample")
    study_ids = qdb.sql_connection.TRN.execute_fetchflatten()

    for s_id in study_ids:
        st = qdb.metadata_template.sample_template.SampleTemplate(s_id)
        st.generate_files()

    # Get all the prep templates
    qdb.sql_connection.TRN.add(
        "SELECT DISTINCT prep_template_id from qiita.prep_template")
    prep_ids = qdb.sql_connection.TRN.execute_fetchflatten()
    for prep_id in prep_ids:
        pt = qdb.metadata_template.prep_template.PrepTemplate(prep_id)
        pt.generate_files()
