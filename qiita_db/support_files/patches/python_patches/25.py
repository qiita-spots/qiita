# May 19, 2015
# We attach the prep template directly to the study. The raw data is no longer
# attached to the study directly, the prep template points to them. This will
# make the RawData to be effectively just a container for the raw files,
# which is how it was acting previously.

from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.data import RawData
from qiita_db.util import move_filepaths_to_upload_folder

conn_handler = SQLConnectionHandler()
queue = "PATCH_25"
conn_handler.create_queue(queue)

# the system may contain raw data with no prep template associated to it.
# Retrieve all those raw data ids
sql = """SELECT raw_data_id
         FROM qiita.raw_data
         WHERE raw_data_id NOT IN (
            SELECT DISTINCT raw_data_id FROM qiita.prep_template);"""
rd_ids = [x[0] for x in conn_handler.execute_fetchall(sql)]

# We will delete those RawData. However, if they have files attached, we should
# move them to the uploads folder of the study
sql_detach = """DELETE FROM qiita.study_raw_data
                WHERE raw_data_id = %s AND study_id = %s"""
sql_unlink = "DELETE FROM qiita.raw_filepath WHERE raw_data_id = %s"
sql_delete = "DELETE FROM qiita.raw_data WHERE raw_data_id = %s"
move_files = []
for rd_id in rd_ids:
    rd = RawData(rd_id)
    filepaths = rd.get_filepaths()
    studies = sorted(rd.studies)
    if filepaths:
        # we need to move the files to a study. We chose the one with lower
        # study id. Currently there is no case in the live database in which a
        # RawData with no prep templates is attached to more than one study,
        # but I think it is better to normalize this just in case
        move_files.append((min(studies), filepaths))

    # To delete the RawData we first need to unlink all the files
    conn_handler.add_to_queue(queue, sql_unlink, (rd_id,))

    # Then, remove the raw data from all the studies
    for st_id in studies:
        conn_handler.add_to_queue(queue, sql_detach, (rd_id, st_id))

    conn_handler.add_to_queue(queue, sql_delete, (rd_id,))

# We can now perform all changes in the DB. Although this changes can be
# done in an SQL patch, they are done here because we need to execute the
# previous clean up in the database before we can actually execute the SQL
# patch.
sql = """CREATE TABLE qiita.study_prep_template (
    study_id             bigint  NOT NULL,
    prep_template_id     bigint  NOT NULL,
    CONSTRAINT idx_study_prep_template
        PRIMARY KEY ( study_id, prep_template_id )
 );

CREATE INDEX idx_study_prep_template_0
    ON qiita.study_prep_template ( study_id );

CREATE INDEX idx_study_prep_template_1
    ON qiita.study_prep_template ( prep_template_id );

COMMENT ON TABLE qiita.study_prep_template IS
    'links study to its prep templates';

ALTER TABLE qiita.study_prep_template
    ADD CONSTRAINT fk_study_prep_template_study
    FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id );

ALTER TABLE qiita.study_prep_template
    ADD CONSTRAINT fk_study_prep_template_pt
    FOREIGN KEY ( prep_template_id )
    REFERENCES qiita.prep_template( prep_template_id );

-- Connect the existing prep templates in the system with their studies
DO $do$
DECLARE
    vals RECORD;
BEGIN
FOR vals IN
    SELECT prep_template_id, study_id
    FROM qiita.prep_template
    JOIN qiita.study_raw_data USING (raw_data_id)
LOOP
    INSERT INTO qiita.study_prep_template (study_id, prep_template_id)
    VALUES (vals.study_id, vals.prep_template_id);
END LOOP;
END $do$;

--- Drop the study_raw__data table as it's not longer used
DROP TABLE qiita.study_raw_data;

-- The raw_data_id column now can be nullable
ALTER TABLE qiita.prep_template
    ALTER COLUMN raw_data_id DROP NOT NULL;
"""
conn_handler.add_to_queue(queue, sql)
conn_handler.execute_queue(queue)

# After the changes in the database have been performed, move the files
# to the uploads folder
errors = []
for st_id, fps in move_files:
    try:
        move_filepaths_to_upload_folder(st_id, fps)
    except Exception, e:
        # An error here is unlikely. However, it's possible and there is no
        # clean way that we can unroll all the previous changes in the DB.
        errors.append((st_id, fps, str(e)))

# Show the user any error that could have been generated during the files
# movement
if errors:
    print ("The following errors where generated when trying to move files "
           "to the upload folder")
    for st_id, fps, e in errors:
        print "Study: %d, Filepaths: %s, Error: %s" % (st_id, fps, e)
