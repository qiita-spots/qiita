# Feberuary 7, 2015
# This patch recreates all the QIIME mapping files to avoid lower/upper case
# problems. See https://github.com/biocore/qiita/issues/799
#
# heavily based on 7.py

from os.path import basename

from qiita_db.util import get_mountpoint
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.metadata_template import PrepTemplate

conn_handler = SQLConnectionHandler()

_id, fp_base = get_mountpoint('templates')[0]

sql = "SELECT prep_template_id FROM qiita.prep_template"
for prep_template_id in conn_handler.execute_fetchall(sql):

    prep_template_id = prep_template_id[0]
    pt = PrepTemplate(prep_template_id)
    fps = pt.get_filepaths()

    # get the QIIME mapping file, note that the way to figure out what is and
    # what's not a qiime mapping file is to check for the existance of the
    # word qiime in the basename of the file path, hacky but that's the way
    # it is being done in qiita_pet/uimodules/raw_data_tab.py
    mapping_files = [f for f in fps if '_qiime_' in basename(f[1])]

    table = 'prep_template_filepath'
    column = 'prep_template_id'

    # unlink all the qiime mapping files for this prep template object
    for mf in mapping_files:
        q_name = 'queue-for-mapping-file-%d' % mf[0]
        conn_handler.create_queue(q_name)

        # (1) get the ids that we are going to delete.
        # because of the FK restriction, we cannot just delete the ids
        ids = conn_handler.execute_fetchall(
            'SELECT filepath_id FROM qiita.{0} WHERE '
            '{1}=%s and filepath_id=%s'.format(table, column), (pt.id, mf[0]))
        ids = sum(ids, [])

        # (2) delete the entries from the prep_template_filepath table
        conn_handler.add_to_queue(
            q_name, "DELETE FROM qiita.{0} "
            "WHERE {1}=%s and filepath_id=%s;".format(table, column),
            (pt.id, mf[0]))

        # (3) delete the entries from the filepath table
        conn_handler.add_to_queue(
            q_name,
            "DELETE FROM qiita.filepath WHERE "
            "filepath_id IN ({0});".format(', '.join(map(str, ids))))

        try:
            conn_handler.execute_queue(q_name)
        except Exception as e:
            print 'exception happened while processing file "%d"-"%s"' % mf
            raise

    # we can guarantee that all the filepaths will be prep templates so
    # we can just generate the qiime mapping files
    for _, fpt in pt.get_filepaths():
        pt.create_qiime_mapping_file(fpt)
