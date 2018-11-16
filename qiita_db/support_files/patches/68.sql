-- November 16th, 2018
-- moving from relational to key, value pairs

-- First, sample template
DO $do$
DECLARE
    dyn_t varchar;
    dyn_table varchar;
    dyn_table_bk varchar;
    cname varchar;
BEGIN
  FOR dyn_t IN
      SELECT DISTINCT table_name
      FROM information_schema.columns
      WHERE SUBSTR(table_name, 1, 7) = 'sample_'
          AND table_schema = 'qiita'
          AND table_name != 'sample_template_filepath'
  LOOP
    dyn_table := 'qiita.' || dyn_t;
    dyn_table_bk := dyn_t || '_bk';

    -- EVAL : we need to check if removing indexes before renaming will improve speed
    -- rename the tables so we can move the data later
    EXECUTE 'ALTER TABLE ' || dyn_table || ' RENAME TO ' || dyn_table_bk;

    -- create the new table, note that there are no constraints so the
    -- inserts go fast but we will add them later
    EXECUTE 'CREATE TABLE ' || dyn_table || '(sample_id VARCHAR NOT NULL, column_name VARCHAR NOT NULL, column_value VARCHAR);';

    -- inserting value per value of the table, this might take forever
    FOR cname IN
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = 'qiita'
        AND table_name = dyn_table_bk
        AND column_name != 'sample_id'
    LOOP
      EXECUTE 'INSERT INTO ' || dyn_table || ' (sample_id, column_name, column_value) SELECT sample_id, ''' || cname || ''', ' || cname || ' FROM qiita.' || dyn_table_bk || ';';
    END LOOP;

    -- adding index
    EXECUTE 'CREATE INDEX ' || dyn_t || '_idx ON ' || dyn_table || ' (sample_id, column_name)';

    -- TOADD: remove old table
  END LOOP;
END $do$;

-- Now, let's move the data for the prep templates
DO $do$
DECLARE
    dyn_t varchar;
    dyn_table varchar;
    dyn_table_bk varchar;
    cname varchar;
BEGIN
  FOR dyn_t IN
    SELECT DISTINCT table_name
    FROM information_schema.columns
    WHERE SUBSTR(table_name, 1, 5) = 'prep_'
        AND table_schema = 'qiita'
        AND table_name NOT IN ('prep_template',
                               'prep_template_preprocessed_data',
                               'prep_template_filepath',
                               'prep_columns',
                               'prep_template_processing_job',
                               'prep_template_sample')
  LOOP
    dyn_table := 'qiita.' || dyn_t;
    dyn_table_bk := dyn_t || '_bk';

    -- EVAL : we need to check if removing indexes before renaming will improve speed
    -- rename the tables so we can move the data later
    EXECUTE 'ALTER TABLE ' || dyn_table || ' RENAME TO ' || dyn_table_bk;

    -- create the new table, note that there are no constraints so the
    -- inserts go fast but we will add them later
    EXECUTE 'CREATE TABLE ' || dyn_table || '(sample_id VARCHAR NOT NULL, column_name VARCHAR NOT NULL, column_value VARCHAR);';

    -- inserting value per value of the table, this might take forever
    FOR cname IN
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = 'qiita'
        AND table_name = dyn_table_bk
        AND column_name != 'sample_id'
    LOOP
      EXECUTE 'INSERT INTO ' || dyn_table || ' (sample_id, column_name, column_value) SELECT sample_id, ''' || cname || ''', ' || cname || ' FROM qiita.' || dyn_table_bk || ';';
    END LOOP;

    -- adding index
    EXECUTE 'CREATE INDEX ' || dyn_t || '_idx ON ' || dyn_table || ' (sample_id, column_name)';

    -- TOADD: remove old table
  END LOOP;
END $do$;
