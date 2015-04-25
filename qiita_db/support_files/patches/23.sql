-- Apr 16, 2015
-- This patch relaxes the sample template metadata constraints on the database,
-- so from now on they're going to be enforced by code, except
-- required_sample_info_status which is completely deprecated

DO $do$
DECLARE
    dyn_t varchar;
    dyn_table varchar;
    st_id bigint;
BEGIN

-- First, sample template
FOR dyn_t IN
    SELECT DISTINCT table_name
    FROM information_schema.columns
    WHERE SUBSTR(table_name, 1, 7) = 'sample_'
        AND table_schema = 'qiita'
        AND table_name != 'sample_template_filepath'
LOOP
    st_id := SUBSTR(dyn_t, 8)::int;
    dyn_table := 'qiita.' || dyn_t;

    -- Add the new columns to the study_sample_columns table
    INSERT INTO qiita.study_sample_columns (study_id, column_name, column_type)
        VALUES (st_id, 'physical_specimen_location', 'varchar'),
               (st_id, 'physical_specimen_remaining', 'bool'),
               (st_id, 'dna_extracted', 'bool'),
               (st_id, 'sample_type', 'varchar'),
               (st_id, 'collection_timestamp', 'timestamp'),
               (st_id, 'host_subject_id', 'varchar'),
               (st_id, 'description', 'varchar'),
               (st_id, 'latitude', 'float8'),
               (st_id, 'longitude', 'float8'),
               (st_id, 'required_sample_info_status', 'varchar');

    -- Add the new columns to the dynamic table
    EXECUTE 'ALTER TABLE ' || dyn_table || '
                ADD COLUMN physical_specimen_location varchar, 
                ADD COLUMN physical_specimen_remaining boolean, 
                ADD COLUMN dna_extracted boolean, 
                ADD COLUMN sample_type varchar, 
                ADD COLUMN collection_timestamp timestamp, 
                ADD COLUMN host_subject_id varchar, 
                ADD COLUMN description varchar, 
                ADD COLUMN latitude float8, 
                ADD COLUMN longitude float8, 
                ADD COLUMN required_sample_info_status varchar;';

    -- Copy the values from the required_sample_info table to the dynamic table
    EXECUTE '
        WITH sv AS (SELECT * FROM qiita.required_sample_info
                    JOIN qiita.required_sample_info_status
                        USING (required_sample_info_status_id)
                    WHERE study_id = ' || st_id || ')
        UPDATE ' || dyn_table || '
            SET physical_specimen_location=sv.physical_location,
                physical_specimen_remaining=sv.has_physical_specimen,
                dna_extracted=sv.has_extracted_data,
                sample_type=sv.sample_type,
                collection_timestamp=sv.collection_timestamp,
                host_subject_id=sv.host_subject_id,
                description=sv.description,
                latitude=sv.latitude,
                longitude=sv.longitude,
                required_sample_info_status=sv.status
            FROM sv
            WHERE ' || dyn_table || '.sample_id = sv.sample_id;';

END LOOP;
END $do$;

-- We can now drop the columns in the required_sample_info_table
ALTER TABLE qiita.required_sample_info
    DROP COLUMN physical_location,
    DROP COLUMN has_physical_specimen,
    DROP COLUMN has_extracted_data,
    DROP COLUMN sample_type,
    DROP COLUMN required_sample_info_status_id,
    DROP COLUMN collection_timestamp,
    DROP COLUMN host_subject_id,
    DROP COLUMN description,
    DROP COLUMN latitude,
    DROP COLUMN longitude;

-- Since that table no longer stores required metadata,
-- we will rename it
ALTER TABLE qiita.required_sample_info RENAME TO study_sample;

-- The table required_sample_info_status_id is no longer needed
DROP TABLE qiita.required_sample_info_status;

-- Now, let's move the data for the prep templates
DO $do$
DECLARE
    dyn_t varchar;
    dyn_table varchar;
    prep_id bigint;
BEGIN
FOR dyn_t IN
    SELECT DISTINCT table_name
    FROM information_schema.columns
    WHERE SUBSTR(table_name, 1, 5) = 'prep_'
        AND table_schema = 'qiita'
        AND table_name NOT IN ('prep_template',
                               'prep_template_preprocessed_data',
                               'prep_template_filepath',
                               'prep_columns')
LOOP
    prep_id := SUBSTR(dyn_t, 6)::int;
    dyn_table := 'qiita.' || dyn_t;

    -- Add the new columns to the prep_template_columns table
    INSERT INTO qiita.prep_columns (prep_template_id, column_name, column_type)
        VALUES (prep_id, 'center_name', 'varchar'),
               (prep_id, 'center_project_name', 'varchar'),
               (prep_id, 'emp_status', 'varchar');

    -- Add the new columns to the dynamic table
    EXECUTE 'ALTER TABLE ' || dyn_table || '
                ADD COLUMN center_name varchar,
                ADD COLUMN center_project_name varchar,
                ADD COLUMN emp_status varchar;';

    -- Copy the values from the common_prep_info table to the dynamic table
    EXECUTE '
        WITH sv AS (SELECT * FROM qiita.common_prep_info
                        JOIN qiita.emp_status USING (emp_status_id)
                    WHERE prep_template_id = ' || prep_id || ')
        UPDATE ' || dyn_table || '
            SET center_name=sv.center_name,
                center_project_name=sv.center_project_name,
                emp_status=sv.emp_status
            FROM sv
            WHERE ' || dyn_table || '.sample_id=sv.sample_id;';

END LOOP;
END $do$;

-- We can now drop the columns in the required_sample_info_table
ALTER TABLE qiita.common_prep_info
    DROP COLUMN center_name,
    DROP COLUMN center_project_name,
    DROP COLUMN emp_status_id;

-- Since that table no longer stores common metadata, we will rename it
ALTER TABLE qiita.common_prep_info RENAME to prep_template_sample;

-- The table emp_status is no longer needed
DROP TABLE qiita.emp_status;