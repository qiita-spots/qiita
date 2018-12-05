-- November 21, 2018
-- moving sample and prep info files to jsonb

-- 3/3 This is the continuation of the patching that started in 68.sql, let's
-- move the data for the prep templates but now for prep ids >= 3500
DO $do$
DECLARE
    dyn_t varchar;
    dyn_table varchar;
    dyn_table_bk varchar;
    sid varchar;
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
        AND table_name NOT LIKE '%_bk'
        AND SUBSTR(table_name, 6)::INT >= 3500
  LOOP
    dyn_table := 'qiita.' || dyn_t;
    dyn_table_bk := dyn_t || '_bk';

    -- rename the tables so we can move the data later
    EXECUTE format('ALTER TABLE %1$s RENAME TO %2$s', dyn_table, dyn_table_bk);

    -- create the new table, note that there are no constraints so the
    -- inserts go fast but we will add them later
    EXECUTE format('CREATE TABLE %1$s (sample_id VARCHAR NOT NULL, sample_values JSONB)', dyn_table);

    -- inserting our helper column qiita_sample_column_names, which is going keep all our columns; this is much easier than trying to keep all rows with the same values
    EXECUTE 'INSERT INTO ' || dyn_table || ' (sample_id, sample_values) VALUES (''qiita_sample_column_names'',  (''{"columns":'' || (SELECT json_agg(column_name::text) FROM information_schema.columns WHERE table_name=''' || dyn_table_bk || ''' AND table_schema=''qiita'' AND column_name != ''sample_id'')::text || ''}'')::json);';

    -- inserting value per value of the table, this might take forever
    FOR sid IN
      EXECUTE 'SELECT sample_id FROM qiita.' || dyn_table_bk
    LOOP
      EXECUTE 'INSERT INTO ' || dyn_table || ' (sample_id, sample_values) VALUES (''' || sid || ''',  (SELECT row_to_json(t)::jsonb - ''sample_id'' FROM (SELECT * FROM qiita.' || dyn_table_bk || ' WHERE sample_id = ''' || sid || ''') t));';
    END LOOP;

    -- adding index
    EXECUTE 'ALTER TABLE ' || dyn_table || ' ADD CONSTRAINT pk_jsonb_' || dyn_t || ' PRIMARY KEY ( sample_id );';
  END LOOP;
END $do$;

-- Dropping all the _bk tables
DO $do$
DECLARE
    dyn_table varchar;
BEGIN
  FOR dyn_table IN
    SELECT DISTINCT table_name
    FROM information_schema.columns
    WHERE table_name LIKE '%_bk'
  LOOP
    EXECUTE 'DROP TABLE qiita.' || dyn_table;
  END LOOP;
END $do$;
