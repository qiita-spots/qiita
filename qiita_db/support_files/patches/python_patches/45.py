# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from future.utils import viewitems

from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.sql_connection import TRN

with TRN:
    # a few notes: just getting the preps with duplicated values; ignoring
    # column 'sample_id' and tables 'study_sample', 'prep_template',
    # 'prep_template_sample'
    sql = """SELECT table_name, array_agg(column_name::text)
                FROM information_schema.columns
                WHERE column_name IN %s
                    AND column_name != 'sample_id'
                    AND table_name LIKE 'prep_%%'
                    AND table_name NOT IN (
                        'prep_template', 'prep_template_sample')
                GROUP BY table_name"""
    # note that we are looking for those columns with duplicated names in
    # the headers
    TRN.add(sql, [tuple(
        set(PrepTemplate.metadata_headers()) &
        set(SampleTemplate.metadata_headers()))])
    overlapping = dict(TRN.execute_fetchindex())

# finding actual duplicates
for table_name, cols in viewitems(overlapping):
    # leaving print so when we patch in the main system we know that
    # nothing was renamed or deal with that
    print table_name
    with TRN:
        for c in cols:
            sql = 'ALTER TABLE qiita.%s RENAME COLUMN %s TO %s_renamed' % (
                table_name, c, c)
            TRN.add(sql)
        TRN.execute()
