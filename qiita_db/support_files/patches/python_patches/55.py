# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_db.sql_connection import TRN

sql = """
    SELECT constraint_name AS cname, 'qiita.' || table_name AS tname
    FROM information_schema.table_constraints
    WHERE constraint_type ='FOREIGN KEY' AND (
        (constraint_name LIKE 'fk_sample_%' AND table_name LIKE 'sample_%') OR
        (constraint_name LIKE 'fk_prep_%' AND table_name LIKE 'prep_%')) AND
        table_name NOT IN (
            'prep_template', 'prep_template_sample', 'prep_template_filepath',
            'prep_template_processing_job')"""

with TRN:
    TRN.add(sql)
    to_delete = TRN.execute_fetchindex()

for cname, tname in to_delete:
    with TRN:
        sql = "ALTER TABLE %s DROP CONSTRAINT %s" % (tname, cname)
        TRN.add(sql)
        TRN.execute()
