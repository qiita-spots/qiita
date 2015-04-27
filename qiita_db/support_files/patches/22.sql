-- April 16, 2015
-- Add primary key to analysis_sample table, first deleting the duplicates
-- http://stackoverflow.com/a/9862688
DO $do$
BEGIN
    CREATE TEMP TABLE temp_table
    ON COMMIT drop AS
        SELECT analysis_id, processed_data_id, sample_id
        FROM qiita.analysis_sample GROUP BY analysis_id, processed_data_id, sample_id;
    DELETE FROM qiita.analysis_sample;
    INSERT INTO qiita.analysis_sample (analysis_id, processed_data_id, sample_id) SELECT analysis_id, processed_data_id, sample_id FROM temp_table;

    ALTER TABLE qiita.analysis_sample ADD CONSTRAINT pk_analysis_sample PRIMARY KEY ( analysis_id, processed_data_id, sample_id );
END $do$