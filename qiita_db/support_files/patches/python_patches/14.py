# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# Feberuary 7, 2015
# This patch recreates all the QIIME mapping files to avoid lower/upper case
# problems. See https://github.com/biocore/qiita/issues/799
#
# heavily based on 7.py

from os.path import basename

import qiita_db as qdb

with qdb.sql_connection.TRN:
    sql = "SELECT prep_template_id FROM qiita.prep_template"
    qdb.sql_connection.TRN.add(sql)
    all_ids = qdb.sql_connection.TRN.execute_fetchflatten()

    # remove all the bad mapping files
    for prep_template_id in all_ids:
        pt = qdb.metadata_template.prep_template.PrepTemplate(prep_template_id)
        fps = pt.get_filepaths()

        # get the QIIME mapping file, note that the way to figure out what is
        # and what's not a qiime mapping file is to check for the existance of
        # the word qiime in the basename of the file path, hacky but that's
        # the way it is being done in qiita_pet/uimodules/raw_data_tab.py
        mapping_files = [f for f in fps if '_qiime_' in basename(f[1])]

        table = 'prep_template_filepath'
        column = 'prep_template_id'

        # unlink all the qiime mapping files for this prep template object
        for mf in mapping_files:

            # (1) get the ids that we are going to delete.
            # because of the FK restriction, we cannot just delete the ids
            sql = """SELECT filepath_id
                     FROM qiita.{0}
                     WHERE {1}=%s AND filepath_id=%s""".format(table, column)
            qdb.sql_connection.TRN.add(sql, [pt.id, mf[0]])
            ids = qdb.sql_connection.TRN.execute_fetchflatten()

            # (2) delete the entries from the prep_template_filepath table
            sql = """DELETE FROM qiita.{0}
                     WHERE {1}=%s and filepath_id=%s""".format(table, column)
            qdb.sql_connection.TRN.add(sql, [pt.id, mf[0]])

            # (3) delete the entries from the filepath table
            sql = "DELETE FROM qiita.filepath WHERE filepath_id IN %s"
            qdb.sql_connection.TRN.add(sql, [tuple(ids)])

    qdb.sql_connection.TRN.execute()

    # create correct versions of the mapping files
    for prep_template_id in all_ids:

        prep_template_id = prep_template_id[0]
        pt = qdb.metadata_template.prep_template.PrepTemplate(prep_template_id)

        # we can guarantee that all the filepaths will be prep templates so
        # we can just generate the qiime mapping files
        for _, fpt in pt.get_filepaths():
            pt.create_qiime_mapping_file(fpt)
